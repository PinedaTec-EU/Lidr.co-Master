from __future__ import annotations

from math import ceil
from typing import Protocol

import tiktoken

from app.embedding_pipeline.schemas import (
    Budget,
    BudgetComponent,
    Chunk,
    ChunkMetadata,
    ChunkingOptions,
    ChunkingStrategy,
)

EMBEDDING_MODEL = "text-embedding-3-small"


class Chunker(Protocol):
    def chunk(self, budgets: list[Budget]) -> list[Chunk]: ...


def build_chunker(options: ChunkingOptions) -> Chunker:
    if options.strategy is ChunkingStrategy.FIXED_WINDOW:
        return FixedWindowChunker(
            max_characters=options.max_characters,
            overlap_characters=options.overlap_characters,
            include_parent_context=options.include_parent_context,
        )
    if options.strategy is ChunkingStrategy.HIERARCHICAL:
        return HierarchicalChunker(include_parent_context=options.include_parent_context)
    return JSONStructuralChunker(include_parent_context=options.include_parent_context)


class BaseBudgetChunker:
    def __init__(self, *, model_name: str = EMBEDDING_MODEL, include_parent_context: bool = True) -> None:
        self._encoding = tiktoken.encoding_for_model(model_name)
        self.include_parent_context = include_parent_context

    def _token_count(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def _metadata(self, budget: Budget, component: BudgetComponent) -> ChunkMetadata:
        return ChunkMetadata(
            budget_id=budget.budget_id,
            component_id=component.component_id,
            client_sector=budget.client_metadata.sector,
            main_technology=budget.main_technology,
            year=budget.year,
            complexity=component.complexity,
            estimated_hours=component.estimated_hours,
        )

    def _header(self, budget: Budget) -> str:
        if not self.include_parent_context:
            return ""
        return (
            f"[Project: {budget.project_summary}]\n"
            f"[Client sector: {budget.client_metadata.sector} | Year: {budget.year} | "
            f"Main tech: {budget.main_technology}]\n\n"
        )

    def _component_body(self, component: BudgetComponent) -> str:
        tech_stack = ", ".join(component.tech_stack) if component.tech_stack else "n/a"
        dependencies = ", ".join(component.dependencies) if component.dependencies else "none"
        return (
            f"Component: {component.name}\n"
            f"Description: {component.description}\n"
            f"Tech stack: {tech_stack}\n"
            f"Complexity: {component.complexity.value}\n"
            f"Estimated hours: {component.estimated_hours}\n"
            f"Dependencies: {dependencies}"
        )


class JSONStructuralChunker(BaseBudgetChunker):
    def chunk(self, budgets: list[Budget]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for budget in budgets:
            for component in budget.components:
                text = self._header(budget) + self._component_body(component)
                chunks.append(
                    Chunk(
                        chunk_id=f"{budget.budget_id}::{component.component_id}",
                        text=text,
                        metadata=self._metadata(budget, component),
                        token_count=self._token_count(text),
                        chunking_strategy=ChunkingStrategy.STRUCTURAL,
                    )
                )
        return chunks


class FixedWindowChunker(BaseBudgetChunker):
    def __init__(
        self,
        *,
        model_name: str = EMBEDDING_MODEL,
        include_parent_context: bool = True,
        max_characters: int = 900,
        overlap_characters: int = 120,
    ) -> None:
        super().__init__(model_name=model_name, include_parent_context=include_parent_context)
        self.max_characters = max_characters
        self.overlap_characters = min(overlap_characters, max_characters // 2)

    def chunk(self, budgets: list[Budget]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for budget in budgets:
            header = self._header(budget)
            for component in budget.components:
                body = self._component_body(component)
                windows = _split_text(body, self.max_characters - len(header), self.overlap_characters)
                for index, window in enumerate(windows, start=1):
                    text = f"{header}{window}"
                    chunks.append(
                        Chunk(
                            chunk_id=f"{budget.budget_id}::{component.component_id}::part-{index:02d}",
                            text=text,
                            metadata=self._metadata(budget, component),
                            token_count=self._token_count(text),
                            chunking_strategy=ChunkingStrategy.FIXED_WINDOW,
                        )
                    )
        return chunks


class HierarchicalChunker(BaseBudgetChunker):
    def chunk(self, budgets: list[Budget]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for budget in budgets:
            summary_text = self._budget_summary(budget)
            summary_component = budget.components[0]
            chunks.append(
                Chunk(
                    chunk_id=f"{budget.budget_id}::summary",
                    text=summary_text,
                    metadata=self._metadata(budget, summary_component),
                    token_count=self._token_count(summary_text),
                    chunking_strategy=ChunkingStrategy.HIERARCHICAL,
                )
            )
            for component in budget.components:
                text = self._header(budget) + self._component_body(component)
                chunks.append(
                    Chunk(
                        chunk_id=f"{budget.budget_id}::{component.component_id}",
                        text=text,
                        metadata=self._metadata(budget, component),
                        token_count=self._token_count(text),
                        chunking_strategy=ChunkingStrategy.HIERARCHICAL,
                    )
                )
        return chunks

    def _budget_summary(self, budget: Budget) -> str:
        component_lines = "\n".join(
            f"- {component.name} ({component.estimated_hours}h, {component.complexity.value})"
            for component in budget.components
        )
        return (
            f"[Project summary chunk]\n"
            f"Budget id: {budget.budget_id}\n"
            f"Project: {budget.project_summary}\n"
            f"Sector: {budget.client_metadata.sector}\n"
            f"Main tech: {budget.main_technology}\n"
            f"Total estimated hours: {budget.total_estimated_hours}\n"
            f"Components:\n{component_lines}"
        )


def _split_text(text: str, max_characters: int, overlap_characters: int) -> list[str]:
    if len(text) <= max_characters:
        return [text]

    windows: list[str] = []
    start = 0
    step = max(max_characters - overlap_characters, 1)
    window_count = ceil(max(len(text) - overlap_characters, 0) / step)
    for _index in range(window_count):
        slice_end = min(start + max_characters, len(text))
        windows.append(text[start:slice_end].strip())
        if slice_end >= len(text):
            break
        start += step
    return windows
