import asyncio
import logging
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.reddit import RedditCollector
from app.collectors.play_store import PlayStoreCollector
from app.collectors.rss_feeds import RSSCollector
from app.collectors.instagram import InstagramCollector
from app.collectors.google_trends import GoogleTrendsCollector
from app.collectors.news import NewsCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_collectors")

async def test_collector(collector_class, name):
    logger.info(f"--- Testing {name} ---")
    collector = collector_class()
    try:
        # Just run collect() instead of run() to avoid hitting the DB and Redis for this simple test
        # Though we could call run() if DB is set up. Let's stick to collect to just verify scraping.
        signals = await collector.collect()
        logger.info(f"{name} collected {len(signals)} signals.")
        if signals:
            logger.info(f"Sample signal: {signals[0]}")
    except Exception as e:
        logger.error(f"{name} failed: {e}")
    logger.info("-" * 40)

async def main():
    logger.info("Starting collector tests...")
    
    # We can test them sequentially
    await test_collector(NewsCollector, "NewsCollector")
    await test_collector(RSSCollector, "RSSCollector")
    await test_collector(RedditCollector, "RedditCollector")
    await test_collector(PlayStoreCollector, "PlayStoreCollector")
    await test_collector(GoogleTrendsCollector, "GoogleTrendsCollector")
    await test_collector(InstagramCollector, "InstagramCollector")

if __name__ == "__main__":
    asyncio.run(main())
