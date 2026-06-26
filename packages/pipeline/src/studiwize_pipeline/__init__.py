"""studiwize_pipeline — PDF/EPUB -> chapter-marked M4B audio + LLM study guide.

Web/db-free core library (open-core seam, D-006). See README.md.
"""

from studiwize_pipeline.document import Block, BlockType, Chapter, Document

__all__ = ["Document", "Chapter", "Block", "BlockType"]
