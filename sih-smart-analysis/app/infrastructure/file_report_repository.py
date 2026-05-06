from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import RunReport
from app.infrastructure.report_normalizer import ReportNormalizer


class FileRunReportRepository:
    def __init__(self, reports_dir: Path, normalizer: ReportNormalizer | None = None) -> None:
        self._reports_dir = reports_dir
        self._normalizer = normalizer or ReportNormalizer()

    def latest(self, workflow: str, environment: str, limit: int) -> list[RunReport]:
        matching = [
            run
            for run in self.all()
            if run.workflow == workflow and run.environment == environment
        ]
        return sorted(matching, key=lambda run: run.started_at, reverse=True)[:limit]

    def all(self) -> list[RunReport]:
        if not self._reports_dir.exists():
            return []

        runs: list[RunReport] = []
        for path in sorted(self._reports_dir.rglob("*.json")):
            with path.open("r", encoding="utf-8") as handler:
                runs.append(self._normalizer.normalize(json.load(handler)))
        return runs

