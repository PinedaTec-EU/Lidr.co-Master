from __future__ import annotations

from app.application.cag_recent_analysis import RecentRunsAnalyzer
from app.application.llm_report_analysis import LLMReportAnalyst
from app.config import get_settings
from app.domain.models import AnalysisResult, RunReport
from app.domain.repositories import RunReportRepository
from app.domain.semantic import RunSemanticText, TokenSimilarity


class SemanticRunsAnalyzer:
    def __init__(
        self,
        repository: RunReportRepository,
        recent_analyzer: RecentRunsAnalyzer | None = None,
        text_builder: RunSemanticText | None = None,
        similarity: TokenSimilarity | None = None,
    ) -> None:
        self._repository = repository
        self._recent_analyzer = recent_analyzer or RecentRunsAnalyzer(repository)
        self._text_builder = text_builder or RunSemanticText()
        self._similarity = similarity or TokenSimilarity()

    def retrieve_similar(self, current: RunReport, top_k: int = 8) -> list[tuple[RunReport, float]]:
        if top_k < 1:
            raise ValueError("top_k must be greater than zero")

        current_text = self._text_builder.build(current)
        candidates = [run for run in self._repository.all() if run.run_id != current.run_id]
        scored = [
            (run, self._similarity.score(current_text, self._text_builder.build(run)))
            for run in candidates
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

    def analyze(
        self,
        current: RunReport,
        top_k: int = 8,
        enrich_with_llm: bool = True,
    ) -> AnalysisResult:
        similar = self.retrieve_similar(current, top_k=top_k)
        sources = tuple(run.run_id for run, score in similar if score > 0)

        recent_like_repository = _InMemoryWindowRepository([current, *[run for run, _ in similar]])
        result = RecentRunsAnalyzer(recent_like_repository).analyze(
            workflow=current.workflow,
            environment=current.environment,
            limit=min(top_k + 1, len(similar) + 1),
            enrich_with_llm=False,
        )

        semantic_result = AnalysisResult(
            mode="semantic-rag",
            workflow=result.workflow,
            environment=result.environment,
            current_run_id=result.current_run_id,
            health_score=result.health_score,
            summary=f"{result.summary} Semantic retrieval contributed {len(sources)} historical sources.",
            failure_type=result.failure_type,
            regressions=result.regressions,
            recommendations=result.recommendations,
            sources=sources,
        )
        if not enrich_with_llm:
            return semantic_result
        return LLMReportAnalyst(get_settings()).enrich(semantic_result, self.context_reports(current, top_k))

    def context_reports(self, current: RunReport, top_k: int = 8) -> list[RunReport]:
        return [current, *[run for run, _ in self.retrieve_similar(current, top_k=top_k)]]


class _InMemoryWindowRepository:
    def __init__(self, runs: list[RunReport]) -> None:
        self._runs = runs

    def latest(self, workflow: str, environment: str, limit: int) -> list[RunReport]:
        return [
            run for run in self._runs if run.workflow == workflow and run.environment == environment
        ][:limit]

    def all(self) -> list[RunReport]:
        return list(self._runs)
