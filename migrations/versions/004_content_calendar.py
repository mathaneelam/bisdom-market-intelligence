"""content calendar fields

Revision ID: 004
Revises: 003
Create Date: 2026-07-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_pieces", sa.Column("scheduled_date", sa.Date(), nullable=True))
    op.add_column("content_pieces", sa.Column("image_brief", sa.Text(), nullable=True))
    op.add_column("content_pieces", sa.Column("comment_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_pieces", "comment_note")
    op.drop_column("content_pieces", "image_brief")
    op.drop_column("content_pieces", "scheduled_date")
