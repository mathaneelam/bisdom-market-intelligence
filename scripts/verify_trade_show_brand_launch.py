import asyncio
import logging
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import base as models_base
from app.config import settings
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal
from app.models.trade_show import TradeShow
from app.processors.scorer import Scorer
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_extraction")

async def test_verification():
    logger.info("Initializing database...")
    models_base.init_db(settings.DATABASE_URL)
    
    # 1. Create a dummy signal for Trade Show
    logger.info("Creating a mock Trade Show news signal...")
    trade_show_raw = (
        "News Title: Garments & Textiles Expo 2026 to showcase sustainable fashion in Mumbai.\n"
        "The upcoming Garments & Textiles Expo 2026, the premier B2B apparel exhibition in India, "
        "will be held at the Bombay Exhibition Centre (Nesco) in Mumbai from 2026-10-15 to 2026-10-18. "
        "Over 500 manufacturers and D2C brands are expected to participate, showing the latest fabrics and garments."
    )
    
    trade_show_signal = Signal(
        stream="trade_show",
        source="Google News",
        source_url="https://example.com/garments-expo-2026",
        raw_content=trade_show_raw,
        author="Textile News Network",
        language="en",
        collected_at=datetime.now(),
        is_processed=False,
        is_duplicate=False
    )
    
    # 2. Create a dummy signal for Brand Launch
    logger.info("Creating a mock Brand Launch news signal...")
    brand_launch_raw = (
        "News Title: New B2B fashion startup BrandX launches in Bangalore.\n"
        "BrandX, a direct-to-consumer (D2C) clothing brand specializing in organic cotton knitwear, "
        "announced its official launch today in Bangalore. Founded by industry veterans, the startup "
        "aims to bridge the gap between traditional weavers and modern consumers, securing $2M in pre-seed funding."
    )
    
    brand_launch_signal = Signal(
        stream="brand_launch",
        source="Google News",
        source_url="https://example.com/brandx-launch",
        raw_content=brand_launch_raw,
        author="Startup Daily",
        language="en",
        collected_at=datetime.now(),
        is_processed=False,
        is_duplicate=False
    )
    
    async with models_base.AsyncSessionLocal() as session:
        session.add(trade_show_signal)
        session.add(brand_launch_signal)
        await session.commit()
        
        ts_id = trade_show_signal.id
        bl_id = brand_launch_signal.id
        logger.info(f"Mock signals created. Trade Show Signal ID: {ts_id}, Brand Launch Signal ID: {bl_id}")
        
    # 3. Run Scorer to process these signals
    logger.info("Running Scorer to process the mock signals...")
    scorer = Scorer()
    processed_count = await scorer.process_batch(batch_size=2)
    logger.info(f"Scorer processed {processed_count} signals.")
    
    # 4. Verify results in Database
    async with models_base.AsyncSessionLocal() as session:
        # Check ProcessedSignal for Trade Show
        stmt = select(ProcessedSignal).where(ProcessedSignal.signal_id == ts_id)
        res = await session.execute(stmt)
        processed_ts = res.scalar_one_or_none()
        
        if processed_ts:
            logger.info("✅ ProcessedSignal for Trade Show successfully created!")
            logger.info(f"   Summary: {processed_ts.summary}")
            logger.info(f"   Relevance Score: {processed_ts.relevance_score}")
            logger.info(f"   Insight: {processed_ts.insight}")
            logger.info(f"   Stream: {processed_ts.stream}")
        else:
            logger.error("❌ ProcessedSignal for Trade Show was NOT created.")
            
        # Check ProcessedSignal for Brand Launch
        stmt = select(ProcessedSignal).where(ProcessedSignal.signal_id == bl_id)
        res = await session.execute(stmt)
        processed_bl = res.scalar_one_or_none()
        
        if processed_bl:
            logger.info("✅ ProcessedSignal for Brand Launch successfully created!")
            logger.info(f"   Summary: {processed_bl.summary}")
            logger.info(f"   Relevance Score: {processed_bl.relevance_score}")
            logger.info(f"   Insight: {processed_bl.insight}")
            logger.info(f"   Stream: {processed_bl.stream}")
        else:
            logger.error("❌ ProcessedSignal for Brand Launch was NOT created.")
            
        # Check TradeShow table record
        stmt = select(TradeShow).where(TradeShow.website == "https://example.com/garments-expo-2026")
        res = await session.execute(stmt)
        trade_show_rec = res.scalar_one_or_none()
        
        if trade_show_rec:
            logger.info("✅ TradeShow database record successfully created!")
            logger.info(f"   Name: {trade_show_rec.name}")
            logger.info(f"   City: {trade_show_rec.city}")
            logger.info(f"   Venue: {trade_show_rec.venue}")
            logger.info(f"   Start Date: {trade_show_rec.start_date}")
            logger.info(f"   End Date: {trade_show_rec.end_date}")
            logger.info(f"   Relevance Note: {trade_show_rec.relevance_note}")
        else:
            logger.error("❌ TradeShow database record was NOT created.")
            
        # Clean up
        logger.info("Cleaning up mock records from database...")
        await session.execute(delete(ProcessedSignal).where(ProcessedSignal.signal_id.in_([ts_id, bl_id])))
        await session.execute(delete(Signal).where(Signal.id.in_([ts_id, bl_id])))
        if trade_show_rec:
            await session.execute(delete(TradeShow).where(TradeShow.id == trade_show_rec.id))
        await session.commit()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(test_verification())
