# fastapi_app.py
#
# Interface web (API + page de chat), en plus de la CLI (main.py) et de
# Streamlit (streamlit_app.py). Reutilise les memes classes (ManagerAgent,
# VectorDB) : aucune logique metier dupliquee, seul le transport change.

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.agent import MissingGroqApiKey
from src.config import VECTOR_STORE_DIR
from src.freshness_label import format_freshness_label
from src.manager_agent import ManagerAgent, PromptInjectionDetected
from src.vector_db import VectorDB


STATIC_DIR = Path(__file__).resolve().parent / "static"

AVERTISSEMENT = (
    "Cet assistant ne fournit pas de conseil juridique. "
    "Consultez un avocat ou l'inspection du travail pour votre situation personnelle."
)

MESSAGE_ERREUR_GENERIQUE = (
    "Une erreur est survenue pendant le traitement de votre question "
    "(service indisponible ou quota dépassé). Réessayez dans quelques instants."
)


class QuestionRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    article: str
    theme: str
    fraicheur: str = ""


class AnswerResponse(BaseModel):
    response: str
    sources: list[SourceResponse]
    avertissement: str
    refuse: bool = False
    erreur: bool = False


def build_manager() -> ManagerAgent:
    vector_db = VectorDB(vector_db_path=VECTOR_STORE_DIR)
    return ManagerAgent(vector_db_object=vector_db)


try:
    manager = build_manager()
except MissingGroqApiKey as e:
    raise SystemExit(f"Erreur : {e}")
except LookupError as e:
    raise SystemExit(f"Erreur chargement base vectorielle : {e}. Lancez d'abord index.py.")


app = FastAPI(title="Assistant Code du travail")


@app.get("/", response_class=HTMLResponse)
def serve_chat_page() -> str:
    return (STATIC_DIR / "chat.html").read_text(encoding="utf-8")


@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QuestionRequest) -> AnswerResponse:
    try:
        response, _, metadatas = manager.ask(payload.question)
        sources = [
            SourceResponse(
                article=meta.get("article", "Inconnu"),
                theme=meta.get("theme", ""),
                fraicheur=format_freshness_label(meta),
            )
            for meta in metadatas
        ]
        return AnswerResponse(response=response, sources=sources, avertissement=AVERTISSEMENT)
    except PromptInjectionDetected as e:
        return AnswerResponse(
            response=f"Question refusée : {e.raison}",
            sources=[],
            avertissement=AVERTISSEMENT,
            refuse=True,
        )
    except Exception:
        return AnswerResponse(
            response=MESSAGE_ERREUR_GENERIQUE,
            sources=[],
            avertissement=AVERTISSEMENT,
            erreur=True,
        )
