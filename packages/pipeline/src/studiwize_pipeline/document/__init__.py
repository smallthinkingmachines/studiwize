"""The shared structured-document model.

Every extractor emits a `Document`; chunking, TTS, assembly, and study-guide
generation all consume it. This is the contract that decouples the (hard, fragile)
extraction step from the two downstream output paths (audio + study guide), which
both fork from the same `Document`.

Kept deliberately minimal and provider-agnostic: no PDF/EPUB-library types leak in,
no audio/HTTP/db concepts leak in.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    """Coarse semantic kind of a text block, used downstream for pacing and to
    decide what is spoken vs. skipped (e.g. tables/figures may be summarized or
    skipped in audio; headings get a spoken callout + a silence gap)."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    QUOTE = "quote"
    CAPTION = "caption"
    TABLE = "table"
    CODE = "code"
    FOOTNOTE = "footnote"
    OTHER = "other"


class Block(BaseModel):
    """An atomic unit of content within a chapter, in reading order."""

    type: BlockType = BlockType.PARAGRAPH
    text: str
    # Heading depth (1 = top-level). None for non-headings.
    level: int | None = None
    # Source page (1-indexed) when the extractor can attribute it; aids debugging
    # extraction quality and lets the UI deep-link to a page later.
    page: int | None = None


class Chapter(BaseModel):
    """A detected chapter/section. Drives both the audio chapter markers (M4B atoms)
    and the per-chapter study guide. Chapter detection quality is the load-bearing
    risk flagged in Phase 0a — bad boundaries here break the core differentiator."""

    index: int = Field(..., description="0-based order within the document")
    title: str
    blocks: list[Block] = Field(default_factory=list)
    # How this chapter boundary was determined — invaluable for the Phase 0a
    # extraction spike scoring ("did we get structure from the ToC or guess it?").
    detected_via: str | None = Field(
        default=None,
        description="e.g. 'epub_toc', 'pdf_outline', 'heuristic_heading', 'whole_document'",
    )

    @property
    def text(self) -> str:
        """Flattened plain text of the chapter (what TTS / the LLM ultimately see)."""
        return "\n\n".join(b.text for b in self.blocks if b.text.strip())

    @property
    def char_count(self) -> int:
        """Character count — the unit TTS cost and time-metering are based on
        (~600K chars ≈ a 300-page book ≈ ~11 hrs audio)."""
        return sum(len(b.text) for b in self.blocks)


class Document(BaseModel):
    """A fully extracted source document, ready for chunking/TTS/study-guide."""

    title: str
    source_format: str = Field(..., description="'pdf' | 'epub' | ...")
    chapters: list[Chapter] = Field(default_factory=list)
    # Free-form extractor metadata (engine name, version, page count, warnings).
    meta: dict[str, str] = Field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return sum(c.char_count for c in self.chapters)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    def estimated_audio_seconds(self, words_per_minute: float = 150.0) -> float:
        """Rough audio-length estimate (~6 chars/word incl. spaces). Used by the
        backend's time-meter to admit/reject a job *before* incurring TTS cost."""
        words = self.char_count / 6.0
        return (words / words_per_minute) * 60.0
