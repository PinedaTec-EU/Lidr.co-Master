import asyncio
from datetime import datetime, timezone

import streamlit as st

from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType, UserTier
from app.services.session_service import (
    create_session,
    estimate_session_turn,
    get_session,
    persist_last_run_info,
    set_session_user_profile,
    update_external_context_config,
)
from app.services.llm_service import (
    get_available_friendly_names,
    get_context_summary,
    get_system_prompt,
)
from app.context.sample_transcriptions import (
    list_sample_transcriptions,
    read_sample_transcription,
)
from app.context.sample_documents import (
    list_sample_documents,
    resolve_sample_document_paths,
)


st.set_page_config(
    page_title="Software Estimator CAG",
    page_icon="📝",
    layout="wide",
)


def _empty_usage() -> dict:
    return {"prompt": 0, "completion": 0, "total": 0}


def _split_multiline_values(raw_value: str) -> list[str]:
    normalized = raw_value.replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _clear_query_params() -> None:
    try:
        del st.query_params["chatid"]
    except KeyError:
        pass


def _sync_query_params(session_id: str) -> None:
    st.query_params["chatid"] = session_id


def _hydrate_messages_from_session(session_id: str) -> list[dict]:
    session = get_session(session_id)
    messages = [
        {
            "role": "assistant",
            "content": "La sesión está lista. Añade contexto del proyecto y continuaré sobre la misma conversación.",
            "metadata": None,
        }
    ]
    if session is None:
        return messages

    if session.conversation_messages:
        messages.extend(
            {"role": message["role"], "content": message["content"], "metadata": None}
            for message in session.conversation_messages
        )
        return messages

    for user_message, assistant_message in session.history.turns:
        messages.append({"role": "user", "content": user_message, "metadata": None})
        messages.append({"role": "assistant", "content": assistant_message, "metadata": None})
    return messages


def _hydrate_last_run_state_from_session(session_id: str) -> dict:
    session = get_session(session_id)
    if session is None:
        return {
            "last_usage": _empty_usage(),
            "last_model": "",
            "last_provider": "",
            "last_response_time": 0.0,
            "last_document_context": [],
            "notion_page_ids_text": "",
            "notion_search_terms_text": "",
            "last_external_context": [],
        }

    last_run_info = session.last_run_info or {}
    return {
        "last_usage": last_run_info.get("tokens_used", _empty_usage()),
        "last_model": last_run_info.get("model", ""),
        "last_provider": last_run_info.get("provider", ""),
        "last_response_time": float(last_run_info.get("response_time", 0.0)),
        "last_document_context": session.last_document_context,
        "notion_page_ids_text": "\n".join(session.external_context_config.notion_page_ids),
        "notion_search_terms_text": "\n".join(session.external_context_config.notion_search_terms),
        "last_external_context": session.last_external_context,
    }


def _resolve_initial_session_id() -> str | None:
    requested_session_id = st.query_params.get("chatid")
    if requested_session_id:
        session = get_session(requested_session_id)
        if session is not None:
            return requested_session_id

    return None


def _default_messages() -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": (
                "Selecciona un role y un nombre visible para esta sesión. "
                "Quedará fijado hasta que abras una conversación nueva."
            ),
            "metadata": None,
        }
    ]


def _sync_state_from_session(session_id: str) -> None:
    hydrated = _hydrate_last_run_state_from_session(session_id)
    session = get_session(session_id)

    st.session_state.session_id = session_id
    st.session_state.messages = _hydrate_messages_from_session(session_id)
    st.session_state.last_usage = hydrated["last_usage"]
    st.session_state.last_model = hydrated["last_model"]
    st.session_state.last_provider = hydrated["last_provider"]
    st.session_state.last_response_time = hydrated["last_response_time"]
    st.session_state.last_document_context = hydrated["last_document_context"]
    st.session_state.notion_page_ids_text = hydrated["notion_page_ids_text"]
    st.session_state.notion_search_terms_text = hydrated["notion_search_terms_text"]
    st.session_state.last_external_context = hydrated["last_external_context"]
    st.session_state.selected_user_tier = session.user_tier if session else None
    st.session_state.user_display_name = session.user_display_name if session else ""


