from datetime import date
import logging
import re
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.content_piece import ContentPiece
from app.models.pattern import Pattern
from app.models.signal import Signal
from app.config import settings
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-pieces", tags=["content"])


# ── Image generation: the "compiler" ─────────────────────────────────────────
# We don't hand the model mood words ("premium", "trustworthy") — it can't paint
# concepts, only pixels at positions, and guesses abstractions badly. Instead
# `_build_image_prompt` compiles each content piece into ONE concrete prompt where
# every idea is an exact hex colour, an explicit position, a short quoted string, or
# an exclusion. Division of labour: THIS file owns the fixed scaffold (canvas, palette,
# wordmark, style-lock, exclusions); the writer (gemma4) supplies only two variables
# per piece inside `image_brief` — one literal focal object + an OPTIONAL on-image
# phrase of <=4 words. Verified on gemini-3.1-flash-image: short quoted strings render
# reliably, full sentences garble — so long text is capped out here and set in Canva.
NAVY = "#0a1628"       # background
BLUE = "#1889f6"       # the single accent
OFFWHITE = "#ebebeb"   # text / highlights

# Per-format canvas only: orientation label + the three Gemini-safe sizes (1792x1024
# wide, 1024x1024 square, 1024x1792 tall) that match the frontend preview box aspect
# exactly with no cropping. Deliberately no mood words — the formula carries the look.
FORMAT_IMAGE_STYLE = {
    "linkedin":         {"orientation": "Wide",              "width": 1792, "height": 1024},
    "linkedin_article": {"orientation": "Wide",              "width": 1792, "height": 1024},
    "instagram_post":   {"orientation": "Square",            "width": 1024, "height": 1024},
    "instagram_reel":   {"orientation": "Vertical portrait", "width": 1024, "height": 1792},
    "whatsapp":         {"orientation": "Square",            "width": 1024, "height": 1024},
    "email":            {"orientation": "Wide",              "width": 1792, "height": 1024},
    "blog":             {"orientation": "Wide",              "width": 1792, "height": 1024},
}
# Fallback for any legacy/unknown format so generation never hard-fails.
_DEFAULT_STYLE = {"orientation": "Square", "width": 1024, "height": 1024}


def _parse_brief(brief: str | None) -> tuple[str, str | None]:
    """Split the writer's Image line into (focal object, short on-image text).

    The writer emits: `<one literal object> On-image text: "<=4 words"` (or
    `On-image text: none`). We keep the quoted phrase ONLY when it's short — anything
    over 4 words would garble on the model, so we drop it (it belongs on a Canva
    headline layer, not baked into pixels). Legacy briefs with no marker fall back to
    a pure object scene with no overlay text.
    """
    brief = (brief or "").strip()
    marker = re.search(r"on-image text:\s*(.*)$", brief, re.IGNORECASE | re.DOTALL)
    if not marker:
        return brief, None
    obj = brief[:marker.start()].strip().rstrip(".").strip()
    phrase = marker.group(1).strip().strip('"').strip("'").strip()
    if not phrase or phrase.lower() in ("none", "no text", "n/a") or len(phrase.split()) > 4:
        phrase = None
    return (obj or brief), phrase


def _build_image_prompt(cp) -> tuple[str, dict]:
    """Compile a content piece into one concrete, formula-shaped image prompt."""
    style = FORMAT_IMAGE_STYLE.get(cp.format, _DEFAULT_STYLE)
    obj, phrase = _parse_brief(cp.image_brief)

    parts = [
        f"{style['orientation']} poster, {style['width']}x{style['height']}px. "
        f"Solid {NAVY} background, flat color, no gradient.",
        f"Centered, a single flat vector motif: {obj}. Drawn in {BLUE} with "
        f"{OFFWHITE} details, generous empty space around it.",
    ]
    if phrase:
        parts.append(
            f'In the upper third, centered, bold geometric sans-serif text in '
            f'{OFFWHITE}, reads exactly: "{phrase}".'
        )
    parts.append(f'In the top-left corner, small text reads exactly: "bisdom" in {BLUE}.')
    parts.append(
        "Flat design, solid colors only, high contrast, generous empty space, "
        "rounded corners on all shapes."
    )
    parts.append(
        "No photorealistic elements, no additional icons, no illustrations beyond what "
        "is described above, no extra text, no gradients, no drop shadows, no clutter."
    )
    return " ".join(parts), style


