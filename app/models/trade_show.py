import uuid
from datetime import date
from sqlalchemy import String, Text, Boolean, Date, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TradeShow(Base):
    __tablename__ = "trade_shows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    venue: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    website: Mapped[str | None] = mapped_column(Text)
    relevance_note: Mapped[str | None] = mapped_column(Text)
    is_upcoming: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
