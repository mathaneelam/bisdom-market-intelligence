import json
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.config import settings
from app.models import base as models_base
from app.models.processed_signal import ProcessedSignal

logger = logging.getLogger(__name__)

DEDUP_PROMPT = """You are an assistant that finds semantically duplicate market intelligence signals.
Given a list of signals with their IDs and summaries, identify which signals are saying the exact same thing (semantic duplicates).
For any group of duplicates, pick one as the 'primary' and list the others as 'duplicates'.

Return ONLY valid JSON in this exact format:
{
  "duplicate_ids": ["uuid-of-duplicate-1", "uuid-of-duplicate-2"]
}

If there are no duplicates, return {"duplicate_ids": []}.
Return JSON only. No preamble. No markdown.
"""

class Deduplicator:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=DEDUP_PROMPT)
        else:
            self.model = None

    async def run(self):
        """
        Finds and marks semantic duplicates in the past 24 hours of processed signals.
        (We'll just mark them in memory for the brief builder, or delete them, or set a flag.
        Since the schema for ProcessedSignal doesn't have an `is_duplicate` flag, we can add it or just return the list of IDs to exclude).
        Let's just return the list of duplicate IDs for the brief builder to exclude.
        """
        yesterday = datetime.utcnow() - timedelta(days=1)
        duplicate_ids_to_exclude = []
        
        async with models_base.AsyncSessionLocal() as session:
            stmt = select(ProcessedSignal).where(ProcessedSignal.processed_at >= yesterday)
            result = await session.execute(stmt)
            signals = result.scalars().all()
            
            if not signals or not self.model:
                return []

            # Group by stream to reduce context window and improve accuracy
            streams = {}
            for s in signals:
                streams.setdefault(s.stream, []).append(s)
                
            for stream, stream_signals in streams.items():
                if len(stream_signals) < 2:
                    continue
                    
                # Format payload
                payload = "Signals to evaluate:\n"
                for s in stream_signals:
                    payload += f"- ID: {str(s.id)} | Summary: {s.summary}\n"
                    
                try:
                    response = await self.model.generate_content_async(
                        payload,
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="application/json",
                        )
                    )
                    
                    result_text = response.text.strip()
                    if result_text.startswith("```json"):
                        result_text = result_text[7:]
                    if result_text.startswith("```"):
                        result_text = result_text[3:]
                    if result_text.endswith("```"):
                        result_text = result_text[:-3]
                        
                    data = json.loads(result_text.strip())
                    dupes = data.get("duplicate_ids", [])
                    duplicate_ids_to_exclude.extend(dupes)
                    
                except Exception as e:
                    logger.error(f"Error deduplicating stream {stream}: {e}")
                    
                await asyncio.sleep(1) # Rate limit protection

        logger.info(f"Identified {len(duplicate_ids_to_exclude)} semantic duplicates.")
        return duplicate_ids_to_exclude

async def run_deduplicator():
    d = Deduplicator()
    await d.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_deduplicator())
