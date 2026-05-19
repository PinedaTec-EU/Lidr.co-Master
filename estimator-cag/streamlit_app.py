import asyncio
from datetime import datetime, timezone

import streamlit as st

from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType
from app.services.session_service import create_session, estimate_session_turn, get_session
from app.services.llm_service import (
    get_available_friendly_names,
    get_context_summary,
    get_system_prompt,
)
from app.context.sample_transcriptions import (
    list_sample_transcriptions,
    read_sample_transcription,
)


st.set_page_config(
    page_title="Software Estimator CAG",
    page_icon="📝",
    layout="wide",
)


def _empty_usage() -> dict:
    return {"prompt": 0, "completion": 0, "total": 0}


def _init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = create_session()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "La sesión está lista. Añade contexto del proyecto y continuaré sobre la misma conversación.",
                "metadata": None,
            }
        ]
    if "last_usage" not in st.session_state:
        st.session_state.last_usage = _empty_usage()
    if "last_model" not in st.session_state:
        st.session_state.last_model = ""
    if "last_provider" not in st.session_state:
        st.session_state.last_provider = ""
    if "last_response_time" not in st.session_state:
        st.session_state.last_response_time = 0.0
    if "pending_request_data" not in st.session_state:
        st.session_state.pending_request_data = None
    if "form_description" not in st.session_state:
        st.session_state.form_description = ""
    if "form_project_type" not in st.session_state:
        st.session_state.form_project_type = ProjectType.WEB_SAAS.value
    if "form_detail_level" not in st.session_state:
        st.session_state.form_detail_level = DetailLevel.MEDIUM.value
    if "form_output_format" not in st.session_state:
        st.session_state.form_output_format = OutputFormat.NARRATIVE.value


def _reset_conversation() -> None:
    st.session_state.session_id = create_session()
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Nueva conversación creada. Puedes empezar un proyecto distinto.",
            "metadata": None,
        }
    ]
    st.session_state.last_usage = _empty_usage()
    st.session_state.last_model = ""
    st.session_state.last_provider = ""
    st.session_state.last_response_time = 0.0
    st.session_state.pending_request_data = None
    st.session_state.form_description = ""
    st.session_state.form_project_type = ProjectType.WEB_SAAS.value
    st.session_state.form_detail_level = DetailLevel.MEDIUM.value
    st.session_state.form_output_format = OutputFormat.NARRATIVE.value


def _apply_pending_form_data() -> None:
    pending_data = st.session_state.pending_request_data or {}
    if not pending_data:
        return

    st.session_state.form_description = pending_data.get("description", "")
    st.session_state.form_project_type = pending_data.get(
        "project_type",
        ProjectType.WEB_SAAS.value,
    )
    st.session_state.form_detail_level = pending_data.get(
        "detail_level",
        DetailLevel.MEDIUM.value,
    )
    st.session_state.form_output_format = pending_data.get(
        "output_format",
        OutputFormat.NARRATIVE.value,
    )
    st.session_state.pending_request_data = None


def _project_type_label(value: ProjectType) -> str:
    labels = {
        ProjectType.MOBILE_APP: "Mobile app",
        ProjectType.WEB_SAAS: "Web SaaS",
        ProjectType.INTERNAL_TOOL: "Internal tool",
        ProjectType.DATA_PIPELINE: "Data pipeline",
    }
    return labels[value]


def _detail_level_label(value: DetailLevel) -> str:
    labels = {
        DetailLevel.SUMMARY: "Summary",
        DetailLevel.MEDIUM: "Medium",
        DetailLevel.DETAILED: "Detailed",
    }
    return labels[value]


def _output_format_label(value: OutputFormat) -> str:
    labels = {
        OutputFormat.PHASES_TABLE: "Phases table",
        OutputFormat.LINE_ITEMS: "Line items",
        OutputFormat.NARRATIVE: "Narrative",
    }
    return labels[value]


