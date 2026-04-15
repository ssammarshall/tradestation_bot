from config.settings import Settings
from app.auth.auth_service import AuthService
from app.auth.token_manager import TokenManager
from app.auth.auth_session import AuthenticatedSession


class TradeStationClient:
    def __init__(self, settings: Settings):
        self.settings = settings

        auth_service = AuthService(settings)
        token_manager = TokenManager(auth_service)
        self.http = AuthenticatedSession(token_manager)
    
    def get(self, path: str, **kwargs):
        url = f"{self.settings.api_base_url}{path}"
        return self.http.request("GET", url, **kwargs)