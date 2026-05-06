from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ExecuteWorkflowRequest(BaseModel):
    workflow: Path = Path("../.sphere/workflows/test-estimate-endpoint.workflow")
    environment: str = "local"
    catalog: Path | None = Path("../.sphere/api.catalog")
    varsfile: Path | None = Path("../.sphere/workflows/test-estimate-endpoint.wfvars")
    report_format: str = Field(default="both", pattern="^(json|html|both|none)$")
    capture_http: str = Field(default="bodies", pattern="^(none|headers|bodies)$")
    refresh_cache: bool = False
    mocked: bool = False


class ExecuteWorkflowResponse(BaseModel):
    exit_code: int
    succeeded: bool
    stdout: str
    stderr: str
