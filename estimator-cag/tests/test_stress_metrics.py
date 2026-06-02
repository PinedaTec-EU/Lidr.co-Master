from evals.stress.metrics import CostBudgetMetric, LatencyBudgetMetric, MemoryDriftMetric


def test_latency_budget_metric_passes_within_budget() -> None:
    result = LatencyBudgetMetric(budget_ms=4000).evaluate({"latency_ms": 3999.9})

    assert result.passed is True
    assert result.score == 1.0


def test_cost_budget_metric_fails_outside_budget() -> None:
    result = CostBudgetMetric(budget_usd=0.01).evaluate({"cost_usd": 0.02})

    assert result.passed is False
    assert result.score == 0.0


def test_memory_drift_metric_matches_case_insensitively_on_metadata() -> None:
    result = MemoryDriftMetric("Nimbus").evaluate(
        {
            "summary_text": "",
            "anchors": [],
            "project_metadata": {"project_name": "nimbus", "mentioned_technologies": ["react"]},
        }
    )

    assert result.passed is True
    assert result.score == 1.0
