from __future__ import annotations

from app.domain.models import AnalysisResult, RegressionSignal, RunReport, RunStatus, Severity
from app.domain.repositories import RunReportRepository
from app.domain.scoring import HealthScorer
from app.application.llm_report_analysis import LLMReportAnalyst
from app.config import get_settings


class RecentRunsAnalyzer:
    def __init__(self, repository: RunReportRepository, scorer: HealthScorer | None = None) -> None:
        self._repository = repository
        self._scorer = scorer or HealthScorer()

    def analyze(
        self,
        workflow: str,
        environment: str,
        limit: int = 5,
        enrich_with_llm: bool = True,
    ) -> AnalysisResult:
        if limit < 2:
            raise ValueError("limit must be at least 2 to compare the current run with history")

        runs = self._repository.latest(workflow=workflow, environment=environment, limit=limit)
        if not runs:
            raise ValueError("no reports found for workflow and environment")

        current = runs[0]
        history = runs[1:]
        regressions = self._detect_regressions(current, history)
        failure_type = self._scorer.dominant_failure_type(current)
        health_score = self._scorer.score(current, history)

        result = AnalysisResult(
            mode="recent-cag",
            workflow=current.workflow,
            environment=current.environment,
            current_run_id=current.run_id,
            health_score=health_score,
            summary=self._summarize(current, history, regressions),
            failure_type=failure_type,
            regressions=tuple(regressions),
            recommendations=tuple(self._recommend(current, regressions)),
            sources=tuple(run.run_id for run in runs),
        )
        if not enrich_with_llm:
            return result
        return LLMReportAnalyst(get_settings()).enrich(result, runs)

    def _detect_regressions(self, current: RunReport, history: list[RunReport]) -> list[RegressionSignal]:
        signals: list[RegressionSignal] = []
        history_by_stage = self._history_by_stage(history)

        for stage in current.stages:
            previous = history_by_stage.get(stage.name, [])
            if not previous:
                continue

            passed_previous = [item for item in previous if item.status == RunStatus.PASSED]
            if stage.failed and passed_previous:
                signals.append(
                    RegressionSignal(
                        stage=stage.name,
                        signal="stage failed after passing in recent history",
                        severity=Severity.HIGH,
                        evidence=f"{len(passed_previous)} recent successful executions for this stage",
                    )
                )

            previous_durations = [item.duration_ms for item in previous if item.duration_ms > 0]
            if previous_durations:
                average = sum(previous_durations) / len(previous_durations)
                if average > 0 and stage.duration_ms >= average * 1.35:
                    severity = Severity.HIGH if stage.duration_ms >= average * 1.75 else Severity.MEDIUM
                    signals.append(
                        RegressionSignal(
                            stage=stage.name,
                            signal="stage duration increased versus recent history",
                            severity=severity,
                            evidence=f"{stage.duration_ms}ms current versus {round(average)}ms recent average",
                        )
                    )

        return signals

    def _history_by_stage(self, history: list[RunReport]):
        grouped = {}
        for run in history:
            for stage in run.stages:
                grouped.setdefault(stage.name, []).append(stage)
        return grouped

    def _summarize(
        self,
        current: RunReport,
        history: list[RunReport],
        regressions: list[RegressionSignal],
    ) -> str:
        if current.status == RunStatus.PASSED and not regressions:
            return f"{current.workflow} passed without relevant regressions across the recent execution window."

        failed_names = ", ".join(stage.name for stage in current.failed_stages) or "no failed stages"
        return (
            f"{current.workflow} finished as {current.status}. "
            f"Current failed stages: {failed_names}. "
            f"Compared with {len(history)} previous runs, {len(regressions)} regression signals were detected."
        )

    def _recommend(self, current: RunReport, regressions: list[RegressionSignal]) -> list[str]:
        recommendations: list[str] = []
        for stage in current.failed_stages:
            if stage.http_status in {400, 409, 422}:
                recommendations.append(f"Review request and contract validation around stage {stage.name}.")
            elif stage.http_status in {401, 403}:
                recommendations.append(f"Check credentials, token propagation, and permissions for stage {stage.name}.")
            elif stage.http_status and stage.http_status >= 500:
                recommendations.append(f"Inspect downstream dependency health for stage {stage.name}.")
            else:
                recommendations.append(f"Inspect execution trace and generated context for stage {stage.name}.")

        if any(signal.signal.startswith("stage duration") for signal in regressions):
            recommendations.append("Compare stage timings with the last green baseline before promoting the version.")

        return recommendations or ["No immediate corrective action detected from the recent execution window."]
