# studiwize

BYO-content web app that turns PDF/EPUB files into chapter-marked audio + an LLM
study guide. "The full book, built for students."

Monorepo (D-007): TS apps in `apps/`, Python library + services in `packages/` and
`services/`. Same shape as the `~/dev/rasin` precedent — `uv` workspaces for Python,
`pnpm` workspaces for TS, `flake.nix` dev shell, `just` as the task runner.

## Layout

```
apps/
  landing/    marketing site — static HTML/CSS/JS, no build step (studiwize.com)
  web/        Next.js App Router — product UI + API routes (jobs, SSE)
packages/
  pipeline/   Python library: extract -> chunk -> TTS -> assemble -> study guide
              (open-core seam, D-006 — no HTTP/DB, publishable standalone)
services/
  worker/     thin FastAPI wrapper around packages/pipeline (D-007 job contract:
              POST /jobs, GET /jobs/{id}, DELETE /jobs/{id})
```

`apps/web`'s API routes are the only place BullMQ/Postgres/Redis will live (D-008);
`services/worker` is the only place that adds HTTP on top of the pipeline library.
Both are currently stubs — see each directory's README for status.

## Dev setup

```bash
nix develop        # or `direnv allow` — node_22 + python3 + uv
pnpm install        # apps/* workspace
uv sync --extra dev --package studiwize-worker   # packages/* + services/* workspace
```

## Common tasks

```bash
just web      # run apps/web (Next.js dev server)
just worker   # run services/worker (FastAPI, :8000)
just test     # pytest across packages/pipeline + services/worker
just lint     # ruff (Python) + tsc --noEmit (web)
```

For the landing page specifically (static, no build step), see `apps/landing/README.md`.
For Phase 0 de-risking spikes (extraction quality, Kokoro TTS quality — gate before
building out the pipeline further), see `packages/pipeline/spikes/README.md`.

## Deploy

`apps/landing` deploys independently via Dokploy (autoDeploy on push to `main`) — see
`apps/landing/AGENTS.md`. The product app (`apps/web` + `services/worker`) has no
deploy pipeline yet.
