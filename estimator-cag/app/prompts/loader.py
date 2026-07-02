from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas import EstimationRequest, RetrievalPromptContext, UserTier
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
    retrieval_context: RetrievalPromptContext | None = None,
    user_tier: UserTier = UserTier.DEVELOPER,
    user_display_name: str | None = None,
) -> tuple[str, str]:
    environment = _environment()
    context = {
        **request.model_dump(mode="json"),
        "examples_template": f"estimation/{version}/examples.j2",
        "tier_template": f"estimation/{version}/tiers/{user_tier.value}.j2",
        "user_tier": user_tier.value,
        "user_display_name": (user_display_name or "").strip(),
        "project_metadata": (project_metadata or ProjectMetadata()).model_dump(),
        "external_context": [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in (external_context or [])
        ],
        "retrieval_context": (
            {
                "query": retrieval_context.query,
                "effective_query": retrieval_context.effective_query,
                "context_text": retrieval_context.context_text,
                "included_chunks_count": retrieval_context.included_chunks_count,
                "retrieved_results_count": retrieval_context.retrieved_results_count,
                "truncated": retrieval_context.truncated,
            }
            if retrieval_context is not None
            else None
        ),
    }
    system = environment.get_template(f"estimation/{version}/system.j2").render(context)
    user = environment.get_template(f"estimation/{version}/user.j2").render(context)
    return system.strip(), user.strip()
