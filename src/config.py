"""Central configuration for the chunking, embedding, and indexing pipeline."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

CORPUS_FILE = Path("data/processed/corpus_legi_clean.json")

VECTOR_STORE_DIR = "data/vector_store"
COLLECTION_NAME = "code_travail"

# Doit rester identique sur toutes les branches de l'equipe (voir .env.example) :
# changer de modele sans reindexer casse la recherche.
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

ARTICLE_CHUNK_SIZE_THRESHOLD = 1500
CHUNK_OVERLAP_RATIO = 0.15

DEFAULT_TOP_K = 5
