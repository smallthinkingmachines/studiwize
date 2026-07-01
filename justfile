# studiwize task runner (D-007)

default:
    @just --list

# === Development ===

# Run the Next.js app (UI + API routes)
web:
    cd apps/web && pnpm dev

# Run the FastAPI worker service
worker:
    uv run uvicorn studiwize_worker.main:app --reload --port 8000

# === Testing ===

test-worker:
    uv run pytest services/worker/tests -q

test-pipeline:
    uv run pytest packages/pipeline -q --no-header || [ $? -eq 5 ]

test: test-worker test-pipeline

# === Linting ===

lint-py:
    uv run ruff check packages/pipeline services/worker

lint-web:
    cd apps/web && npx tsc --noEmit

lint: lint-py lint-web
