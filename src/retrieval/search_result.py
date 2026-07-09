"""Data structure returned by a similarity search."""

from dataclasses import dataclass


@dataclass
class SearchResult:
    chunk_id: str
    article: str
    theme: str
    title: str
    text: str
    distance: float
