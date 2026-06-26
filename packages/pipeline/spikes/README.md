# Phase 0 — de-risking spikes

These are **throwaway scripts**, not production code. They exist to answer the
go/no-go questions that gate the whole build (see the plan's Phase 0). Run them
locally, eyeball/listen to the output, record the verdict in `docs/adr/`, then
move on. Do not import these from the library.

## What you must supply

1. **Sample files** for 0a — drop 5 representative files in `spikes/samples/`:
   - a multi-column textbook chapter (PDF)
   - a footnote-heavy journal article (PDF)
   - an EPUB (the easy case — structured ToC comes free)
   - a slide-deck PDF
   - a formula-dense chapter (PDF)
   Use files you own. They are gitignored.

2. **A hosted-TTS API key** for 0b — either:
   - `REPLICATE_API_TOKEN`  (Replicate, ~$0.65/1M chars), or
   - `DEEPINFRA_API_KEY`    (DeepInfra, ~$0.80/1M chars)

## Setup

```
cd packages/pipeline
uv venv && source .venv/bin/activate
uv pip install -e ".[extract,tts]"
```

`docling` is a large install (pulls ML models on first run). If you only want the
fast path first, `uv pip install -e ".[tts]"` plus `uv pip install pymupdf ebooklib beautifulsoup4`.

## 0a — extraction spike

```
python spikes/extraction_spike.py spikes/samples/*.pdf spikes/samples/*.epub
```
Writes per-(file × engine) extracted Markdown to `spikes/out/extraction/` and prints
a comparison table: char count, chapter count, how chapters were detected, heading
count, and timing. **Then read the Markdown against the source PDFs** — the score
table is a guide; fidelity is a human judgment. Verdict expected: Docling primary,
PyMuPDF fallback.

## 0b — Kokoro long-form quality check

```
python spikes/kokoro_check.py spikes/out/extraction/<best-chapter>.md
# or feed raw text:  python spikes/kokoro_check.py --text-file chapter.txt
```
Synthesizes a full ~30-min chapter via hosted Kokoro to `spikes/out/audio/`.
**Then LISTEN end-to-end** for pronunciation drift, pacing, and artifacts. This is
the gate for ratifying D-005. If quality fails: fallback is Chatterbox (MIT) or a
restructured-pricing paid provider.

## 0c — chunking probe

`kokoro_check.py --probe` synthesizes the same passage chunked three ways
(sentence / paragraph / section) with assembly-time silence pacing, so you can
compare pacing quality and measure per-strategy parallelism/cost.
