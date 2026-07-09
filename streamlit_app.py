# streamlit_app.py
#
# Interface web de l'assistant, en plus de la boucle CLI (main.py).
# Reutilise les memes classes (ManagerAgent, VectorDB) : aucune logique
# metier dupliquee, seul l'affichage change.

import streamlit as st

from src.agent import MissingGroqApiKey
from src.config import VECTOR_STORE_DIR
from src.freshness_label import format_freshness_label
from src.manager_agent import ManagerAgent, PromptInjectionDetected
from src.vector_db import VectorDB


AVERTISSEMENT = (
    "Cet assistant ne fournit pas de conseil juridique. "
    "Consultez un avocat ou l'inspection du travail pour votre situation personnelle."
)

MESSAGE_ERREUR_GENERIQUE = (
    "Une erreur est survenue pendant le traitement de votre question "
    "(service indisponible ou quota dépassé). Réessayez dans quelques instants."
)


@st.cache_resource(show_spinner="Chargement de la base vectorielle...")
def load_manager() -> ManagerAgent:
    vector_db = VectorDB(vector_db_path=VECTOR_STORE_DIR)
    return ManagerAgent(vector_db_object=vector_db)


def init_history() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []


def render_sources(metadatas: list[dict]) -> None:
    if not metadatas:
        return
    st.markdown("**Sources :**")
    for i, meta in enumerate(metadatas, start=1):
        article = meta.get("article", "Inconnu")
        theme = meta.get("theme", "")
        ligne = f"{i}. Article **{article}** — {theme}"
        fraicheur = format_freshness_label(meta)
        if fraicheur:
            ligne += f" _({fraicheur})_"
        st.markdown(ligne)


def render_history() -> None:
    for entry in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            if entry.get("erreur"):
                st.warning(entry["response"])
            else:
                st.markdown(entry["response"])
            render_sources(entry["metadatas"])
            st.caption(AVERTISSEMENT)


def ask_question(manager: ManagerAgent, question: str) -> dict:
    try:
        response, _, metadatas = manager.ask(question)
        return {"question": question, "response": response, "metadatas": metadatas}
    except PromptInjectionDetected as e:
        return {
            "question": question,
            "response": f"Question refusée : {e.raison}",
            "metadatas": [],
        }
    except Exception:
        return {
            "question": question,
            "response": MESSAGE_ERREUR_GENERIQUE,
            "metadatas": [],
            "erreur": True,
        }


def load_manager_or_stop() -> ManagerAgent:
    try:
        return load_manager()
    except MissingGroqApiKey as e:
        st.error(str(e))
        st.stop()
    except LookupError as e:
        st.error(f"Base vectorielle introuvable : {e}. Lancez d'abord `python index.py`.")
        st.stop()


def main() -> None:
    st.set_page_config(page_title="Assistant Code du travail", page_icon="⚖️")
    st.title("Assistant Code du travail")
    st.caption(AVERTISSEMENT)

    init_history()
    manager = load_manager_or_stop()
    render_history()

    question = st.chat_input("Posez votre question sur le Code du travail...")
    if question:
        with st.spinner("Recherche en cours..."):
            entry = ask_question(manager, question)
        st.session_state.history.append(entry)
        st.rerun()


if __name__ == "__main__":
    main()
