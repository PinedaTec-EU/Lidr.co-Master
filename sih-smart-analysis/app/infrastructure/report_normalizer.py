from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.models import FailureType, RunReport, RunStatus, StageReport


class ReportNormalizer:
    def normalize(self, raw: dict[str, Any]) -> RunReport:
        stages = tuple(self._stage(stage) for stage in self._get(raw, "stages", "Stages", default=[]))
        started_at = self._datetime(self._get(raw, "started_at", "StartedAtUtc"))
        duration_ms = int(self._get(raw, "duration_ms", "DurationMs", default=0) or sum(stage.duration_ms for stage in stages))

        return RunReport(
            run_id=str(self._get(raw, "run_id", "ExecutionId")),
            workflow=str(self._get(raw, "workflow", "WorkflowName")),
            environment=str(self._get(raw, "environment", "Environment")),
            version=str(self._get(raw, "version", "WorkflowVersion")),
            started_at=started_at,
            status=self._status(self._get(raw, "status", "Result")),
            duration_ms=duration_ms,
            tool_version=self._get(raw, "tool_version", "ToolVersion"),
            stages=stages,
        )

    def _stage(self, raw: dict[str, Any]) -> StageReport:
        http_status = self._get(raw, "http_status", "HttpStatusCode", default=None)
        message = self._get(raw, "message", "ErrorMessage", default=None)
        return StageReport(
            name=str(self._get(raw, "name", "StageName")),
            status=self._status(self._get(raw, "status", "Status")),
            duration_ms=int(self._get(raw, "duration_ms", "DurationMs", default=0) or 0),
            http_status=http_status,
            error_type=self._failure_type(self._get(raw, "error_type", default=None), http_status, message),
            message=message,
            request_uri=self._get(raw, "request_uri", "RequestUri", default=None),
            http_method=self._get(raw, "http_method", "HttpMethod", default=None),
        )

    def _datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.now(tz=timezone.utc)
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _get(self, raw: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in raw:
                return raw[key]
        return default

    def _status(self, value: Any) -> RunStatus:
        normalized = str(value or "").lower()
        if normalized in {"ok", "passed", "success", "succeeded"}:
            return RunStatus.PASSED
        if normalized in {"failed", "fail", "error", "ko"}:
            return RunStatus.FAILED
        if normalized in {"skipped", "skip"}:
            return RunStatus.SKIPPED
        return RunStatus.FAILED

    def _failure_type(
        self,
        explicit: Any,
        http_status: int | None,
        message: str | None,
    ) -> FailureType:
        if explicit:
            return FailureType(str(explicit).lower())

        text = (message or "").lower()
        if http_status in {400, 409, 422}:
            return FailureType.CONTRACT_VALIDATION
        if http_status in {401, 403}:
            return FailureType.AUTHENTICATION
        if http_status and http_status >= 500:
            return FailureType.DEPENDENCY
        if "timeout" in text:
            return FailureType.TIMEOUT
        if "contract" in text or "schema" in text or "validation" in text:
            return FailureType.CONTRACT_VALIDATION
        return FailureType.NONE
