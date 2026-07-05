from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.content_piece import ContentPiece
from app.models.pattern import Pattern
from app.models.signal import Signal

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

    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(cp.id),
            "pattern_id": str(cp.pattern_id) if cp.pattern_id else None,
            "pattern_name": pattern_name,
            "audience": cp.audience,
            "format": cp.format,
            "tone": cp.tone,
            "title": cp.title,
            "body": cp.body,
            "status": cp.status,
            "receipt_count": len(cp.source_review_ids) if cp.source_review_ids else 0,
            "created_at": cp.created_at,
        }
        for cp, pattern_name in rows
    ]


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
