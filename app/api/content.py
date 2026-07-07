from datetime import date
import logging
import os
import base64
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.base import get_db
from app.models.content_piece import ContentPiece
from app.models.pattern import Pattern
from app.models.signal import Signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-pieces", tags=["content"])


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

    api_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(api_dir)
    static_dir = os.path.join(app_dir, "static")

    result = []
    for cp, pattern_name in rows:
        image_filename = f"{cp.id}.png"
        image_exists = os.path.exists(os.path.join(static_dir, image_filename))
        image_url = f"/static/{image_filename}" if image_exists else None

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

    api_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(api_dir)
    static_dir = os.path.join(app_dir, "static")
    image_filename = f"{cp.id}.png"
    image_exists = os.path.exists(os.path.join(static_dir, image_filename))
    image_url = f"/static/{image_filename}" if image_exists else None

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
    if update.body is not None:
        cp.body = update.body
    if update.title is not None:
        cp.title = update.title

    await db.commit()
    return {"status": "ok", "id": str(cp.id)}


@router.post("/{content_id}/generate-image")
async def generate_image(content_id: str, db: AsyncSession = Depends(get_db)):
    """Call Google's Imagen 3 API using the image brief to generate and save an image."""
    cp = await db.get(ContentPiece, content_id)
    if not cp:
        raise HTTPException(404, "Content piece not found")
    if not cp.image_brief:
        raise HTTPException(400, "Content piece has no image brief")
    if not settings.GEMINI_API_KEY:
        raise HTTPException(400, "GEMINI_API_KEY is not configured in environment")

    # Define paths
    api_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(api_dir)
    static_dir = os.path.join(app_dir, "static")
    image_filename = f"{cp.id}.png"
    image_path = os.path.join(static_dir, image_filename)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:predict?key={settings.GEMINI_API_KEY}"
    payload = {
        "instances": [{"prompt": cp.image_brief}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "outputMimeType": "image/png"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            if response.status_code != 200:
                logger.error("Imagen API returned error %d: %s", response.status_code, response.text)
                raise HTTPException(502, f"Google AI API error: {response.text}")

            data = response.json()
            predictions = data.get("predictions", [])
            if not predictions or "bytesBase64Encoded" not in predictions[0]:
                logger.error("Invalid Imagen API response structure: %s", data)
                raise HTTPException(502, "Invalid image generation response from Google AI API")

            base64_image = predictions[0]["bytesBase64Encoded"]
            image_bytes = base64.b64decode(base64_image)

            # Ensure directory exists and write file
            os.makedirs(static_dir, exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(image_bytes)

            logger.info("Successfully generated image for content piece %s", cp.id)
            return {"status": "ok", "image_url": f"/static/{image_filename}"}

    except httpx.HTTPError as e:
        logger.error("HTTP error calling Google AI API: %s", e)
        raise HTTPException(502, f"HTTP error talking to Google AI API: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error in image generation: %s", e)
        raise HTTPException(500, f"Error processing image generation: {str(e)}")
