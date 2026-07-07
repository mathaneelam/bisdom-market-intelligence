from datetime import date
import logging
import os
import urllib.parse
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.content_piece import ContentPiece
from app.models.pattern import Pattern
from app.models.signal import Signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-pieces", tags=["content"])


# Every generated image shares this brand thread so all 7 platform images read
# as one Bisdom family. "no text, no letters" matters: image models garble any
# words they try to draw — the copy lives in the caption, the image carries mood.
_BRAND_THREAD = (
    "Bisdom B2B commerce brand aesthetic, subtle blue accent color, clean modern "
    "professional, Indian textile and garment manufacturing business context, "
    "no text, no words, no letters, no logos, high quality"
)

# One "style card" per platform: the mood phrase appended to the image_brief, plus
# the output dimensions that match how that platform actually shows an image.
# Tweak the phrases freely — this is the single place platform look & feel lives.
FORMAT_IMAGE_STYLE = {
    "linkedin":         {"style": "clean corporate infographic style, professional muted palette, data-driven business visual, flat minimal illustration", "width": 1200, "height": 628},
    "linkedin_article": {"style": "editorial thought-leadership cover illustration, sophisticated muted tones, professional banner", "width": 1200, "height": 628},
    "instagram_post":   {"style": "vibrant bold scroll-stopping poster, high contrast saturated colors, trendy modern social media graphic, eye-catching", "width": 1024, "height": 1024},
    "instagram_reel":   {"style": "dynamic energetic vertical reel cover, bold vibrant colors, sense of motion, trendy thumbnail", "width": 1024, "height": 1792},
    "whatsapp":         {"style": "simple clear friendly graphic, warm approachable, uncluttered, mobile-first", "width": 1024, "height": 1024},
    "email":            {"style": "clean professional newsletter header banner, warm inviting marketing hero", "width": 1200, "height": 628},
    "blog":             {"style": "editorial magazine-quality hero banner illustration, wide cinematic, thoughtful storytelling visual", "width": 1200, "height": 675},
}
# Fallback for any legacy/unknown format so generation never hard-fails.
_DEFAULT_STYLE = {"style": "clean modern professional business illustration", "width": 1024, "height": 1024}


class ContentPieceUpdate(BaseModel):
    status: str | None = None   # draft | approved | posted | rejected
    body: str | None = None
    title: str | None = None


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
async def generate_image(content_id: str, db: AsyncSession = Depends(get_db)):
    """Call Pollinations.ai API using the image brief to generate and save an image."""
    cp = await db.get(ContentPiece, content_id)
    if not cp:
        raise HTTPException(404, "Content piece not found")
    if not cp.image_brief:
        raise HTTPException(400, "Content piece has no image brief")

    style = FORMAT_IMAGE_STYLE.get(cp.format, _DEFAULT_STYLE)
    full_prompt = f"{cp.image_brief}. {style['style']}. {_BRAND_THREAD}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={style['width']}&height={style['height']}&nologo=true"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            if response.status_code != 200:
                logger.error("Pollinations API returned error %d: %s", response.status_code, response.text)
                raise HTTPException(502, f"Free image generation service error: {response.text}")

            image_bytes = response.content

            cp.image_bytes = image_bytes
            await db.commit()

            logger.info("Successfully generated image for content piece %s", cp.id)
            return {"status": "ok", "image_url": f"/content-pieces/{cp.id}/image"}

    except httpx.HTTPError as e:
        logger.error("HTTP error calling Pollinations API: %s", e)
        raise HTTPException(502, f"HTTP error talking to free image generation service: {str(e)}")
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
