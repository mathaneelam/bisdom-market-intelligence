import logging
import asyncio
from datetime import datetime
import time
import feedparser
import urllib.parse

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Keywords for Google News search
COMPETITOR_NEWS_KEYWORDS = [
    "IndiaMART new feature",
    "Fiber2Fashion launch",
    "Locofast update",
    "Fashinza funding",
    "B2B textile platform India launch",
]

OPPORTUNITY_NEWS_KEYWORDS = [
    "funded D2C brand India",
    "garment manufacturer India expansion",
]

class NewsCollector(BaseCollector):
    """
    Collector for fetching news related to competitors and industry opportunities
    using Google News RSS feeds.
    """
    
    stream = "mixed"

    async def _fetch_news_for_keyword(self, keyword: str, stream_type: str) -> list[dict]:
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=en-IN&gl=IN&ceid=IN:en"
        signals = []
        
        try:
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(None, feedparser.parse, url)
            
            for entry in parsed.entries[:5]: # Get top 5 news articles per keyword
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                content = f"News Title: {title}"
                
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    collected_at = datetime.fromtimestamp(time.mktime(published_parsed))
                else:
                    collected_at = datetime.utcnow()
                    
                signals.append({
                    "stream": stream_type,
                    "source": f"Google News",
                    "source_url": link,
                    "raw_content": content,
                    "author": entry.get("source", {}).get("title"), # Source name often in author field or source tag
                    "language": "en",
                    "collected_at": collected_at
                })
        except Exception as e:
            logger.error(f"Error fetching News for keyword {keyword}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        all_signals = []
        
        for keyword in COMPETITOR_NEWS_KEYWORDS:
            signals = await self._fetch_news_for_keyword(keyword, "competitor_move")
            all_signals.extend(signals)
            
        for keyword in OPPORTUNITY_NEWS_KEYWORDS:
            signals = await self._fetch_news_for_keyword(keyword, "opportunity_signal")
            all_signals.extend(signals)
            
        return all_signals
