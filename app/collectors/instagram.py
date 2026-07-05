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
            loop = asyncio.get_event_loop()
            
            def get_posts_json():
                # Query mobile tags endpoint with exact required parameters
                return L.context.get_iphone_json(
                    "api/v1/tags/web_info/",
                    {
                        "__a": 1,
                        "__d": "dis",
                        "tag_name": hashtag
                    }
                )
                
            response = await loop.run_in_executor(None, get_posts_json)
            
            # Recursive parser to extract all media objects from raw response JSON
            raw_posts = []
            def extract_media(data):
                if isinstance(data, dict):
                    if "pk" in data and "code" in data and "user" in data:
                        raw_posts.append(data)
                    else:
                        for v in data.values():
                            extract_media(v)
                elif isinstance(data, list):
                    for i in data:
                        extract_media(i)
                        
            extract_media(response)
            
            # Filter and take up to 10 posts
            count = 0
            for post in raw_posts:
                caption_obj = post.get("caption")
                content = caption_obj.get("text", "") if caption_obj else ""
                
                taken_at = post.get("taken_at")
                collected_at = datetime.utcfromtimestamp(taken_at) if taken_at else datetime.utcnow()
                
                user_obj = post.get("user", {})
                author = user_obj.get("username", "unknown")
                
                signals.append({
                    "stream": self.stream,
                    "source": "Instagram",
                    "source_url": f"https://www.instagram.com/p/{post.get('code')}/",
                    "raw_content": content,
                    "author": author,
                    "language": "en",
                    "collected_at": collected_at
                })
                
                count += 1
                if count >= 10:
                    break
                    
        except Exception as e:
            logger.error(f"Error fetching Instagram hashtag #{hashtag}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        if not settings.INSTAGRAM_USERNAME:
            logger.warning("Instagram username not set. Skipping Instagram collection.")
            return []
            
        all_signals = []
        
        try:
            L = instaloader.Instaloader()
            loop = asyncio.get_event_loop()
            
            # Check if we have a saved session file. If so, load it!
            try:
                logger.info(f"InstagramCollector: Attempting to load saved session for '{settings.INSTAGRAM_USERNAME}'...")
                await loop.run_in_executor(
                    None,
                    L.load_session_from_file,
                    settings.INSTAGRAM_USERNAME
                )
                logger.info("InstagramCollector: Successfully loaded saved session file!")
            except Exception as session_err:
                logger.warning(f"InstagramCollector: Could not load session file ({session_err}). Attempting password login...")
                if not settings.INSTAGRAM_PASSWORD:
                    logger.error("Instagram password not set and no session file exists. Skipping collection.")
                    return []
                # Fallback to login
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
