# src/reference_retriever_agent.py
#
# "Agent recuperateur de reference" du schema d'architecture de l'equipe :
# pour chaque article cite dans la reponse, va verifier sur l'API Legifrance
# si le texte stocke localement (jalon 1) est toujours a jour.

from src.legifrance.exceptions import LegifranceApiError, LegifranceAuthError
from src.legifrance.legifrance_client import LegifranceClient


class ReferenceRetrieverAgent:
    def __init__(self, legifrance_client: LegifranceClient):
        self.legifrance_client = legifrance_client

    def check_freshness(self, documents: list[str], metadatas: list[dict]) -> list[dict]:
        return [self._check_one(doc, meta) for doc, meta in zip(documents, metadatas)]

    def _check_one(self, document: str, metadata: dict) -> dict:
        enriched = dict(metadata)
        legi_id = metadata.get("legi_id")

        if not legi_id:
            enriched["fraicheur"] = "non_verifiable"
            return enriched

        try:
            live_article = self.legifrance_client.get_article(legi_id)
        except (LegifranceApiError, LegifranceAuthError):
            enriched["fraicheur"] = "verification_indisponible"
            return enriched

        enriched["etat_legifrance"] = live_article["etat"]
        enriched["fraicheur"] = self._compare(document, live_article)
        return enriched

    def _compare(self, stored_text: str, live_article: dict) -> str:
        if live_article["etat"] != "VIGUEUR":
            return "obsolete"
        if live_article["texte"].strip() != stored_text.strip():
            return "modifie"
        return "a_jour"
