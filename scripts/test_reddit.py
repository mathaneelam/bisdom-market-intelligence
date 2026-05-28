import asyncio
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.models.base import init_db
from app.collectors.reddit import RedditCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_reddit")

async def main():
    logger.info("Initializing Database Connection...")
    init_db(settings.DATABASE_URL)
    
    logger.info("Starting Reddit Collector...")
    collector = RedditCollector()
    
    # Run the collector (this fetches signals and saves them to the DB)
    await collector.run()
    
    logger.info("Reddit Collector finished. Check your dashboard to see if the Total Signals count went up!")

if __name__ == "__main__":
    asyncio.run(main())
