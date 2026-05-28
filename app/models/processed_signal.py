import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ProcessedSignal(Base):
    __tablename__ = "processed_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id")
    )
    summary: Mapped[str | None] = mapped_column(Text)
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    sentiment: Mapped[str | None] = mapped_column(String(20))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    stream: Mapped[str | None] = mapped_column(String(50))
    insight: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
