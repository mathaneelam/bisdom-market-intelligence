import logging
import asyncio
from datetime import datetime
from pytrends.request import TrendReq

from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Base keywords to find related trending queries
TRENDS_KEYWORDS = [
    "IndiaMART",
    "garment manufacturer",
    "textile supplier"
]

class GoogleTrendsCollector(BaseCollector):
    """
    Collector for fetching trending queries related to base keywords using Google Trends.
    Trending queries might indicate pain points (e.g. "IndiaMART alternatives") 
    or opportunities (e.g. "garment manufacturer near me").
    """
    
    stream = "mixed"

    async def _fetch_related_queries(self, pytrend: TrendReq, keyword: str) -> list[dict]:
        signals = []
        try:
            loop = asyncio.get_event_loop()
            
            def get_trends():
                pytrend.build_payload(kw_list=[keyword], geo='IN', timeframe='now 7-d')
                return pytrend.related_queries()
                
            related = await loop.run_in_executor(None, get_trends)
            
            if keyword in related and related[keyword] and 'rising' in related[keyword]:
                rising = related[keyword]['rising']
                if rising is not None and not rising.empty:
                    # Get top 5 rising queries
                    for index, row in rising.head(5).iterrows():
                        query = row['query']
                        value = row['value'] # percentage increase
                        
                        # Determine stream heuristically
                        stream_type = "pain_pulse" if any(w in query.lower() for w in ["complaint", "fake", "alternative", "fraud"]) else "opportunity_signal"
                        
                        content = f"Trending query related to '{keyword}': '{query}' (Increase: {value}%)"
                        
                        signals.append({
                            "stream": stream_type,
                            "source": "Google Trends",
                            "source_url": f"https://trends.google.com/trends/explore?geo=IN&q={query.replace(' ', '%20')}",
                            "raw_content": content,
                            "author": None,
                            "language": "en",
                            "collected_at": datetime.utcnow()
                        })
        except Exception as e:
            logger.error(f"Error fetching Google Trends for {keyword}: {e}")
            
        return signals

    async def collect(self) -> list[dict]:
        all_signals = []
        
        try:
            pytrend = TrendReq(hl='en-US', tz=330) # tz=330 is IST (+5:30)
            
            for keyword in TRENDS_KEYWORDS:
                signals = await self._fetch_related_queries(pytrend, keyword)
                all_signals.extend(signals)
                await asyncio.sleep(2) # Be gentle on rate limits
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends Collector: {e}")
            
        return all_signals
