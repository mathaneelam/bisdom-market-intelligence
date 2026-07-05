import logging
import asyncio
from datetime import datetime
import instaloader

from app.collectors.base import BaseCollector
from app.collectors.instagram_session_store import load_session_from_db, save_session_to_db
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
            username = settings.INSTAGRAM_USERNAME
            session_loaded = False

            # 1. Try the session stored in the database first — survives redeploys
            # on hosts with an ephemeral filesystem (Railway, Render), unlike a local file.
            try:
                logger.info(f"InstagramCollector: Attempting to load DB-stored session for '{username}'...")
                session_loaded = await load_session_from_db(L, username)
                if session_loaded:
                    logger.info("InstagramCollector: Successfully loaded session from database!")
            except Exception as db_err:
                logger.warning(f"InstagramCollector: Could not load session from database ({db_err}).")

            # 2. Fall back to a local session file (useful for local dev)
            if not session_loaded:
                try:
                    logger.info(f"InstagramCollector: Attempting to load local session file for '{username}'...")
                    await loop.run_in_executor(None, L.load_session_from_file, username)
                    session_loaded = True
                    logger.info("InstagramCollector: Successfully loaded local session file!")
                    await save_session_to_db(L, username)
                except Exception as session_err:
                    logger.warning(f"InstagramCollector: Could not load session file ({session_err}).")

            # 3. Last resort: password login, then persist the new session to the DB
            if not session_loaded:
                if not settings.INSTAGRAM_PASSWORD:
                    logger.error("Instagram password not set and no session available. Skipping collection.")
                    return []
                logger.warning("InstagramCollector: No saved session found. Attempting password login...")
                await loop.run_in_executor(
                    None,
                    L.login,
                    username,
                    settings.INSTAGRAM_PASSWORD
                )
                await save_session_to_db(L, username)

            for hashtag in OPPORTUNITY_HASHTAGS:
                signals = await self._fetch_hashtag_posts(L, hashtag)
                all_signals.extend(signals)
                await asyncio.sleep(2) # Be gentle on rate limits
                
        except Exception as e:
            logger.error(f"Failed to initialize Instagram Collector: {e}")
            
        return all_signals
