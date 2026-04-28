from fastapi import FastAPI

from app.routers.estimations import router as estimations_router

app = FastAPI(title="Software Estimator CAG", version="0.1.0")

app.include_router(estimations_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
