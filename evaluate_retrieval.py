"""Milestone 3 entry point: validate retrieval alone, before any LLM call.

Loads the persisted vector store (built by index.py, never reindexes) and
checks that 5 known questions surface their expected article in the top-k
results. See README, section "Jalon 3".
"""

from src.config import COLLECTION_NAME, DEFAULT_TOP_K, EMBEDDING_MODEL_NAME, VECTOR_STORE_DIR
from src.embedding.embedding_model import EmbeddingModel
from src.indexing.vector_store import VectorStore
from src.retrieval.evaluation_result import EvaluationResult
from src.retrieval.retrieval_evaluator import RetrievalEvaluator
from src.retrieval.retriever import Retriever
from src.retrieval.test_question import TestQuestion


TEST_QUESTIONS = [
    TestQuestion("Qu'est-ce qu'une rupture conventionnelle du contrat de travail ?", "L1237-11"),
    TestQuestion("Qu'est-ce que le harcelement moral au travail ?", "L1152-1"),
    TestQuestion("Quel est le role du salaire minimum de croissance (SMIC) ?", "L3231-2"),
    TestQuestion("Quelle est la duree legale du travail par semaine ?", "L3121-27"),
    TestQuestion("Quelle est la periode de prise des conges payes ?", "L3141-13"),
]


def print_report(results: list[EvaluationResult]) -> None:
    success_count = sum(1 for result in results if result.success)

    for result in results:
        status = "OK" if result.success else "ECHEC"
        print(f"[{status}] {result.test_question.question}")
        print(f"  Article attendu : {result.test_question.expected_article}")
        print(f"  Articles trouves : {result.found_articles}")

    print(f"\nResultat : {success_count}/{len(results)} questions ont retrouve l'article attendu.")


def main() -> None:
    embedding_model = EmbeddingModel(EMBEDDING_MODEL_NAME)
    vector_store = VectorStore(VECTOR_STORE_DIR, COLLECTION_NAME)
    retriever = Retriever(vector_store, embedding_model)
    evaluator = RetrievalEvaluator(retriever, DEFAULT_TOP_K)

    results = evaluator.evaluate(TEST_QUESTIONS)
    print_report(results)


if __name__ == "__main__":
    main()
