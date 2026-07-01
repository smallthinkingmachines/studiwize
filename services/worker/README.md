# studiwize_worker

Thin FastAPI wrapper around `packages/pipeline` (D-007). This is the only place
that adds HTTP/DB/job-orchestration concerns on top of the pure pipeline library —
the D-006 open-core seam stays intact because `packages/pipeline` never imports this
service.

The Node BullMQ layer (D-008) dispatches one HTTP call per chapter to this service
and polls/deletes by job ID. Job state here is **in-memory and per-chapter** — the
Node layer owns the durable `jobs`/`chapters` Postgres tables and treats this service
as a stateless-ish worker it can poll.

## Contract (D-007)

- `POST /jobs` — enqueue a pipeline run for one chapter; returns `202` + `{"job_id", "status_url"}`
- `GET /jobs/{id}` — poll status: `pending|running|done|failed`
- `DELETE /jobs/{id}` — cooperative cancel; worker checks the flag at chunk boundaries

## Dev

```bash
cd services/worker
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn studiwize_worker.main:app --reload --port 8000
```
