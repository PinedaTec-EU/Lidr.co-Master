from __future__ import annotations

import time

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.query_rewrite import rewrite_query
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
        rewrite = rewrite_query(query=request.query, strategy=request.rewrite_strategy)

        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        query_vector = embedder.embed_one(rewrite.effective_query)

        indexed_embedding = cast(ChunkRecord.embedding, HALFVEC(EMBEDDING_DIMENSIONS))
        distance = indexed_embedding.cosine_distance(query_vector)
        score = 1 - distance
        stmt = (
            select(
                ChunkRecord.id,
                ChunkRecord.document_id,
                ChunkRecord.chunk_type,
                ChunkRecord.content,
                ChunkRecord.metadata_json,
                DocumentRecord.document_type,
                distance.label("distance"),
                score.label("score"),
            )
            .join(DocumentRecord, DocumentRecord.id == ChunkRecord.document_id)
            .where(ChunkRecord.embedding.is_not(None))
        )
        count_stmt = (
            select(func.count())
            .select_from(ChunkRecord)
            .join(DocumentRecord, DocumentRecord.id == ChunkRecord.document_id)
            .where(ChunkRecord.embedding.is_not(None))
        )

        if request.filters:
            if request.filters.client_sector:
                criterion = ChunkRecord.metadata_json["client_sector"].astext == request.filters.client_sector
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
            if request.filters.main_technology:
                criterion = (
                    ChunkRecord.metadata_json["main_technology"].astext == request.filters.main_technology
                )
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
            if request.filters.year is not None:
                criterion = ChunkRecord.metadata_json["year"].astext == str(request.filters.year)
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
            if request.filters.complexity is not None:
                criterion = ChunkRecord.metadata_json["complexity"].astext == request.filters.complexity.value
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
            if request.filters.document_type:
                criterion = DocumentRecord.document_type == request.filters.document_type
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
            if request.filters.chunk_type:
                criterion = ChunkRecord.chunk_type == request.filters.chunk_type
                stmt = stmt.where(criterion)
                count_stmt = count_stmt.where(criterion)
        if request.score_threshold is not None:
            criterion = score >= request.score_threshold
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total_candidates_considered = int((await session.execute(count_stmt)).scalar_one())
        stmt = stmt.order_by(distance).limit(request.k)
        rows = (await session.execute(stmt)).all()

        return SearchResponse(
            query=request.query,
            effective_query=rewrite.effective_query,
            k=request.k,
            score_threshold=request.score_threshold,
            rewrite_strategy=request.rewrite_strategy,
            rewrite_notes=rewrite.notes,
            search_time_ms=round((time.perf_counter() - started_at) * 1000, 2),
            low_confidence=len(rows) == 0,
            total_candidates_considered=total_candidates_considered,
            results=[
                SearchResult(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    chunk_type=row.chunk_type,
                    content=row.content,
                    distance=round(float(row.distance), 6),
                    score=round(float(row.score), 6),
                    metadata=row.metadata_json,
                )
                for row in rows
            ],
        )
