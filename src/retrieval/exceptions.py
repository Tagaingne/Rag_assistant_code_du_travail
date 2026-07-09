"""Custom exceptions for the retrieval module."""


class EmbeddingModelMismatch(Exception):
    def __init__(self, index_model: str, query_model: str):
        self.index_model = index_model
        self.query_model = query_model
        message = (
            f"Le modele d'embedding utilise pour la recherche ({query_model}) "
            f"ne correspond pas a celui de l'index ({index_model})."
        )
        super().__init__(message)
