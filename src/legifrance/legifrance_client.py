"""Thin client for the Legifrance (PISTE) article lookup endpoint."""

import requests

from src.legifrance.exceptions import LegifranceApiError
from src.legifrance.oauth_client import LegifranceOAuthClient


API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"


class LegifranceClient:
    def __init__(self, oauth_client: LegifranceOAuthClient):
        self.oauth_client = oauth_client

    def get_article(self, legi_id: str) -> dict:
        try:
            response = requests.post(
                f"{API_BASE_URL}/consult/getArticle",
                headers=self._auth_headers(),
                json={"id": legi_id},
                timeout=15,
            )
        except requests.exceptions.RequestException as e:
            raise LegifranceApiError(0, str(e)) from e

        if response.status_code != 200:
            raise LegifranceApiError(response.status_code, response.text)

        return self._parse_article(response.json())

    def _auth_headers(self) -> dict:
        token = self.oauth_client.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _parse_article(self, payload: dict) -> dict:
        article = payload["article"]
        return {
            "legi_id": article["id"],
            "num": article.get("num"),
            "texte": article.get("texte", ""),
            "etat": article.get("etat"),
        }
