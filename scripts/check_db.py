import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.models.base import init_db
from app.models import base as models_base
from app.models.brief import Brief
from sqlalchemy import select

async def main():
    init_db(settings.DATABASE_URL)
    async with models_base.AsyncSessionLocal() as session:
        result = await session.execute(select(Brief))
        briefs = result.scalars().all()
        print("Total Briefs in DB:", len(briefs))
        for b in briefs:
            print(f"Brief ID: {b.id}, Date: {b.brief_date}")
            print(f"Pain Pulse: {len(b.pain_pulse) if b.pain_pulse else 0}")
            print(f"Competitor Move: {len(b.competitor_move) if b.competitor_move else 0}")
            print(f"Opportunity: {len(b.opportunity) if b.opportunity else 0}")

if __name__ == "__main__":
    asyncio.run(main())
