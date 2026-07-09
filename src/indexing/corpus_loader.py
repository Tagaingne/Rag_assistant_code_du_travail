"""Load the clean corpus produced by milestone 1."""

import json
from pathlib import Path

from src.config import CORPUS_FILE


class CorpusLoader:
    def __init__(self, corpus_path: Path = CORPUS_FILE):
        self.corpus_path = corpus_path

    def load_documents(self) -> list[dict]:
        if not self.corpus_path.exists():
            raise FileNotFoundError(
                f"Corpus introuvable: {self.corpus_path}. "
                "Lancez d'abord le pipeline du jalon 1 (src/data/extract_legi_corpus.py)."
            )

        with self.corpus_path.open(encoding="utf-8") as file:
            return json.load(file)
