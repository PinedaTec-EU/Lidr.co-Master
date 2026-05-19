from functools import lru_cache

from app.application.estimation import EstimationService
from app.application.estimation_jobs import EstimationJobService
from app.prompts.loader import JinjaEstimationPromptRenderer
from app.services.job_store import InMemoryEstimationJobStore
from app.services.llm_service import LiteLlmEstimationGateway


@lru_cache(maxsize=1)
def get_estimation_service() -> EstimationService:
    return EstimationService(
        prompt_renderer=JinjaEstimationPromptRenderer(),
        model_gateway=LiteLlmEstimationGateway(),
    )


@lru_cache(maxsize=1)
def get_estimation_job_store() -> InMemoryEstimationJobStore:
    return InMemoryEstimationJobStore()


@lru_cache(maxsize=1)
def get_estimation_job_service() -> EstimationJobService:
    return EstimationJobService(
        estimation_service=get_estimation_service(),
        job_store=get_estimation_job_store(),
    )
