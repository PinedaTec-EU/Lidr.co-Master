from __future__ import annotations

import pytest

from app.embedding_pipeline.augmentation_service import RetrievalAugmentationService
from app.embedding_pipeline.schemas import (
    ContextAssemblyRequest,
    QueryRewriteStrategy,
    SearchResponse,
)


class FakeSearchService:
    async def search(self, *, session, request):
        return SearchResponse(
            query=request.query,
            effective_query=request.query,
            k=request.k,
            score_threshold=request.score_threshold,
            rewrite_strategy=QueryRewriteStrategy.DISABLED,
            rewrite_notes=[],
            search_time_ms=12.5,
            results=[
                {
                    "chunk_id": 11,
                    "document_id": 2,
                    "chunk_type": "budget_component",
                    "content": (
                        "OAuth 2.0 authentication backend with banking compliance, audit logging, "
                        "role segregation, supplier onboarding, payment orchestration and "
                        "reporting obligations for regulated healthcare workflows. "
                        "Includes reconciliation checkpoints, exception handling and "
                        "operational monitoring for back-office teams."
                    ),
                    "distance": 0.14,
                    "score": 0.86,
                    "metadata": {
                        "budget_id": "BUD-2024-001",
                        "component_id": "AUTH-001",
                        "client_sector": "finance",
                        "main_technology": "ruby_on_rails",
                    },
                },
                {
                    "chunk_id": 12,
                    "document_id": 2,
                    "chunk_type": "budget_component",
                    "content": "Secondary chunk that should be truncated away when the context budget is very small.",
                    "distance": 0.22,
                    "score": 0.78,
                    "metadata": {
                        "budget_id": "BUD-2024-001",
                        "component_id": "AUDIT-002",
                        "client_sector": "finance",
                        "main_technology": "ruby_on_rails",
                    },
                },
            ],
        )


@pytest.mark.anyio
async def test_augmentation_service_builds_compact_context() -> None:
    service = RetrievalAugmentationService(search_service=FakeSearchService())
    response = await service.assemble_context(
        session=object(),
        request=ContextAssemblyRequest(
            query="oauth backend banking",
            k=5,
            max_chunks=2,
            max_context_chars=1000,
        ),
    )

    assert response.search.query == "oauth backend banking"
    assert len(response.included_chunks) == 2
    assert '<source id="11"' in response.context_text
    assert 'budget_id="BUD-2024-001"' in response.context_text
    assert 'score="0.860"' in response.context_text


@pytest.mark.anyio
async def test_augmentation_service_marks_truncation_when_budget_is_tight() -> None:
    service = RetrievalAugmentationService(search_service=FakeSearchService())
    response = await service.assemble_context(
        session=object(),
        request=ContextAssemblyRequest(
            query="oauth backend banking",
            k=5,
            max_chunks=2,
            max_context_chars=400,
        ),
    )

    assert response.truncated is True
    assert len(response.included_chunks) == 1
