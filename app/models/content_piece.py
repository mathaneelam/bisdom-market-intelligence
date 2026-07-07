import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, ForeignKey, Date, text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ContentPiece(Base):
    """
    One piece of marketing content generated from a pain pattern.
    A single pattern produces many pieces (LinkedIn post/article, Instagram
    post/reel, WhatsApp, email, blog) across two audiences (buyer, supplier).
    Each row is reviewed and shipped on its own.
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
    # linkedin | linkedin_article | instagram_post | instagram_reel | whatsapp | email | blog
    format: Mapped[str] = mapped_column(String(20))
    tone: Mapped[str] = mapped_column(String(20))       # educational | contrast
    title: Mapped[str | None] = mapped_column(Text)     # blog/article title, email subject (null for most)
    body: Mapped[str] = mapped_column(Text)             # the actual content
    # Receipts: the raw Signal IDs (real, dated reviews) this content is based on.
    source_review_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    model: Mapped[str | None] = mapped_column(String(50))   # which model wrote it, e.g. gemma4:cloud
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))  # draft | approved | posted | rejected
    # The calendar day this piece is scheduled to post. NULL for legacy pieces
    # generated before the weekly-calendar model (they only show in List view).
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    image_brief: Mapped[str | None] = mapped_column(Text)   # AI-written description of the accompanying visual
    comment_note: Mapped[str | None] = mapped_column(Text)  # author's first-comment text, posted after publishing
    image_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True) # persistent cloud image bytes
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

