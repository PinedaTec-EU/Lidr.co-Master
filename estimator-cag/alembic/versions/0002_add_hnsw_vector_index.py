"""Add HNSW vector index for semantic search

Revision ID: 0002_add_hnsw_vector_index
Revises: 0001_initial_schema
Create Date: 2026-06-11 17:30:00
"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0002_add_hnsw_vector_index"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
