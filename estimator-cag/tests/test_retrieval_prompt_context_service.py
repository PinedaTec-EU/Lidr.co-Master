from __future__ import annotations

import pytest

from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType, RetrievalContextConfig
from app.services import retrieval_prompt_context_service as service


class FakeAsyncSession:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSessionFactory:
    def __call__(self):
        return FakeAsyncSession()


class FakeRetrievalAugmentationService:
    async def assemble_context(self, *, session, request):
        from app.embedding_pipeline.schemas import ContextAssemblyResponse, QueryRewriteStrategy, SearchResponse

        return ContextAssemblyResponse(
            search=SearchResponse(
                query=request.query,
                effective_query="normalized query",
                k=request.k,
                score_threshold=request.score_threshold,
                rewrite_strategy=QueryRewriteStrategy.NORMALIZE,
                rewrite_notes=["removed conversational prefix"],
                search_time_ms=10.0,
                results=[],
            ),
            context_text="[Chunk 11] useful retrieval context",
            included_chunks=[
                {
                    "chunk_id": 11,
                    "document_id": 2,
                    "chunk_type": "budget_component",
                    "score": 0.81,
                    "metadata": {"budget_id": "BUD-2024-001"},
                    "excerpt": "useful retrieval context",
                }
            ],
            truncated=False,
        )


@pytest.mark.anyio
async def test_resolve_retrieval_prompt_context_returns_none_when_disabled(monkeypatch) -> None:
    request = EstimationRequest(
        description="Portal B2B con autenticación, reporting y notificaciones automáticas por email.",
        project_type=ProjectType.WEB_SAAS,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.NARRATIVE,
    )

    result = await service.resolve_retrieval_prompt_context(request)

    assert result is None


@pytest.mark.anyio
async def test_resolve_retrieval_prompt_context_builds_prompt_context(monkeypatch) -> None:
    request = EstimationRequest(
        description="Portal B2B con autenticación, reporting y notificaciones automáticas por email.",
        project_type=ProjectType.WEB_SAAS,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.NARRATIVE,
        retrieval=RetrievalContextConfig(enabled=True, rewrite_strategy="normalize"),
    )

    monkeypatch.setattr(service, "AsyncSessionLocal", FakeSessionFactory())
    monkeypatch.setattr(service, "RetrievalAugmentationService", lambda: FakeRetrievalAugmentationService())

    result = await service.resolve_retrieval_prompt_context(request)

    assert result is not None
    assert result.effective_query == "normalized query"
    assert result.included_chunks_count == 1
    assert "useful retrieval context" in result.context_text
