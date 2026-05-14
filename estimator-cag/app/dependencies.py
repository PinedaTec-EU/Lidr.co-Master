from functools import lru_cache

from app.application.estimation import EstimationService
from app.prompts.loader import JinjaEstimationPromptRenderer
from app.services.llm_service import LiteLlmEstimationGateway


@lru_cache(maxsize=1)
def get_estimation_service() -> EstimationService:
    return EstimationService(
        prompt_renderer=JinjaEstimationPromptRenderer(),
        model_gateway=LiteLlmEstimationGateway(),
    )
