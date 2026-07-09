"""Central configuration for the whole pipeline: indexing, retrieval, generation."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Optionnels : sans ces identifiants, la verification de fraicheur via
# l'API Legifrance (jalon 6, agent recuperateur de reference) est desactivee
# proprement plutot que de faire planter le pipeline.
LEGIFRANCE_CLIENT_ID = os.environ.get("LEGIFRANCE_CLIENT_ID")
LEGIFRANCE_CLIENT_SECRET = os.environ.get("LEGIFRANCE_CLIENT_SECRET")

CORPUS_FILE = Path("data/processed/corpus_legi_clean.json")

VECTOR_STORE_DIR = "data/vector_store"
COLLECTION_NAME = "code_travail"

# Doivent rester identiques sur toutes les branches de l'equipe (voir .env.example) :
# changer de modele sans reindexer/sans le repercuter partout casse le pipeline.
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
MODERATOR_MODEL = os.environ.get("MODERATOR_MODEL", "llama-3.1-8b-instant")

ARTICLE_CHUNK_SIZE_THRESHOLD = 1500
CHUNK_OVERLAP_RATIO = 0.15

DEFAULT_TOP_K = 5

# Apres decomposition (jalon 6), plusieurs sous-questions peuvent remonter des
# chunks en double : ce plafond evite de noyer le contexte envoye au LLM.
MAX_CONTEXT_CHUNKS = 8
