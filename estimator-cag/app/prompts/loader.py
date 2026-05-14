from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas import EstimationRequest

PROMPTS_ROOT = Path(__file__).resolve().parent


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(PROMPTS_ROOT)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


class JinjaEstimationPromptRenderer:
    def __init__(self) -> None:
        self._environment = _environment()

    def render(
        self,
        request: EstimationRequest,
        version: str = "v1",
    ) -> tuple[str, str]:
        context = request.model_dump(mode="json")
        template_prefix = f"estimation/{version}"
        system = self._environment.get_template(f"{template_prefix}/system.j2").render(**context)
        user = self._environment.get_template(f"{template_prefix}/user.j2").render(**context)
        return system.strip(), user.strip()


def render_estimation_prompt(
    request: EstimationRequest,
    version: str = "v1",
) -> tuple[str, str]:
    return JinjaEstimationPromptRenderer().render(request, version)
