import subprocess
from pathlib import Path

from app.infrastructure.sih_cli_runner import SihCliRunner, SihRunCommand


def test_sih_cli_runner_builds_command(monkeypatch):
    captured = {}

    def fake_run(args, capture_output, text, check):
        captured["args"] = args
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = SihCliRunner(Path("/tmp/sih")).run(
        SihRunCommand(
            workflow=Path("workflow.workflow"),
            environment="local",
            catalog=Path("api.catalog"),
            varsfile=Path("workflow.wfvars"),
            report_format="both",
            capture_http="bodies",
            refresh_cache=True,
        )
    )

    assert result.succeeded
    assert captured["args"] == [
        "/tmp/sih",
        "--workflow",
        "workflow.workflow",
        "--env",
        "local",
        "--report-format",
        "both",
        "--capture-http",
        "bodies",
        "--catalog",
        "api.catalog",
        "--varsfile",
        "workflow.wfvars",
        "--refresh-cache",
    ]
