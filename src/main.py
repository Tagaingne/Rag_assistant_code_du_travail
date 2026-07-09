# src/main.py

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manager_agent import ManagerAgent, PromptInjectionDetected
from vector_db import VectorDB
from config import VECTOR_DB_PATH

AVERTISSEMENT = """
  Cet assistant ne fournit pas de conseil juridique.
    Consultez un avocat ou l'inspection du travail pour votre situation personnelle.
"""

def afficher_sources(documents, metadatas):
    print("\n Sources :")
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        article = meta.get("article", "Inconnu")
        section = meta.get("section", "")
        print(f"  [{i+1}] Article {article} — {section}")

def main():
    print("=" * 60)
    print("  Assistant Code du travail français")
    print("=" * 60)
    print(AVERTISSEMENT)

    # Charger la base vectorielle
    print(" Chargement de la base vectorielle...")
    try:
        vector_db = VectorDB(vector_db_path=VECTOR_DB_PATH)
    except Exception as e:
        print(f" Erreur chargement base vectorielle : {e}")
        print(" Lancez d'abord le script d'indexation.")
        sys.exit(1)

    manager = ManagerAgent(vector_db_object=vector_db)
    print(" Assistant prêt ! Tapez 'quitter' pour arrêter.\n")

    # Boucle interactive
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