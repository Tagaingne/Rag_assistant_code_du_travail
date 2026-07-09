"""Persisted ChromaDB collection: the only place that talks to ChromaDB."""

import chromadb

from src.chunking.chunk import Chunk
from src.config import COLLECTION_NAME, VECTOR_STORE_DIR


class VectorStore:
    def __init__(
        self,
        persist_directory: str = VECTOR_STORE_DIR,
        collection_name: str = COLLECTION_NAME,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=persist_directory)

    def collection_exists(self) -> bool:
        existing_names = [c.name for c in self._client.list_collections()]
        return self.collection_name in existing_names

    def reset_collection(self, metadata: dict) -> None:
        """Drop any existing collection and create a fresh one (indexation only)."""
        if self.collection_exists():
            self._client.delete_collection(self.collection_name)
        self._client.create_collection(name=self.collection_name, metadata=metadata)

    def get_collection(self):
        """Load the existing collection without recreating or reindexing it."""
        if not self.collection_exists():
            raise LookupError(
                f"Collection '{self.collection_name}' introuvable dans {self.persist_directory}. "
                "Lancez d'abord index.py."
            )
        return self._client.get_collection(self.collection_name)

    def get_collection_metadata(self) -> dict:
        return self.get_collection().metadata or {}

    def count(self) -> int:
        return self.get_collection().count()

    def add_chunks(self, chunks: list[Chunk], embeddings) -> None:
        collection = self.get_collection()
        collection.add(
            ids=[chunk.id for chunk in chunks],
            embeddings=[embedding.tolist() for embedding in embeddings],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.to_metadata() for chunk in chunks],
        )

    def query(self, query_embedding, top_k: int) -> dict:
        collection = self.get_collection()
        return collection.query(query_embeddings=[query_embedding.tolist()], n_results=top_k)
