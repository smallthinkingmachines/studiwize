from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CreateJobRequest(BaseModel):
    source_key: str
    chapter_index: int
    voice: str = "default"


class CreateJobResponse(BaseModel):
    job_id: str
    status_url: str


class JobResult(BaseModel):
    audio_key: str | None = None
    duration_seconds: float | None = None
    guide: dict | None = None


class Job(BaseModel):
    id: str
    status: JobStatus = JobStatus.PENDING
    source_key: str
    chapter_index: int
    voice: str = "default"
    result: JobResult | None = None
    error: str | None = None
