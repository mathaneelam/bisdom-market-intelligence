from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.brief import Brief

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("/today")
async def get_today_brief(db: AsyncSession = Depends(get_db)):
    """Returns today's brief, or a clear message if none has been generated yet."""
    today = datetime.utcnow().date()
    brief = (
        await db.execute(select(Brief).where(Brief.brief_date == today))
    ).scalars().first()

    if not brief:
        return {"message": "No brief generated yet for today", "brief": None}

    return {
        "message": "ok",
        "brief": {
            "id": str(brief.id),
            "brief_date": brief.brief_date,
            "pain_pulse": brief.pain_pulse,
            "competitor_move": brief.competitor_move,
            "opportunity": brief.opportunity,
            "delivered_email": brief.delivered_email,
            "delivered_tg": brief.delivered_tg,
            "delivered_wa": brief.delivered_wa,
            "created_at": brief.created_at,
        },
    }


@router.get("")
async def list_briefs(db: AsyncSession = Depends(get_db)):
    """Last 30 briefs, newest first (metadata only, no HTML)."""
    briefs = (
        await db.execute(select(Brief).order_by(Brief.brief_date.desc()).limit(30))
    ).scalars().all()

    return [
        {
            "id": str(b.id),
            "brief_date": b.brief_date,
            "delivered_email": b.delivered_email,
            "delivered_tg": b.delivered_tg,
            "delivered_wa": b.delivered_wa,
            "created_at": b.created_at,
        }
        for b in briefs
    ]
