import logging
from datetime import datetime
from google_play_scraper import reviews, Sort

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Target apps for Play Store reviews (competitors)
COMPETITOR_APP_IDS = [
    "com.indiamart.m",       # IndiaMART
    "com.tradeindia.app",    # TradeIndia
    "com.alibaba.intl.android.apps.poseidon", # Alibaba
    # Add more as needed
]

class PlayStoreCollector(BaseCollector):
    """
    Collector for fetching bad reviews (1-2 stars) from competitor apps.
    These translate directly to 'pain_pulse' signals.
    """
    
    stream = "pain_pulse"

    async def collect(self) -> list[dict]:
        all_signals = []
        
        for app_id in COMPETITOR_APP_IDS:
            try:
                # Fetch recent reviews
                result, _ = reviews(
                    app_id,
                    lang='en', 
                    country='in', 
                    sort=Sort.NEWEST,
                    count=50 # Number of reviews to fetch per app
                )
                
                for review in result:
                    # We are mostly interested in bad reviews to find user pain points
                    if review.get("score", 5) <= 2:
                        content = review.get("content", "").strip()
                        if len(content) < 10:
                            continue # Ignore very short generic complaints
                            
                        all_signals.append({
                            "stream": self.stream,
                            "source": f"Play Store ({app_id})",
                            # Use review ID for deduplication, as there isn't a direct URL for individual reviews
                            "source_url": f"playstore://{app_id}/review/{review.get('reviewId')}",
                            "raw_content": content,
                            "author": review.get("userName"),
                            "language": "en",
                            "collected_at": review.get("at", datetime.utcnow())
                        })
            except Exception as e:
                logger.error(f"Error fetching Play Store reviews for {app_id}: {e}")
                
        return all_signals
