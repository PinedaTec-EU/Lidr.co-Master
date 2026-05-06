from fastapi.testclient import TestClient

from app.api.executions import runner
from app.infrastructure.sih_cli_runner import SihRunResult
from app.main import app


class FakeRunner:
    def run(self, command):
        self.command = command
        return SihRunResult(exit_code=0, stdout="generated", stderr="")


def test_run_workflow_endpoint_invokes_runner():
    fake_runner = FakeRunner()
    app.dependency_overrides[runner] = lambda: fake_runner
    client = TestClient(app)

    response = client.post(
        "/api/v1/executions/run",
        json={
            "workflow": "../.sphere/workflows/test-estimate-endpoint.workflow",
            "environment": "local",
            "report_format": "json",
            "capture_http": "headers",
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["succeeded"] is True
    assert fake_runner.command.environment == "local"
    assert fake_runner.command.report_format == "json"
