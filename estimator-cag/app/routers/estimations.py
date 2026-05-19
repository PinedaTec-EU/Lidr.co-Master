from fastapi import APIRouter, Depends, HTTPException

from app.application.estimation import EstimationService
from app.application.estimation_jobs import EstimationJobService
from app.dependencies import get_estimation_job_service, get_estimation_service
from app.schemas import EstimationJob, EstimationRequest, EstimationResponse
from app.services.llm_service import get_available_friendly_names

router = APIRouter()


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(
    request: EstimationRequest,
    estimation_service: EstimationService = Depends(get_estimation_service),
):
    try:
        result = await estimation_service.estimate(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result


@router.post("/estimate-jobs", response_model=EstimationJob, status_code=202)
async def create_estimation_job(
    request: EstimationRequest,
    estimation_job_service: EstimationJobService = Depends(get_estimation_job_service),
):
    return await estimation_job_service.submit(request)


@router.get("/estimate-jobs", response_model=list[EstimationJob])
async def list_estimation_jobs(
    estimation_job_service: EstimationJobService = Depends(get_estimation_job_service),
):
    return await estimation_job_service.list()


@router.get("/estimate-jobs/{job_id}", response_model=EstimationJob)
async def get_estimation_job(
    job_id: str,
    estimation_job_service: EstimationJobService = Depends(get_estimation_job_service),
):
    job = await estimation_job_service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/estimate/friendly-names")
async def estimate_friendly_names():
    return {"friendly_names": get_available_friendly_names()}
