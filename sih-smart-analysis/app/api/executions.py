from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.infrastructure.sih_cli_runner import SihCliRunner, SihRunCommand
from app.schemas.executions import ExecuteWorkflowRequest, ExecuteWorkflowResponse

router = APIRouter(prefix="/executions", tags=["executions"])


def runner(settings: Settings = Depends(get_settings)) -> SihCliRunner:
    return SihCliRunner(settings.sih_command)


@router.post("/run", response_model=ExecuteWorkflowResponse)
def run_workflow(
    request: ExecuteWorkflowRequest,
    sih_runner: SihCliRunner = Depends(runner),
) -> ExecuteWorkflowResponse:
    result = sih_runner.run(
        SihRunCommand(
            workflow=request.workflow,
            environment=request.environment,
            catalog=request.catalog,
            varsfile=request.varsfile,
            report_format=request.report_format,
            capture_http=request.capture_http,
            refresh_cache=request.refresh_cache,
            mocked=request.mocked,
        )
    )

    if not result.succeeded:
        raise HTTPException(
            status_code=502,
            detail={
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    return ExecuteWorkflowResponse(
        exit_code=result.exit_code,
        succeeded=result.succeeded,
        stdout=result.stdout,
        stderr=result.stderr,
    )
