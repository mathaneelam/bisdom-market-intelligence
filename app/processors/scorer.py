import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import base as models_base
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal
from app.models.trade_show import TradeShow
from app.processors.ollama_processor import OllamaProcessor
from datetime import datetime

logger = logging.getLogger(__name__)

class Scorer:
    def __init__(self):
        self.processor = OllamaProcessor()

    async def process_batch(self, batch_size: int = 50) -> int:
        """
        Fetches unprocessed signals, runs them through Ollama, and saves the results.
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
                # 2. Analyze with Ollama
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
                    
                    # 3.5 Check for Trade Show details and create record
                    if analysis.get("stream") == "trade_show" and analysis.get("trade_show_details"):
                        trade_details = analysis["trade_show_details"]
                        
                        start_dt = None
                        if trade_details.get("start_date"):
                            try:
                                start_dt = datetime.strptime(trade_details["start_date"], "%Y-%m-%d").date()
                            except ValueError:
                                pass
                                
                        end_dt = None
                        if trade_details.get("end_date"):
                            try:
                                end_dt = datetime.strptime(trade_details["end_date"], "%Y-%m-%d").date()
                            except ValueError:
                                pass

                        ts = TradeShow(
                            name=trade_details.get("name", "Unknown Trade Show"),
                            city=trade_details.get("city"),
                            venue=trade_details.get("venue"),
                            start_date=start_dt,
                            end_date=end_dt,
                            website=signal.source_url,
                            relevance_note=analysis.get("insight")
                        )
                        session.add(ts)
                        
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
