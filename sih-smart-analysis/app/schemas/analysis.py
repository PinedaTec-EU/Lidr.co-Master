from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RecentAnalysisRequest(BaseModel):
    workflow: str
    environment: str
    limit: int = Field(default=5, ge=2, le=20)


class SemanticAnalysisRequest(BaseModel):
    current_report: dict[str, Any]
    top_k: int = Field(default=8, ge=1, le=30)


class RegressionSignalResponse(BaseModel):
    stage: str
    signal: str
    severity: str
    evidence: str


class AnalysisResponse(BaseModel):
    mode: str
    workflow: str
    environment: str
    current_run_id: str
    health_score: int
    summary: str
    failure_type: str
    regressions: list[RegressionSignalResponse]
    recommendations: list[str]
    sources: list[str]
    llm_insights: str | None = None
