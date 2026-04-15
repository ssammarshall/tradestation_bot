import requests
from config.settings import Settings


class AuthService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def refresh_access_token(self) -> dict:
        url = f"{self.settings.auth_base_url}/oauth/token"

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "refresh_token": self.settings.refresh_token,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()