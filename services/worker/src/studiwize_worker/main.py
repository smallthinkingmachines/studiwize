from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException

from studiwize_worker.models import (
    CreateJobRequest,
    CreateJobResponse,
    Job,
    JobStatus,
)
from studiwize_worker.store import job_store

app = FastAPI(title="studiwize-worker")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs", status_code=202)
def create_job(req: CreateJobRequest) -> CreateJobResponse:
    job_id = str(uuid.uuid4())
    job_store.create(
        Job(
            id=job_id,
            source_key=req.source_key,
            chapter_index=req.chapter_index,
            voice=req.voice,
        )
    )
    # Pipeline execution (extract -> chunk -> tts -> assemble -> studyguide) is
    # not wired up yet — packages/pipeline's extract/tts adapters are still
    # stubs pending the Phase 0 spike gate. This endpoint currently only
    # registers the job; running it is the next step once the pipeline is
    # promoted out of spike code.
    return CreateJobResponse(job_id=job_id, status_url=f"/jobs/{job_id}")


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> Job:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.delete("/jobs/{job_id}")
def cancel_job(job_id: str) -> Job:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED):
        return job
    job.status = JobStatus.CANCELLED
    return job_store.update(job)
