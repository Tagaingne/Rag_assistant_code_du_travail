# main.py (a la racine)

import sys

from src.agent import MissingGroqApiKey
from src.config import VECTOR_STORE_DIR
from src.manager_agent import ManagerAgent, PromptInjectionDetected
from src.vector_db import VectorDB


AVERTISSEMENT = """
  Cet assistant ne fournit pas de conseil juridique.
    Consultez un avocat ou l'inspection du travail pour votre situation personnelle.
"""


def afficher_sources(documents, metadatas):
    print("\n Sources :")
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        article = meta.get("article", "Inconnu")
        theme = meta.get("theme", "")
        print(f"  [{i+1}] Article {article} — {theme}")


def main():
    print("=" * 60)
    print("  Assistant Code du travail français")
    print("=" * 60)
    print(AVERTISSEMENT)

    print(" Chargement de la base vectorielle...")
    try:
        vector_db = VectorDB(vector_db_path=VECTOR_STORE_DIR)
    except LookupError as e:
        print(f" Erreur chargement base vectorielle : {e}")
        print(" Lancez d'abord index.py.")
        sys.exit(1)

    try:
        manager = ManagerAgent(vector_db_object=vector_db)
    except MissingGroqApiKey as e:
        print(f" Erreur : {e}")
        sys.exit(1)

    print(" Assistant prêt ! Tapez 'quitter' pour arrêter.\n")

    while True:
        try:
            question = input(" Votre question : ").strip()

            if not question:
                continue

            if question.lower() in ["quitter", "exit", "quit", "q"]:
                print("Au revoir !")
                break

            print("\n Recherche en cours...")
            response, documents, metadatas = manager.ask(question)

            print(f"\n Réponse :\n{response}")
            afficher_sources(documents, metadatas)
            print(AVERTISSEMENT)
            print("-" * 60)

        except PromptInjectionDetected as e:
            print(f"\n Question refusée : {e.raison}")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\nAu revoir !")
            break

        except Exception as e:
            print(f"\n Erreur : {e}")
            print("-" * 60)


if __name__ == "__main__":
    main()
