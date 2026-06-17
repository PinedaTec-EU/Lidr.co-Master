"""Switch HNSW index to halfvec expression

Revision ID: 0003_halfvec_hnsw
Revises: 0002_add_hnsw_vector_index
Create Date: 2026-06-11 18:00:00
"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0003_halfvec_hnsw"
down_revision = "0002_add_hnsw_vector_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_halfvec_hnsw
        ON chunks
        USING hnsw ((CAST(embedding AS halfvec(1536))) halfvec_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_halfvec_hnsw")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
        """
    )
