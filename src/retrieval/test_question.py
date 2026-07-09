"""A retrieval test case: a question paired with the article it should surface."""

from dataclasses import dataclass


@dataclass
class TestQuestion:
    question: str
    expected_article: str
