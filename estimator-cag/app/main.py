from fastapi import FastAPI

from app.routers.estimations import router as estimations_router

app = FastAPI(
    title="Software Estimator CAG",
    description=(
        "API de estimación de software con contrato tipado y prompts Jinja2 versionados. "
        "Recibe una descripción de proyecto y parámetros de salida, renderiza prompts "
        "separados de system/user y devuelve una estimación textual."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(estimations_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "estimator-cag", "version": "0.1.0"}
