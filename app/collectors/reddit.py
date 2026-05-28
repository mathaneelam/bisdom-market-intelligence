import logging
import asyncio
from datetime import datetime
import httpx

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Keywords as per MODEL.md
PAIN_PULSE_KEYWORDS = [
    "IndiaMART fake leads",
    "B2B platform complaint India",
    "garment sourcing problem India",
    "manufacturer WhatsApp chaos",
    "textile supplier fraud India",
    "IndiaMART renewal not worth it",
    "sourcing vendor problem",
]

OPPORTUNITY_KEYWORDS = [
    "looking for garment manufacturer India",
    "fabric supplier India MOQ",
    "clothing brand manufacturer",
    "D2C brand sourcing India",
    "knitwear manufacturer India",
    "need textile supplier",
    "recommend fabric manufacturer",
]

class RedditCollector(BaseCollector):
    """
    Collector for fetching signals from Reddit search.
    Fetches both Pain Pulse and Opportunity signals.
    """
    
    stream = "mixed" # Will set per signal

    async def _fetch_search_results(self, keyword: str, stream_type: str, client: httpx.AsyncClient) -> list[dict]:
        url = f"https://www.reddit.com/search.json?q={keyword}&sort=new&limit=10"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        
        signals = []
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                
                content = f"Title: {title}\n\n{selftext}".strip()
                
                signals.append({
                    "stream": stream_type,
                    "source": "Reddit",
                    "source_url": f"https://www.reddit.com{post.get('permalink')}",
                    "raw_content": content,
                    "author": post.get("author"),
                    "language": "en",
                    "collected_at": datetime.utcnow()
                })
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Reddit rate limit hit for keyword: {keyword}")
            else:
                logger.error(f"Reddit HTTP error for keyword {keyword}: {e}")
        except Exception as e:
            logger.error(f"Error fetching Reddit data for keyword {keyword}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        all_signals = []
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # We fetch serially or with asyncio.gather, gather is faster but might hit rate limits quicker.
            # Let's do simple sequential for now to be gentle on rate limits.
            for keyword in PAIN_PULSE_KEYWORDS:
                signals = await self._fetch_search_results(keyword, "pain_pulse", client)
                all_signals.extend(signals)
                await asyncio.sleep(1) # Be gentle on rate limits
                
            for keyword in OPPORTUNITY_KEYWORDS:
                signals = await self._fetch_search_results(keyword, "opportunity_signal", client)
                all_signals.extend(signals)
                await asyncio.sleep(1)
                
        return all_signals
