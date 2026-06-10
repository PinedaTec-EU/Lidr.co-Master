from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.embedding_pipeline.schemas import Budget, Chunk


class ChunkContextualizer:
    def __init__(self, client: OpenAI | None = None) -> None:
        if client is None and not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required to enrich chunks with LLM context.")
        self.client = client or OpenAI(
            api_key=settings.openai_api_key or None,
            base_url=settings.openai_base_url or None,
        )

    def enrich_chunks(self, chunks: list[Chunk], budgets_by_id: dict[str, Budget]) -> list[Chunk]:
        enriched: list[Chunk] = []
        for chunk in chunks:
            budget = budgets_by_id.get(chunk.metadata.budget_id)
            context_line = self._context_line(chunk.text, budget.project_summary if budget else "")
            enriched.append(
                chunk.model_copy(
                    update={
                        "llm_context": context_line,
                        "text": f"[LLM context: {context_line}]\n{chunk.text}",
                    }
                )
            )
        return enriched

    def _context_line(self, chunk_text: str, project_summary: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.embedding_context_model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write one short sentence that explains how this chunk fits into the parent software "
                        "project. Keep it factual, under 25 words, and do not repeat the full chunk."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Project summary: {project_summary}\n\nChunk:\n{chunk_text}",
                },
            ],
        )
        content = response.choices[0].message.content or ""
        return content.strip()
