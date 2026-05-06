from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.executions import router as executions_router

app = FastAPI(
    title="SIH Smart Analysis",
    description=(
        "Execution intelligence for SphereIntegrationHub reports. "
        "Phase 1 analyzes the last executions with CAG-style fixed context. "
        "Phase 2 retrieves semantically similar historical executions for RAG-style analysis."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(analysis_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "sih-smart-analysis", "version": "0.1.0"}
