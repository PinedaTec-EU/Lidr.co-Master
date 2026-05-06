from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.application.cag_recent_analysis import RecentRunsAnalyzer
from app.application.rag_semantic_analysis import SemanticRunsAnalyzer
from app.config import Settings, get_settings
from app.domain.models import AnalysisResult
from app.infrastructure.file_report_repository import FileRunReportRepository
from app.infrastructure.report_normalizer import ReportNormalizer
from app.schemas.analysis import AnalysisResponse, RecentAnalysisRequest, SemanticAnalysisRequest

router = APIRouter(prefix="/analysis", tags=["analysis"])


def repository(settings: Settings = Depends(get_settings)) -> FileRunReportRepository:
    return FileRunReportRepository(settings.reports_dir)


@router.post("/recent", response_model=AnalysisResponse)
def analyze_recent(
    request: RecentAnalysisRequest,
    report_repository: FileRunReportRepository = Depends(repository),
) -> AnalysisResponse:
    try:
        result = RecentRunsAnalyzer(report_repository).analyze(
            workflow=request.workflow,
            environment=request.environment,
            limit=request.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _response(result)


@router.post("/semantic", response_model=AnalysisResponse)
def analyze_semantic(
    request: SemanticAnalysisRequest,
    report_repository: FileRunReportRepository = Depends(repository),
) -> AnalysisResponse:
    current = ReportNormalizer().normalize(request.current_report)
    try:
        result = SemanticRunsAnalyzer(report_repository).analyze(current=current, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _response(result)


def _response(result: AnalysisResult) -> AnalysisResponse:
    return AnalysisResponse(
        mode=result.mode,
        workflow=result.workflow,
        environment=result.environment,
        current_run_id=result.current_run_id,
        health_score=result.health_score,
        summary=result.summary,
        failure_type=result.failure_type.value,
        regressions=[
            {
                "stage": signal.stage,
                "signal": signal.signal,
                "severity": signal.severity.value,
                "evidence": signal.evidence,
            }
            for signal in result.regressions
        ],
        recommendations=list(result.recommendations),
        sources=list(result.sources),
    )

