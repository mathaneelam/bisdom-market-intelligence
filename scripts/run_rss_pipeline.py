import asyncio
import logging
import sys
import os

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.base import init_db
from app.collectors.rss_feeds import RSSCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("run_rss")

async def main():
    logger.info("Initializing Database Connection...")
    init_db(settings.DATABASE_URL)
    
    logger.info("Starting RSS Collector (End-to-End Mode)...")
    # We create the collector
    collector = RSSCollector()
    
    # We call .run() instead of .collect() so it actually saves to the Database and checks Redis for duplicates
    saved_count = await collector.run()
    
    logger.info(f"Successfully collected and saved {saved_count} new signals to the database.")

if __name__ == "__main__":
    asyncio.run(main())
