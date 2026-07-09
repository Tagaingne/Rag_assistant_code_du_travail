"""Custom exceptions for the Legifrance (PISTE) API client."""


class LegifranceAuthError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Authentification Legifrance echouee ({status_code}) : {detail}")


class LegifranceApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Appel API Legifrance echoue ({status_code}) : {detail}")
