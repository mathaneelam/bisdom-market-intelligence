"""
Deleted Signals Bin — Cloud-based Recycle Bin
=============================================
Stores soft-deleted signals in Supabase Postgres with a 7-day expiry.
Render auto-cleans expired records at 3AM IST every day.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class DeletedSignal(Base):
    __tablename__ = "deleted_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    original_id: Mapped[str | None] = mapped_column(String(255))       # original record ID
    source_name: Mapped[str | None] = mapped_column(String(100))       # e.g. "signals", "processed_signals"
    content: Mapped[dict | None] = mapped_column(JSONB)                # full record as JSON
    deleted_reason: Mapped[str | None] = mapped_column(Text)           # why it was deleted
    deleted_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime | None] = mapped_column()              # deleted_at + 7 days
