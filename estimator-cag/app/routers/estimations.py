from fastapi import APIRouter, HTTPException, Query

from app.schemas import EstimationRequest, EstimationResponse
from app.services.llm_service import get_available_friendly_names, get_estimation

router = APIRouter()


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(
    request: EstimationRequest,
    friendly_name: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    try:
        result = await get_estimation(
            request,
            friendly_name=friendly_name,
            provider=provider,
            model=model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return EstimationResponse(text=result["text"], prompt_version=result["prompt_version"])


@router.get("/estimate/friendly-names")
async def estimate_friendly_names():
    return {"friendly_names": get_available_friendly_names()}
