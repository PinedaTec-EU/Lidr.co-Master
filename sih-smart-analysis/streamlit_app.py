from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.application.cag_recent_analysis import RecentRunsAnalyzer
from app.application.rag_semantic_analysis import SemanticRunsAnalyzer
from app.config import get_settings
from app.domain.models import AnalysisResult
from app.infrastructure.file_report_repository import FileRunReportRepository
from app.infrastructure.report_normalizer import ReportNormalizer


st.set_page_config(
    page_title="SIH Smart Analysis",
    page_icon="📊",
    layout="wide",
)


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Selecciona un modo de análisis y ejecuta una revisión de reports SIH.",
                "result": None,
            }
        ]
    if "workflow" not in st.session_state:
        st.session_state.workflow = "checkout-smoke"
    if "environment" not in st.session_state:
        st.session_state.environment = "staging"
    if "limit" not in st.session_state:
        st.session_state.limit = 5
    if "top_k" not in st.session_state:
        st.session_state.top_k = 5
    if "selected_report_path" not in st.session_state:
        paths = _report_paths()
        st.session_state.selected_report_path = paths[0].as_posix() if paths else ""


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
        }

        .report-meta {
            color: #9ca3af;
            font-size: 0.82rem;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stDialog"] div[role="dialog"] {
            width: 90vw;
            max-width: 90vw;
        }

        div[data-testid="stDialog"] pre {
            white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _repository() -> FileRunReportRepository:
    reports_dir = get_settings().reports_dir
    if not list(reports_dir.rglob("*.json")) and Path("sample-reports").exists():
        reports_dir = Path("sample-reports")
    return FileRunReportRepository(reports_dir)


def _repository_for(workflow: str, environment: str) -> FileRunReportRepository:
    repository = _repository()
    if repository.latest(workflow=workflow, environment=environment, limit=1):
        return repository
    if Path("sample-reports").exists():
        return FileRunReportRepository(Path("sample-reports"))
    return repository


def _active_reports_dir() -> Path:
    reports_dir = get_settings().reports_dir
    if not list(reports_dir.rglob("*.json")) and Path("sample-reports").exists():
        return Path("sample-reports")
    return reports_dir


def _report_paths() -> list[Path]:
    return sorted(_active_reports_dir().rglob("*.json"), reverse=True)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_report(path: Path):
    return ReportNormalizer().normalize(_load_json(path))


def _report_label(path: Path) -> str:
    report = _load_report(path)
    started = report.started_at.strftime("%Y-%m-%d %H:%M")
    return f"{report.workflow} · {report.environment} · {report.status.value} · {started}"


def _selected_report_path() -> Path | None:
    selected = st.session_state.get("selected_report_path", "")
    if not selected:
        return None
    path = Path(selected)
    return path if path.exists() else None


def _select_report(path: Path) -> None:
    report = _load_report(path)
    st.session_state.selected_report_path = path.as_posix()
    st.session_state.workflow = report.workflow
    st.session_state.environment = report.environment


def _render_result(result: AnalysisResult) -> str:
    lines = [
        f"## {result.mode}",
        f"**Workflow:** {result.workflow}",
        f"**Environment:** {result.environment}",
        f"**Current run:** {result.current_run_id}",
        f"**Health score:** {result.health_score}",
        f"**Failure type:** {result.failure_type.value}",
        "",
        result.summary,
    ]

    if result.regressions:
        lines.extend(["", "### Regression signals"])
        for signal in result.regressions:
            lines.append(
                f"- **{signal.stage}** ({signal.severity.value}): "
                f"{signal.signal}. {signal.evidence}"
            )

    if result.recommendations:
        lines.extend(["", "### Recommendations"])
        lines.extend(f"- {item}" for item in result.recommendations)

    if result.sources:
        lines.extend(["", "### Sources"])
        lines.extend(f"- {source}" for source in result.sources)

    if result.llm_insights:
        lines.extend(["", "### LLM insights", result.llm_insights])

    return "\n".join(lines)


def _render_conversation() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("result"):
                st.json(message["result"])


def _run_recent(workflow: str, environment: str, limit: int) -> None:
    result = RecentRunsAnalyzer(_repository_for(workflow, environment)).analyze(
        workflow=workflow,
        environment=environment,
        limit=limit,
    )
    st.session_state.messages.append(
        {
            "role": "user",
            "content": (
                f"Analiza las últimas {limit} ejecuciones de `{workflow}` "
                f"en `{environment}`."
            ),
            "result": None,
        }
    )
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": _render_result(result),
            "result": None,
        }
    )
    st.rerun()


