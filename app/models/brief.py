import uuid
from datetime import date, datetime
from sqlalchemy import Date, Text, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    brief_date: Mapped[date | None] = mapped_column(Date, unique=True)
    pain_pulse: Mapped[dict | None] = mapped_column(JSONB)
    competitor_move: Mapped[dict | None] = mapped_column(JSONB)
    opportunity: Mapped[dict | None] = mapped_column(JSONB)
    full_html: Mapped[str | None] = mapped_column(Text)
    delivered_email: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    delivered_tg: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    delivered_wa: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
