"""Text-to-speech — the provider boundary that makes the business model possible.

The cost spread across TTS providers is ~400x (ElevenLabs $30-180/book vs. hosted
Kokoro ~$0.40-0.50/book), so the single most valuable property here is *swappability*:
the rest of the pipeline depends only on `TTSProvider` (text chunk in -> audio segment
out) and never on a specific vendor SDK. Provider choice is an *economics* decision,
settled for MVP by D-005: hosted Kokoro default, OpenAI adapter behind the same
interface for A/B and a premium voice tier, self-hosted Kokoro as the at-scale endgame.

These classes are stubs — the working hosted-Kokoro synthesis logic lives in
`spikes/kokoro_check.py` and gets promoted in here once the Phase 0b long-form quality
check ratifies D-005.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = [
    "TTSProvider",
    "TTSError",
    "Voice",
    "AudioSegment",
    "KokoroReplicate",
    "KokoroDeepInfra",
    "OpenAITTS",
]


class TTSError(Exception):
    """Raised when synthesis fails (provider error, auth, rate limit, bad input).
    The worker retries per-chunk and may fall back to another provider behind the
    same interface."""


@dataclass(frozen=True)
class Voice:
    """A selectable narration voice. `id` is the provider-native preset name
    (e.g. Kokoro 'af_heart'); `label` is user-facing. Voices are provider-scoped —
    the entitlement layer decides which are offered per tier (premium voices gated)."""

    id: str
    label: str
    language: str = "en-US"
    premium: bool = False


@dataclass
class AudioSegment:
    """The output unit: synthesized audio for one input chunk, plus what the
    assembly step needs to stitch + pace it (silence insertion) and bill it."""

    audio: bytes
    sample_rate: int
    # Container/codec of `audio` as returned by the provider (e.g. 'wav', 'mp3').
    audio_format: str = "wav"
    # Measured duration when the provider reports it; assembly can also probe via
    # ffmpeg. Drives chapter-marker timing and the *actual* (vs estimated) time-meter.
    duration_seconds: float | None = None
    # Characters synthesized — the unit cost is computed against.
    char_count: int = 0
    meta: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class TTSProvider(Protocol):
    """The TTS provider boundary: text chunk in -> audio segment out.

    Structural (Protocol) so adapters need not subclass. Deliberately granular
    (per-chunk) so the worker can fan out chunk synthesis in parallel, retry a single
    failed chunk without redoing the rest, and report `completed/total` progress.
    """

    name: str
    """Stable identifier recorded in artifact metadata (e.g. 'kokoro-replicate')."""

    cost_per_million_chars: float
    """USD per 1M input characters at the hosted rate — the load-bearing number for
    the cost model and server-side time-metering. (Kokoro ~0.65-0.80; OpenAI ~15.)"""

    def voices(self) -> list[Voice]:
        """Voices this provider offers (for UI selection + entitlement gating)."""
        ...

    def synthesize(self, text: str, voice: Voice) -> AudioSegment:
        """Synthesize one text chunk into an `AudioSegment`.

        Raises `TTSError` on failure. Implementations should be safe to call
        concurrently across chunks.
        """
        ...

    def estimate_cost(self, char_count: int) -> float:
        """USD estimate for synthesizing `char_count` characters at this provider's
        rate. Used to admit/reject a job against the free-tier meter *before* spend."""
        ...


class _BaseTTSProvider:
    """Shared scaffolding: a default cost model and a NotImplementedError stub."""

    name: str = "base"
    cost_per_million_chars: float = 0.0
    _voices: tuple[Voice, ...] = ()

    def voices(self) -> list[Voice]:
        return list(self._voices)

    def estimate_cost(self, char_count: int) -> float:
        return (char_count / 1_000_000) * self.cost_per_million_chars

    def synthesize(self, text: str, voice: Voice) -> AudioSegment:  # pragma: no cover - stub
        raise NotImplementedError(
            f"{type(self).__name__}.synthesize is a Phase 1 stub. Promote the working "
            f"hosted-Kokoro adapter from spikes/kokoro_check.py after the Phase 0b "
            f"long-form quality check ratifies D-005."
        )


# A small default voice set; real presets are confirmed during 0b. Kept identical
# across Kokoro adapters since they wrap the same model.
_KOKORO_VOICES: tuple[Voice, ...] = (
    Voice(id="af_heart", label="Heart (US, warm)"),
    Voice(id="af_bella", label="Bella (US)"),
    Voice(id="am_adam", label="Adam (US, male)"),
    Voice(id="bf_emma", label="Emma (UK)"),
)


class KokoroReplicate(_BaseTTSProvider):
    """MVP default path A: Kokoro-82M (Apache 2.0) via Replicate (~$0.65/1M chars).

    Replicate's jaaari/kokoro-82m auto-splits long text, so a full chapter can go in
    one call. Stub: see `spikes/kokoro_check.py::synth_replicate`.
    """

    name = "kokoro-replicate"
    cost_per_million_chars = 0.65
    _voices = _KOKORO_VOICES


class KokoroDeepInfra(_BaseTTSProvider):
    """MVP default path B: Kokoro-82M via DeepInfra (~$0.80/1M chars).

    POST /v1/inference/hexgrad/Kokoro-82M. Interchangeable with the Replicate path;
    keep both so a provider outage doesn't stop synthesis. Stub: see
    `spikes/kokoro_check.py::synth_deepinfra`.
    """

    name = "kokoro-deepinfra"
    cost_per_million_chars = 0.80
    _voices = _KOKORO_VOICES


class OpenAITTS(_BaseTTSProvider):
    """A/B + premium-voice path: OpenAI gpt-4o-mini-tts (~$15/1M chars).

    ~20x the Kokoro cost — NOT viable as the default full-book path (breaks freemium
    economics), kept behind the same interface for quality A/B and a possible premium
    tier. The ~400x cost spread vs ElevenLabs is exactly why this boundary exists.
    """

    name = "openai-tts"
    cost_per_million_chars = 15.0
    _voices = (
        Voice(id="alloy", label="Alloy", premium=True),
        Voice(id="nova", label="Nova", premium=True),
        Voice(id="shimmer", label="Shimmer", premium=True),
    )
