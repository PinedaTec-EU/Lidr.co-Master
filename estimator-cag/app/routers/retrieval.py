from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.embedding_pipeline.augmentation_service import RetrievalAugmentationService
from app.embedding_pipeline.db import get_async_session
from app.embedding_pipeline.schemas import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
    SearchRequest,
    SearchResponse,
)
from app.embedding_pipeline.search_service import SemanticSearchService
from app.rate_limit import enforce_rate_limit
from app.security import require_retrieval_key

router = APIRouter(tags=["retrieval"])


@router.post("/retrieval/search", response_model=SearchResponse)
async def search_retrieval(
    request: Request,
    payload: SearchRequest,
    session: AsyncSession = Depends(get_async_session),
    x_api_key: str = Depends(require_retrieval_key),
) -> SearchResponse:
    enforce_rate_limit(
        request=request,
        x_api_key=x_api_key,
        limit=settings.retrieval_rate_limit_per_minute,
        namespace="retrieval",
    )
    service = SemanticSearchService()
    try:
        return await service.search(session=session, request=payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected error while searching retrieval data.") from exc


@router.post("/retrieval/context", response_model=ContextAssemblyResponse)
async def assemble_retrieval_context(
    request: Request,
    payload: ContextAssemblyRequest,
    session: AsyncSession = Depends(get_async_session),
    x_api_key: str = Depends(require_retrieval_key),
) -> ContextAssemblyResponse:
    enforce_rate_limit(
        request=request,
        x_api_key=x_api_key,
        limit=settings.retrieval_rate_limit_per_minute,
        namespace="retrieval",
    )
    service = RetrievalAugmentationService()
    try:
        return await service.assemble_context(session=session, request=payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while assembling retrieval context.",
        ) from exc
