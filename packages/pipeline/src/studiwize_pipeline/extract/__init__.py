"""Text extraction — the first, hardest, most fragile pipeline stage.

Defines the provider boundary (`Extractor`) that decouples the rest of the pipeline
from any specific extraction library, and the concrete adapters behind it. Every
adapter takes a source file and returns a `Document` (see `..document`); nothing
downstream knows which engine produced it.

Engine choice is a *quality* decision settled by the Phase 0a spike
(`spikes/extraction_spike.py`): Docling primary, PyMuPDF fallback for text-layer
PDFs, dedicated EPUB path. These classes are stubs — the spike adapters hold the
working extraction logic and get promoted in here once 0a ratifies the choice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from studiwize_pipeline.document import Document

__all__ = [
    "Extractor",
    "ExtractionError",
    "DoclingExtractor",
    "PyMuPDFExtractor",
    "EpubExtractor",
    "select_extractor",
]


class ExtractionError(Exception):
    """Raised when a source file cannot be extracted (corrupt, unsupported,
    encrypted, or empty text layer). Callers decide whether to fall back to a
    different engine (e.g. Docling -> PyMuPDF) or surface a user-facing error."""


@runtime_checkable
class Extractor(Protocol):
    """The extraction provider boundary.

    Structural (Protocol) so adapters need not subclass — a class with a matching
    `extract` / `supports` is an `Extractor`. The worker layer depends only on this,
    never on docling/fitz/ebooklib directly.
    """

    name: str
    """Stable identifier recorded in Document.meta['engine'] (e.g. 'docling')."""

    def supports(self, path: Path) -> bool:
        """Whether this engine can handle the given file (by suffix / sniffing)."""
        ...

    def extract(self, path: Path) -> Document:
        """Extract `path` into a structured `Document`.

        Must populate chapters with `detected_via` set, and `meta['engine']`.
        Raises `ExtractionError` on unrecoverable failure.
        """
        ...


class _BaseExtractor:
    """Shared scaffolding for the concrete stubs (suffix-based `supports`)."""

    name: str = "base"
    suffixes: tuple[str, ...] = ()

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.suffixes

    def extract(self, path: Path) -> Document:  # pragma: no cover - stub
        raise NotImplementedError(
            f"{type(self).__name__}.extract is a Phase 1 stub. Promote the working "
            f"adapter from spikes/extraction_spike.py after the Phase 0a spike ratifies "
            f"the extractor choice."
        )


class DoclingExtractor(_BaseExtractor):
    """Primary: layout-aware structured extraction (Docling, MIT).

    Best on the hard case — multi-column, footnote-heavy academic PDFs — and emits
    document structure that feeds chapter detection. Handles both PDF and EPUB.
    Stub: see `spikes/extraction_spike.py::extract_docling`.
    """

    name = "docling"
    suffixes = (".pdf", ".epub")


class PyMuPDFExtractor(_BaseExtractor):
    """Fallback: fast text-layer PDF extraction (PyMuPDF/fitz, AGPL — server-side).

    Chapters via the PDF outline (ToC) when present, else a single whole-document
    chapter. Cheap first-pass / sanity check and the fallback when Docling fails or
    is overkill. Stub: see `spikes/extraction_spike.py::extract_pymupdf`.
    """

    name = "pymupdf"
    suffixes = (".pdf",)


class EpubExtractor(_BaseExtractor):
    """EPUB-native path (ebooklib + BeautifulSoup, AGPL — server-side).

    EPUB is the easy case: the spine + NCX/nav ToC give chapter structure for free.
    Stub: see `spikes/extraction_spike.py::extract_epub`.
    """

    name = "epub"
    suffixes = (".epub",)


# Dispatch order per file type. Docling is preferred; PyMuPDF/EpubExtractor are the
# format-specific fallbacks. The worker tries them in order until one supports +
# succeeds. Order/choice is provisional until Phase 0a ratifies it.
_DEFAULT_CHAIN: tuple[Extractor, ...] = (
    DoclingExtractor(),
    PyMuPDFExtractor(),
    EpubExtractor(),
)


def select_extractor(
    path: Path, chain: tuple[Extractor, ...] = _DEFAULT_CHAIN
) -> Extractor:
    """Return the first extractor in `chain` that supports `path`.

    Raises `ExtractionError` if no engine handles the file type. (Runtime fallback
    *between* supporting engines on failure is the worker's concern, not this
    selector's.)
    """
    for extractor in chain:
        if extractor.supports(path):
            return extractor
    raise ExtractionError(f"No extractor supports {path.suffix!r} (file: {path.name})")
