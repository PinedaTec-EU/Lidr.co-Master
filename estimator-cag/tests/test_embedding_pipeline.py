import json
from pathlib import Path

from app.embedding_pipeline.db import Base
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.chunker import JSONStructuralChunker
from app.embedding_pipeline.schemas import (
    ComplexityLevel,
    DocumentIngestRequest,
    DocumentIngestResponse,
    QueryRewriteStrategy,
    SearchResponse,
)
from app.embedding_pipeline.db import get_async_session
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


SAMPLE_BUDGETS = [
    {
        "budget_id": "BUD-2024-014",
        "client_metadata": {"name": "FintechCorp", "sector": "finance", "country": "ES"},
        "project_summary": "Mobile banking API with OAuth 2.0 authentication and PSD2 compliance",
        "main_technology": "ruby_on_rails",
        "year": 2024,
        "total_estimated_hours": 480,
        "components": [
            {
                "component_id": "AUTH-001",
                "name": "OAuth 2.0 authentication backend",
                "description": "Authorization code and refresh token flows for the mobile banking API.",
                "tech_stack": ["ruby_on_rails", "postgresql", "redis"],
                "complexity": "high",
                "estimated_hours": 120,
            },
            {
                "component_id": "AUDIT-002",
                "name": "Audit trail and compliance reporting",
                "description": "Operational audit logs and compliance-ready reporting exports.",
                "tech_stack": ["ruby_on_rails", "postgresql"],
                "complexity": "medium",
                "estimated_hours": 80,
            },
        ],
    }
]


def test_ingest_request_accepts_valid_payload() -> None:
    request = DocumentIngestRequest(
        source_path="data/budgets/budget_2024_q1_fintech.json",
        document_type="historical_budget",
        content=SAMPLE_BUDGETS[0],
    )

    assert request.content.components[0].complexity is ComplexityLevel.HIGH
    assert request.content.budget_id == "BUD-2024-014"


def test_structural_chunker_creates_one_chunk_per_component() -> None:
    request = DocumentIngestRequest(
        source_path="data/budgets/budget_2024_q1_fintech.json",
        document_type="historical_budget",
        content=SAMPLE_BUDGETS[0],
    )
    chunker = JSONStructuralChunker()

    chunks = chunker.chunk([request.content])

    assert len(chunks) == 2
    assert chunks[0].chunk_id == "BUD-2024-014::AUTH-001"
    assert "Client sector: finance" in chunks[0].text
    assert chunks[0].metadata.main_technology == "ruby_on_rails"
    assert chunks[0].token_count > 0


def test_sample_file_matches_ingest_request_schema() -> None:
    payload = json.loads(Path("data/budgets_sample.json").read_text())
    assert "budgets" in payload
    assert len(payload["budgets"]) == 15

    request = DocumentIngestRequest(
        source_path="data/budgets/budget_2024_q1_fintech.json",
        document_type="historical_budget",
        content=payload["budgets"][0],
    )

    assert request.content.budget_id.startswith("BUD-2024-")


def test_sqlalchemy_metadata_contains_documents_and_chunks() -> None:
    assert DocumentRecord.__tablename__ == "documents"
    assert ChunkRecord.__tablename__ == "chunks"
    assert "documents" in Base.metadata.tables
    assert "chunks" in Base.metadata.tables


def test_embeddings_ingest_endpoint_persists_document(monkeypatch) -> None:
    class FakeSession:
        pass

    class FakeService:
        async def ingest_document(self, *, session, request):
            assert isinstance(session, FakeSession)
            assert request.document_type == "historical_budget"
            return DocumentIngestResponse(
                document_id=42,
                chunks_created=2,
                embedding_dimension=1536,
                ingestion_time_ms=123.45,
            )

    async def fake_session_dependency():
        yield FakeSession()

    app.dependency_overrides[get_async_session] = fake_session_dependency
    monkeypatch.setattr("app.embedding_pipeline.router.EmbeddingIngestService", FakeService)

    response = client.post(
        "/api/v1/embeddings/ingest",
        json={
            "source_path": "data/budgets/budget_2024_q1_fintech.json",
            "document_type": "historical_budget",
            "content": SAMPLE_BUDGETS[0],
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == 42
    assert body["chunks_created"] == 2
    assert body["embedding_dimension"] == 1536
    assert body["ingestion_time_ms"] == 123.45


def test_embeddings_ingest_endpoint_returns_409_for_duplicate_document(monkeypatch) -> None:
    class FakeSession:
        pass

    class FakeService:
        async def ingest_document(self, *, session, request):
            from app.embedding_pipeline.ingest_service import DocumentAlreadyIngestedError

            raise DocumentAlreadyIngestedError(42)

    async def fake_session_dependency():
        yield FakeSession()

    app.dependency_overrides[get_async_session] = fake_session_dependency
    monkeypatch.setattr("app.embedding_pipeline.router.EmbeddingIngestService", FakeService)

    response = client.post(
        "/api/v1/embeddings/ingest",
        json={
            "source_path": "data/budgets/budget_2024_q1_fintech.json",
            "document_type": "historical_budget",
            "content": SAMPLE_BUDGETS[0],
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert response.json() == {"detail": "Document already ingested", "document_id": 42}


def test_embeddings_search_endpoint_returns_matches(monkeypatch) -> None:
    class FakeSession:
        pass

    class FakeSearchService:
        async def search(self, *, session, request):
            assert isinstance(session, FakeSession)
            return SearchResponse(
                query=request.query,
                effective_query="OAuth authentication for banking",
                k=request.k,
                score_threshold=request.score_threshold,
                rewrite_strategy=request.rewrite_strategy,
                rewrite_notes=[],
                search_time_ms=87.0,
                results=[
                    {
                        "chunk_id": 156,
                        "document_id": 12,
                        "chunk_type": "budget_component",
                        "content": "Backend service implementation with JWT-based authentication...",
                        "distance": 0.231,
                        "score": 0.769,
                        "metadata": {
                            "scope": "backend",
                            "technologies": ["python", "fastapi"],
                        },
                    }
                ],
            )

    async def fake_session_dependency():
        yield FakeSession()

    app.dependency_overrides[get_async_session] = fake_session_dependency
    monkeypatch.setattr("app.embedding_pipeline.router.SemanticSearchService", FakeSearchService)

    response = client.post(
        "/api/v1/search",
        json={"query": "OAuth authentication for banking", "k": 3},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "OAuth authentication for banking"
    assert body["effective_query"] == "OAuth authentication for banking"
    assert body["k"] == 3
    assert body["score_threshold"] is None
    assert body["rewrite_strategy"] == QueryRewriteStrategy.DISABLED.value
    assert body["search_time_ms"] == 87.0
    assert body["results"][0]["chunk_id"] == 156
    assert body["results"][0]["document_id"] == 12
    assert body["results"][0]["score"] == 0.769
