import logging
import asyncio
from datetime import datetime, timedelta, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import base as models_base
from app.models.processed_signal import ProcessedSignal
from app.models.brief import Brief
from app.processors.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

def build_html(brief_date: date, sections: dict) -> str:
    html = f"<html><body style='font-family: Arial, sans-serif;'>"
    html += f"<h2>Bisdom Intelligence Brief - {brief_date}</h2>"
    
    stream_titles = {
        "pain_pulse": "🔴 Pain Pulse (Buyer/Supplier Complaints)",
        "competitor_move": "🔵 Competitor Moves",
        "opportunity_signal": "🟢 Opportunity Signals"
    }
    
    for stream, title in stream_titles.items():
        signals = sections.get(stream, [])
        html += f"<h3>{title}</h3>"
        if not signals:
            html += "<p>No significant signals found today.</p>"
        else:
            html += "<ul>"
            for sig in signals:
                html += f"<li><strong>{sig['summary']}</strong> (Score: {sig['relevance_score']})<br/>"
                html += f"<em>Insight:</em> {sig['insight']}</li>"
            html += "</ul>"
            
    html += "</body></html>"
    return html

class BriefBuilder:
    def __init__(self):
        self.deduplicator = Deduplicator()

    async def run(self) -> Brief | None:
        """
        Builds the daily brief by aggregating top unique signals.
        """
        today = datetime.utcnow().date()
        yesterday_dt = datetime.utcnow() - timedelta(days=1)
        
        logger.info(f"Building intelligence brief for {today}")
        
        # 1. Get duplicate IDs to exclude
        duplicate_ids = await self.deduplicator.run()
        
        async with models_base.AsyncSessionLocal() as session:
            # Check if brief already exists for today
            stmt = select(Brief).where(Brief.brief_date == today)
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                logger.warning(f"Brief for {today} already exists. Deleting it to regenerate.")
                await session.delete(existing)
                await session.commit()
            
            # 2. Fetch processed signals from the last 24h
            stmt = select(ProcessedSignal).where(ProcessedSignal.processed_at >= yesterday_dt)
            result = await session.execute(stmt)
            all_signals = result.scalars().all()
            
            # 3. Filter and sort
            valid_signals = [
                s for s in all_signals 
                if str(s.id) not in duplicate_ids and (s.relevance_score or 0) >= 7
            ]
            
            # Group by stream
            streams = {
                "pain_pulse": [],
                "competitor_move": [],
                "opportunity_signal": []
            }
            
            for s in valid_signals:
                if s.stream in streams:
                    streams[s.stream].append(s)
            
            # Sort by relevance desc and take top 3
            sections = {}
            for stream, signals in streams.items():
                sorted_signals = sorted(signals, key=lambda x: x.relevance_score or 0, reverse=True)[:3]
                sections[stream] = [
                    {
                        "id": str(s.id),
                        "summary": s.summary,
                        "relevance_score": s.relevance_score,
                        "insight": s.insight,
                        "tags": s.tags
                    } for s in sorted_signals
                ]
            
            # 4. Generate HTML
            html_content = build_html(today, sections)
            
            # 5. Create Brief
            brief = Brief(
                brief_date=today,
                pain_pulse=sections.get("pain_pulse"),
                competitor_move=sections.get("competitor_move"),
                opportunity=sections.get("opportunity_signal"),
                full_html=html_content
            )
            
            session.add(brief)
            await session.commit()
            
            logger.info("Successfully built and saved today's brief.")
            return brief

async def run_brief_builder():
    builder = BriefBuilder()
    await builder.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_brief_builder())