def _init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = _resolve_initial_session_id()
    session = get_session(st.session_state.session_id) if st.session_state.session_id else None
    hydrated = (
        _hydrate_last_run_state_from_session(st.session_state.session_id)
        if st.session_state.session_id
        else {
            "last_usage": _empty_usage(),
            "last_model": "",
            "last_provider": "",
            "last_response_time": 0.0,
            "last_document_context": [],
            "notion_page_ids_text": "",
            "notion_search_terms_text": "",
            "last_external_context": [],
        }
    )
    if "messages" not in st.session_state:
        st.session_state.messages = (
            _hydrate_messages_from_session(st.session_state.session_id)
            if st.session_state.session_id
            else _default_messages()
        )
    if "last_usage" not in st.session_state:
        st.session_state.last_usage = hydrated["last_usage"]
    if "last_model" not in st.session_state:
        st.session_state.last_model = hydrated["last_model"]
    if "last_provider" not in st.session_state:
        st.session_state.last_provider = hydrated["last_provider"]
    if "last_response_time" not in st.session_state:
        st.session_state.last_response_time = hydrated["last_response_time"]
    if "pending_request_data" not in st.session_state:
        st.session_state.pending_request_data = None
    if "form_description" not in st.session_state:
        st.session_state.form_description = ""
    if "form_project_type" not in st.session_state:
        st.session_state.form_project_type = ProjectType.WEB_SAAS
    if "form_detail_level" not in st.session_state:
        st.session_state.form_detail_level = DetailLevel.MEDIUM
    if "form_output_format" not in st.session_state:
        st.session_state.form_output_format = OutputFormat.NARRATIVE
    if "selected_sample_documents" not in st.session_state:
        st.session_state.selected_sample_documents = []
    if "last_document_context" not in st.session_state:
        st.session_state.last_document_context = hydrated["last_document_context"]
    if "notion_page_ids_text" not in st.session_state:
        st.session_state.notion_page_ids_text = hydrated["notion_page_ids_text"]
    if "notion_search_terms_text" not in st.session_state:
        st.session_state.notion_search_terms_text = hydrated["notion_search_terms_text"]
    if "last_external_context" not in st.session_state:
        st.session_state.last_external_context = hydrated["last_external_context"]
    if "selected_user_tier" not in st.session_state:
        st.session_state.selected_user_tier = session.user_tier if session else None
    elif session and session.user_tier is not None:
        st.session_state.selected_user_tier = session.user_tier
    if "user_display_name" not in st.session_state:
        st.session_state.user_display_name = session.user_display_name if session else ""
    elif session and session.user_display_name:
        st.session_state.user_display_name = session.user_display_name
    if "pending_user_tier_selection" not in st.session_state:
        st.session_state.pending_user_tier_selection = (
            st.session_state.selected_user_tier.value
            if st.session_state.selected_user_tier
            else UserTier.DEVELOPER.value
        )
    if "pending_user_display_name" not in st.session_state:
        st.session_state.pending_user_display_name = (
            session.user_display_name if session and session.user_display_name else ""
        )


def _reset_conversation() -> None:
    st.session_state.session_id = None
    _clear_query_params()
    st.session_state.messages = _default_messages()
    st.session_state.last_usage = _empty_usage()
    st.session_state.last_model = ""
    st.session_state.last_provider = ""
    st.session_state.last_response_time = 0.0
    st.session_state.pending_request_data = None
    st.session_state.form_description = ""
    st.session_state.form_project_type = ProjectType.WEB_SAAS
    st.session_state.form_detail_level = DetailLevel.MEDIUM
    st.session_state.form_output_format = OutputFormat.NARRATIVE
    st.session_state.selected_sample_documents = []
    st.session_state.last_document_context = []
    st.session_state.notion_page_ids_text = ""
    st.session_state.notion_search_terms_text = ""
    st.session_state.last_external_context = []
    st.session_state.selected_user_tier = None
    st.session_state.user_display_name = ""
    st.session_state.pending_user_tier_selection = UserTier.DEVELOPER.value
    st.session_state.pending_user_display_name = ""


def _apply_pending_form_data() -> None:
    pending_data = st.session_state.pending_request_data or {}
    if not pending_data:
        return

    st.session_state.form_description = pending_data.get("description", "")
    st.session_state.form_project_type = pending_data.get(
        "project_type",
        ProjectType.WEB_SAAS.value,
    )
    st.session_state.form_project_type = ProjectType(st.session_state.form_project_type)
    st.session_state.form_detail_level = pending_data.get(
        "detail_level",
        DetailLevel.MEDIUM.value,
    )
    st.session_state.form_detail_level = DetailLevel(st.session_state.form_detail_level)
    st.session_state.form_output_format = pending_data.get(
        "output_format",
        OutputFormat.NARRATIVE.value,
    )
    st.session_state.form_output_format = OutputFormat(st.session_state.form_output_format)
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


