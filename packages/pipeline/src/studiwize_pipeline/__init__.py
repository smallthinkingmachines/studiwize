"""studiwize_pipeline — PDF/EPUB -> chapter-marked M4B audio + LLM study guide.

Web/db-free core library (open-core seam, D-006). See README.md.
"""

from studiwize_pipeline.document import Block, BlockType, Chapter, Document
from studiwize_pipeline.extract import (
    Extractor,
    ExtractionError,
    select_extractor,
)
from studiwize_pipeline.tts import (
    AudioSegment,
    TTSError,
    TTSProvider,
    Voice,
)

__all__ = [
    # document model
    "Document",
    "Chapter",
    "Block",
    "BlockType",
    # extraction boundary
    "Extractor",
    "ExtractionError",
    "select_extractor",
    # tts boundary
    "TTSProvider",
    "TTSError",
    "Voice",
    "AudioSegment",
]
