from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.embedding_pipeline.router import router as embeddings_router
from app.embedding_pipeline.vector_store import PgVectorStore
from app.routers.estimations import router as estimations_router
from app.routers.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.vector_db_initialize_on_start and settings.vector_database_url:
        PgVectorStore().ensure_schema()
    yield

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
    lifespan=lifespan,
)

app.include_router(estimations_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(embeddings_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "estimator-cag", "version": "0.1.0"}
