from fastapi import FastAPI

from app.routers.estimations import router as estimations_router

app = FastAPI(
    title="Software Estimator CAG",
    description=(
        "API de estimación de software basada en Claude AI con generación aumentada por contexto (CAG). "
        "Analiza historias de usuario y genera estimaciones de esfuerzo en puntos de historia "
        "junto con una justificación detallada."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(estimations_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "estimator-cag", "version": "0.1.0"}
