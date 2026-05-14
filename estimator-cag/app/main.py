from fastapi import FastAPI

from app.routers.estimations import router as estimations_router

app = FastAPI(
    title="Software Estimator CAG",
    description=(
        "API de estimación de software con Context Augmented Generation (CAG). "
        "Recibe la transcripción de una reunión, inyecta ejemplos estáticos de estimaciones "
        "y devuelve una propuesta de esfuerzo, equipo y duración."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(estimations_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "estimator-cag", "version": "0.1.0"}
