import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.processors.gemini_processor import GeminiProcessor
from app.processors.scorer import Scorer
from app.processors.deduplicator import Deduplicator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_processors")

async def test_gemini():
    logger.info("--- Testing GeminiProcessor ---")
    processor = GeminiProcessor()
    
    sample_content = "IndiaMART is facing a huge issue with fake leads. Many users are complaining about paying premium fees but getting no real buyers. The WhatsApp groups are full of angry suppliers."
    
    result = await processor.analyze_signal(f"Source: MockReddit\nContent: {sample_content}", default_stream="pain_pulse")
    logger.info(f"Gemini Analysis Result: {result}")
    logger.info("-" * 40)

async def test_dedup():
    from app.models.base import init_db
    from app.config import settings
    init_db(settings.DATABASE_URL)
    
    logger.info("--- Testing Deduplicator (if DB has processed signals) ---")
    dedup = Deduplicator()
    dupes = await dedup.run()
    logger.info(f"Deduplicator returned IDs to exclude: {dupes}")
    logger.info("-" * 40)

async def main():
    logger.info("Starting processor tests...")
    
    # Just test the API wrapper directly since the DB might not be set up yet for scorer
    await test_gemini()
    
    # Check deduplicator
    await test_dedup()

if __name__ == "__main__":
    asyncio.run(main())
