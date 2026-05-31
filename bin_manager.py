"""
Bisdom Cloud Bin Manager
========================
Saves deleted records to the `deleted_signals` table in Supabase.
Runs 24/7 on Render — works whether your laptop is on or off.

Usage:
    from bin_manager import BinManager
    bm = BinManager(session)

    # Save records to bin before deleting
    await bm.save(records, source_name="signals", reason="User requested noise removal")

    # List everything in the bin
    await bm.list_bin()

    # Restore records from bin by keyword
    await bm.restore(keyword="signals")

    # Auto-cleanup records older than 7 days (runs automatically at 3AM IST)
    await bm.cleanup(days=7)
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deleted_signal import DeletedSignal

logger = logging.getLogger(__name__)


class BinManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, records: list[dict], source_name: str = "signals", reason: str = "Deleted by user") -> int:
        """
        Save a list of records (as dicts) to the bin before permanent deletion.
        Returns the number of records saved.
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)

        bin_records = [
            DeletedSignal(
                original_id=str(r.get("id", "")),
                source_name=source_name,
                content=r,
                deleted_reason=reason,
                deleted_at=now,
                expires_at=expires_at,
            )
            for r in records
        ]
        self.session.add_all(bin_records)
        await self.session.flush()
        logger.info("[BIN] Saved %d record(s) to bin (expires %s).", len(bin_records), expires_at.date())
        return len(bin_records)

    async def list_bin(self) -> list[dict]:
        """List all records currently in the bin."""
        stmt = select(DeletedSignal).order_by(DeletedSignal.deleted_at.desc())
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        if not rows:
            logger.info("[BIN] Bin is empty.")
            return []
        now = datetime.utcnow()
        items = []
        for row in rows:
            age = now - row.deleted_at
            expires_in = row.expires_at - now if row.expires_at else None
            items.append({
                "id": str(row.id),
                "source": row.source_name,
                "reason": row.deleted_reason,
                "deleted_at": str(row.deleted_at.date()),
                "expires_in_days": max(0, expires_in.days) if expires_in else "unknown",
            })
            logger.info("[BIN] %s | source=%s | deleted=%s | expires_in=%s days",
                        row.id, row.source_name, row.deleted_at.date(),
                        max(0, expires_in.days) if expires_in else "?")
        return items

    async def restore(self, keyword: str = None, bin_id: str = None) -> list[dict]:
        """
        Restore records from the bin.
        Filter by source_name keyword or specific bin record ID.
        Returns the raw content of the restored records.
        """
        stmt = select(DeletedSignal)
        if bin_id:
            stmt = stmt.where(DeletedSignal.id == bin_id)
        elif keyword:
            stmt = stmt.where(DeletedSignal.source_name.ilike(f"%{keyword}%"))
        stmt = stmt.order_by(DeletedSignal.deleted_at.desc())

        result = await self.session.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.info("[BIN] No records found to restore.")
            return []

        restored = [row.content for row in rows]
        logger.info("[BIN] Restored %d record(s) from bin.", len(restored))
        return restored

    async def cleanup(self, days: int = 7) -> int:
        """
        Permanently delete bin records older than `days` days.
        Runs automatically at 3AM IST every day on Render.
        Returns number of records permanently deleted.
        """
        expiry_cutoff = datetime.utcnow()
        stmt = delete(DeletedSignal).where(DeletedSignal.expires_at <= expiry_cutoff)
        result = await self.session.execute(stmt)
        count = result.rowcount
        if count:
            logger.info("[BIN] Permanently deleted %d expired record(s) from cloud bin.", count)
        else:
            logger.info("[BIN] Nothing to clean up. All bin records are within %d days.", days)
        return count
