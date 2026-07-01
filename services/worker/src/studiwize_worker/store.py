from __future__ import annotations

import threading

from studiwize_worker.models import Job


class JobStore:
    """In-memory job registry.

    The Node BullMQ layer owns the durable jobs/chapters tables (D-008); this
    store only tracks in-flight work for this process. Not shared across
    worker replicas — fine while the service dispatches one chapter per call
    and the caller polls the same instance.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def delete(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.pop(job_id, None)


job_store = JobStore()
