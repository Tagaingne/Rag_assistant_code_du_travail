"""Check whether the retriever surfaces the expected article for known questions."""

from src.config import DEFAULT_TOP_K
from src.retrieval.evaluation_result import EvaluationResult
from src.retrieval.retriever import Retriever
from src.retrieval.test_question import TestQuestion


class RetrievalEvaluator:
    def __init__(self, retriever: Retriever, top_k: int = DEFAULT_TOP_K):
        self.retriever = retriever
        self.top_k = top_k

    def evaluate(self, test_questions: list[TestQuestion]) -> list[EvaluationResult]:
        return [self._evaluate_one(test_question) for test_question in test_questions]

    def _evaluate_one(self, test_question: TestQuestion) -> EvaluationResult:
        results = self.retriever.search(test_question.question, self.top_k)
        found_articles = [result.article for result in results]
        success = test_question.expected_article in found_articles
        return EvaluationResult(test_question, found_articles, success)
