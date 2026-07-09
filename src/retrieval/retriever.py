"""Search the persisted vector store for the chunks most relevant to a query."""

from src.config import DEFAULT_TOP_K
from src.embedding.embedding_model import EmbeddingModel
from src.indexing.vector_store import VectorStore
from src.retrieval.exceptions import EmbeddingModelMismatch
from src.retrieval.search_result import SearchResult


class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self._check_embedding_model_matches_index()

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[SearchResult]:
        query_embedding = self.embedding_model.encode_query(query)
        raw_results = self.vector_store.query(query_embedding, top_k)
        return self._parse_results(raw_results)

    def _check_embedding_model_matches_index(self) -> None:
        index_model = self.vector_store.get_collection_metadata().get("embedding_model")
        if index_model and index_model != self.embedding_model.model_name:
            raise EmbeddingModelMismatch(index_model, self.embedding_model.model_name)

    def _parse_results(self, raw_results: dict) -> list[SearchResult]:
        ids = raw_results["ids"][0]
        documents = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0]
        distances = raw_results["distances"][0]

        return [
            self._build_search_result(ids[index], documents[index], metadatas[index], distances[index])
            for index in range(len(ids))
        ]

    def _build_search_result(
        self,
        chunk_id: str,
        text: str,
        metadata: dict,
        distance: float,
    ) -> SearchResult:
        return SearchResult(
            chunk_id=chunk_id,
            article=metadata["article"],
            theme=metadata["theme"],
            title=metadata["title"],
            text=text,
            distance=distance,
        )
