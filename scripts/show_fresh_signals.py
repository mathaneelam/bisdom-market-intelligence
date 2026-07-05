import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.models import base as models_base
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal

async def main():
    models_base.init_db(settings.DATABASE_URL)
    async with models_base.AsyncSessionLocal() as session:
        stmt = select(ProcessedSignal, Signal).join(Signal, ProcessedSignal.signal_id == Signal.id)\
            .where(ProcessedSignal.stream == "pain_pulse", ProcessedSignal.relevance_score >= 8)\
            .order_by(ProcessedSignal.processed_at.desc()).limit(10)
            
        result = await session.execute(stmt)
        rows = result.all()
        
        print("="*60)
        print("FRESH PLAY STORE PAIN PULSE SIGNALS IN DATABASE")
        print("="*60)
        
        for idx, (ps, sig) in enumerate(rows, 1):
            # Clean emojis or non-ascii to avoid windows encoding errors
            summary = ps.summary.encode('ascii', 'ignore').decode('ascii')
            insight = ps.insight.encode('ascii', 'ignore').decode('ascii')
            raw_content = sig.raw_content.encode('ascii', 'ignore').decode('ascii')
            author = sig.author.encode('ascii', 'ignore').decode('ascii') if sig.author else "Unknown"
            
            print(f"\n[{idx}] {sig.source.upper()} Complaint")
            print(f"    Relevance Score: {ps.relevance_score}/10")
            print(f"    Summary: {summary}")
            print(f"    Insight: {insight}")
            print(f"    Author: {author}")
            print(f"    Review: \"{raw_content}\"")
            print("-" * 50)
        
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
