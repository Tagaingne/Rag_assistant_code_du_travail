

from dotenv import load_dotenv
import os

load_dotenv()

try:
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]
except KeyError:
    raise Exception("La variable GROQ_API_KEY est absente du fichier .env")

# Modèles
LLM_MODEL = "llama-3.3-70b-versatile"
# EMBEDDING_MODEL = "distiluse-base-multilingual-cased-v2"
# EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
MODERATOR_MODEL = "llama-3.1-8b-instant"

# Base vectorielle
VECTOR_DB_PATH = "vector_db"

# Nombre de chunks à récupérer
TOP_K = 5