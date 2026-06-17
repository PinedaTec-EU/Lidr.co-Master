from __future__ import annotations
from collections.abc import AsyncIterator, Iterator
import os
from pathlib import Path
import shutil
import subprocess
import time

from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
import psycopg
import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.embedding_pipeline.db import get_async_session
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.schemas import EmbeddedChunk
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "estimator-cag"
SYNC_DATABASE_URL = "postgresql://estimator:estimator@127.0.0.1:5432/estimator"
ASYNC_DATABASE_URL = "postgresql+asyncpg://estimator:estimator@127.0.0.1:5432/estimator"

SAMPLE_FINANCE_BUDGET = {
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

SAMPLE_ECOMMERCE_BUDGET = {
    "budget_id": "BUD-2024-015",
    "client_metadata": {"name": "ShopWave", "sector": "ecommerce", "country": "PT"},
    "project_summary": "Headless commerce backend with promotions and order orchestration",
    "main_technology": "nodejs",
    "year": 2024,
    "total_estimated_hours": 420,
    "components": [
        {
            "component_id": "CAT-001",
            "name": "Catalog and pricing service",
            "description": "Product catalog, dynamic pricing and promotions rules engine.",
            "tech_stack": ["nodejs", "mongodb"],
            "complexity": "medium",
            "estimated_hours": 110,
        }
    ],
}


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True, check=False).returncode == 0


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker is required for integration tests.")


@pytest.fixture(scope="session")
def integration_database() -> Iterator[None]:
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "pgvector"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "Integration database could not be started. "
            f"Docker compose failed for pgvector: {exc.stderr.strip()}"
        )

    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            with psycopg.connect(SYNC_DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                break
        except psycopg.Error:
            time.sleep(1)
    else:
        raise RuntimeError("pgvector database did not become ready in time.")

    os.environ["DATABASE_URL"] = ASYNC_DATABASE_URL
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture
async def integration_session_factory(
    integration_database: None,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(ASYNC_DATABASE_URL, future=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield session_factory
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(
    integration_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    async with integration_session_factory() as session:
        async with session.begin():
            await session.execute(delete(ChunkRecord))
            await session.execute(delete(DocumentRecord))
    yield


@pytest.fixture
async def api_client(
    integration_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        async with integration_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_ingest_endpoint_persists_document_and_chunks(
    monkeypatch: pytest.MonkeyPatch,
    integration_session_factory: async_sessionmaker[AsyncSession],
    api_client: AsyncClient,
) -> None:
    class FakeEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed_many(self, chunks):
            embedded = []
            for index, chunk in enumerate(chunks, start=1):
                vector = [0.0] * 1536
                vector[index - 1] = 1.0
                embedded.append(
                    EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=chunk.metadata,
                        token_count=chunk.token_count,
                        chunking_strategy=chunk.chunking_strategy,
                        llm_context=chunk.llm_context,
                        embedding=vector,
                        embedding_model="text-embedding-3-small",
                    )
                )
            return embedded

        def dimensions(self) -> int:
            return 1536

    monkeypatch.setattr("app.embedding_pipeline.ingest_service.OpenAIEmbedder", FakeEmbedder)

    response = await api_client.post(
        "/api/v1/embeddings/ingest",
        json={
            "source_path": "data/budgets/budget_finance.json",
            "document_type": "historical_budget",
            "content": SAMPLE_FINANCE_BUDGET,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["chunks_created"] == 2
    assert body["embedding_dimension"] == 1536

    async with integration_session_factory() as session:
        document = await session.scalar(select(DocumentRecord))
        chunks = (await session.execute(select(ChunkRecord).order_by(ChunkRecord.id))).scalars().all()

        assert document is not None
        assert document.source_path == "data/budgets/budget_finance.json"
        assert document.document_type == "historical_budget"
        assert len(chunks) == 2
        assert chunks[0].chunk_type == "budget_component"
        assert chunks[0].metadata_json["client_sector"] == "finance"
        assert chunks[1].metadata_json["component_id"] == "AUDIT-002"


@pytest.mark.anyio
async def test_search_endpoint_respects_metadata_filters(
    monkeypatch: pytest.MonkeyPatch,
    integration_session_factory: async_sessionmaker[AsyncSession],
    api_client: AsyncClient,
) -> None:
    class FakeIngestEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed_many(self, chunks):
            embedded = []
            for chunk in chunks:
                vector = [0.0] * 1536
                if chunk.metadata.client_sector == "finance":
                    vector[0] = 1.0
                else:
                    vector[1] = 1.0
                embedded.append(
                    EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=chunk.metadata,
                        token_count=chunk.token_count,
                        chunking_strategy=chunk.chunking_strategy,
                        llm_context=chunk.llm_context,
                        embedding=vector,
                        embedding_model="text-embedding-3-small",
                    )
                )
            return embedded

        def dimensions(self) -> int:
            return 1536

    class FakeQueryEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed_one(self, text: str):
            vector = [0.0] * 1536
            vector[1] = 1.0
            return vector

    monkeypatch.setattr("app.embedding_pipeline.ingest_service.OpenAIEmbedder", FakeIngestEmbedder)
    monkeypatch.setattr("app.embedding_pipeline.search_service.OpenAIEmbedder", FakeQueryEmbedder)

    for source_path, budget in [
        ("data/budgets/budget_finance.json", SAMPLE_FINANCE_BUDGET),
        ("data/budgets/budget_ecommerce.json", SAMPLE_ECOMMERCE_BUDGET),
    ]:
        response = await api_client.post(
            "/api/v1/embeddings/ingest",
            json={
                "source_path": source_path,
                "document_type": "historical_budget",
                "content": budget,
            },
        )
        assert response.status_code == 200

    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "catalog promotions service",
            "k": 5,
            "filters": {"client_sector": "finance"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert all(result["metadata"]["client_sector"] == "finance" for result in body["results"])

    async with integration_session_factory() as session:
        documents = (await session.execute(select(DocumentRecord).order_by(DocumentRecord.id))).scalars().all()
        chunks = (await session.execute(select(ChunkRecord).order_by(ChunkRecord.id))).scalars().all()

        assert len(documents) == 2
        assert {document.source_path for document in documents} == {
            "data/budgets/budget_finance.json",
            "data/budgets/budget_ecommerce.json",
        }
        assert len(chunks) == 3
        assert {chunk.metadata_json["client_sector"] for chunk in chunks} == {"finance", "ecommerce"}


@pytest.mark.anyio
async def test_migrations_create_hnsw_vector_index(
    integration_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with integration_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' AND indexname = 'ix_chunks_embedding_halfvec_hnsw'
                """
            )
        )
        row = result.one_or_none()

    assert row is not None
    assert row.indexname == "ix_chunks_embedding_halfvec_hnsw"
    assert "USING hnsw" in row.indexdef
    assert "embedding)::halfvec(1536)" in row.indexdef
    assert "halfvec_cosine_ops" in row.indexdef
