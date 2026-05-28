from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.trade_show import TradeShow

router = APIRouter(prefix="/trade-shows", tags=["trade_shows"])


@router.get("")
async def list_trade_shows(
    upcoming_only: bool = Query(True, description="Show only upcoming events"),
    db: AsyncSession = Depends(get_db),
):
    """Upcoming trade shows sorted by start date."""
    stmt = select(TradeShow).order_by(TradeShow.start_date)
    if upcoming_only:
        stmt = stmt.where(TradeShow.is_upcoming == True)

    shows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "category": t.category,
            "city": t.city,
            "venue": t.venue,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "website": t.website,
            "relevance_note": t.relevance_note,
            "is_upcoming": t.is_upcoming,
        }
        for t in shows
    ]
