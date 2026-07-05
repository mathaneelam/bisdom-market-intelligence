import asyncio
import logging
from sqlalchemy import select, delete, text
from app.config import settings
from app.models import base
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

async def main():
    base.init_db(settings.DATABASE_URL)
    async with base.AsyncSessionLocal() as session:
        # 1. Identify signals from 'RSS (Sourcing Journal)'
        sourcing_journal_q = select(Signal.id).where(Signal.source == "RSS (Sourcing Journal)")
        sourcing_journal_ids = (await session.execute(sourcing_journal_q)).scalars().all()
        logger.info(f"Found {len(sourcing_journal_ids)} signals from Sourcing Journal to delete.")

        # 2. Identify signals with other country content (e.g., Bangladesh, Vietnam, US, UK) that do not mention India/Indian/etc.
        other_countries = ["bangladesh", "vietnam", "pakistan", "sri lanka", "cambodia", "china", "usa", "europe"]
        india_terms = ["india", "indian", "delhi", "mumbai", "tiruppur", "surat", "ludhiana", "ahmedabad", "coimbatore", "bengaluru", "chennai"]

        all_signals_q = select(Signal.id, Signal.raw_content)
        all_signals = (await session.execute(all_signals_q)).all()

        intl_ids = []
        for sig_id, raw_content in all_signals:
            if not raw_content:
                continue
            content_lower = raw_content.lower()
            has_intl = any(c in content_lower for c in other_countries)
            has_india = any(i in content_lower for i in india_terms)
            if has_intl and not has_india:
                intl_ids.append(sig_id)

        logger.info(f"Found {len(intl_ids)} signals mentioning other countries without India to delete.")

        # Combine all IDs to delete
        to_delete_ids = list(set(sourcing_journal_ids + intl_ids))
        logger.info(f"Total unique signal IDs to delete: {len(to_delete_ids)}")

        if to_delete_ids:
            # Get processed_signals IDs that correspond to to_delete_ids
            proc_ids_q = select(ProcessedSignal.id).where(ProcessedSignal.signal_id.in_(to_delete_ids))
            proc_ids = (await session.execute(proc_ids_q)).scalars().all()
            logger.info(f"Found {len(proc_ids)} processed_signals records to delete.")

            if proc_ids:
                # Delete from signal_patterns first (which references processed_signals.id)
                await session.execute(
                    text("DELETE FROM signal_patterns WHERE signal_id = ANY(:ids)"),
                    {"ids": proc_ids}
                )
                logger.info(f"Deleted referencing rows from signal_patterns.")

            # Delete from processed_signals
            del_processed_stmt = delete(ProcessedSignal).where(ProcessedSignal.signal_id.in_(to_delete_ids))
            res_proc = await session.execute(del_processed_stmt)
            logger.info(f"Deleted {res_proc.rowcount} rows from processed_signals.")

            # Delete from signals
            del_signals_stmt = delete(Signal).where(Signal.id.in_(to_delete_ids))
            res_sig = await session.execute(del_signals_stmt)
            logger.info(f"Deleted {res_sig.rowcount} rows from signals.")

            await session.commit()
            logger.info("Database transaction committed successfully.")
        else:
            logger.info("No signals found to delete.")

if __name__ == "__main__":
    asyncio.run(main())
