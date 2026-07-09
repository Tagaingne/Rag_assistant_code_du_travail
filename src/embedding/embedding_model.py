"""Wrapper around the sentence-transformers model used for embeddings."""

import numpy as np
from sentence_transformers import SentenceTransformer


E5_PREFIX_MARKER = "e5"


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._uses_e5_prefixes = E5_PREFIX_MARKER in model_name.lower()

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Encode indexable texts (articles/chunks) into normalized embeddings."""
        prefixed_texts = self._add_passage_prefix(texts) if self._uses_e5_prefixes else texts
        return self._encode(prefixed_texts)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single search query with the same model used for indexing."""
        prefixed_query = self._add_query_prefix(query) if self._uses_e5_prefixes else query
        return self._encode([prefixed_query])[0]

    def _encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def _add_passage_prefix(self, texts: list[str]) -> list[str]:
        return [f"passage: {text}" for text in texts]

    def _add_query_prefix(self, query: str) -> str:
        return f"query: {query}"
