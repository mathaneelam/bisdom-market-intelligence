import logging
import asyncio
from datetime import datetime
import instaloader

from app.collectors.base import BaseCollector
from app.config import settings

logger = logging.getLogger(__name__)

# Instagram Hashtags to track opportunity signals
OPPORTUNITY_HASHTAGS = [
    "garmentmanufacturerindia",
    "fabricsupplierindia",
    "clothingmanufacturer",
    "textilesupplierindia",
]

class InstagramCollector(BaseCollector):
    """
    Collector for fetching opportunity signals from Instagram hashtags.
    Requires INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env.
    """
    
    stream = "opportunity_signal"

    async def _fetch_hashtag_posts(self, L: instaloader.Instaloader, hashtag: str) -> list[dict]:
        signals = []
        try:
            # instaloader is blocking, wrap in executor
            loop = asyncio.get_event_loop()
            
            def get_posts():
                node = instaloader.Node.get_all_hashtags(L.context, hashtag)
                # Just get top 10 recent posts to avoid rate limit
                count = 0
                results = []
                for post in instaloader.Hashtag.from_name(L.context, hashtag).get_recent_posts():
                    results.append(post)
                    count += 1
                    if count >= 10:
                        break
                return results

            posts = await loop.run_in_executor(None, get_posts)
            
            for post in posts:
                content = post.caption if post.caption else ""
                
                signals.append({
                    "stream": self.stream,
                    "source": "Instagram",
                    "source_url": f"https://www.instagram.com/p/{post.shortcode}/",
                    "raw_content": content,
                    "author": post.owner_username,
                    "language": "en", # default to en, could try to detect
                    "collected_at": post.date_utc or datetime.utcnow()
                })
        except Exception as e:
            logger.error(f"Error fetching Instagram hashtag #{hashtag}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            logger.warning("Instagram credentials not set. Skipping Instagram collection.")
            return []
            
        all_signals = []
        
        try:
            L = instaloader.Instaloader()
            # Login (can cause rate limits or blocks if done too frequently without session saving)
            # In a real production scenario, we should save and load session files.
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                L.login, 
                settings.INSTAGRAM_USERNAME, 
                settings.INSTAGRAM_PASSWORD
            )
            
            for hashtag in OPPORTUNITY_HASHTAGS:
                signals = await self._fetch_hashtag_posts(L, hashtag)
                all_signals.extend(signals)
                await asyncio.sleep(2) # Be gentle on rate limits
                
        except Exception as e:
            logger.error(f"Failed to initialize Instagram Collector: {e}")
            
        return all_signals
