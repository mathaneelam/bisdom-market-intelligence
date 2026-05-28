import asyncio
import logging
import sys
import os

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.base import init_db
from app.processors.scorer import Scorer
from app.processors.brief_builder import BriefBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("run_ai_pipeline")

async def main():
    logger.info("Initializing Database Connection...")
    init_db(settings.DATABASE_URL)
    
    logger.info("1. Starting AI Scorer...")
    scorer = Scorer()
    processed_count = await scorer.process_batch(batch_size=50)
    logger.info(f"AI processed {processed_count} signals.")
    
    logger.info("2. Starting Brief Builder...")
    builder = BriefBuilder()
    brief = await builder.run()
    
    if brief:
        logger.info(f"Successfully built Brief ID: {brief.id}")
    else:
        logger.info("No brief was generated (maybe no signals scored high enough).")

if __name__ == "__main__":
    asyncio.run(main())
