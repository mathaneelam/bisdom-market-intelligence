import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import base as models_base
from app.models.processed_signal import ProcessedSignal
from app.processors.ollama_processor import OllamaProcessor

logger = logging.getLogger(__name__)


class Deduplicator:
    def __init__(self):
        self.processor = OllamaProcessor()

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
            
            if not signals:
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

                dupes = await self.processor.find_duplicates(payload)
                duplicate_ids_to_exclude.extend(dupes)

                await asyncio.sleep(0.5)  # Gentle on Ollama rate limits

        logger.info(f"Identified {len(duplicate_ids_to_exclude)} semantic duplicates.")
        return duplicate_ids_to_exclude

async def run_deduplicator():
    d = Deduplicator()
    await d.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_deduplicator())
