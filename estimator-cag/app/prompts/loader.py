from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas import EstimationRequest
from app.sessions import ExternalContextItem, ProjectMetadata


PROMPTS_DIR = Path(__file__).resolve().parent


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(PROMPTS_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_estimation_prompt(
    request: EstimationRequest,
    version: str = "v1",
    project_metadata: ProjectMetadata | None = None,
    external_context: list[ExternalContextItem] | None = None,
) -> tuple[str, str]:
    environment = _environment()
    context = {
        **request.model_dump(mode="json"),
        "examples_template": f"estimation/{version}/examples.j2",
        "project_metadata": (project_metadata or ProjectMetadata()).model_dump(),
        "external_context": [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in (external_context or [])
        ],
    }
    system = environment.get_template(f"estimation/{version}/system.j2").render(context)
    user = environment.get_template(f"estimation/{version}/user.j2").render(context)
    return system.strip(), user.strip()
