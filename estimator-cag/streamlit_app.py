import os

import httpx
import streamlit as st

from app.schemas import (
    DetailLevel,
    EstimationJob,
    EstimationJobStatus,
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
    if "selected_job_id" not in st.session_state:
        st.session_state.selected_job_id = None


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

        .job-chip {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
        }

        .job-chip.pending { background: #fff4cc; color: #8a5a00; }
        .job-chip.running { background: #dbeafe; color: #1d4ed8; }
        .job-chip.succeeded { background: #dcfce7; color: #166534; }
        .job-chip.failed { background: #fee2e2; color: #b91c1c; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Servicio")
        st.code(f"{API_BASE_URL}/estimate-jobs")
        st.caption("La UI crea jobs asíncronos y consulta su estado.")
        st.divider()
        st.subheader("Controles")
        st.caption("Usa el refresco manual para consultar estados sin bloquear la página.")


def _job_status_chip(status: EstimationJobStatus) -> str:
    return f'<span class="job-chip {status.value}">{status.value}</span>'


def _submit_job(request: EstimationRequest) -> None:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/estimate-jobs",
            json=request.model_dump(mode="json"),
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        st.error(f"El servicio devolvió {exc.response.status_code}: {exc.response.text}")
        return
    except httpx.HTTPError as exc:
        st.error(f"No se pudo contactar con la API: {exc}")
        return

    job = EstimationJob.model_validate(response.json())
    st.session_state.selected_job_id = job.id
    st.success(f"Petición creada: {job.id}")


def _load_jobs() -> list[EstimationJob]:
    try:
        response = httpx.get(f"{API_BASE_URL}/estimate-jobs", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        st.error(f"No se pudo cargar el histórico: {exc}")
        return []

    return [EstimationJob.model_validate(item) for item in response.json()]


def _load_job(job_id: str) -> EstimationJob | None:
    try:
        response = httpx.get(f"{API_BASE_URL}/estimate-jobs/{job_id}", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        st.error(f"No se pudo cargar la petición {job_id}: {exc}")
        return None

    return EstimationJob.model_validate(response.json())


def _render_form() -> None:
    st.subheader("Nueva petición")
    st.caption("El envío devuelve un job en `pending` y la UI queda libre.")

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
        submitted = st.form_submit_button("Crear petición", use_container_width=True)

    if not submitted:
        return

    cleaned_description = description.strip()
    if not cleaned_description:
        st.warning("La descripción no puede estar vacía.")
        return

    _submit_job(
        EstimationRequest(
            description=cleaned_description,
            project_type=ProjectType(project_type),
            detail_level=DetailLevel(detail_level),
            output_format=OutputFormat(output_format),
        )
    )


def _render_job_sections(jobs: list[EstimationJob]) -> None:
    pending_jobs = [job for job in jobs if job.status is EstimationJobStatus.PENDING]
    running_jobs = [job for job in jobs if job.status is EstimationJobStatus.RUNNING]
    completed_jobs = [
        job for job in jobs if job.status in {EstimationJobStatus.SUCCEEDED, EstimationJobStatus.FAILED}
    ]

    counts = st.columns(4)
    counts[0].metric("Total", len(jobs))
    counts[1].metric("Pending", len(pending_jobs))
    counts[2].metric("Running", len(running_jobs))
    counts[3].metric("Completed", len(completed_jobs))

    col_left, col_right = st.columns([1.1, 1.2], gap="large")

    with col_left:
        st.subheader("Pendientes")
        if not pending_jobs:
            st.caption("No hay peticiones pendientes.")
        for job in pending_jobs:
            st.markdown(
                f"{_job_status_chip(job.status)} `{job.id}`",
                unsafe_allow_html=True,
            )
            st.caption(job.request.description[:140])

        st.subheader("En ejecución")
        if not running_jobs:
            st.caption("No hay peticiones en ejecución.")
        for job in running_jobs:
            st.markdown(
                f"{_job_status_chip(job.status)} `{job.id}`",
                unsafe_allow_html=True,
            )
            st.caption(job.request.description[:140])

    with col_right:
        st.subheader("Histórico")
        if not jobs:
            st.caption("Todavía no hay peticiones.")
        for job in jobs:
            title = f"{job.status.value} · {job.request.project_type.value} · {job.id[:8]}"
            with st.expander(title, expanded=st.session_state.selected_job_id == job.id):
                st.markdown(_job_status_chip(job.status), unsafe_allow_html=True)
                st.caption(f"creado {job.created_at}")
                st.write(job.request.description)

                if job.response is not None:
                    st.markdown(
                        f'<div class="result-card">{job.response.text}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"prompt_version={job.response.prompt_version}")

                if job.error_message:
                    st.error(job.error_message)

_init_state()
_apply_styles()
_render_sidebar()

st.title("Software Estimator CAG")
st.caption("Portal de peticiones asíncronas con histórico, estados y detalle de ejecución.")

toolbar = st.columns([0.7, 0.3])
with toolbar[0]:
    st.caption("Crea peticiones y revisa el histórico sin bloquear la interfaz.")
with toolbar[1]:
    if st.button("Refrescar histórico", use_container_width=True):
        st.rerun()

_render_form()

jobs = _load_jobs()
if st.session_state.selected_job_id:
    selected_job = _load_job(st.session_state.selected_job_id)
    if selected_job is not None:
        jobs = [selected_job] + [job for job in jobs if job.id != selected_job.id]

_render_job_sections(jobs)
