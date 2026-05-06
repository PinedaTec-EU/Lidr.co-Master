import asyncio
from datetime import datetime, timezone

import streamlit as st

from app.services.llm_service import (
    get_available_friendly_names,
    get_context_summary,
    get_system_prompt,
    stream_estimation,
)


st.set_page_config(
    page_title="Software Estimator CAG",
    page_icon="📝",
    layout="wide",
)


def _empty_usage() -> dict:
    return {"prompt": 0, "completion": 0, "total": 0}


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Pega una transcripción de reunión y generaré una estimación de software.",
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
    if "transcription_text" not in st.session_state:
        st.session_state.transcription_text = ""


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


async def _collect_stream(transcription: str, friendly_name: str) -> tuple[str, dict]:
    content = ""
    metadata = {
        "model": "",
        "provider": "",
        "tokens_used": _empty_usage(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    placeholder = st.empty()
    started_at = datetime.now(timezone.utc)

    async for event in stream_estimation(transcription, friendly_name=friendly_name):
        if event["type"] == "delta":
            content += event["content"]
            placeholder.markdown(content + "▌")
        elif event["type"] == "metadata":
            metadata.update(event)

    placeholder.markdown(content)
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    metadata["response_time"] = elapsed
    return content, metadata


def _render_control_panel() -> str:
    friendly_names = get_available_friendly_names()
    context = get_context_summary()

    with st.sidebar:
        st.subheader("Configuración")
        selected_name = st.selectbox("Modelo", friendly_names, index=0)

        st.divider()
        st.subheader("Última llamada")
        st.metric("Proveedor", st.session_state.last_provider or "-")
        st.metric("Modelo", st.session_state.last_model or "-")
        st.metric("Tokens entrada", st.session_state.last_usage["prompt"])
        st.metric("Tokens salida", st.session_state.last_usage["completion"])
        st.metric("Tokens total", st.session_state.last_usage["total"])
        st.metric("Tiempo", f"{st.session_state.last_response_time:.2f}s")

        if st.button("Limpiar conversación", use_container_width=True):
            st.session_state.clear()
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
                    "Pegar en el formulario",
                    key=f"use_example_{index}",
                    use_container_width=True,
                ):
                    st.session_state.transcription_text = example["transcription"]
                    st.rerun()

    return selected_name


@st.dialog("System prompt activo", width="large")
def _show_prompt_dialog() -> None:
    st.code(get_system_prompt(), language="markdown")


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


def _send_transcription(transcription: str, selected_friendly_name: str) -> None:
    st.session_state.messages.append(
        {"role": "user", "content": transcription, "metadata": None}
    )
    with st.chat_message("user"):
        st.markdown(transcription)

    with st.chat_message("assistant"):
        try:
            estimation, metadata = asyncio.run(
                _collect_stream(transcription, selected_friendly_name)
            )
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
_apply_styles()
selected_friendly_name = _render_control_panel()

st.title("Software Estimator CAG")
st.caption("Chat conversacional con Streamlit usando el mismo system prompt del endpoint CAG.")

st.subheader("Estimador")
transcription = st.text_area(
    "Transcripción de reunión",
    key="transcription_text",
    height=220,
    placeholder="Pega aquí la transcripción de la reunión o usa una conversación de ejemplo.",
)
submitted = st.button("Enviar estimación", use_container_width=True)
_render_conversation()

_render_prompt_panel()

if submitted:
    cleaned_transcription = transcription.strip()
    if cleaned_transcription:
        _send_transcription(cleaned_transcription, selected_friendly_name)
    else:
        st.warning("La transcripción no puede estar vacía.")
