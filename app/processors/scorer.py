import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import base as models_base
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal
from app.processors.gemini_processor import GeminiProcessor

logger = logging.getLogger(__name__)

class Scorer:
    def __init__(self):
        self.processor = GeminiProcessor()

    async def process_batch(self, batch_size: int = 50) -> int:
        """
        Fetches unprocessed signals, runs them through Gemini, and saves the results.
        Returns the number of signals processed.
        """
        processed_count = 0
        
        async with models_base.AsyncSessionLocal() as session:
            # 1. Fetch unprocessed and non-duplicate signals
            stmt = select(Signal).where(
                Signal.is_processed == False, 
                Signal.is_duplicate == False
            ).limit(batch_size)
            
            result = await session.execute(stmt)
            signals = result.scalars().all()
            
            if not signals:
                logger.info("No unprocessed signals found.")
                return 0
                
            logger.info(f"Processing {len(signals)} signals...")
            
            for signal in signals:
                # 2. Analyze with Gemini
                content_to_analyze = f"Source: {signal.source}\nContent: {signal.raw_content}"
                analysis = await self.processor.analyze_signal(content_to_analyze, default_stream=signal.stream)
                
                if analysis:
                    # 3. Create ProcessedSignal
                    processed_signal = ProcessedSignal(
                        signal_id=signal.id,
                        summary=analysis.get("summary"),
                        relevance_score=analysis.get("relevance_score"),
                        sentiment=analysis.get("sentiment"),
                        tags=analysis.get("tags", []),
                        insight=analysis.get("insight"),
                        stream=analysis.get("stream", signal.stream)
                    )
                    session.add(processed_signal)
                    
                    # 4. Mark original as processed
                    signal.is_processed = True
                    processed_count += 1
                else:
                    logger.warning(f"Failed to analyze signal {signal.id}")
                    
                # Small delay to avoid API rate limits
                await asyncio.sleep(1)
                
            # Commit the batch
            await session.commit()
            logger.info(f"Successfully processed {processed_count} signals.")
            
        return processed_count

async def run_scorer():
    scorer = Scorer()
    await scorer.process_batch()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scorer())
