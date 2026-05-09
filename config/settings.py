from dataclasses import dataclass, field
from dotenv import load_dotenv
import os

load_dotenv()

def required_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' is required but not set.")
    return value

@dataclass(frozen=True)
class Settings:
    client_id: str = field(default_factory=lambda: required_env_var("CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: required_env_var("CLIENT_SECRET"))
    refresh_token: str = field(default_factory=lambda: required_env_var("REFRESH_TOKEN"))
    redirect_uri: str = field(default_factory=lambda: os.getenv("REDIRECT_URI", "http://localhost:3000"))
    environment: str = field(default_factory=lambda: os.getenv("TS_ENV", "sim"))  # sim or live
    account_id: str = field(default_factory=lambda: required_env_var("ACCOUNT_ID"))
    sim_account_id: str = field(default_factory=lambda: required_env_var("SIM_ACCOUNT_ID"))


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