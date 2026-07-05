import uuid
from datetime import datetime

from sqlalchemy import LargeBinary, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InstagramSession(Base):
    """Persists the instaloader session so it survives redeploys/restarts on ephemeral hosts (Railway, Render)."""

    __tablename__ = "instagram_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    username: Mapped[str] = mapped_column(String(255), unique=True)
    session_data: Mapped[bytes] = mapped_column(LargeBinary)
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
