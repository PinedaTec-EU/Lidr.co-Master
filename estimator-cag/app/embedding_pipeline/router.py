from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.db import get_async_session
from app.embedding_pipeline.ingest_service import (
    DocumentAlreadyIngestedError,
    EmbeddingIngestService,
)
from app.embedding_pipeline.search_service import SemanticSearchService
from app.embedding_pipeline.schemas import (
    ChunkingStrategy,
    DocumentIngestRequest,
    DocumentIngestResponse,
    EmbeddingModelName,
    SearchRequest,
    SearchResponse,
)

router = APIRouter(tags=["embeddings"])
logger = structlog.get_logger()


@router.get("/embeddings/options")
def get_embedding_options() -> dict[str, list[str]]:
    return {
        "chunking_strategies": [strategy.value for strategy in ChunkingStrategy],
        "embedding_models": [model.value for model in EmbeddingModelName],
    }


@router.post("/embeddings/ingest", response_model=DocumentIngestResponse)
async def ingest_embeddings(
    request: DocumentIngestRequest,
    session: AsyncSession = Depends(get_async_session),
) -> DocumentIngestResponse:
    service = EmbeddingIngestService()
    try:
        return await service.ingest_document(session=session, request=request)
    except DocumentAlreadyIngestedError as exc:
        return JSONResponse(
            status_code=409,
            content={"detail": "Document already ingested", "document_id": exc.document_id},
        )
    except Exception as exc:
        logger.exception("embedding_ingest_failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while generating embeddings.",
        ) from exc


@router.post("/search", response_model=SearchResponse)
async def search_embeddings(
    request: SearchRequest,
    session: AsyncSession = Depends(get_async_session),
) -> SearchResponse:
    service = SemanticSearchService()
    try:
        return await service.search(session=session, request=request)
    except Exception as exc:
        logger.exception("embedding_search_failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while searching embeddings.",
        ) from exc
