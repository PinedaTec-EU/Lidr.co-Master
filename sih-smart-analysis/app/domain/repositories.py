from __future__ import annotations

from typing import Protocol

from app.domain.models import RunReport


class RunReportRepository(Protocol):
    def latest(self, workflow: str, environment: str, limit: int) -> list[RunReport]:
        ...

    def all(self) -> list[RunReport]:
        ...

