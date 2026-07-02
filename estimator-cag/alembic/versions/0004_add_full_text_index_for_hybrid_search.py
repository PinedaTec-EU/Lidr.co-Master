"""Add generated full-text column for hybrid search.

Revision ID: 0004_full_text_hybrid
Revises: 0003_halfvec_hnsw
Create Date: 2026-07-02 10:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_full_text_hybrid"
down_revision = "0003_halfvec_hnsw"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chunks",
        sa.Column(
            "content_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_chunks_content_tsv_gin",
        "chunks",
        ["content_tsv"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_chunks_content_tsv_gin", table_name="chunks")
    op.drop_column("chunks", "content_tsv")
