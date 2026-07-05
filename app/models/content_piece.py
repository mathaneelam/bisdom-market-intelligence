import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ContentPiece(Base):
    """
    One piece of marketing content generated from a pain pattern.
    A single pattern produces many pieces (LinkedIn, Instagram, blog, ad, email)
    across two audiences (buyer, supplier). Each row is reviewed and shipped on its own.
    """
    __tablename__ = "content_pieces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # The pain pattern this content was generated from.
    pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patterns.id")
    )
    audience: Mapped[str] = mapped_column(String(20))   # buyer | supplier
    format: Mapped[str] = mapped_column(String(20))     # linkedin | instagram | blog | ad | email
    tone: Mapped[str] = mapped_column(String(20))       # educational | contrast
    title: Mapped[str | None] = mapped_column(Text)     # blog title / reel hook (null for most)
    body: Mapped[str] = mapped_column(Text)             # the actual content
    # Receipts: the raw Signal IDs (real, dated reviews) this content is based on.
    source_review_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    model: Mapped[str | None] = mapped_column(String(50))   # which model wrote it, e.g. gemma4:cloud
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))  # draft | approved | posted | rejected
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
