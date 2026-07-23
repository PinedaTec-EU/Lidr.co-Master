from __future__ import annotations

from app.embedding_pipeline.augmentation_service import RetrievalAugmentationService
from app.embedding_pipeline.db import AsyncSessionLocal
from app.embedding_pipeline.schemas import ContextAssemblyRequest
from app.schemas import EstimationRequest, RetrievalPromptContext


async def resolve_retrieval_prompt_context(
    request: EstimationRequest,
) -> RetrievalPromptContext | None:
    config = request.retrieval
    if not config.enabled:
        return None
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL is required when retrieval context is enabled.")

    query = (config.query_override or request.description).strip()
    service = RetrievalAugmentationService()
    async with AsyncSessionLocal() as session:
        assembled = await service.assemble_context(
            session=session,
            request=ContextAssemblyRequest(
                query=query,
                k=config.k,
                score_threshold=config.score_threshold,
                rewrite_strategy=config.rewrite_strategy,
                max_chunks=config.max_chunks,
                max_context_chars=config.max_context_chars,
                include_scores=config.include_scores,
            ),
        )

    if not assembled.context_text.strip():
        return None

    return RetrievalPromptContext(
        query=query,
        effective_query=assembled.search.effective_query,
        context_text=assembled.context_text,
        included_chunks_count=len(assembled.included_chunks),
        retrieved_results_count=len(assembled.search.results),
        truncated=assembled.truncated,
        source_refs=[str(item.chunk_id) for item in assembled.included_chunks],
    )
