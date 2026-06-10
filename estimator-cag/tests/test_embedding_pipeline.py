import json
from pathlib import Path

from app.embedding_pipeline.db import Base
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.chunker import JSONStructuralChunker
from app.embedding_pipeline.schemas import (
    ComplexityLevel,
    EmbeddedChunk,
    IngestRequest,
    SearchMatch,
)
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
    request = IngestRequest(budgets=SAMPLE_BUDGETS)

    assert request.budgets[0].components[0].complexity is ComplexityLevel.HIGH
    assert request.budgets[0].budget_id == "BUD-2024-014"


def test_structural_chunker_creates_one_chunk_per_component() -> None:
    request = IngestRequest(budgets=SAMPLE_BUDGETS)
    chunker = JSONStructuralChunker()

    chunks = chunker.chunk(request.budgets)

    assert len(chunks) == 2
    assert chunks[0].chunk_id == "BUD-2024-014::AUTH-001"
    assert "Client sector: finance" in chunks[0].text
    assert chunks[0].metadata.main_technology == "ruby_on_rails"
    assert chunks[0].token_count > 0


def test_sample_file_matches_ingest_request_schema() -> None:
    payload = json.loads(Path("data/budgets_sample.json").read_text())
    request = IngestRequest.model_validate(payload)

    assert len(request.budgets) == 15
    assert request.budgets[0].budget_id.startswith("BUD-2024-")


def test_sqlalchemy_metadata_contains_documents_and_chunks() -> None:
    assert DocumentRecord.__tablename__ == "documents"
    assert ChunkRecord.__tablename__ == "chunks"
    assert "documents" in Base.metadata.tables
    assert "chunks" in Base.metadata.tables


def test_embeddings_ingest_endpoint_returns_vectorized_chunks(monkeypatch) -> None:
    class FakeEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed_many(self, chunks):
            return [
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    token_count=chunk.token_count,
                    embedding=[0.1, 0.2, 0.3],
                )
                for chunk in chunks
            ]

        def estimate_cost_usd(self, total_tokens: int) -> float:
            return 0.000123

    monkeypatch.setattr("app.embedding_pipeline.router.OpenAIEmbedder", FakeEmbedder)

    response = client.post("/api/v1/embeddings/ingest", json={"budgets": SAMPLE_BUDGETS})

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total_budgets"] == 1
    assert body["stats"]["total_chunks"] == 2
    assert body["stats"]["estimated_cost_usd"] == 0.000123
    assert body["stats"]["processing_latency_ms"] >= 0
    assert body["chunks"][0]["chunk_id"] == "BUD-2024-014::AUTH-001"
    assert body["chunks"][0]["embedding"] == [0.1, 0.2, 0.3]


def test_embeddings_search_endpoint_returns_matches(monkeypatch) -> None:
    class FakeEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed_one(self, text: str):
            return [0.1, 0.2, 0.3]

    class FakeStore:
        def ensure_schema(self):
            return None

        def search(self, **kwargs):
            return [
                SearchMatch.model_validate(
                    {
                        "chunk_id": "BUD-2024-014::AUTH-001",
                        "text": "chunk text",
                        "metadata": {
                            "budget_id": "BUD-2024-014",
                            "component_id": "AUTH-001",
                            "client_sector": "finance",
                            "main_technology": "ruby_on_rails",
                            "year": 2024,
                            "complexity": "high",
                            "estimated_hours": 120,
                        },
                        "token_count": 42,
                        "chunking_strategy": "structural",
                        "embedding_model": "text-embedding-3-small",
                        "score": 0.91,
                    }
                )
            ]

    monkeypatch.setattr("app.embedding_pipeline.router.OpenAIEmbedder", FakeEmbedder)
    monkeypatch.setattr("app.embedding_pipeline.router.PgVectorStore", FakeStore)

    response = client.post(
        "/api/v1/embeddings/search",
        json={"query": "OAuth authentication for banking", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["returned_matches"] == 1
    assert body["matches"][0]["chunk_id"] == "BUD-2024-014::AUTH-001"
