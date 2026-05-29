import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Text, Date, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))       # pain_pulse, opportunity_signal, competitor_move
    bisdom_action: Mapped[str | None] = mapped_column(Text)  # what Bisdom should do about this
    signal_count: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    trend: Mapped[str] = mapped_column(String(20), server_default=text("'new'"))  # new, growing, stable, declining
    importance_score: Mapped[int] = mapped_column(Integer, server_default=text("50"))
    first_seen: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    last_seen: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
