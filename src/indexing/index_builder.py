"""Orchestrator that builds and persists the vector store from the corpus."""

from src.chunking.article_chunker import ArticleChunker
from src.chunking.chunk import Chunk
from src.embedding.embedding_model import EmbeddingModel
from src.indexing.corpus_loader import CorpusLoader
from src.indexing.vector_store import VectorStore


class IndexBuilder:
    def __init__(
        self,
        corpus_loader: CorpusLoader,
        article_chunker: ArticleChunker,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
    ):
        self.corpus_loader = corpus_loader
        self.article_chunker = article_chunker
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def build(self) -> int:
        """Chunk, embed, and persist the whole corpus. Returns the chunk count."""
        documents = self.corpus_loader.load_documents()
        chunks = self._chunk_documents(documents)

        self.vector_store.reset_collection(self._collection_metadata(documents))
        embeddings = self.embedding_model.encode_passages([chunk.embed_text for chunk in chunks])
        self.vector_store.add_chunks(chunks, embeddings)

        return len(chunks)

    def _chunk_documents(self, documents: list[dict]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(self.article_chunker.chunk_article(document))
        return chunks

    def _collection_metadata(self, documents: list[dict]) -> dict:
        return {
            "embedding_model": self.embedding_model.model_name,
            "corpus_date": self._latest_extraction_date(documents),
        }

    def _latest_extraction_date(self, documents: list[dict]) -> str:
        extraction_dates = [d.get("date_extraction", "") for d in documents if d.get("date_extraction")]
        return max(extraction_dates) if extraction_dates else ""
