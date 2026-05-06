from __future__ import annotations

from datetime import datetime, timezone

from app.domain.models import FailureType, RunReport, RunStatus, StageReport


def stage(
    name: str,
    status: RunStatus = RunStatus.PASSED,
    duration_ms: int = 100,
    http_status: int | None = 200,
    error_type: FailureType = FailureType.NONE,
    message: str | None = None,
) -> StageReport:
    return StageReport(
        name=name,
        status=status,
        duration_ms=duration_ms,
        http_status=http_status,
        error_type=error_type,
        message=message,
    )


def run(
    run_id: str = "run-1",
    workflow: str = "checkout-smoke",
    environment: str = "staging",
    version: str = "1.0.0",
    day: int = 1,
    status: RunStatus = RunStatus.PASSED,
    duration_ms: int = 1000,
    stages: tuple[StageReport, ...] | None = None,
) -> RunReport:
    return RunReport(
        run_id=run_id,
        workflow=workflow,
        environment=environment,
        version=version,
        started_at=datetime(2026, 5, day, 9, 0, tzinfo=timezone.utc),
        status=status,
        duration_ms=duration_ms,
        stages=stages or (stage("login"), stage("create-order", duration_ms=300), stage("confirm-order")),
    )


class InMemoryRunRepository:
    def __init__(self, runs):
        self.runs = list(runs)

    def latest(self, workflow: str, environment: str, limit: int):
        return sorted(
            [item for item in self.runs if item.workflow == workflow and item.environment == environment],
            key=lambda item: item.started_at,
            reverse=True,
        )[:limit]

    def all(self):
        return list(self.runs)

