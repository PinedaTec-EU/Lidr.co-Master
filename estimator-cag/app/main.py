from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.embedding_pipeline.db import async_engine
from app.embedding_pipeline.index_maintenance import reconcile_managed_metadata_indexes
from app.embedding_pipeline.router import router as embeddings_router
from app.routers.estimate_runtime import router as estimate_runtime_router
from app.routers.agent_estimations import router as agent_estimations_router
from app.routers.estimations import router as estimations_router
from app.routers.retrieval import router as retrieval_router
from app.routers.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.vector_db_initialize_on_start and async_engine is not None:
        await reconcile_managed_metadata_indexes(async_engine)
    if not settings.agent_checkpoint_database_url:
        yield
        return
    async with AsyncPostgresSaver.from_conn_string(settings.agent_checkpoint_database_url) as checkpointer:
        await checkpointer.setup()
        _app.state.agent_checkpointer = checkpointer
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
app.include_router(retrieval_router, prefix="/api/v1")
app.include_router(estimate_runtime_router, prefix="/api/v1")
app.include_router(agent_estimations_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "estimator-cag", "version": "0.1.0"}
