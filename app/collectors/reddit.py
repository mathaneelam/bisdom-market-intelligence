import logging
import asyncio
from datetime import datetime
import httpx
import feedparser
import urllib.parse

from app.collectors.base import BaseCollector
from app.config import settings

logger = logging.getLogger(__name__)

# Keywords as per MODEL.md
PAIN_PULSE_KEYWORDS = [
    "IndiaMART fake leads",
    "B2B platform complaint India",
    "garment sourcing problem India",
    "manufacturer WhatsApp chaos India",
    "textile supplier fraud India",
    "IndiaMART renewal not worth it",
    "sourcing vendor problem India",
]

OPPORTUNITY_KEYWORDS = [
    # Buyer side — brands/corporates looking for manufacturers
    "looking for garment manufacturer India",
    "fabric supplier India MOQ",
    "clothing brand manufacturer India",
    "D2C brand sourcing India",
    "knitwear manufacturer India",
    "need textile supplier India",
    "recommend fabric manufacturer India",
    # Supplier side — manufacturers with capacity looking for buyers
    "manufacturer looking for buyers India",
    "garment factory export capacity India",
    "textile mill surplus capacity India",
]

class RedditCollector(BaseCollector):
    """
    Collector for fetching signals from Reddit search.
    Supports official OAuth2 API if client ID and secret are configured in .env,
    otherwise falls back to public RSS feeds using optimized combined queries.
    """
    
    stream = "mixed"  # Set per signal dynamically

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        """Obtains an OAuth2 access token for the official Reddit API."""
        url = "https://www.reddit.com/api/v1/access_token"
        user_agent = "windows:bisdom-market-intel:v1.0.0 (by /u/bisdom_intel_bot)"
        headers = {"User-Agent": user_agent}
        data = {"grant_type": "client_credentials"}
        
        auth = (settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET)
        response = await client.post(url, auth=auth, data=data, headers=headers)
        response.raise_for_status()
        return response.json().get("access_token")

    async def _collect_via_api(self) -> list[dict]:
        """Fetches signals using official Reddit API (OAuth2)."""
        logger.info("RedditCollector: Using official OAuth2 API connection...")
        all_signals = []
        user_agent = "windows:bisdom-market-intel:v1.0.0 (by /u/bisdom_intel_bot)"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                token = await self._get_access_token(client)
                headers = {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": user_agent
                }
                
                # Fetch Pain Pulse signals
                for keyword in PAIN_PULSE_KEYWORDS:
                    url = f"https://oauth.reddit.com/search.json?q={urllib.parse.quote(keyword)}&sort=new&limit=10"
                    res = await client.get(url, headers=headers)
                    res.raise_for_status()
                    data = res.json()
                    
                    for child in data.get("data", {}).get("children", []):
                        post = child.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")
                        
                        all_signals.append({
                            "stream": "pain_pulse",
                            "source": "Reddit",
                            "source_url": f"https://www.reddit.com{post.get('permalink')}",
                            "raw_content": f"Title: {title}\n\n{selftext}".strip(),
                            "author": post.get("author"),
                            "language": "en",
                            "collected_at": datetime.utcnow()
                        })
                    await asyncio.sleep(1) # Polite delay
                    
                # Fetch Opportunity signals
                for keyword in OPPORTUNITY_KEYWORDS:
                    url = f"https://oauth.reddit.com/search.json?q={urllib.parse.quote(keyword)}&sort=new&limit=10"
                    res = await client.get(url, headers=headers)
                    res.raise_for_status()
                    data = res.json()
                    
                    for child in data.get("data", {}).get("children", []):
                        post = child.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")
                        
                        all_signals.append({
                            "stream": "opportunity_signal",
                            "source": "Reddit",
                            "source_url": f"https://www.reddit.com{post.get('permalink')}",
                            "raw_content": f"Title: {title}\n\n{selftext}".strip(),
                            "author": post.get("author"),
                            "language": "en",
                            "collected_at": datetime.utcnow()
                        })
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Reddit API collection failed: {e}. Falling back to RSS.")
                # Fallback to RSS if API fails during execution
                return await self._collect_via_rss()
                
        return all_signals

    async def _collect_via_rss(self) -> list[dict]:
        """Fetches signals using public RSS feeds with optimized combined queries."""
        logger.info("RedditCollector: Using public RSS fallback connection...")
        all_signals = []
        
        # Combine both Pain Pulse and Opportunity keywords into one single request to prevent 429 rate limiting
        all_keywords = PAIN_PULSE_KEYWORDS + OPPORTUNITY_KEYWORDS
        formatted_kws = [f'"{kw}"' for kw in all_keywords]
        combined_query = " OR ".join(formatted_kws)
        
        url = f"https://www.reddit.com/search.rss?q={urllib.parse.quote(combined_query)}&sort=new"
        
        # Use browser user-agent to bypass bot protection on public RSS search endpoint
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    feed = feedparser.parse(res.text)
                    for entry in feed.entries:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        
                        # Classify stream locally by checking text content for keywords
                        post_text = f"{title} {summary}".lower()
                        
                        # Check if any opportunity keywords are in the text
                        is_opp = any(kw.lower() in post_text for kw in OPPORTUNITY_KEYWORDS)
                        stream_type = "opportunity_signal" if is_opp else "pain_pulse"
                        
                        all_signals.append({
                            "stream": stream_type,
                            "source": "Reddit",
                            "source_url": link,
                            "raw_content": f"Title: {title}\n\n{summary}".strip(),
                            "author": entry.get("author"),
                            "language": "en",
                            "collected_at": datetime.utcnow()
                        })
                    logger.info(f"Reddit RSS: Successfully collected {len(all_signals)} signals in exactly 1 request.")
                elif res.status_code == 429:
                    logger.warning("Reddit RSS: Rate limit (429) hit for combined query.")
                else:
                    logger.error(f"Reddit RSS error {res.status_code} for combined query.")
            except Exception as e:
                logger.error(f"Reddit RSS failed: {e}")
                
        return all_signals

    async def collect(self) -> list[dict]:
        # Choose connection route based on availability of credentials
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            return await self._collect_via_api()
        else:
            return await self._collect_via_rss()
