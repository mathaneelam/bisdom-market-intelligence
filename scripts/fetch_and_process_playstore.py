import asyncio
import os
import sys
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.models import base as models_base
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal
from app.collectors.play_store import PlayStoreCollector
from app.processors.scorer import Scorer
from app.processors.deduplicator import Deduplicator
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fetch_playstore")

async def main():
    logger.info("Initializing database...")
    models_base.init_db(settings.DATABASE_URL)
    
    # 1. Run Play Store collector
    logger.info("Running Play Store reviews collector...")
    collector = PlayStoreCollector()
    collected_signals = await collector.collect()
    logger.info(f"Collected {len(collected_signals)} negative reviews (1-2 stars) from Play Store.")
    
    if not collected_signals:
        logger.info("No reviews found. Exiting.")
        return
        
    # 2. Save signals to database and check deduplication
    logger.info("Saving signals to DB...")
    new_signals_count = 0
    async with models_base.AsyncSessionLocal() as session:
        for sig_dict in collected_signals:
            # Check if source_url already exists in DB
            stmt = select(Signal).where(Signal.source_url == sig_dict["source_url"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if not existing:
                new_sig = Signal(
                    stream=sig_dict["stream"],
                    source=sig_dict["source"],
                    source_url=sig_dict["source_url"],
                    raw_content=sig_dict["raw_content"],
                    author=sig_dict["author"],
                    language=sig_dict["language"],
                    collected_at=sig_dict["collected_at"],
                    is_processed=False,
                    is_duplicate=False
                )
                session.add(new_sig)
                new_signals_count += 1
                
        await session.commit()
    logger.info(f"Saved {new_signals_count} new unique signals to database.")
    
    if new_signals_count == 0:
        logger.info("All collected reviews were already in the database. No new signals to process.")
        return

    # 3. Deduplicate
    logger.info("Running Deduplicator...")
    dedup = Deduplicator()
    dupes = await dedup.run()
    logger.info(f"Deduplicated {len(dupes)} signals.")

    # 4. Score signals using Ollama
    logger.info("Running Scorer...")
    scorer = Scorer()
    processed_count = await scorer.process_batch(batch_size=new_signals_count)
    logger.info(f"Processed {processed_count} signals.")

    # 5. Display high-value Pain Pulse signals (Score >= 8)
    async with models_base.AsyncSessionLocal() as session:
        stmt = select(ProcessedSignal, Signal).join(Signal, ProcessedSignal.signal_id == Signal.id)\
            .where(ProcessedSignal.stream == "pain_pulse", ProcessedSignal.relevance_score >= 8)\
            .order_by(ProcessedSignal.processed_at.desc()).limit(10)
            
        result = await session.execute(stmt)
        rows = result.all()
        
        print("\n" + "="*60)
        print("🚀 FRESH PLAY STORE PAIN PULSE SIGNALS IN DATABASE 🚀")
        print("="*60)
        
        if not rows:
            print("No high-value Play Store Pain Pulse signals (Score >= 8) found in the latest batch.")
        else:
            for idx, (ps, sig) in enumerate(rows, 1):
                print(f"\n[{idx}] {sig.source.upper()} Complaint")
                print(f"    Relevance Score: {ps.relevance_score}/10")
                print(f"    Summary: {ps.summary}")
                print(f"    Insight: {ps.insight}")
                print(f"    Author: {sig.author}")
                print(f"    Review: \"{sig.raw_content}\"")
                print("-" * 50)
                
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
