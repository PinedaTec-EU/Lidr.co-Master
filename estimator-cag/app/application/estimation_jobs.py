import asyncio
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.application.estimation import EstimationService
from app.schemas import EstimationJob, EstimationJobStatus, EstimationRequest


class EstimationJobStore(Protocol):
    async def create(self, request: EstimationRequest, prompt_version: str) -> EstimationJob: ...

    async def get(self, job_id: str) -> EstimationJob | None: ...

    async def list(self) -> list[EstimationJob]: ...

    async def update_status(
        self,
        job_id: str,
        status: EstimationJobStatus,
        *,
        response=None,
        error_message: str | None = None,
    ) -> EstimationJob | None: ...


class EstimationJobService:
    def __init__(
        self,
        estimation_service: EstimationService,
        job_store: EstimationJobStore,
    ) -> None:
        self._estimation_service = estimation_service
        self._job_store = job_store
        self._tasks: set[asyncio.Task] = set()

    async def submit(
        self,
        request: EstimationRequest,
        prompt_version: str = "v1",
    ) -> EstimationJob:
        job = await self._job_store.create(request, prompt_version)
        task = asyncio.create_task(
            self._run_job(
                job_id=job.id,
                request=request,
                prompt_version=prompt_version,
            )
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def get(self, job_id: str) -> EstimationJob | None:
        return await self._job_store.get(job_id)

    async def list(self) -> list[EstimationJob]:
        return await self._job_store.list()

    async def _run_job(
        self,
        *,
        job_id: str,
        request: EstimationRequest,
        prompt_version: str,
    ) -> None:
        await self._job_store.update_status(job_id, EstimationJobStatus.RUNNING)
        try:
            response = await self._estimation_service.estimate(
                request,
                prompt_version=prompt_version,
            )
        except Exception as exc:  # noqa: BLE001
            await self._job_store.update_status(
                job_id,
                EstimationJobStatus.FAILED,
                error_message=str(exc),
            )
            return

        await self._job_store.update_status(
            job_id,
            EstimationJobStatus.SUCCEEDED,
            response=response,
        )


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_job_id() -> str:
    return uuid4().hex
