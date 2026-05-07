from __future__ import annotations

from datetime import datetime, timezone
import json
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
            context=self._context(
                raw,
                "Inputs",
                "Output",
                "WorkflowOutput",
                "WorkflowResult",
                "ErrorMessage",
                "Preflight",
            ),
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
            context=self._context(
                raw,
                "Output",
                "WorkflowInputs",
                "WorkflowOutput",
                "WorkflowResult",
                "RequestBody",
                "ResponseBody",
                "EnsureMode",
                "EnsureStatus",
            ),
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

    def _context(self, raw: dict[str, Any], *keys: str, max_chars: int = 1600) -> str | None:
        parts = []
        for key in keys:
            value = raw.get(key)
            if value in (None, "", {}, []):
                continue
            parts.append(f"{key}: {self._serialize(value, max_chars=max_chars // 2)}")

        if not parts:
            return None
        text = "\n".join(parts)
        return text[:max_chars]

    def _serialize(self, value: Any, max_chars: int) -> str:
        if isinstance(value, str):
            return value[:max_chars]
        if isinstance(value, dict):
            scalar_items = []
            complex_items = []
            for key, item in value.items():
                target = scalar_items if item is None or isinstance(item, str | int | float | bool) else complex_items
                target.append((key, item))

            compact = {}
            for key, item in [*scalar_items, *complex_items]:
                if isinstance(item, str):
                    compact[key] = item[:500]
                elif isinstance(item, list):
                    compact[key] = item[:3]
                elif isinstance(item, dict):
                    compact[key] = {nested_key: nested_value for nested_key, nested_value in list(item.items())[:12]}
                else:
                    compact[key] = item

            try:
                text = json.dumps(compact, ensure_ascii=False)
            except TypeError:
                text = str(compact)
            return text[:max_chars]
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            text = str(value)
        return text[:max_chars]

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
