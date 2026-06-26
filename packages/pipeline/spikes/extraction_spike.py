#!/usr/bin/env python3
"""Phase 0a — extraction spike.

Run candidate extractors (Docling, PyMuPDF, ebooklib for EPUB) on real student files,
normalize each into our Document model, and emit a comparison so we can ratify the
extractor + chapter-detection strategy before building anything else.

This is a throwaway spike. The *numbers* it prints are a guide; the real verdict comes
from reading the extracted Markdown against the source PDFs (extraction fidelity on
multi-column / footnote-heavy academic PDFs is the standing top risk).

Usage:
    python spikes/extraction_spike.py spikes/samples/*.pdf spikes/samples/*.epub

Engines that aren't installed are skipped with a note (so you can start with just the
fast path and add Docling later).
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Make the library importable when run from the package root without installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from studiwize_pipeline.document import Block, BlockType, Chapter, Document  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "out" / "extraction"


@dataclass
class Result:
    engine: str
    file: str
    ok: bool
    seconds: float = 0.0
    doc: Document | None = None
    error: str | None = None


# --------------------------------------------------------------------------------------
# Engine adapters — each returns a Document or raises. Imports are lazy so a missing
# optional dependency only disables that one engine.
# --------------------------------------------------------------------------------------


def extract_pymupdf(path: Path) -> Document:
    """Fast text-layer extraction. Chapters via the PDF outline (ToC) if present,
    else a single whole-document chapter (the honest fallback — heuristic heading
    detection is deferred to the library, not this spike)."""
    import fitz  # PyMuPDF

    pdf = fitz.open(path)
    page_texts = [pdf[i].get_text("text") for i in range(pdf.page_count)]
    toc = pdf.get_toc(simple=True)  # [[level, title, page], ...]

    chapters: list[Chapter] = []
    if toc:
        # Use top-level (level 1) outline entries as chapter boundaries.
        tops = [(title, page) for level, title, page in toc if level == 1]
        for idx, (title, start_page) in enumerate(tops):
            end_page = tops[idx + 1][1] - 1 if idx + 1 < len(tops) else pdf.page_count
            blocks = [
                Block(type=BlockType.PARAGRAPH, text=page_texts[p - 1], page=p)
                for p in range(start_page, end_page + 1)
                if 1 <= p <= pdf.page_count and page_texts[p - 1].strip()
            ]
            chapters.append(
                Chapter(index=idx, title=title.strip(), blocks=blocks, detected_via="pdf_outline")
            )
    if not chapters:
        blocks = [
            Block(type=BlockType.PARAGRAPH, text=t, page=i + 1)
            for i, t in enumerate(page_texts)
            if t.strip()
        ]
        chapters = [
            Chapter(index=0, title=path.stem, blocks=blocks, detected_via="whole_document")
        ]

    return Document(
        title=path.stem,
        source_format="pdf",
        chapters=chapters,
        meta={"engine": "pymupdf", "pages": str(pdf.page_count), "had_toc": str(bool(toc))},
    )


def extract_docling(path: Path) -> Document:
    """Layout-aware structured extraction (primary candidate). Docling emits a
    document tree with headings/sections; we map heading items to chapter boundaries."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(path))
    dl = result.document

    chapters: list[Chapter] = []
    cur: Chapter | None = None
    idx = 0

    # Iterate the document's body items in reading order. Docling exposes text items
    # with a label (section_header, paragraph, list_item, table, caption, ...).
    for item, _level in dl.iterate_items():
        label = getattr(item, "label", "") or ""
        text = (getattr(item, "text", "") or "").strip()
        if not text:
            continue
        if "header" in label.lower() or "title" in label.lower():
            cur = Chapter(index=idx, title=text, detected_via="docling_structure")
            chapters.append(cur)
            idx += 1
            continue
        if cur is None:
            cur = Chapter(index=idx, title=path.stem, detected_via="docling_structure")
            chapters.append(cur)
            idx += 1
        btype = BlockType.PARAGRAPH
        ll = label.lower()
        if "list" in ll:
            btype = BlockType.LIST_ITEM
        elif "table" in ll:
            btype = BlockType.TABLE
        elif "caption" in ll:
            btype = BlockType.CAPTION
        elif "footnote" in ll:
            btype = BlockType.FOOTNOTE
        cur.blocks.append(Block(type=btype, text=text))

    if not chapters:
        chapters = [Chapter(index=0, title=path.stem, detected_via="whole_document")]

    return Document(
        title=getattr(dl, "name", None) or path.stem,
        source_format=path.suffix.lstrip(".").lower(),
        chapters=chapters,
        meta={"engine": "docling"},
    )


