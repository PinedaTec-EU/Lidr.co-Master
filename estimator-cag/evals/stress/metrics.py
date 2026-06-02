from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float
    passed: bool
    details: str


class LatencyBudgetMetric:
    def __init__(self, budget_ms: int) -> None:
        self.budget_ms = budget_ms

    def evaluate(self, observation: dict[str, Any]) -> MetricResult:
        latency_ms = float(observation.get("latency_ms", 0.0))
        passed = latency_ms <= self.budget_ms
        return MetricResult(
            name="latency_budget",
            score=1.0 if passed else 0.0,
            passed=passed,
            details=f"latency_ms={latency_ms:.2f} budget_ms={self.budget_ms}",
        )


class CostBudgetMetric:
    def __init__(self, budget_usd: float) -> None:
        self.budget_usd = budget_usd

    def evaluate(self, observation: dict[str, Any]) -> MetricResult:
        cost_usd = float(observation.get("cost_usd", 0.0))
        passed = cost_usd <= self.budget_usd
        return MetricResult(
            name="cost_budget",
            score=1.0 if passed else 0.0,
            passed=passed,
            details=f"cost_usd={cost_usd:.8f} budget_usd={self.budget_usd:.8f}",
        )


class MemoryDriftMetric:
    def __init__(self, fact: str, where: list[str] | None = None) -> None:
        self.fact = fact.strip()
        self.where = where or ["summary_text", "anchors", "project_metadata"]

    def evaluate(self, session_snapshot: dict[str, Any]) -> MetricResult:
        haystacks: list[str] = []
        for field_name in self.where:
            value = session_snapshot.get(field_name, "")
            if isinstance(value, list):
                haystacks.append(" ".join(str(item) for item in value))
            else:
                haystacks.append(str(value))

        normalized_fact = self.fact.casefold()
        matched = any(normalized_fact in haystack.casefold() for haystack in haystacks)
        return MetricResult(
            name="memory_drift",
            score=1.0 if matched else 0.0,
            passed=matched,
            details=f"fact={self.fact} where={','.join(self.where)}",
        )
