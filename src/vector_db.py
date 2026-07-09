"""Adapter exposing the persisted vector store through a simple retrieve() call.

Bridges the generation agents (which only need question -> (documents, metadatas))
to the VectorStore/EmbeddingModel/Retriever built for indexing and evaluation,
so both sides of the pipeline share the same underlying search logic.
"""

from src.config import COLLECTION_NAME, DEFAULT_TOP_K, EMBEDDING_MODEL_NAME, VECTOR_STORE_DIR
from src.embedding.embedding_model import EmbeddingModel
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever
from src.retrieval.search_result import SearchResult


class VectorDB:
    def __init__(self, vector_db_path: str = VECTOR_STORE_DIR):
        embedding_model = EmbeddingModel(EMBEDDING_MODEL_NAME)
        vector_store = VectorStore(vector_db_path, COLLECTION_NAME)
        self._retriever = Retriever(vector_store, embedding_model)

    def retrieve(self, question: str, n: int = DEFAULT_TOP_K) -> tuple[list[str], list[dict]]:
        results = self._retriever.search(question, top_k=n)
        documents = [result.text for result in results]
        metadatas = [self._to_metadata_dict(result) for result in results]
        return documents, metadatas

    def _to_metadata_dict(self, result: SearchResult) -> dict:
        return {
            "article": result.article,
            "theme": result.theme,
            "title": result.title,
            "distance": result.distance,
        }
