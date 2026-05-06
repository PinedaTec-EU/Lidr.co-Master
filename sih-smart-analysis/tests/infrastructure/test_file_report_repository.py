import json

from app.infrastructure.file_report_repository import FileRunReportRepository


def test_repository_loads_reports_and_returns_latest_sorted(tmp_path):
    first = {
        "run_id": "old",
        "workflow": "checkout-smoke",
        "environment": "staging",
        "version": "1.0.0",
        "started_at": "2026-05-01T09:00:00Z",
        "status": "passed",
        "duration_ms": 10,
        "stages": [],
    }
    second = {**first, "run_id": "new", "started_at": "2026-05-02T09:00:00Z"}
    (tmp_path / "old.json").write_text(json.dumps(first), encoding="utf-8")
    (tmp_path / "new.json").write_text(json.dumps(second), encoding="utf-8")

    reports = FileRunReportRepository(tmp_path).latest("checkout-smoke", "staging", 2)

    assert [report.run_id for report in reports] == ["new", "old"]

