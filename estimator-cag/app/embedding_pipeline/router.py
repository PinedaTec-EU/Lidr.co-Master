from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, HTTPException

from app.embedding_pipeline.chunker import build_chunker
from app.embedding_pipeline.contextualizer import ChunkContextualizer
from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.evaluation import summarize_case
from app.embedding_pipeline.schemas import (
    ChunkingStrategy,
    EmbeddingModelName,
    IngestRequest,
    IngestResponse,
    IngestStats,
    RetrievalEvalRequest,
    RetrievalEvalResponse,
    RetrievalEvalSummary,
    SearchRequest,
    SearchResponse,
    SearchStats,
)
from app.embedding_pipeline.vector_store import PgVectorStore

router = APIRouter(tags=["embeddings"])
logger = structlog.get_logger()


@router.get("/embeddings/options")
def get_embedding_options() -> dict[str, list[str]]:
    return {
        "chunking_strategies": [strategy.value for strategy in ChunkingStrategy],
        "embedding_models": [model.value for model in EmbeddingModelName],
    }


@router.post("/embeddings/ingest", response_model=IngestResponse)
def ingest_embeddings(request: IngestRequest) -> IngestResponse:
    started_at = time.perf_counter()
    chunker = build_chunker(request.chunking)
    embedder = OpenAIEmbedder(model_name=request.embedding_model)

    try:
        chunks = chunker.chunk(request.budgets)
        if request.chunking.llm_enrich_context:
            contextualizer = ChunkContextualizer()
            budgets_by_id = {budget.budget_id: budget for budget in request.budgets}
            chunks = contextualizer.enrich_chunks(chunks, budgets_by_id)
        embedded_chunks = embedder.embed_many(chunks)

        persisted_chunks = 0
        if request.persist:
            store = PgVectorStore()
            store.ensure_schema()
            persisted_chunks = store.upsert_chunks(embedded_chunks)
    except Exception as exc:
        logger.exception("embedding_ingest_failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while generating embeddings.",
        ) from exc

    total_tokens = sum(chunk.token_count for chunk in chunks)
    processing_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    stats = IngestStats(
        total_budgets=len(request.budgets),
        total_chunks=len(embedded_chunks),
        total_tokens=total_tokens,
        estimated_cost_usd=embedder.estimate_cost_usd(total_tokens),
        processing_latency_ms=processing_latency_ms,
        persisted_chunks=persisted_chunks,
    )
    return IngestResponse(chunks=embedded_chunks, stats=stats)


@router.post("/embeddings/search", response_model=SearchResponse)
def search_embeddings(request: SearchRequest) -> SearchResponse:
    started_at = time.perf_counter()
    try:
        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        query_embedding = embedder.embed_one(request.query)
        store = PgVectorStore()
        store.ensure_schema()
        matches = store.search(
            query_embedding=query_embedding,
            embedding_model=request.embedding_model,
            top_k=request.top_k,
            filters=request.filters,
        )
    except Exception as exc:
        logger.exception("embedding_search_failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while searching embeddings.",
        ) from exc

    return SearchResponse(
        matches=matches,
        stats=SearchStats(
            returned_matches=len(matches),
            latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
        ),
    )


@router.post("/embeddings/evaluate", response_model=RetrievalEvalResponse)
def evaluate_embeddings(request: RetrievalEvalRequest) -> RetrievalEvalResponse:
    try:
        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        store = PgVectorStore()
        store.ensure_schema()
        results = []
        for case in request.cases:
            query_embedding = embedder.embed_one(case.query)
            matches = store.search(
                query_embedding=query_embedding,
                embedding_model=request.embedding_model,
                top_k=request.top_k,
                filters=case.filters,
            )
            results.append(
                summarize_case(
                    query=case.query,
                    relevant_chunk_ids=case.relevant_chunk_ids,
                    retrieved_chunk_ids=[match.chunk_id for match in matches],
                    k=request.top_k,
                )
            )
    except Exception as exc:
        logger.exception("embedding_eval_failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while evaluating semantic retrieval.",
        ) from exc

    mean_recall = round(sum(result.recall_at_k for result in results) / len(results), 4)
    mean_ndcg = round(sum(result.ndcg_at_k for result in results) / len(results), 4)
    return RetrievalEvalResponse(
        cases=results,
        summary=RetrievalEvalSummary(
            mean_recall_at_k=mean_recall,
            mean_ndcg_at_k=mean_ndcg,
        ),
    )
