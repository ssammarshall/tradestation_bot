import requests
from app.auth.token_manager import TokenManager


class AuthenticatedSession:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.session = requests.Session()

    def request(self, method: str, url: str, **kwargs):
        token = self.token_manager.get_access_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        response = self.session.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            self.token_manager._refresh()
            fresh_token = self.token_manager.get_access_token()
            headers["Authorization"] = f"Bearer {fresh_token}"
            response = self.session.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()
        return response

    def close(self):
        self.session.close()