"""Outcome of evaluating one test question against the retriever."""

from dataclasses import dataclass

from src.retrieval.test_question import TestQuestion


@dataclass
class EvaluationResult:
    test_question: TestQuestion
    found_articles: list[str]
    success: bool
