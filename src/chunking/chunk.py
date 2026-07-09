"""Data structure representing one indexable unit of text."""

from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    text: str
    embed_text: str
    article: str
    theme: str
    title: str
    source: str
    legi_id: str
    chunk_index: int
    chunk_count: int

    def to_metadata(self) -> dict:
        """Return the chunk fields ChromaDB can store as metadata (no text)."""
        return {
            "article": self.article,
            "theme": self.theme,
            "title": self.title,
            "source": self.source,
            "legi_id": self.legi_id,
            "chunk_index": self.chunk_index,
            "chunk_count": self.chunk_count,
        }