def extract_epub(path: Path) -> Document:
    """EPUB is the easy case — the spine + NCX/nav ToC gives chapter structure for free."""
    from bs4 import BeautifulSoup
    from ebooklib import ITEM_DOCUMENT, epub

    book = epub.read_epub(str(path))
    title_meta = book.get_metadata("DC", "title")
    title = title_meta[0][0] if title_meta else path.stem

    chapters: list[Chapter] = []
    for idx, item in enumerate(book.get_items_of_type(ITEM_DOCUMENT)):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        # Chapter title: first heading in the document, else the file name.
        heading = soup.find(["h1", "h2", "h3"])
        ch_title = heading.get_text(strip=True) if heading else f"Section {idx + 1}"
        blocks: list[Block] = []
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
            t = el.get_text(" ", strip=True)
            if not t:
                continue
            tag = el.name
            if tag.startswith("h"):
                blocks.append(Block(type=BlockType.HEADING, text=t, level=int(tag[1])))
            elif tag == "li":
                blocks.append(Block(type=BlockType.LIST_ITEM, text=t))
            elif tag == "blockquote":
                blocks.append(Block(type=BlockType.QUOTE, text=t))
            else:
                blocks.append(Block(type=BlockType.PARAGRAPH, text=t))
        if blocks:
            chapters.append(
                Chapter(index=len(chapters), title=ch_title, blocks=blocks, detected_via="epub_toc")
            )

    if not chapters:
        chapters = [Chapter(index=0, title=title, detected_via="whole_document")]

    return Document(
        title=title, source_format="epub", chapters=chapters, meta={"engine": "ebooklib"}
    )


def engines_for(path: Path) -> list[tuple[str, callable]]:
    """Which engines apply to this file type."""
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return [("ebooklib", extract_epub), ("docling", extract_docling)]
    if suffix == ".pdf":
        return [("pymupdf", extract_pymupdf), ("docling", extract_docling)]
    return []


def to_markdown(doc: Document) -> str:
    """Cheap Markdown rendering of the extracted Document for eyeballing fidelity."""
    lines = [f"# {doc.title}", "", f"_engine: {doc.meta.get('engine')}_", ""]
    for ch in doc.chapters:
        lines.append(f"## [{ch.index}] {ch.title}  _(via {ch.detected_via})_")
        lines.append("")
        for b in ch.blocks:
            prefix = {BlockType.HEADING: "### ", BlockType.LIST_ITEM: "- "}.get(b.type, "")
            lines.append(f"{prefix}{b.text}")
            lines.append("")
    return "\n".join(lines)


def run(paths: list[Path]) -> list[Result]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[Result] = []
    for path in paths:
        for engine_name, fn in engines_for(path):
            t0 = time.perf_counter()
            try:
                doc = fn(path)
                dt = time.perf_counter() - t0
                md = to_markdown(doc)
                out = OUT_DIR / f"{path.stem}__{engine_name}.md"
                out.write_text(md, encoding="utf-8")
                results.append(Result(engine_name, path.name, True, dt, doc))
            except ModuleNotFoundError as e:
                results.append(
                    Result(engine_name, path.name, False, error=f"not installed: {e.name}")
                )
            except Exception as e:  # noqa: BLE001 — spike: surface any failure, keep going
                results.append(Result(engine_name, path.name, False, error=f"{type(e).__name__}: {e}"))
    return results


def print_report(results: list[Result]) -> None:
    print("\n=== Phase 0a extraction spike ===\n")
    hdr = f"{'file':<28} {'engine':<10} {'ok':<4} {'secs':>6} {'chars':>9} {'chaps':>6} {'detected_via':<22}"
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        if r.ok and r.doc:
            via = r.doc.chapters[0].detected_via if r.doc.chapters else "-"
            print(
                f"{r.file:<28.28} {r.engine:<10} {'yes':<4} {r.seconds:>6.1f} "
                f"{r.doc.char_count:>9,} {r.doc.chapter_count:>6} {via:<22}"
            )
        else:
            print(f"{r.file:<28.28} {r.engine:<10} {'NO':<4} {'-':>6} {'-':>9} {'-':>6} {r.error or ''}")
    print(f"\nExtracted Markdown written to: {OUT_DIR}")
    print("NEXT: read the .md files against the source PDFs. The table is a guide;")
    print("      extraction fidelity is a human judgment. Record verdict in docs/adr/.\n")


def main() -> int:
    args = [Path(a) for a in sys.argv[1:]]
    paths = [p for p in args if p.exists() and p.suffix.lower() in (".pdf", ".epub")]
    if not paths:
        print(__doc__)
        print("ERROR: no .pdf/.epub files given. Drop samples in spikes/samples/ first.")
        return 1
    print_report(run(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