class ContentPieceUpdate(BaseModel):
    status: str | None = None   # draft | approved | posted | rejected
    body: str | None = None
    title: str | None = None


class GenerateImageRequest(BaseModel):
    model: str | None = None


@router.get("")
async def list_content_pieces(
    audience: str | None = Query(None, description="buyer | supplier"),
    format: str | None = Query(None, description="linkedin | linkedin_article | instagram_post | instagram_reel | whatsapp | email | blog"),
    tone: str | None = Query(None, description="educational | contrast"),
    status: str | None = Query(None, description="draft | approved | posted | rejected"),
    pattern_id: str | None = Query(None),
    scheduled_date_from: date | None = Query(None, description="Calendar view: start of date range (inclusive)"),
    scheduled_date_to: date | None = Query(None, description="Calendar view: end of date range (inclusive)"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Paginated content pieces, newest first, with the pattern name they came from."""
    stmt = (
        select(ContentPiece, Pattern.name)
        .outerjoin(Pattern, Pattern.id == ContentPiece.pattern_id)
        .order_by(ContentPiece.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if audience:
        stmt = stmt.where(ContentPiece.audience == audience)
    if format:
        stmt = stmt.where(ContentPiece.format == format)
    if tone:
        stmt = stmt.where(ContentPiece.tone == tone)
    if status:
        stmt = stmt.where(ContentPiece.status == status)
    if pattern_id:
        stmt = stmt.where(ContentPiece.pattern_id == pattern_id)
    if scheduled_date_from:
        stmt = stmt.where(ContentPiece.scheduled_date >= scheduled_date_from)
    if scheduled_date_to:
        stmt = stmt.where(ContentPiece.scheduled_date <= scheduled_date_to)

    rows = (await db.execute(stmt)).all()

    result = []
    for cp, pattern_name in rows:
        image_url = f"/content-pieces/{cp.id}/image" if cp.image_bytes is not None else None

        result.append({
            "id": str(cp.id),
            "pattern_id": str(cp.pattern_id) if cp.pattern_id else None,
            "pattern_name": pattern_name,
            "audience": cp.audience,
            "format": cp.format,
            "tone": cp.tone,
            "title": cp.title,
            "body": cp.body,
            "image_brief": cp.image_brief,
            "image_url": image_url,
            "comment_note": cp.comment_note,
            "scheduled_date": cp.scheduled_date,
            "status": cp.status,
            "receipt_count": len(cp.source_review_ids) if cp.source_review_ids else 0,
            "created_at": cp.created_at,
        })
    return result


@router.get("/{content_id}")
async def get_content_piece(content_id: str, db: AsyncSession = Depends(get_db)):
    """One content piece, with the pattern it came from and the real reviews (receipts) behind it."""
    cp = await db.get(ContentPiece, content_id)
    if not cp:
        raise HTTPException(404, "Content piece not found")

    pattern = await db.get(Pattern, cp.pattern_id) if cp.pattern_id else None

    receipts = []
    if cp.source_review_ids:
        stmt = (
            select(Signal)
            .where(Signal.id.in_(cp.source_review_ids))
            .order_by(Signal.collected_at.desc())
        )
        signals = (await db.execute(stmt)).scalars().all()
        receipts = [
            {
                "id": str(sig.id),
                "source": sig.source,
                "source_url": sig.source_url,
                "author": sig.author,
                "collected_at": sig.collected_at,
                "snippet": (sig.raw_content or "")[:300],
            }
            for sig in signals
        ]

    image_url = f"/content-pieces/{cp.id}/image" if cp.image_bytes is not None else None

    return {
        "id": str(cp.id),
        "pattern_id": str(cp.pattern_id) if cp.pattern_id else None,
        "pattern_name": pattern.name if pattern else None,
        "pattern_description": pattern.description if pattern else None,
        "audience": cp.audience,
        "format": cp.format,
        "tone": cp.tone,
        "title": cp.title,
        "body": cp.body,
        "image_brief": cp.image_brief,
        "image_url": image_url,
        "comment_note": cp.comment_note,
        "scheduled_date": cp.scheduled_date,
        "status": cp.status,
        "model": cp.model,
        "created_at": cp.created_at,
        "receipts": receipts,
    }


@router.patch("/{content_id}")
async def update_content_piece(content_id: str, update: ContentPieceUpdate, db: AsyncSession = Depends(get_db)):
    """Approve, reject, or edit a content piece."""
    cp = await db.get(ContentPiece, content_id)
    if not cp:
        raise HTTPException(404, "Content piece not found")

    if update.status is not None:
        cp.status = update.status
        if update.status == "posted":
            cp.image_bytes = None
    if update.body is not None:
        cp.body = update.body
    if update.title is not None:
        cp.title = update.title

    await db.commit()
    return {"status": "ok", "id": str(cp.id)}


@router.post("/{content_id}/generate-image")
async def generate_image(content_id: str, request: GenerateImageRequest = None, db: AsyncSession = Depends(get_db)):
    """Call OmniRoute (Gemini image model) with the image brief to generate and save an image."""
    cp = await db.get(ContentPiece, content_id)
    if not cp:
        raise HTTPException(404, "Content piece not found")
    if not cp.image_brief:
        raise HTTPException(400, "Content piece has no image brief")

    # Compile the piece into one concrete, formula-shaped prompt (see _build_image_prompt).
    full_prompt, style = _build_image_prompt(cp)

    url = f"{settings.OMNIROUTE_BASE_URL.rstrip('/')}/images/generations"
    headers = {"Content-Type": "application/json"}
    if settings.OMNIROUTE_API_KEY:
        headers["Authorization"] = f"Bearer {settings.OMNIROUTE_API_KEY}"

    payload = {
        "model": request.model if request and request.model else "antigravity/gemini-3.1-flash-image",
        "prompt": full_prompt,
        "n": 1,
        "size": f"{style['width']}x{style['height']}",
        "response_format": "b64_json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if response.status_code != 200:
                logger.error("OmniRoute API returned error %d: %s", response.status_code, response.text)
                raise HTTPException(502, f"OmniRoute image generation service error: {response.text}")

            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                img_data = data["data"][0]
                if "b64_json" in img_data:
                    image_bytes = base64.b64decode(img_data["b64_json"])
                elif "url" in img_data:
                    url_response = await client.get(img_data["url"], timeout=30.0)
                    if url_response.status_code != 200:
                        raise HTTPException(502, "Failed to download image from returned URL")
                    image_bytes = url_response.content
                else:
                    raise HTTPException(502, "Invalid image data format returned from OmniRoute")
            else:
                raise HTTPException(502, f"No image data returned from OmniRoute: {data}")

            cp.image_bytes = image_bytes
            await db.commit()

            logger.info("Successfully generated image for content piece %s", cp.id)
            return {"status": "ok", "image_url": f"/content-pieces/{cp.id}/image"}

    except httpx.HTTPError as e:
        logger.error("HTTP error calling OmniRoute API: %s", e)
        raise HTTPException(502, f"HTTP error talking to OmniRoute image generation service: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error in image generation: %s", e)
        raise HTTPException(500, f"Error processing image generation: {str(e)}")


@router.get("/{content_id}/image")
async def get_content_piece_image(content_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch the image bytes from the cloud database and return as image/png response."""
    cp = await db.get(ContentPiece, content_id)
    if not cp or not cp.image_bytes:
        raise HTTPException(404, "Image not found")
    return Response(content=cp.image_bytes, media_type="image/png")
