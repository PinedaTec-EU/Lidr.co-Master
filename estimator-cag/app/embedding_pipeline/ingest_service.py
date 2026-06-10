from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.chunker import build_chunker
from app.embedding_pipeline.contextualizer import ChunkContextualizer
from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.models import ChunkRecord, DocumentRecord
from app.embedding_pipeline.schemas import DocumentIngestRequest, DocumentIngestResponse


class DocumentAlreadyIngestedError(Exception):
    def __init__(self, document_id: int) -> None:
        super().__init__("Document already ingested")
        self.document_id = document_id


class EmbeddingIngestService:
    async def ingest_document(
        self,
        *,
        session: AsyncSession,
        request: DocumentIngestRequest,
    ) -> DocumentIngestResponse:
        started_at = time.perf_counter()
        chunker = build_chunker(request.chunking)
        chunks = chunker.chunk([request.content])
        if request.chunking.llm_enrich_context:
            contextualizer = ChunkContextualizer()
            chunks = contextualizer.enrich_chunks(chunks, {request.content.budget_id: request.content})

        embedder = OpenAIEmbedder(model_name=request.embedding_model)
        embedded_chunks = embedder.embed_many(chunks)

        async with session.begin():
            existing = await session.scalar(
                select(DocumentRecord).where(DocumentRecord.source_path == request.source_path)
            )
            if existing is not None:
                raise DocumentAlreadyIngestedError(existing.id)

            document = DocumentRecord(
                source_path=request.source_path,
                document_type=request.document_type,
                metadata_json={
                    "budget_id": request.content.budget_id,
                    "client_name": request.content.client_metadata.name,
                    "client_sector": request.content.client_metadata.sector,
                    "country": request.content.client_metadata.country,
                    "main_technology": request.content.main_technology,
                    "year": request.content.year,
                    "chunking_strategy": request.chunking.strategy.value,
                },
            )
            session.add(document)
            await session.flush()

            chunk_records = [
                ChunkRecord(
                    document_id=document.id,
                    chunk_type=_chunk_type(chunk.chunk_id),
                    content=chunk.text,
                    embedding=chunk.embedding,
                    metadata_json={
                        "chunk_id": chunk.chunk_id,
                        "budget_id": chunk.metadata.budget_id,
                        "component_id": chunk.metadata.component_id,
                        "client_sector": chunk.metadata.client_sector,
                        "main_technology": chunk.metadata.main_technology,
                        "year": chunk.metadata.year,
                        "complexity": chunk.metadata.complexity.value,
                        "estimated_hours": chunk.metadata.estimated_hours,
                        "token_count": chunk.token_count,
                        "chunking_strategy": chunk.chunking_strategy.value,
                        "embedding_model": chunk.embedding_model.value,
                        "llm_context": chunk.llm_context,
                    },
                )
                for chunk in embedded_chunks
            ]
            session.add_all(chunk_records)

        return DocumentIngestResponse(
            document_id=document.id,
            chunks_created=len(embedded_chunks),
            embedding_dimension=embedder.dimensions(),
            ingestion_time_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )


def _chunk_type(chunk_id: str) -> str:
    if chunk_id.endswith("::summary"):
        return "budget_summary"
    return "budget_component"
