from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass(frozen=True)
class Settings:
    client_id: str = os.getenv("CLIENT_ID")
    client_secret: str = os.getenv("CLIENT_SECRET")
    refresh_token: str = os.getenv("REFRESH_TOKEN")
    redirect_uri: str = os.getenv("REDIRECT_URI", "http://localhost:3000")
    environment: str = os.getenv("TS_ENV", "sim")  # sim or live
    account_id: str = os.getenv("ACCOUNT_ID")
    sim_account_id: str = os.getenv("SIM_ACCOUNT_ID")


    @property
    def active_account_id(self) -> str:
        if self.environment == "live":
            return self.account_id
        return self.sim_account_id

    @property
    def api_base_url(self) -> str:
        if self.environment == "live":
            return "https://api.tradestation.com/v3"
        return "https://sim-api.tradestation.com/v3"

    @property
    def auth_base_url(self) -> str:
        return "https://signin.tradestation.com"