def _run_semantic(path: Path, top_k: int) -> None:
    current = _load_report(path)
    result = SemanticRunsAnalyzer(_repository()).analyze(current=current, top_k=top_k)
    st.session_state.messages.append(
        {
            "role": "user",
            "content": f"Analiza semánticamente `{current.run_id}` contra {top_k} fuentes.",
            "result": None,
        }
    )
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": _render_result(result),
            "result": None,
        }
    )
    st.rerun()


def _render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Configuración")
        st.number_input("Ventana reciente", min_value=2, max_value=20, key="limit")
        st.number_input("Fuentes semánticas", min_value=1, max_value=30, key="top_k")

        if st.button("Limpiar conversación", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        st.subheader("Catálogo de reports")
        paths = _report_paths()
        st.caption(f"{len(paths)} reports disponibles")
        base_dir = _active_reports_dir()
        by_folder: dict[Path, list[Path]] = {}
        for path in paths:
            by_folder.setdefault(path.parent.relative_to(base_dir), []).append(path)

        for folder, folder_paths in by_folder.items():
            folder_label = folder.as_posix() if folder.as_posix() != "." else base_dir.name
            with st.expander(folder_label, expanded=False):
                for path in folder_paths:
                    selected = path.as_posix() == st.session_state.selected_report_path
                    label = f"{'✓ ' if selected else ''}{path.name}"
                    if st.button(label, key=f"select_{path.as_posix()}", use_container_width=True):
                        _select_report(path)
                        st.rerun()
                    st.markdown(
                        f'<div class="report-meta">{_report_label(path)}</div>',
                        unsafe_allow_html=True,
                    )


@st.dialog("Contexto activo SIH Smart Analysis", width="large")
def _show_context_dialog() -> None:
    settings = get_settings()
    context = {
        "reports_dir": str(settings.reports_dir),
        "ui_active_reports_dir": str(_active_reports_dir()),
        "recent_mode": "CAG determinista sobre las últimas N ejecuciones",
        "semantic_mode": "RAG local por similitud de tokens sobre reports históricos",
        "llm_enabled": settings.llm_enabled,
        "llm_model": settings.llm_model,
        "llm_max_tokens": settings.llm_max_tokens,
        "public_endpoints": [
            "POST /api/v1/analysis/recent",
            "POST /api/v1/analysis/semantic",
            "POST /api/v1/executions/run",
        ],
    }
    st.json(context)


_init_state()
_apply_styles()
_render_sidebar()

st.title("SIH Smart Analysis")
st.caption("Wrapper conversacional para analizar reports de SphereIntegrationHub.")

mode = st.segmented_control(
    "Modo de análisis",
    options=["Recent CAG", "Semantic RAG"],
    default="Recent CAG",
)

if mode == "Recent CAG":
    left, right = st.columns(2)
    with left:
        workflow = st.text_input("Workflow", key="workflow")
    with right:
        environment = st.text_input("Environment", key="environment")
    if st.button("Analizar ventana reciente", use_container_width=True):
        try:
            _run_recent(workflow.strip(), environment.strip(), int(st.session_state.limit))
        except Exception as exc:
            st.error(f"No se pudo analizar la ventana reciente: {exc}")

else:
    selected_path = _selected_report_path()
    if selected_path:
        st.info(f"Report seleccionado: `{selected_path.relative_to(_active_reports_dir())}`")
        st.caption(_report_label(selected_path))
    else:
        st.warning("No hay ningún report seleccionado en el catálogo.")

    if st.button("Analizar por similitud semántica", use_container_width=True):
        try:
            if not selected_path:
                raise ValueError("selecciona un report del catálogo")
            _run_semantic(selected_path, int(st.session_state.top_k))
        except Exception as exc:
            st.error(f"No se pudo analizar el report actual: {exc}")

_render_conversation()

if st.button("Ver contexto activo", use_container_width=True):
    _show_context_dialog()
