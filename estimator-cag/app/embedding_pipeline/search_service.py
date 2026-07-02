from __future__ import annotations

import time
from datetime import date
from dataclasses import dataclass

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.hybrid_fusion import reciprocal_rank_fusion
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.query_fusion import interleave_rankings
from app.embedding_pipeline.query_rewrite import rewrite_query
from app.embedding_pipeline.reranker import rerank_candidates
from app.embedding_pipeline.search_routing import DOCUMENT_TYPES_BY_TARGET, route_search_targets
from app.embedding_pipeline.schemas import (
    QueryFusionStrategy,
    SearchFilters,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchStrategy,
    SearchTarget,
)
from app.embedding_pipeline.temporal import contextual_boost, temporal_weight

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
    temporal_weight: float | None = None
    contextual_boost: float | None = None


class SemanticSearchService:
    async def search(
        self,
        *,
        session: AsyncSession,
        request: SearchRequest,
    ) -> SearchResponse:
        started_at = time.perf_counter()
        rewrite = rewrite_query(query=request.query, strategy=request.rewrite_strategy)
        routing = route_search_targets(
            query=rewrite.effective_query,
            explicit_targets=request.target_collections,
        )
        effective_queries = rewrite.effective_queries[: request.max_rewrite_queries]
        candidate_pool_k = request.candidate_pool_k or request.k

        per_query_candidates = [
            await self._search_candidates_for_query(
                session=session,
                query=effective_query,
                request=request,
                limit=candidate_pool_k,
                targets=routing.targets,
            )
            for effective_query in effective_queries
        ]

        if len(per_query_candidates) == 1:
            candidates = per_query_candidates[0]
        else:
            candidates = self._fuse_rewritten_queries(
                per_query_candidates=per_query_candidates,
                fusion_strategy=rewrite.fusion_strategy,
                top_k=candidate_pool_k,
                smoothing_k=request.rrf_smoothing_k,
            )

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

        self._apply_soft_weights(
            candidates=candidates,
            query=rewrite.effective_query,
            request=request,
        )

        candidates.sort(key=lambda item: item.final_score, reverse=True)
        total_candidates_considered = len(candidates)
        candidates = candidates[: request.k]

        return SearchResponse(
            query=request.query,
            effective_query=rewrite.effective_query,
            effective_queries=effective_queries,
            k=request.k,
            candidate_pool_k=candidate_pool_k,
            score_threshold=request.score_threshold,
            rewrite_strategy=request.rewrite_strategy,
            query_fusion_strategy=rewrite.fusion_strategy,
            search_strategy=request.search_strategy,
            resolved_target_collections=routing.targets,
            routing_reason=routing.reason,
            rerank_strategy=request.rerank_strategy,
            rrf_smoothing_k=(
                request.rrf_smoothing_k
                if request.search_strategy == SearchStrategy.HYBRID
                or rewrite.fusion_strategy == QueryFusionStrategy.CONSENSUS
                else None
            ),
            rewrite_notes=rewrite.notes,
            search_time_ms=round((time.perf_counter() - started_at) * 1000, 2),
            low_confidence=len(candidates) == 0,
            total_candidates_considered=total_candidates_considered,
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
                    temporal_weight=(
                        round(item.temporal_weight, 6) if item.temporal_weight is not None else None
                    ),
                    contextual_boost=(
                        round(item.contextual_boost, 6) if item.contextual_boost is not None else None
                    ),
                    metadata=item.metadata,
                )
                for item in candidates
            ],
        )

    async def _search_candidates_for_query(
        self,
        *,
        session: AsyncSession,
        query: str,
        request: SearchRequest,
        limit: int,
        targets: list[SearchTarget],
    ) -> list[SearchCandidate]:
        if len(targets) > 1:
            per_target = [
                await self._search_candidates_for_query(
                    session=session,
                    query=query,
                    request=request,
                    limit=limit,
                    targets=[target],
                )
                for target in targets
            ]
            return self._fuse_rewritten_queries(
                per_query_candidates=per_target,
                fusion_strategy=QueryFusionStrategy.COVERAGE,
                top_k=limit,
                smoothing_k=request.rrf_smoothing_k,
            )

        semantic_candidates = await self._search_semantic_candidates(
            session=session,
            query=query,
            request=request,
            limit=limit,
            target=targets[0],
        )
        if request.search_strategy != SearchStrategy.HYBRID:
            return semantic_candidates

        lexical_candidates = await self._search_lexical_candidates(
            session=session,
            query=query,
            request=request,
            limit=limit,
            target=targets[0],
        )
        return self._fuse_hybrid_candidates(
            semantic_candidates=semantic_candidates,
            lexical_candidates=lexical_candidates,
            smoothing_k=request.rrf_smoothing_k,
        )

    async def _search_semantic_candidates(
        self,
        *,
        session: AsyncSession,
        query: str,
        request: SearchRequest,
        limit: int,
        target: SearchTarget,
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
        stmt = self._apply_target_filter(stmt, target)
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
        target: SearchTarget,
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
        stmt = self._apply_target_filter(stmt, target)

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

    def _fuse_rewritten_queries(
        self,
        *,
        per_query_candidates: list[list[SearchCandidate]],
        fusion_strategy: QueryFusionStrategy | None,
        top_k: int,
        smoothing_k: int,
    ) -> list[SearchCandidate]:
        merged: dict[int, SearchCandidate] = {}
        rankings: list[list[int]] = []

        for candidates in per_query_candidates:
            rankings.append([candidate.chunk_id for candidate in candidates])
            for candidate in candidates:
                existing = merged.get(candidate.chunk_id)
                if existing is None or candidate.final_score > existing.final_score:
                    merged[candidate.chunk_id] = candidate

        if fusion_strategy == QueryFusionStrategy.COVERAGE:
            ordered_ids = interleave_rankings(rankings, top_k=top_k)
            return [merged[chunk_id] for chunk_id in ordered_ids if chunk_id in merged]

        fusion_scores = reciprocal_rank_fusion(rankings, smoothing_k=smoothing_k)
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
        if filters.year_from is not None:
            stmt = stmt.where(
                ChunkRecord.metadata_json["year"].astext.cast(Integer) >= filters.year_from
            )
        if filters.year_to is not None:
            stmt = stmt.where(
                ChunkRecord.metadata_json["year"].astext.cast(Integer) <= filters.year_to
            )
        if filters.complexity:
            stmt = stmt.where(
                ChunkRecord.metadata_json["complexity"].astext == filters.complexity.value
            )
        if filters.chunk_type:
            stmt = stmt.where(ChunkRecord.chunk_type == filters.chunk_type)
        if filters.document_type:
            stmt = stmt.where(DocumentRecord.document_type == filters.document_type)
        return stmt

    def _apply_target_filter(self, stmt, target: SearchTarget):
        return stmt.where(
            DocumentRecord.document_type.in_(DOCUMENT_TYPES_BY_TARGET[target])
        )

    def _apply_soft_weights(
        self,
        *,
        candidates: list[SearchCandidate],
        query: str,
        request: SearchRequest,
    ) -> None:
        for candidate in candidates:
            boost = 1.0
            weight = 1.0
            if request.contextual_boost_enabled:
                boost = contextual_boost(
                    query=query,
                    client_sector=candidate.metadata.get("client_sector"),
                    main_technology=candidate.metadata.get("main_technology"),
                )
                candidate.contextual_boost = boost
            if request.temporal_decay_enabled:
                weight = temporal_weight(
                    document_year=candidate.metadata.get("year"),
                    now=date.today(),
                    half_life_days=request.temporal_half_life_days,
                )
                candidate.temporal_weight = weight
            candidate.final_score *= boost * weight
