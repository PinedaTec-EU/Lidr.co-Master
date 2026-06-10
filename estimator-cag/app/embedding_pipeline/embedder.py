from __future__ import annotations

import time

from openai import OpenAI, RateLimitError
import structlog

from app.config import settings
from app.embedding_pipeline.schemas import Chunk, EmbeddedChunk, EmbeddingModelName

EMBEDDING_BATCH_SIZE = 100
EMBEDDING_COSTS_PER_MILLION_INPUT_TOKENS_USD = {
    EmbeddingModelName.TEXT_EMBEDDING_3_SMALL: 0.02,
    EmbeddingModelName.TEXT_EMBEDDING_3_LARGE: 0.13,
}
EMBEDDING_DIMENSIONS = {
    EmbeddingModelName.TEXT_EMBEDDING_3_SMALL: 1536,
    EmbeddingModelName.TEXT_EMBEDDING_3_LARGE: 3072,
}
logger = structlog.get_logger()


class OpenAIEmbedder:
    def __init__(
        self,
        *,
        model_name: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        client: OpenAI | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        if client is None and not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required to generate embeddings.")
        self.client = client or OpenAI(
            api_key=settings.openai_api_key or None,
            base_url=settings.openai_base_url or None,
        )

    def embed_one(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name.value, input=text)
        return list(response.data[0].embedding)

    def embed_many(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        embedded_chunks: list[EmbeddedChunk] = []
        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start : start + self.batch_size]
            embeddings = self._embed_batch(batch)
            for chunk, embedding in zip(batch, embeddings, strict=True):
                embedded_chunks.append(
                    EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=chunk.metadata,
                        token_count=chunk.token_count,
                        chunking_strategy=chunk.chunking_strategy,
                        llm_context=chunk.llm_context,
                        embedding=embedding,
                        embedding_model=self.model_name,
                    )
                )
        return embedded_chunks

    def estimate_cost_usd(self, total_tokens: int) -> float:
        estimated_cost = (
            total_tokens / 1_000_000
        ) * EMBEDDING_COSTS_PER_MILLION_INPUT_TOKENS_USD[self.model_name]
        return round(estimated_cost, 8)

    def dimensions(self) -> int:
        return EMBEDDING_DIMENSIONS[self.model_name]

    def _embed_batch(self, batch: list[Chunk]) -> list[list[float]]:
        inputs = [chunk.text for chunk in batch]
        total_tokens = sum(chunk.token_count for chunk in batch)
        last_error: RateLimitError | None = None

        for attempt, delay_seconds in enumerate((0, 1, 2, 4), start=1):
            if delay_seconds:
                time.sleep(delay_seconds)

            started_at = time.perf_counter()
            try:
                response = self.client.embeddings.create(model=self.model_name.value, input=inputs)
                latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                logger.info(
                    "embedding_batch_processed",
                    batch_size=len(batch),
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    model=self.model_name.value,
                    attempt=attempt,
                )
                return [list(item.embedding) for item in response.data]
            except RateLimitError as exc:
                last_error = exc
                logger.warning(
                    "embedding_batch_rate_limited",
                    batch_size=len(batch),
                    total_tokens=total_tokens,
                    model=self.model_name.value,
                    attempt=attempt,
                )

        assert last_error is not None
        raise last_error
