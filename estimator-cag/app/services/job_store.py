import asyncio

from app.application.estimation_jobs import next_job_id, timestamp_utc
from app.schemas import EstimationJob, EstimationJobStatus, EstimationRequest, EstimationResponse


class InMemoryEstimationJobStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._jobs: dict[str, EstimationJob] = {}

    async def create(self, request: EstimationRequest, prompt_version: str) -> EstimationJob:
        async with self._lock:
            now = timestamp_utc()
            job = EstimationJob(
                id=next_job_id(),
                status=EstimationJobStatus.PENDING,
                created_at=now,
                updated_at=now,
                request=request,
                prompt_version=prompt_version,
            )
            self._jobs[job.id] = job
            return job

    async def get(self, job_id: str) -> EstimationJob | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            return job.model_copy(deep=True) if job else None

    async def list(self) -> list[EstimationJob]:
        async with self._lock:
            jobs = sorted(
                self._jobs.values(),
                key=lambda job: job.created_at,
                reverse=True,
            )
            return [job.model_copy(deep=True) for job in jobs]

    async def update_status(
        self,
        job_id: str,
        status: EstimationJobStatus,
        *,
        response: EstimationResponse | None = None,
        error_message: str | None = None,
    ) -> EstimationJob | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            updated_job = job.model_copy(
                update={
                    "status": status,
                    "updated_at": timestamp_utc(),
                    "response": response,
                    "error_message": error_message,
                }
            )
            self._jobs[job_id] = updated_job
            return updated_job.model_copy(deep=True)
