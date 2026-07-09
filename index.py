"""Milestone 2 entry point: build and persist the vector store.

This script always (re)builds the collection from the corpus. It is meant to
be run once (or whenever the corpus changes) -- query.py never reindexes, it
only loads what this script persisted. See README, section "Jalon 2".
"""

from src.chunking.article_chunker import ArticleChunker
from src.config import COLLECTION_NAME, CORPUS_FILE, EMBEDDING_MODEL_NAME, VECTOR_STORE_DIR
from src.embedding.embedding_model import EmbeddingModel
from src.indexing.corpus_loader import CorpusLoader
from src.indexing.index_builder import IndexBuilder
from src.indexing.vector_store import VectorStore


def main() -> None:
    corpus_loader = CorpusLoader(CORPUS_FILE)
    article_chunker = ArticleChunker()
    embedding_model = EmbeddingModel(EMBEDDING_MODEL_NAME)
    vector_store = VectorStore(VECTOR_STORE_DIR, COLLECTION_NAME)

    index_builder = IndexBuilder(corpus_loader, article_chunker, embedding_model, vector_store)
    chunk_count = index_builder.build()

    print(f"Base vectorielle construite : {chunk_count} chunks indexes.")
    print(f"Modele d'embedding : {embedding_model.model_name}")
    print(f"Persistee dans : {VECTOR_STORE_DIR} (collection '{COLLECTION_NAME}')")


if __name__ == "__main__":
    main()
