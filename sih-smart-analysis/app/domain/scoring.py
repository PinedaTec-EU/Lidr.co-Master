from __future__ import annotations

from app.domain.models import FailureType, RunReport, RunStatus


class HealthScorer:
    def score(self, current: RunReport, history: list[RunReport]) -> int:
        score = 100

        if current.status == RunStatus.FAILED:
            score -= 35

        score -= min(len(current.failed_stages) * 12, 30)
        score -= self._duration_penalty(current, history)
        score -= self._repeat_failure_penalty(current, history)

        return max(0, min(100, score))

    def dominant_failure_type(self, current: RunReport) -> FailureType:
        failed_stages = current.failed_stages
        if not failed_stages:
            return FailureType.NONE

        counts: dict[FailureType, int] = {}
        for stage in failed_stages:
            counts[stage.error_type] = counts.get(stage.error_type, 0) + 1

        return max(counts, key=counts.get)

    def _duration_penalty(self, current: RunReport, history: list[RunReport]) -> int:
        passed_history = [run.duration_ms for run in history if run.status == RunStatus.PASSED]
        if not passed_history:
            return 0

        average = sum(passed_history) / len(passed_history)
        if average <= 0:
            return 0

        increase_ratio = current.duration_ms / average
        if increase_ratio >= 1.75:
            return 20
        if increase_ratio >= 1.35:
            return 12
        if increase_ratio >= 1.15:
            return 6
        return 0

    def _repeat_failure_penalty(self, current: RunReport, history: list[RunReport]) -> int:
        current_failed_names = {stage.name for stage in current.failed_stages}
        if not current_failed_names:
            return 0

        repeated = 0
        for run in history:
            history_failed_names = {stage.name for stage in run.failed_stages}
            if current_failed_names & history_failed_names:
                repeated += 1

        return min(repeated * 5, 15)

