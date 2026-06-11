from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.models import ChunkRecord
from app.embedding_pipeline.schemas import SearchRequest, SearchResponse, SearchResult


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

        distance = ChunkRecord.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                ChunkRecord.id,
                ChunkRecord.document_id,
                ChunkRecord.chunk_type,
                ChunkRecord.content,
                ChunkRecord.metadata_json,
                distance.label("distance"),
            )
            .where(ChunkRecord.embedding.is_not(None))
            .order_by(distance)
            .limit(request.k)
        )
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
