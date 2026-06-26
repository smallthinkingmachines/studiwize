#!/usr/bin/env python3
"""Phase 0b — Kokoro long-form quality check  +  Phase 0c — chunking probe.

Synthesize a full ~30-min chapter via *hosted* Kokoro so we can LISTEN for
pronunciation drift, pacing, and artifacts before committing the cost model to it
(ratifies decision D-005). Also a `--probe` mode that synthesizes the same passage
chunked three ways (sentence / paragraph / section) with assembly-time silence
pacing, to settle the chunking strategy (0c).

Provider is auto-detected from the environment:
    REPLICATE_API_TOKEN  -> Replicate (model jaaari/kokoro-82m, auto-splits long text)
    DEEPINFRA_API_KEY    -> DeepInfra (POST /v1/inference/hexgrad/Kokoro-82M)

This is a throwaway spike. The verdict is your ears, not a metric.

Usage:
    python spikes/kokoro_check.py spikes/out/extraction/<chapter>.md
    python spikes/kokoro_check.py --text-file chapter.txt
    python spikes/kokoro_check.py --text-file chapter.txt --probe
    python spikes/kokoro_check.py --text-file chapter.txt --voice af_heart --max-chars 30000
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys
import time
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "out" / "audio"
DEFAULT_VOICE = "af_heart"  # a common Kokoro American-English preset; swap freely
SILENCE_AFTER_HEADING_MS = 800
SILENCE_BETWEEN_CHUNKS_MS = 350


# --------------------------------------------------------------------------------------
# Text loading
# --------------------------------------------------------------------------------------


def load_text(args: argparse.Namespace) -> str:
    if args.text_file:
        raw = Path(args.text_file).read_text(encoding="utf-8")
    elif args.source:
        raw = Path(args.source).read_text(encoding="utf-8")
        # If it's our spike Markdown, strip the heading/underscore scaffolding lightly.
        raw = re.sub(r"^_.*_$", "", raw, flags=re.MULTILINE)
    else:
        raise SystemExit("Provide a Markdown/text source path or --text-file.")
    text = raw.strip()
    if args.max_chars and len(text) > args.max_chars:
        text = text[: args.max_chars]
        print(f"(truncated to {args.max_chars:,} chars for the spike)")
    return text


# --------------------------------------------------------------------------------------
# Hosted Kokoro adapters — return raw audio bytes (wav). Written defensively because
# the exact response shape (url / base64 / binary) differs by provider and changes.
# --------------------------------------------------------------------------------------


def _fetch_url_bytes(url: str) -> bytes:
    import httpx

    return httpx.get(url, timeout=300).content


def synth_replicate(text: str, voice: str) -> bytes:
    import replicate

    # jaaari/kokoro-82m auto-splits long text, so a full chapter can go in one call.
    output = replicate.run(
        "jaaari/kokoro-82m",
        input={"text": text, "voice": voice},
    )
    # Output may be a URL string, a FileOutput, or a list thereof.
    if isinstance(output, list):
        output = output[0]
    if hasattr(output, "read"):  # replicate FileOutput
        return output.read()
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    if isinstance(output, str) and output.startswith("http"):
        return _fetch_url_bytes(output)
    raise RuntimeError(f"Unexpected Replicate output type: {type(output)!r}")


def synth_deepinfra(text: str, voice: str) -> bytes:
    import httpx

    key = os.environ["DEEPINFRA_API_KEY"]
    resp = httpx.post(
        "https://api.deepinfra.com/v1/inference/hexgrad/Kokoro-82M",
        headers={"Authorization": f"bearer {key}", "Content-Type": "application/json"},
        json={"text": text, "preset_voice": [voice]},
        timeout=600,
    )
    resp.raise_for_status()
    ctype = resp.headers.get("content-type", "")
    if ctype.startswith("audio/"):
        return resp.content
    data = resp.json()
    audio = data.get("audio")
    if not audio:
        raise RuntimeError(f"No audio in DeepInfra response: keys={list(data)}")
    if isinstance(audio, str) and audio.startswith("http"):
        return _fetch_url_bytes(audio)
    # data URI or bare base64
    if isinstance(audio, str):
        b64 = audio.split(",", 1)[1] if audio.startswith("data:") else audio
        return base64.b64decode(b64)
    raise RuntimeError(f"Unexpected DeepInfra audio field type: {type(audio)!r}")


def pick_provider() -> tuple[str, callable]:
    if os.environ.get("REPLICATE_API_TOKEN"):
        return "replicate", synth_replicate
    if os.environ.get("DEEPINFRA_API_KEY"):
        return "deepinfra", synth_deepinfra
    raise SystemExit(
        "No TTS key found. Set REPLICATE_API_TOKEN or DEEPINFRA_API_KEY.\n"
        "  Replicate: https://replicate.com/jaaari/kokoro-82m\n"
        "  DeepInfra: https://deepinfra.com/hexgrad/Kokoro-82M"
    )


# --------------------------------------------------------------------------------------
# Assembly-time silence pacing (the provider-independent alternative to SSML).
# --------------------------------------------------------------------------------------


def stitch_with_silence(segments: list[Path], gaps_ms: list[int], out: Path) -> None:
    """Concatenate audio segments inserting `gaps_ms[i]` of silence before segment i+1,
    using ffmpeg. Mirrors how the real assembly step will pace audio without SSML."""
    parts: list[str] = []
    filters: list[str] = []
    inputs: list[str] = []
    for i, seg in enumerate(segments):
        inputs += ["-i", str(seg)]
        parts.append(f"[{i}:a]")
        if i < len(segments) - 1 and i < len(gaps_ms) and gaps_ms[i] > 0:
            dur = gaps_ms[i] / 1000.0
            filters.append(
                f"aevalsrc=0:d={dur}:s=24000:cl=mono[sil{i}]"
            )
            parts.append(f"[sil{i}]")
    fc = (";".join(filters) + ";" if filters else "") + "".join(parts) + f"concat=n={len(parts)}:v=0:a=1[out]"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)


# --------------------------------------------------------------------------------------
# Chunking strategies (0c)
# --------------------------------------------------------------------------------------


def chunk_sentence(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_paragraph(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def chunk_section(text: str) -> list[str]:
    # Split on Markdown-ish headings; fall back to one section.
    parts = re.split(r"\n(?=#{1,4}\s)", text)
    return [p.strip() for p in parts if p.strip()] or [text]


# --------------------------------------------------------------------------------------
# Runs
# --------------------------------------------------------------------------------------


def run_longform(text: str, voice: str) -> None:
    provider, synth = pick_provider()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n=== Phase 0b — Kokoro long-form check ({provider}) ===")
    print(f"chars={len(text):,}  voice={voice}  est_audio≈{len(text)/6/150*60/60:.1f} min")
    t0 = time.perf_counter()
    audio = synth(text, voice)
    dt = time.perf_counter() - t0
    out = OUT_DIR / f"longform_{provider}_{voice}.wav"
    out.write_bytes(audio)
    print(f"synth wall-clock: {dt:.1f}s  ->  {out}  ({len(audio)/1e6:.1f} MB)")
    print("NEXT: LISTEN end-to-end for drift / pacing / artifacts. Verdict in docs/adr/.\n")


def run_probe(text: str, voice: str) -> None:
    provider, synth = pick_provider()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n=== Phase 0c — chunking probe ({provider}) ===")
    strategies = {
        "sentence": chunk_sentence,
        "paragraph": chunk_paragraph,
        "section": chunk_section,
    }
    for name, fn in strategies.items():
        chunks = fn(text)
        seg_dir = OUT_DIR / f"probe_{name}"
        seg_dir.mkdir(exist_ok=True)
        segs: list[Path] = []
        gaps: list[int] = []
        t0 = time.perf_counter()
        for i, ch in enumerate(chunks):
            seg = seg_dir / f"{i:04d}.wav"
            seg.write_bytes(synth(ch, voice))
            segs.append(seg)
            is_heading = ch.lstrip().startswith("#")
            gaps.append(SILENCE_AFTER_HEADING_MS if is_heading else SILENCE_BETWEEN_CHUNKS_MS)
        out = OUT_DIR / f"probe_{name}.wav"
        stitch_with_silence(segs, gaps, out)
        dt = time.perf_counter() - t0
        print(f"  {name:<10} chunks={len(chunks):>4}  {dt:>6.1f}s  -> {out}")
    print("\nNEXT: compare pacing across the three; note cost/parallelism tradeoff.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", help="Markdown/text file (e.g. a spike extraction output)")
    ap.add_argument("--text-file", help="Plain-text file to synthesize")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--max-chars", type=int, default=0, help="Cap chars (0 = no cap)")
    ap.add_argument("--probe", action="store_true", help="Run the 0c chunking probe instead")
    args = ap.parse_args()

    text = load_text(args)
    if args.probe:
        run_probe(text, args.voice)
    else:
        run_longform(text, args.voice)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
