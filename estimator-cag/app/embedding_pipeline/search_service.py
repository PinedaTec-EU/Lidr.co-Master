from __future__ import annotations

import time
from dataclasses import dataclass

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.hybrid_fusion import reciprocal_rank_fusion
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.query_rewrite import rewrite_query
from app.embedding_pipeline.reranker import rerank_candidates
from app.embedding_pipeline.schemas import (
    SearchFilters,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchStrategy,
)

EMBEDDING_DIMENSIONS = 1536
TEXT_SEARCH_CONFIG = "english"


@dataclass
class SearchCandidate:
    chunk_id: int
    document_id: int
    chunk_type: str
    content: str
    metadata: dict
    distance: float
    semantic_score: float
    lexical_score: float | None
    fusion_score: float | None
    final_score: float


class SemanticSearchService:
    async def search(
        self,
        *,
        session: AsyncSession,
        request: SearchRequest,
    ) -> SearchResponse:
        started_at = time.perf_counter()
        rewrite = rewrite_query(query=request.query, strategy=request.rewrite_strategy)
        candidate_pool_k = request.candidate_pool_k or request.k

        semantic_candidates = await self._search_semantic_candidates(
            session=session,
            query=rewrite.effective_query,
            request=request,
            limit=candidate_pool_k,
        )

        if request.search_strategy == SearchStrategy.HYBRID:
            lexical_candidates = await self._search_lexical_candidates(
                session=session,
                query=rewrite.effective_query,
                request=request,
                limit=candidate_pool_k,
            )
            candidates = self._fuse_hybrid_candidates(
                semantic_candidates=semantic_candidates,
                lexical_candidates=lexical_candidates,
                smoothing_k=request.rrf_smoothing_k,
            )
        else:
            candidates = semantic_candidates

        reranked_scores: dict[int, float] = {}
        if request.rerank_strategy.value != "disabled" and candidates:
            reranked_scores = rerank_candidates(
                query=rewrite.effective_query,
                candidates=[
                    {
                        "chunk_id": candidate.chunk_id,
                        "content": candidate.content,
                        "semantic_score": candidate.final_score,
                    }
                    for candidate in candidates
                ],
                alpha=request.rerank_alpha,
            )
            for candidate in candidates:
                if candidate.chunk_id in reranked_scores:
                    candidate.final_score = reranked_scores[candidate.chunk_id]

        candidates.sort(key=lambda item: item.final_score, reverse=True)
        candidates = candidates[: request.k]

        return SearchResponse(
            query=request.query,
            effective_query=rewrite.effective_query,
            k=request.k,
            candidate_pool_k=candidate_pool_k,
            score_threshold=request.score_threshold,
            rewrite_strategy=request.rewrite_strategy,
            search_strategy=request.search_strategy,
            rerank_strategy=request.rerank_strategy,
            rrf_smoothing_k=(
                request.rrf_smoothing_k if request.search_strategy == SearchStrategy.HYBRID else None
            ),
            rewrite_notes=rewrite.notes,
            search_time_ms=round((time.perf_counter() - started_at) * 1000, 2),
            low_confidence=len(candidates) == 0,
            total_candidates_considered=len(candidates),
            results=[
                SearchResult(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    chunk_type=item.chunk_type,
                    content=item.content,
                    distance=round(item.distance, 6),
                    score=round(item.final_score, 6),
                    semantic_score=round(item.semantic_score, 6),
                    lexical_score=(
                        round(item.lexical_score, 6) if item.lexical_score is not None else None
                    ),
                    fusion_score=round(item.fusion_score, 6) if item.fusion_score is not None else None,
                    rerank_score=(
                        round(reranked_scores[item.chunk_id], 6)
                        if item.chunk_id in reranked_scores
                        else None
                    ),
                    metadata=item.metadata,
                )
                for item in candidates
            ],
        )

    async def _search_semantic_candidates(
        self,
        *,
        session: AsyncSession,
        query: str,
        request: SearchRequest,
        limit: int,
    ) -> list[SearchCandidate]:
        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        query_vector = embedder.embed_one(query)

        indexed_embedding = cast(ChunkRecord.embedding, HALFVEC(EMBEDDING_DIMENSIONS))
        distance = indexed_embedding.cosine_distance(query_vector)
        semantic_score = 1 - distance

        stmt = (
            select(
                ChunkRecord.id,
                ChunkRecord.document_id,
                ChunkRecord.chunk_type,
                ChunkRecord.content,
                ChunkRecord.metadata_json,
                distance.label("distance"),
                semantic_score.label("semantic_score"),
            )
            .join(DocumentRecord, DocumentRecord.id == ChunkRecord.document_id)
            .where(ChunkRecord.embedding.is_not(None))
        )

        stmt = self._apply_filters(stmt, request.filters)
        if request.score_threshold is not None:
            stmt = stmt.where(semantic_score >= request.score_threshold)

        rows = (await session.execute(stmt.order_by(distance.asc()).limit(limit))).all()
        return [
            SearchCandidate(
                chunk_id=int(row.id),
                document_id=int(row.document_id),
                chunk_type=row.chunk_type,
                content=row.content,
                metadata=row.metadata_json,
                distance=float(row.distance),
                semantic_score=float(row.semantic_score),
                lexical_score=None,
                fusion_score=None,
                final_score=float(row.semantic_score),
            )
            for row in rows
        ]

    async def _search_lexical_candidates(
        self,
        *,
        session: AsyncSession,
        query: str,
        request: SearchRequest,
        limit: int,
    ) -> list[SearchCandidate]:
        ts_query = func.websearch_to_tsquery(TEXT_SEARCH_CONFIG, query)
        lexical_score = func.ts_rank(ChunkRecord.content_tsv, ts_query)

        stmt = (
            select(
                ChunkRecord.id,
                ChunkRecord.document_id,
                ChunkRecord.chunk_type,
                ChunkRecord.content,
                ChunkRecord.metadata_json,
                lexical_score.label("lexical_score"),
            )
            .join(DocumentRecord, DocumentRecord.id == ChunkRecord.document_id)
            .where(ChunkRecord.content_tsv.op("@@")(ts_query))
        )
        stmt = self._apply_filters(stmt, request.filters)

        rows = (await session.execute(stmt.order_by(lexical_score.desc()).limit(limit))).all()
        return [
            SearchCandidate(
                chunk_id=int(row.id),
                document_id=int(row.document_id),
                chunk_type=row.chunk_type,
                content=row.content,
                metadata=row.metadata_json,
                distance=1.0,
                semantic_score=0.0,
                lexical_score=float(row.lexical_score),
                fusion_score=None,
                final_score=float(row.lexical_score),
            )
            for row in rows
        ]

    def _fuse_hybrid_candidates(
        self,
        *,
        semantic_candidates: list[SearchCandidate],
        lexical_candidates: list[SearchCandidate],
        smoothing_k: int,
    ) -> list[SearchCandidate]:
        merged: dict[int, SearchCandidate] = {
            candidate.chunk_id: candidate for candidate in semantic_candidates
        }

        for candidate in lexical_candidates:
            existing = merged.get(candidate.chunk_id)
            if existing is None:
                merged[candidate.chunk_id] = candidate
                continue
            existing.lexical_score = candidate.lexical_score

        fusion_scores = reciprocal_rank_fusion(
            [
                [candidate.chunk_id for candidate in semantic_candidates],
                [candidate.chunk_id for candidate in lexical_candidates],
            ],
            smoothing_k=smoothing_k,
        )

        for chunk_id, score in fusion_scores.items():
            merged[chunk_id].fusion_score = score
            merged[chunk_id].final_score = score

        return sorted(merged.values(), key=lambda item: item.final_score, reverse=True)

    def _apply_filters(self, stmt, filters: SearchFilters | None):
        if filters is None:
            return stmt

        if filters.client_sector:
            stmt = stmt.where(
                ChunkRecord.metadata_json["client_sector"].astext == filters.client_sector
            )
        if filters.main_technology:
            stmt = stmt.where(
                ChunkRecord.metadata_json["main_technology"].astext == filters.main_technology
            )
        if filters.year is not None:
            stmt = stmt.where(ChunkRecord.metadata_json["year"].astext == str(filters.year))
        if filters.complexity:
            stmt = stmt.where(
                ChunkRecord.metadata_json["complexity"].astext == filters.complexity.value
            )
        if filters.chunk_type:
            stmt = stmt.where(ChunkRecord.chunk_type == filters.chunk_type)
        if filters.document_type:
            stmt = stmt.where(DocumentRecord.document_type == filters.document_type)
        return stmt
