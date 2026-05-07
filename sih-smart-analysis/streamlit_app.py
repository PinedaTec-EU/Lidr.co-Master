from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    if "current_report_json" not in st.session_state:
        st.session_state.current_report_json = ""


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


def _sample_report_paths() -> list[Path]:
    sample_dir = Path("sample-reports")
    if not sample_dir.exists():
        return []
    return sorted(sample_dir.rglob("*.json"), reverse=True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_label(report: dict[str, Any], path: Path) -> str:
    workflow = report.get("workflow") or report.get("WorkflowName") or "workflow"
    status = report.get("status") or report.get("Status") or "status"
    started = report.get("started_at") or report.get("StartedAtUtc") or path.stem
    return f"{workflow} · {status} · {started}"


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


def _run_semantic(current_report_json: str, top_k: int) -> None:
    if not current_report_json.strip():
        paths = _sample_report_paths()
        if not paths:
            raise ValueError("current_report JSON is required")
        current_report_json = json.dumps(_load_json(paths[0]), indent=2, ensure_ascii=False)

    current_report = json.loads(current_report_json)
    current = ReportNormalizer().normalize(current_report)
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
        st.subheader("Reports de ejemplo")
        paths = _sample_report_paths()
        st.caption(f"{len(paths)} reports disponibles")
        for index, path in enumerate(paths, 1):
            report = _load_json(path)
            with st.expander(f"Report {index}", expanded=False):
                st.markdown(_report_label(report, path))
                st.markdown(
                    f'<div class="report-meta">{path.as_posix()}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Usar como current_report",
                    key=f"use_report_{index}",
                    use_container_width=True,
                ):
                    st.session_state.current_report_json = json.dumps(
                        report,
                        indent=2,
                        ensure_ascii=False,
                    )
                    st.session_state.workflow = report.get("workflow", st.session_state.workflow)
                    st.session_state.environment = report.get(
                        "environment",
                        st.session_state.environment,
                    )
                    st.rerun()


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
    report_json = st.text_area(
        "Current report JSON",
        key="current_report_json",
        height=300,
        placeholder="Pega un report JSON o usa uno del panel lateral.",
    )
    if st.button("Analizar por similitud semántica", use_container_width=True):
        try:
            _run_semantic(report_json, int(st.session_state.top_k))
        except Exception as exc:
            st.error(f"No se pudo analizar el report actual: {exc}")

_render_conversation()

if st.button("Ver contexto activo", use_container_width=True):
    _show_context_dialog()
