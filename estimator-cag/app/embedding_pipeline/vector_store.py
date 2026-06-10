from __future__ import annotations

from collections.abc import Iterable

from app.config import settings
from app.embedding_pipeline.embedder import EMBEDDING_DIMENSIONS
from app.embedding_pipeline.schemas import (
    EmbeddedChunk,
    EmbeddingModelName,
    SearchFilters,
    SearchMatch,
)


class PgVectorStore:
    def __init__(self, dsn: str | None = None) -> None:
        resolved_dsn = dsn or settings.vector_database_url
        if not resolved_dsn:
            raise ValueError("VECTOR_DATABASE_URL is required for persistence and semantic search.")
        self.dsn = resolved_dsn

    def ensure_schema(self) -> None:
        connect, _dict_row = _psycopg_primitives()
        with connect(self.dsn) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embedding_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    budget_id TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    client_sector TEXT NOT NULL,
                    main_technology TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    complexity TEXT NOT NULL,
                    estimated_hours INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    chunking_strategy TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    llm_context TEXT,
                    embedding vector NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS embedding_chunks_small_hnsw
                ON embedding_chunks
                USING hnsw ((embedding::vector({EMBEDDING_DIMENSIONS[EmbeddingModelName.TEXT_EMBEDDING_3_SMALL]})) vector_cosine_ops)
                WHERE embedding_model = '{EmbeddingModelName.TEXT_EMBEDDING_3_SMALL.value}'
                """
            )
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS embedding_chunks_large_hnsw
                ON embedding_chunks
                USING hnsw ((embedding::vector({EMBEDDING_DIMENSIONS[EmbeddingModelName.TEXT_EMBEDDING_3_LARGE]})) vector_cosine_ops)
                WHERE embedding_model = '{EmbeddingModelName.TEXT_EMBEDDING_3_LARGE.value}'
                """
            )

    def upsert_chunks(self, chunks: Iterable[EmbeddedChunk]) -> int:
        persisted = 0
        connect, _dict_row = _psycopg_primitives()
        with connect(self.dsn) as conn:
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO embedding_chunks (
                        chunk_id,
                        text,
                        budget_id,
                        component_id,
                        client_sector,
                        main_technology,
                        year,
                        complexity,
                        estimated_hours,
                        token_count,
                        chunking_strategy,
                        embedding_model,
                        llm_context,
                        embedding
                    ) VALUES (
                        %(chunk_id)s,
                        %(text)s,
                        %(budget_id)s,
                        %(component_id)s,
                        %(client_sector)s,
                        %(main_technology)s,
                        %(year)s,
                        %(complexity)s,
                        %(estimated_hours)s,
                        %(token_count)s,
                        %(chunking_strategy)s,
                        %(embedding_model)s,
                        %(llm_context)s,
                        %(embedding)s::vector
                    )
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        text = EXCLUDED.text,
                        client_sector = EXCLUDED.client_sector,
                        main_technology = EXCLUDED.main_technology,
                        year = EXCLUDED.year,
                        complexity = EXCLUDED.complexity,
                        estimated_hours = EXCLUDED.estimated_hours,
                        token_count = EXCLUDED.token_count,
                        chunking_strategy = EXCLUDED.chunking_strategy,
                        embedding_model = EXCLUDED.embedding_model,
                        llm_context = EXCLUDED.llm_context,
                        embedding = EXCLUDED.embedding
                    """,
                    {
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "budget_id": chunk.metadata.budget_id,
                        "component_id": chunk.metadata.component_id,
                        "client_sector": chunk.metadata.client_sector,
                        "main_technology": chunk.metadata.main_technology,
                        "year": chunk.metadata.year,
                        "complexity": chunk.metadata.complexity.value,
                        "estimated_hours": chunk.metadata.estimated_hours,
                        "token_count": chunk.token_count,
                        "chunking_strategy": chunk.chunking_strategy.value,
                        "embedding_model": chunk.embedding_model.value,
                        "llm_context": chunk.llm_context,
                        "embedding": _vector_literal(chunk.embedding),
                    },
                )
                persisted += 1
        return persisted

    def search(
        self,
        *,
        query_embedding: list[float],
        embedding_model: EmbeddingModelName,
        top_k: int,
        filters: SearchFilters | None = None,
    ) -> list[SearchMatch]:
        dimensions = EMBEDDING_DIMENSIONS[embedding_model]
        where_parts = ["embedding_model = %(embedding_model)s"]
        params: dict[str, object] = {
            "embedding_model": embedding_model.value,
            "query_embedding": _vector_literal(query_embedding),
            "top_k": top_k,
        }

        if filters and filters.client_sector:
            where_parts.append("client_sector = %(client_sector)s")
            params["client_sector"] = filters.client_sector
        if filters and filters.main_technology:
            where_parts.append("main_technology = %(main_technology)s")
            params["main_technology"] = filters.main_technology
        if filters and filters.year is not None:
            where_parts.append("year = %(year)s")
            params["year"] = filters.year
        if filters and filters.complexity is not None:
            where_parts.append("complexity = %(complexity)s")
            params["complexity"] = filters.complexity.value

        query = f"""
            SELECT
                chunk_id,
                text,
                budget_id,
                component_id,
                client_sector,
                main_technology,
                year,
                complexity,
                estimated_hours,
                token_count,
                chunking_strategy,
                embedding_model,
                llm_context,
                1 - (embedding::vector({dimensions}) <=> %(query_embedding)s::vector({dimensions})) AS score
            FROM embedding_chunks
            WHERE {" AND ".join(where_parts)}
            ORDER BY embedding::vector({dimensions}) <=> %(query_embedding)s::vector({dimensions})
            LIMIT %(top_k)s
        """

        connect, dict_row = _psycopg_primitives()
        with connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            SearchMatch.model_validate(
                {
                    "chunk_id": row["chunk_id"],
                    "text": row["text"],
                    "metadata": {
                        "budget_id": row["budget_id"],
                        "component_id": row["component_id"],
                        "client_sector": row["client_sector"],
                        "main_technology": row["main_technology"],
                        "year": row["year"],
                        "complexity": row["complexity"],
                        "estimated_hours": row["estimated_hours"],
                    },
                    "token_count": row["token_count"],
                    "chunking_strategy": row["chunking_strategy"],
                    "embedding_model": row["embedding_model"],
                    "score": round(float(row["score"]), 6),
                    "llm_context": row["llm_context"],
                }
            )
            for row in rows
        ]


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.10f}" for value in values) + "]"


def _psycopg_primitives():
    try:
        from psycopg import connect
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required for vector persistence and semantic search. "
            "Install the project dependencies first."
        ) from exc
    return connect, dict_row