def _user_tier_label(value: UserTier) -> str:
    labels = {
        UserTier.DEVELOPER: "Developer",
        UserTier.PM: "PM",
        UserTier.EXECUTIVE: "Executive",
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

        .run-dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-top: 0.35rem;
        }

        .run-kpi {
            background:
                linear-gradient(160deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)),
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 55%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 0.85rem 0.9rem;
            min-height: 88px;
        }

        .run-kpi-label {
            color: #9ca3af;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }

        .run-kpi-value {
            font-size: 1.7rem;
            font-weight: 700;
            line-height: 1.1;
            color: #f8fafc;
        }

        .run-kpi-subvalue {
            font-size: 0.88rem;
            color: #cbd5e1;
            margin-top: 0.35rem;
            word-break: break-word;
        }

        .run-band {
            background:
                linear-gradient(135deg, rgba(251, 191, 36, 0.14), rgba(248, 250, 252, 0.02));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 0.95rem;
            margin-top: 0.35rem;
        }

        .run-band-label {
            color: #9ca3af;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }

        .run-band-value {
            color: #f8fafc;
            font-size: 1rem;
            font-weight: 600;
            line-height: 1.35;
            word-break: break-word;
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


def _render_last_call_dashboard() -> None:
    provider = st.session_state.last_provider or "-"
    model = st.session_state.last_model or "-"
    usage = st.session_state.last_usage
    response_time = f"{st.session_state.last_response_time:.2f}s"

    st.markdown(
        f"""
        <div class="run-band">
            <div class="run-band-label">Provider</div>
            <div class="run-band-value">{provider}</div>
        </div>
        <div class="run-band">
            <div class="run-band-label">Model</div>
            <div class="run-band-value">{model}</div>
        </div>
        <div class="run-dashboard">
            <div class="run-kpi">
                <div class="run-kpi-label">Prompt tokens</div>
                <div class="run-kpi-value">{usage["prompt"]}</div>
            </div>
            <div class="run-kpi">
                <div class="run-kpi-label">Completion</div>
                <div class="run-kpi-value">{usage["completion"]}</div>
            </div>
            <div class="run-kpi">
                <div class="run-kpi-label">Total tokens</div>
                <div class="run-kpi-value">{usage["total"]}</div>
            </div>
            <div class="run-kpi">
                <div class="run-kpi-label">Latency</div>
                <div class="run-kpi-value">{response_time}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


async def _collect_turn(
    request: EstimationRequest,
    friendly_name: str,
    attachments,
    document_paths: list[str],
    display_user_message: str,
) -> tuple[str, dict, list[str]]:
    metadata = {
        "model": "",
        "provider": "",
        "prompt_version": "",
        "tokens_used": _empty_usage(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    started_at = datetime.now(timezone.utc)
    result, project_metadata, document_context_sections = await estimate_session_turn(
        session_id=st.session_state.session_id,
        transcript=request.description,
        project_type=request.project_type,
        detail_level=request.detail_level,
        output_format=request.output_format,
        attachments=attachments,
        document_paths=document_paths,
        display_user_message=display_user_message,
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
    return result["text"], metadata, document_context_sections


def _render_control_panel() -> str:
    friendly_names = get_available_friendly_names()
    context = get_context_summary()
    sample_transcriptions = list_sample_transcriptions()
    sample_documents = list_sample_documents()

    with st.sidebar:
        st.subheader("Configuración")
        selected_name = st.selectbox("Modelo", friendly_names, index=0)
        if st.session_state.selected_user_tier:
            st.caption(
                f"`{_user_tier_label(st.session_state.selected_user_tier)}: "
                f"{st.session_state.user_display_name or '-'}`"
            )
        else:
            st.caption("Role fijo en la sesión: `pendiente`")
        if st.session_state.session_id:
            st.caption(f"session_id: `{st.session_state.session_id}`")
        else:
            st.caption("session_id: `pendiente de crear`")

        st.divider()
        st.subheader("Última llamada")
        _render_last_call_dashboard()

        session = get_session(st.session_state.session_id) if st.session_state.session_id else None
        st.divider()
        st.subheader("Contexto persistido")
        if st.button("Ver project metadata", use_container_width=True):
            _show_project_metadata_dialog()
        if st.button("Ver document sources", use_container_width=True):
            _show_document_sources_dialog()
        if st.button("Ver contexto externo", use_container_width=True):
            _show_external_context_dialog()
        if st.button("Ver configuración externa", use_container_width=True):
            _show_external_context_config_dialog()

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
        st.subheader("Documentos del repo")
        if sample_documents:
            selected_documents = st.multiselect(
                "Sample documents",
                sample_documents,
                default=st.session_state.selected_sample_documents,
            )
            st.session_state.selected_sample_documents = selected_documents
        else:
            st.caption("No hay documentos versionados disponibles.")

        st.divider()
        st.subheader("Fuentes externas")
        st.caption("Configura referencias explícitas o términos para recuperar contexto desde Notion.")
        notion_page_ids_text = st.text_area(
            "Notion page IDs",
            key="notion_page_ids_text",
            height=90,
            placeholder="Uno por línea o separados por coma.",
        )
        notion_search_terms_text = st.text_area(
            "Notion search terms",
            key="notion_search_terms_text",
            height=90,
            placeholder="Cliente, proyecto, iniciativa o palabras clave.",
        )
        if st.button("Guardar fuentes externas", use_container_width=True):
            update_external_context_config(
                st.session_state.session_id,
                notion_page_ids=_split_multiline_values(notion_page_ids_text),
                notion_search_terms=_split_multiline_values(notion_search_terms_text),
            )
            st.toast("Fuentes externas guardadas para esta sesión.")
            st.rerun()

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
    st.code(
        get_system_prompt(
            project_metadata=session.project_metadata if session else None,
            external_context=[
                item for item in (session.last_external_context if session else [])
            ],
            user_tier=session.user_tier if session and session.user_tier else UserTier.DEVELOPER,
            user_display_name=session.user_display_name if session else None,
        ),
        language="markdown",
    )


@st.dialog("Output documental enriquecido", width="large")
def _show_document_context_dialog() -> None:
    session = get_session(st.session_state.session_id)
    sections = st.session_state.last_document_context or (session.last_document_context if session else [])
    if not sections:
        st.info("Todavía no hay contenido documental procesado en esta sesión.")
        return

    for index, section in enumerate(sections, 1):
        st.markdown(f"### Documento {index}")
        st.code(section, language="markdown")


@st.dialog("Project metadata", width="large")
def _show_project_metadata_dialog() -> None:
    session = get_session(st.session_state.session_id)
    if session is None:
        st.info("La sesión actual no existe.")
        return

    st.json(session.project_metadata.model_dump(), expanded=True)


@st.dialog("Selecciona el role de la sesión", width="large")
def _show_user_tier_dialog() -> None:
    st.markdown(
        "Este role y el nombre visible condicionan el estilo de estimación durante toda la sesión. "
        "En esta POC no se puede cambiar una vez fijado."
    )
    st.text_input(
        "Nombre visible del usuario",
        key="pending_user_display_name",
        placeholder="pineda",
    )
    selected_value = st.radio(
        "Role",
        options=[tier.value for tier in UserTier],
        format_func=lambda value: _user_tier_label(UserTier(value)),
        key="pending_user_tier_selection",
    )
    if st.button("Confirmar role", use_container_width=True):
        selected_tier = UserTier(selected_value)
        display_name = st.session_state.pending_user_display_name.strip()
        if not display_name:
            st.warning("Indica un nombre visible para esta sesión.")
            return
        if st.session_state.session_id:
            set_session_user_profile(
                st.session_state.session_id,
                user_tier=selected_tier,
                user_display_name=display_name,
            )
            _sync_state_from_session(st.session_state.session_id)
        else:
            session_id = create_session(
                user_tier=selected_tier,
                user_display_name=display_name,
            )
            _sync_query_params(session_id)
            _sync_state_from_session(session_id)
        st.rerun()


@st.dialog("Configuración de contexto externo", width="large")
def _show_external_context_config_dialog() -> None:
    session = get_session(st.session_state.session_id)
    if session is None:
        st.info("La sesión actual no existe.")
        return

    st.json(session.external_context_config.model_dump(), expanded=True)


@st.dialog("Contexto externo resuelto", width="large")
def _show_external_context_dialog() -> None:
    session = get_session(st.session_state.session_id)
    if session is None:
        st.info("La sesión actual no existe.")
        return

    if not session.last_external_context:
        st.info("Todavía no hay contexto externo resuelto en esta sesión.")
        return

    for index, item in enumerate(session.last_external_context, 1):
        st.markdown(f"### Fuente {index}: {item.get('title', 'Untitled')}")
        st.caption(
            f"{item.get('source', 'external')} · {item.get('updated_at', 'sin fecha')} · "
            f"{item.get('relevance_reason', 'sin motivo registrado')}"
        )
        if item.get("url"):
            st.markdown(f"[Abrir origen]({item['url']})")
        st.code(item.get("content", ""), language="markdown")


@st.dialog("Document sources", width="large")
def _show_document_sources_dialog() -> None:
    session = get_session(st.session_state.session_id)
    if session is None:
        st.info("La sesión actual no existe.")
        return

    if not session.document_sources:
        st.info("Todavía no hay rutas documentales asociadas a esta sesión.")
        return

    for source in session.document_sources:
        st.code(source, language="text")


def _render_prompt_panel() -> None:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("Ver system prompt activo", use_container_width=True):
            _show_prompt_dialog()
    with col_b:
        if st.button("Ver output de Docling", use_container_width=True):
            _show_document_context_dialog()
    with col_c:
        if st.button("Ver contexto externo efectivo", use_container_width=True):
            _show_external_context_dialog()


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


def _send_request(
    request: EstimationRequest,
    attachments,
    document_paths: list[str],
    selected_friendly_name: str,
) -> None:
    request_summary = _request_to_message(request)
    if attachments:
        filenames = ", ".join(getattr(file, "name", "attachment") for file in attachments)
        request_summary += f"\n\n#### Adjuntos\n{filenames}"
    if document_paths:
        request_summary += "\n\n#### Documentos por ruta\n" + "\n".join(
            f"- `{path}`" for path in document_paths
        )
    st.session_state.messages.append(
        {"role": "user", "content": request_summary, "metadata": None}
    )
    with st.chat_message("user"):
        st.markdown(request_summary)

    with st.chat_message("assistant"):
        try:
            estimation, metadata, document_context_sections = asyncio.run(
                _collect_turn(
                    request,
                    selected_friendly_name,
                    attachments,
                    document_paths,
                    request_summary,
                )
            )
            st.markdown(estimation)
        except Exception as exc:
            estimation = f"No se pudo generar la estimación: {exc}"
            metadata = None
            document_context_sections = []
            st.error(estimation)

    st.session_state.messages.append(
        {"role": "assistant", "content": estimation, "metadata": metadata}
    )
    if metadata:
        st.session_state.last_usage = metadata.get("tokens_used", _empty_usage())
        st.session_state.last_model = metadata.get("model", "")
        st.session_state.last_provider = metadata.get("provider", "")
        st.session_state.last_response_time = metadata.get("response_time", 0.0)
        persist_last_run_info(
            st.session_state.session_id,
            provider=st.session_state.last_provider,
            model=st.session_state.last_model,
            tokens_used=st.session_state.last_usage,
            response_time=st.session_state.last_response_time,
        )
    st.session_state.last_document_context = document_context_sections
    session = get_session(st.session_state.session_id)
    st.session_state.last_external_context = session.last_external_context if session else []
    st.rerun()


_init_state()
_apply_pending_form_data()
_apply_styles()
if st.session_state.selected_user_tier is None:
    _show_user_tier_dialog()
    st.title("Software Estimator CAG")
    st.info("Selecciona un role y un nombre visible para crear o recuperar una conversación.")
    st.stop()
if not st.session_state.user_display_name:
    _show_user_tier_dialog()
    st.title("Software Estimator CAG")
    st.info("Completa el nombre visible de la sesión para continuar.")
    st.stop()
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
            format_func=_project_type_label,
            key="form_project_type",
        )
    with col_b:
        detail_level = st.selectbox(
            "Nivel de detalle",
            list(DetailLevel),
            format_func=_detail_level_label,
            key="form_detail_level",
        )
    with col_c:
        output_format = st.selectbox(
            "Formato de salida",
            list(OutputFormat),
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
        _send_request(
            request,
            attachments or [],
            resolve_sample_document_paths(st.session_state.selected_sample_documents),
            selected_friendly_name,
        )