def _request_to_message(request: EstimationRequest) -> str:
    return (
        "### Solicitud de estimación\n"
        f"- Tipo de proyecto: {_project_type_label(request.project_type)}\n"
        f"- Nivel de detalle: {_detail_level_label(request.detail_level)}\n"
        f"- Formato de salida: {_output_format_label(request.output_format)}\n\n"
        "#### Descripción\n"
        f"{request.description.strip()}"
    )


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
        }

        section[data-testid="stSidebar"] {
            width: 360px !important;
            min-width: 360px !important;
            max-width: 360px !important;
        }

        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"] {
            width: 360px !important;
            min-width: 360px !important;
            max-width: 360px !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            margin-left: 360px;
        }

        @media (max-width: 960px) {
            section[data-testid="stSidebar"] {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
            }

            section[data-testid="stSidebar"] > div,
            [data-testid="stSidebarContent"] {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
            }

            [data-testid="stAppViewContainer"] > .main {
                margin-left: 0;
            }
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 8px;
        }

        .example-title {
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .example-text {
            font-size: 0.92rem;
            line-height: 1.4;
            margin-bottom: 0.35rem;
        }

        .example-preview {
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


async def _collect_turn(
    request: EstimationRequest,
    friendly_name: str,
    attachments,
) -> tuple[str, dict]:
    metadata = {
        "model": "",
        "provider": "",
        "prompt_version": "",
        "tokens_used": _empty_usage(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    started_at = datetime.now(timezone.utc)
    result, project_metadata = await estimate_session_turn(
        session_id=st.session_state.session_id,
        transcript=request.description,
        project_type=request.project_type,
        detail_level=request.detail_level,
        output_format=request.output_format,
        attachments=attachments,
        friendly_name=friendly_name,
    )
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    metadata.update(
        {
            "model": result.get("model", ""),
            "provider": result.get("provider", ""),
            "prompt_version": result.get("prompt_version", ""),
            "tokens_used": result.get("tokens_used", _empty_usage()),
            "response_time": elapsed,
            "project_metadata": project_metadata.model_dump(),
        }
    )
    return result["text"], metadata


def _render_control_panel() -> str:
    friendly_names = get_available_friendly_names()
    context = get_context_summary()
    sample_transcriptions = list_sample_transcriptions()

    with st.sidebar:
        st.subheader("Configuración")
        selected_name = st.selectbox("Modelo", friendly_names, index=0)
        st.caption(f"session_id: `{st.session_state.session_id}`")

        st.divider()
        st.subheader("Última llamada")
        st.metric("Proveedor", st.session_state.last_provider or "-")
        st.metric("Modelo", st.session_state.last_model or "-")
        st.metric("Tokens entrada", st.session_state.last_usage["prompt"])
        st.metric("Tokens salida", st.session_state.last_usage["completion"])
        st.metric("Tokens total", st.session_state.last_usage["total"])
        st.metric("Tiempo", f"{st.session_state.last_response_time:.2f}s")

        session = get_session(st.session_state.session_id)
        st.divider()
        st.subheader("Project metadata")
        st.json(session.project_metadata.model_dump() if session else {}, expanded=False)

        if st.button("Nueva conversación", use_container_width=True):
            _reset_conversation()
            st.rerun()

        st.divider()
        st.subheader("Transcripciones versionadas")
        if sample_transcriptions:
            selected_sample = st.selectbox(
                "Sample file",
                sample_transcriptions,
                index=0,
            )
            if st.button("Cargar sample del repo", use_container_width=True):
                st.session_state.pending_request_data = {
                    "description": read_sample_transcription(selected_sample),
                    "project_type": ProjectType.INTERNAL_TOOL.value,
                    "detail_level": DetailLevel.MEDIUM.value,
                    "output_format": OutputFormat.NARRATIVE.value,
                }
                st.rerun()
        else:
            st.caption("No hay transcripciones versionadas disponibles.")

        st.divider()
        st.subheader("Reuniones simuladas")
        st.caption(f"{context['examples_count']} ejemplos disponibles")
        for index, example in enumerate(context["examples"], 1):
            with st.expander(f"Ejemplo {index}", expanded=False):
                st.markdown(
                    f'<div class="example-text">{example["transcription"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="example-preview">{example["estimation_preview"]}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Cargar en el formulario",
                    key=f"use_example_{index}",
                    use_container_width=True,
                ):
                    st.session_state.pending_request_data = {
                        "description": example["transcription"],
                        "project_type": ProjectType.WEB_SAAS.value,
                        "detail_level": DetailLevel.MEDIUM.value,
                        "output_format": OutputFormat.NARRATIVE.value,
                    }
                    st.rerun()

    return selected_name


@st.dialog("System prompt activo", width="large")
def _show_prompt_dialog() -> None:
    session = get_session(st.session_state.session_id)
    st.code(get_system_prompt(project_metadata=session.project_metadata if session else None), language="markdown")


def _render_prompt_panel() -> None:
    if st.button("Ver system prompt activo", use_container_width=True):
        _show_prompt_dialog()


def _render_conversation() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("metadata"):
                tokens = message["metadata"].get("tokens_used", _empty_usage())
                st.caption(
                    f"{message['metadata'].get('provider', '')} · "
                    f"{message['metadata'].get('model', '')} · "
                    f"{tokens['total']} tokens · "
                    f"{message['metadata'].get('response_time', 0.0):.2f}s"
                )


def _send_request(request: EstimationRequest, attachments, selected_friendly_name: str) -> None:
    request_summary = _request_to_message(request)
    if attachments:
        filenames = ", ".join(getattr(file, "name", "attachment") for file in attachments)
        request_summary += f"\n\n#### Adjuntos\n{filenames}"
    st.session_state.messages.append(
        {"role": "user", "content": request_summary, "metadata": None}
    )
    with st.chat_message("user"):
        st.markdown(request_summary)

    with st.chat_message("assistant"):
        try:
            estimation, metadata = asyncio.run(
                _collect_turn(request, selected_friendly_name, attachments)
            )
            st.markdown(estimation)
        except Exception as exc:
            estimation = f"No se pudo generar la estimación: {exc}"
            metadata = None
            st.error(estimation)

    st.session_state.messages.append(
        {"role": "assistant", "content": estimation, "metadata": metadata}
    )
    if metadata:
        st.session_state.last_usage = metadata.get("tokens_used", _empty_usage())
        st.session_state.last_model = metadata.get("model", "")
        st.session_state.last_provider = metadata.get("provider", "")
        st.session_state.last_response_time = metadata.get("response_time", 0.0)
    st.rerun()


_init_state()
_apply_pending_form_data()
_apply_styles()
selected_friendly_name = _render_control_panel()

st.title("Software Estimator CAG")
st.caption("Formulario multi-turno con memoria conversacional y contexto enriquecido.")
_render_conversation()

_render_prompt_panel()

with st.form("estimation-request-form", clear_on_submit=False):
    transcript = st.text_area(
        "Transcripción o nuevo contexto del turno",
        key="form_description",
        height=220,
        placeholder="Añade nueva información sobre el proyecto actual, decisiones, alcance o restricciones.",
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        project_type = st.selectbox(
            "Tipo de proyecto",
            list(ProjectType),
            index=list(ProjectType).index(
                ProjectType(st.session_state.form_project_type)
            ),
            format_func=_project_type_label,
            key="form_project_type",
        )
    with col_b:
        detail_level = st.selectbox(
            "Nivel de detalle",
            list(DetailLevel),
            index=list(DetailLevel).index(
                DetailLevel(st.session_state.form_detail_level)
            ),
            format_func=_detail_level_label,
            key="form_detail_level",
        )
    with col_c:
        output_format = st.selectbox(
            "Formato de salida",
            list(OutputFormat),
            index=list(OutputFormat).index(
                OutputFormat(st.session_state.form_output_format)
            ),
            format_func=_output_format_label,
            key="form_output_format",
        )
    attachments = st.file_uploader(
        "Adjuntos complementarios",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md"],
    )

    submitted = st.form_submit_button("Generar estimación", use_container_width=True)
if submitted:
    try:
        request = EstimationRequest(
            description=transcript,
            project_type=project_type,
            detail_level=detail_level,
            output_format=output_format,
        )
    except Exception as exc:
        st.warning(str(exc))
    else:
        _send_request(request, attachments or [], selected_friendly_name)
