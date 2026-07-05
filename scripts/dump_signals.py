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
        # Get count of all signals
        total_signals = (await session.execute(select(Signal))).scalars().all()
        print(f"Total Signals in DB: {len(total_signals)}")
        
        # Get count of processed signals
        processed_signals = (await session.execute(select(ProcessedSignal))).scalars().all()
        print(f"Total Processed Signals: {len(processed_signals)}")
        
        # Fetch latest 20 processed signals with their raw signals
        stmt = select(ProcessedSignal, Signal).join(Signal, ProcessedSignal.signal_id == Signal.id).order_index = 0
        stmt = select(ProcessedSignal, Signal).join(Signal, ProcessedSignal.signal_id == Signal.id).order_by(ProcessedSignal.processed_at.desc()).limit(20)
        
        result = await session.execute(stmt)
        rows = result.all()
        
        print("\n--- LATEST PROCESSED SIGNALS ---")
        for idx, (ps, sig) in enumerate(rows, 1):
            print(f"\n[{idx}] Stream: {ps.stream.upper()} | Score: {ps.relevance_score}/10 | Sentiment: {ps.sentiment}")
            print(f"    Summary: {ps.summary}")
            print(f"    Insight: {ps.insight}")
            print(f"    Tags: {ps.tags}")
            print(f"    Source: {sig.source} ({sig.source_url[:60]}...)")
            print(f"    Raw Sample: {sig.raw_content[:200].replace('\n', ' ')}...")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
