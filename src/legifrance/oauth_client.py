"""OAuth2 client_credentials token management for the PISTE / Legifrance API."""

import time

import requests

from src.legifrance.exceptions import LegifranceAuthError


TOKEN_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
TOKEN_EXPIRY_MARGIN_SECONDS = 60


class LegifranceOAuthClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        self._expires_at = 0.0

    def get_access_token(self) -> str:
        if self._is_token_expired():
            self._fetch_new_token()
        return self._access_token

    def _is_token_expired(self) -> bool:
        return time.time() >= self._expires_at

    def _fetch_new_token(self) -> None:
        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "openid",
                },
                timeout=15,
            )
        except requests.exceptions.RequestException as e:
            raise LegifranceAuthError(0, str(e)) from e

        if response.status_code != 200:
            raise LegifranceAuthError(response.status_code, response.text)

        payload = response.json()
        self._access_token = payload["access_token"]
        self._expires_at = time.time() + payload["expires_in"] - TOKEN_EXPIRY_MARGIN_SECONDS
