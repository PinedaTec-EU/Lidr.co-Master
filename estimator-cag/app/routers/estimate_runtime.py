from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.config import settings
from app.rate_limit import enforce_rate_limit
from app.schemas import TranscriptEstimateRequest, TranscriptEstimateResponse
from app.security import require_estimate_key
from app.services.rag_estimation_service import estimate_from_transcript

router = APIRouter(tags=["estimate"])


@router.post("/estimate/from-transcript", response_model=TranscriptEstimateResponse)
async def estimate_runtime(
    request: Request,
    response: Response,
    payload: TranscriptEstimateRequest,
    x_api_key: str = Depends(require_estimate_key),
) -> TranscriptEstimateResponse:
    enforce_rate_limit(
        request=request,
        x_api_key=x_api_key,
        limit=settings.estimate_rate_limit_per_minute,
        namespace="estimate",
    )
    try:
        result, request_id = await estimate_from_transcript(
            transcript=payload.transcript,
            idempotency_key=payload.idempotency_key,
            project_type=payload.project_type,
            detail_level=payload.detail_level,
            output_format=payload.output_format,
            retrieval=payload.retrieval,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "Idempotency key" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected error while generating estimate.") from exc

    response.headers["X-Request-ID"] = request_id
    if result.get("idempotency_cache_hit"):
        response.headers["X-Idempotency-Cache"] = "hit"
    return TranscriptEstimateResponse(**result)
