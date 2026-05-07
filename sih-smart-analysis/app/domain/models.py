from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class RunStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureType(StrEnum):
    NONE = "none"
    CONTRACT_VALIDATION = "contract_validation"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    DATA_SETUP = "data_setup"
    BRANCHING = "branching"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class StageReport:
    name: str
    status: RunStatus
    duration_ms: int
    http_status: int | None = None
    error_type: FailureType = FailureType.NONE
    message: str | None = None
    request_uri: str | None = None
    http_method: str | None = None
    context: str | None = None

    @property
    def failed(self) -> bool:
        return self.status == RunStatus.FAILED


@dataclass(frozen=True)
class RunReport:
    run_id: str
    workflow: str
    environment: str
    version: str
    started_at: datetime
    status: RunStatus
    duration_ms: int
    tool_version: str | None = None
    stages: tuple[StageReport, ...] = field(default_factory=tuple)
    context: str | None = None

    @property
    def failed_stages(self) -> tuple[StageReport, ...]:
        return tuple(stage for stage in self.stages if stage.failed)

    @property
    def stage_names(self) -> set[str]:
        return {stage.name for stage in self.stages}


@dataclass(frozen=True)
class RegressionSignal:
    stage: str
    signal: str
    severity: Severity
    evidence: str


@dataclass(frozen=True)
class AnalysisResult:
    mode: str
    workflow: str
    environment: str
    current_run_id: str
    health_score: int
    summary: str
    failure_type: FailureType
    regressions: tuple[RegressionSignal, ...]
    recommendations: tuple[str, ...]
    sources: tuple[str, ...] = field(default_factory=tuple)
    llm_insights: str | None = None
