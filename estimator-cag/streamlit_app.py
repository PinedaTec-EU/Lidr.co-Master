import os

import httpx
import streamlit as st

from app.schemas import (
    DetailLevel,
    EstimationRequest,
    EstimationResponse,
    OutputFormat,
    ProjectType,
)


st.set_page_config(
    page_title="Software Estimator CAG",
    page_icon="📝",
    layout="wide",
)

API_BASE_URL = os.getenv("ESTIMATOR_API_BASE_URL", "http://localhost:8000/api/v1")


def _init_state() -> None:
    if "result_text" not in st.session_state:
        st.session_state.result_text = ""
    if "prompt_version" not in st.session_state:
        st.session_state.prompt_version = ""


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

        .result-card {
            padding: 1rem 1.25rem;
            border: 1px solid rgba(120, 120, 120, 0.25);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.02);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Servicio")
        st.code(f"{API_BASE_URL}/estimate")
        st.caption("El cliente envía un JSON tipado al servicio IA.")


def _submit_request(request: EstimationRequest) -> None:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/estimate",
            json=request.model_dump(mode="json"),
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        st.error(f"El servicio devolvió {exc.response.status_code}: {exc.response.text}")
        return
    except httpx.HTTPError as exc:
        st.error(f"No se pudo contactar con la API: {exc}")
        return

    estimation = EstimationResponse.model_validate(response.json())
    st.session_state.result_text = estimation.text
    st.session_state.prompt_version = estimation.prompt_version


_init_state()
_apply_styles()
_render_sidebar()

st.title("Software Estimator CAG")
st.caption("Formulario tipado que envía un contrato estable al servicio IA.")

with st.form("estimation-form"):
    description = st.text_area(
        "Descripción del proyecto",
        height=220,
        placeholder="Describe el producto, objetivos, alcance, restricciones y plazo esperado.",
    )
    project_type = st.selectbox(
        "Tipo de proyecto",
        [member.value for member in ProjectType],
        index=0,
    )
    detail_level = st.selectbox(
        "Nivel de detalle",
        [member.value for member in DetailLevel],
        index=1,
    )
    output_format = st.selectbox(
        "Formato de salida",
        [member.value for member in OutputFormat],
        index=0,
    )
    submitted = st.form_submit_button("Generar estimación", use_container_width=True)

if submitted:
    cleaned_description = description.strip()
    if cleaned_description:
        _submit_request(
            EstimationRequest(
                description=cleaned_description,
                project_type=ProjectType(project_type),
                detail_level=DetailLevel(detail_level),
                output_format=OutputFormat(output_format),
            )
        )
    else:
        st.warning("La descripción no puede estar vacía.")

if st.session_state.result_text:
    st.subheader("Resultado")
    st.markdown(
        f'<div class="result-card">{st.session_state.result_text}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"prompt_version={st.session_state.prompt_version}")
