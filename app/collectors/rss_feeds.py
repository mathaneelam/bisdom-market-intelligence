import logging
import asyncio
from datetime import datetime
import time
import feedparser

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

COMPETITOR_FEEDS = [
    # B2B / marketplace competitors
    {"name": "IndiaMART Blog",      "url": "https://corporate.indiamart.com/feed/"},

    # Textile & garment industry news
    {"name": "Fibre2Fashion",       "url": "https://www.fibre2fashion.com/rss/news/default.xml"},
    {"name": "FashionNetwork India","url": "https://in.fashionnetwork.com/rss/news.xml"},

    # General tech / startup funding (competitor move signals)
    # (TechCrunch removed per user request to reduce noise)
]

class RSSCollector(BaseCollector):
    """
    Collector for fetching competitor moves and industry news via RSS feeds.
    """
    
    stream = "competitor_move"

    async def _fetch_feed(self, feed_info: dict) -> list[dict]:
        url = feed_info.get("url")
        source_name = feed_info.get("name", "RSS Feed")
        signals = []
        
        try:
            # feedparser is blocking, but network requests usually complete quickly.
            # For strict non-blocking, we could use aiohttp or run in an executor,
            # but feedparser in an async context is often acceptable for light loads.
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in parsed.entries[:10]: # Get top 10 latest entries
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                
                content = f"Title: {title}\n\n{summary}"
                
                # Try to parse published date
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    collected_at = datetime.fromtimestamp(time.mktime(published_parsed))
                else:
                    collected_at = datetime.utcnow()
                    
                signals.append({
                    "stream": self.stream,
                    "source": f"RSS ({source_name})",
                    "source_url": link,
                    "raw_content": content.strip(),
                    "author": entry.get("author"),
                    "language": "en",
                    "collected_at": collected_at
                })
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        all_signals = []
        
        # In a real scenario, we'd fetch feeds from the `competitors` table where `rss_url` IS NOT NULL
        # For now, using hardcoded fallback list as per Phase 2 simplified plan
        for feed in COMPETITOR_FEEDS:
            signals = await self._fetch_feed(feed)
            all_signals.extend(signals)
            
        return all_signals
