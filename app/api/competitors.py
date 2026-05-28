from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.competitor import Competitor

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    """All active competitors, alphabetically sorted."""
    competitors = (
        await db.execute(
            select(Competitor)
            .where(Competitor.is_active == True)
            .order_by(Competitor.name)
        )
    ).scalars().all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "website": c.website,
            "linkedin_url": c.linkedin_url,
            "play_store_id": c.play_store_id,
            "rss_url": c.rss_url,
            "is_active": c.is_active,
        }
        for c in competitors
    ]
