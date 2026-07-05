import logging
import asyncio
from datetime import datetime
import time
import feedparser
import urllib.parse
from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Free public search feeds for LinkedIn posts
LINKEDIN_QUERIES = [
    # Opportunity Signals
    {
        "stream": "opportunity_signal",
        "description": "Looking for manufacturer",
        "query": 'site:linkedin.com/posts "looking for garment manufacturer" OR "looking for fabric supplier" OR "need garment manufacturer"'
    },
    {
        "stream": "opportunity_signal",
        "description": "Clothing brand sourcing",
        "query": 'site:linkedin.com/posts "sourcing clothing brand" OR "clothing brand manufacturer" OR "looking for knitwear manufacturer"'
    },
    # Pain Pulse Signals
    {
        "stream": "pain_pulse",
        "description": "B2B platform complaints",
        "query": 'site:linkedin.com/posts "indiamart fake leads" OR "indiamart waste" OR "tradeindia complaint" OR "indiamart alternative"'
    }
]

class LinkedInCollector(BaseCollector):
    """
    Collector for fetching LinkedIn posts by searching Google News RSS (which is free and indexable).
    """
    stream = "opportunity_signal" # Default stream fallback

    def _get_rss_url(self, query: str) -> str:
        # Google News RSS search URL
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

    async def _fetch_query(self, query_info: dict) -> list[dict]:
        stream_type = query_info.get("stream", self.stream)
        query = query_info.get("query")
        description = query_info.get("description")
        url = self._get_rss_url(query)
        signals = []

        try:
            logger.info(f"LinkedInCollector: Fetching Google News RSS for query: {description}")
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(None, feedparser.parse, url)

            for entry in parsed.entries[:10]: # Get top 10 latest
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                # Clean up title and summary text
                content = f"Title: {title}\n\n{summary}\n\n[Search Category: {description}]"

                # Parse published date
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    collected_at = datetime.fromtimestamp(time.mktime(published_parsed))
                else:
                    collected_at = datetime.utcnow()

                signals.append({
                    "stream": stream_type,
                    "source": "LinkedIn (via Google Index)",
                    "source_url": link,
                    "raw_content": content.strip(),
                    "author": "Public LinkedIn Post",
                    "language": "en",
                    "collected_at": collected_at
                })
        except Exception as e:
            logger.error(f"Error fetching LinkedIn feed via Google Index ({description}): {e}")

        return signals

    async def collect(self) -> list[dict]:
        all_signals = []
        for query_info in LINKEDIN_QUERIES:
            signals = await self._fetch_query(query_info)
            all_signals.extend(signals)
            await asyncio.sleep(1) # Polite pause between query requests
        return all_signals
