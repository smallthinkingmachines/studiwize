# studiwize_pipeline

The core studiwize pipeline as a standalone, web/db-free library:

```
PDF / EPUB  ->  extract  ->  chunk  ->  TTS  ->  assemble (M4B)  ->  study guide
```

This package is the **open-core seam** (decision D-006): it knows nothing about HTTP,
Postgres, users, jobs, or entitlements. It takes file paths / byte streams and an
output location, and returns structured results. The hosted product's API/worker layer
(`apps/api`) imports and orchestrates it; the same code can later ship as an OSS CLI.

## Layout

```
src/studiwize_pipeline/
  document/    Document, Chapter, Block (Pydantic) — the shared structured model  ✓
  extract/     Extractor protocol; Docling/PyMuPDF/Epub adapters    (stubbed)
  chunk/       chapter/section/paragraph chunking strategies            (Phase 1)
  tts/         TTSProvider protocol; Kokoro + OpenAI adapters       (stubbed)
  assemble/    ffmpeg M4B writer (chapter atoms), silence-pacing        (Phase 1)
  studyguide/  StudyGuideProvider protocol; Haiku Batch                 (Phase 1)
  pipeline.py  orchestration (pure functions; fs/stream I/O only)       (Phase 1)
  cli.py       `studiwize book.pdf -o out.m4b`                          (Phase 1)

**Stubbed** = the provider boundary (Protocol) + concrete adapter classes exist and
are tested, but `extract()` / `synthesize()` raise `NotImplementedError`. The working
logic lives in the Phase 0 spikes and gets promoted into these adapters once the
spikes ratify the engine (0a -> extractor) and TTS provider (0b -> D-005).
spikes/        Phase 0 de-risking scripts (throwaway, run locally)
```

## Phase 0 — de-risking spikes (run these first)

Phase 0 is a gate: prove extraction quality on real academic PDFs and Kokoro
long-form audio quality **before** building the rest. See `spikes/README.md`.

## Dev setup

```
cd packages/pipeline
uv venv && source .venv/bin/activate
uv pip install -e ".[extract,tts,studyguide,dev]"   # or just the group a spike needs
```
