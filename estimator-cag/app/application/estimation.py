from dataclasses import dataclass
from typing import Protocol

from app.schemas import EstimationRequest, EstimationResponse


class PromptRenderer(Protocol):
    def render(self, request: EstimationRequest, version: str) -> tuple[str, str]: ...


class EstimationModelGateway(Protocol):
    async def generate(self, *, system_prompt: str, user_prompt: str) -> str: ...


@dataclass(frozen=True)
class RenderedPrompt:
    system: str
    user: str
    version: str


class EstimationService:
    def __init__(
        self,
        prompt_renderer: PromptRenderer,
        model_gateway: EstimationModelGateway,
    ) -> None:
        self._prompt_renderer = prompt_renderer
        self._model_gateway = model_gateway

    async def estimate(
        self,
        request: EstimationRequest,
        prompt_version: str = "v1",
    ) -> EstimationResponse:
        rendered_prompt = self._render_prompt(request, prompt_version)
        text = await self._model_gateway.generate(
            system_prompt=rendered_prompt.system,
            user_prompt=rendered_prompt.user,
        )
        return EstimationResponse(text=text, prompt_version=rendered_prompt.version)

    def _render_prompt(
        self,
        request: EstimationRequest,
        prompt_version: str,
    ) -> RenderedPrompt:
        system_prompt, user_prompt = self._prompt_renderer.render(request, prompt_version)
        return RenderedPrompt(
            system=system_prompt,
            user=user_prompt,
            version=prompt_version,
        )
