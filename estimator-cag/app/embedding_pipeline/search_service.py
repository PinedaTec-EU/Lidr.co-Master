from __future__ import annotations

import time

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.schemas import SearchRequest, SearchResponse, SearchResult

EMBEDDING_DIMENSIONS = 1536


class SemanticSearchService:
    async def search(
        self,
        *,
        session: AsyncSession,
        request: SearchRequest,
    ) -> SearchResponse:
        started_at = time.perf_counter()

        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        query_vector = embedder.embed_one(request.query)

        indexed_embedding = cast(ChunkRecord.embedding, HALFVEC(EMBEDDING_DIMENSIONS))
        distance = indexed_embedding.cosine_distance(query_vector)
        stmt = (
            select(
                ChunkRecord.id,
                ChunkRecord.document_id,
                ChunkRecord.chunk_type,
                ChunkRecord.content,
                ChunkRecord.metadata_json,
                DocumentRecord.document_type,
                distance.label("distance"),
            )
            .join(DocumentRecord, DocumentRecord.id == ChunkRecord.document_id)
            .where(ChunkRecord.embedding.is_not(None))
        )

        if request.filters:
            if request.filters.client_sector:
                stmt = stmt.where(
                    ChunkRecord.metadata_json["client_sector"].astext == request.filters.client_sector
                )
            if request.filters.main_technology:
                stmt = stmt.where(
                    ChunkRecord.metadata_json["main_technology"].astext == request.filters.main_technology
                )
            if request.filters.year is not None:
                stmt = stmt.where(ChunkRecord.metadata_json["year"].astext == str(request.filters.year))
            if request.filters.complexity is not None:
                stmt = stmt.where(
                    ChunkRecord.metadata_json["complexity"].astext == request.filters.complexity.value
                )
            if request.filters.document_type:
                stmt = stmt.where(DocumentRecord.document_type == request.filters.document_type)
            if request.filters.chunk_type:
                stmt = stmt.where(ChunkRecord.chunk_type == request.filters.chunk_type)

        stmt = stmt.order_by(distance).limit(request.k)
        rows = (await session.execute(stmt)).all()

        return SearchResponse(
            query=request.query,
            k=request.k,
            search_time_ms=round((time.perf_counter() - started_at) * 1000, 2),
            results=[
                SearchResult(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    chunk_type=row.chunk_type,
                    content=row.content,
                    distance=round(float(row.distance), 6),
                    metadata=row.metadata_json,
                )
                for row in rows
            ],
        )
