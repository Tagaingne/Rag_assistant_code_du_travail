"""Split legal articles into one or more indexable chunks.

Strategy (see README, Q1 - Granularite du chunking):
- One article = one chunk in the common case.
- Articles longer than a threshold are split into several chunks along
  sentence boundaries, with a small overlap, so no chunk is cut mid-sentence.

embed_text prefixes the theme (e.g. "Rupture conventionnelle. ...") because many
Code du travail articles share dense legal vocabulary (contrat de travail,
employeur, salarie...); the theme name gives the embedding model a topical
signal that the bare article text often lacks (validated on the jalon 3
retrieval questions).
"""

import re

from src.chunking.chunk import Chunk
from src.config import ARTICLE_CHUNK_SIZE_THRESHOLD, CHUNK_OVERLAP_RATIO


UPPERCASE_LETTERS = "A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ"
# Split only when the punctuation is followed by a capitalized word: this avoids
# cutting after legal reference abbreviations such as "L. 1233-63", which contain
# a period but are not sentence boundaries.
SENTENCE_BOUNDARY_PATTERN = re.compile(rf"(?<=[.!?])\s+(?=[{UPPERCASE_LETTERS}])")


class ArticleChunker:
    def __init__(
        self,
        max_chunk_size: int = ARTICLE_CHUNK_SIZE_THRESHOLD,
        overlap_ratio: float = CHUNK_OVERLAP_RATIO,
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio

    def chunk_article(self, document: dict) -> list[Chunk]:
        """Turn one article document into one or more Chunk objects."""
        text_parts = self._split_text(document["text"])
        return [
            self._build_chunk(document, text_part, index, len(text_parts))
            for index, text_part in enumerate(text_parts)
        ]

    def _split_text(self, text: str) -> list[str]:
        if not self._needs_splitting(text):
            return [text]
        return self._split_into_parts_with_overlap(text)

    def _needs_splitting(self, text: str) -> bool:
        return len(text) > self.max_chunk_size

    def _split_into_sentences(self, text: str) -> list[str]:
        return [s.strip() for s in SENTENCE_BOUNDARY_PATTERN.split(text) if s.strip()]

    def _split_into_parts_with_overlap(self, text: str) -> list[str]:
        sentences = self._split_into_sentences(text)
        parts: list[str] = []
        current_sentences: list[str] = []
        current_length = 0

        for sentence in sentences:
            exceeds_size = current_length + len(sentence) > self.max_chunk_size
            if exceeds_size and current_sentences:
                parts.append(" ".join(current_sentences))
                current_sentences = self._carry_overlap(current_sentences)
                current_length = sum(len(s) for s in current_sentences)

            current_sentences.append(sentence)
            current_length += len(sentence)

        if current_sentences:
            parts.append(" ".join(current_sentences))

        return parts

    def _carry_overlap(self, sentences: list[str]) -> list[str]:
        """Keep the trailing sentences of a part to open the next one with them."""
        overlap_budget = int(self.max_chunk_size * self.overlap_ratio)
        carried: list[str] = []
        carried_length = 0

        for sentence in reversed(sentences):
            if carried_length >= overlap_budget:
                break
            carried.insert(0, sentence)
            carried_length += len(sentence)

        return carried

    def _build_chunk(
        self,
        document: dict,
        text_part: str,
        index: int,
        total_parts: int,
    ) -> Chunk:
        chunk_id = document["id"] if total_parts == 1 else f"{document['id']}_part{index + 1}"
        return Chunk(
            id=chunk_id,
            text=text_part,
            embed_text=f"{document['theme']}. {text_part}",
            article=document["article"],
            theme=document["theme"],
            title=document["title"],
            source=document["source"],
            chunk_index=index,
            chunk_count=total_parts,
        )
