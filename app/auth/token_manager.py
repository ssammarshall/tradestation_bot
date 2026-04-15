from __future__ import annotations

from datetime import datetime, timedelta, UTC
from threading import Lock

from app.auth.auth_service import AuthService


class TokenManager:
    def __init__(self, auth_service: AuthService, refresh_buffer_seconds: int = 120):
        self.auth_service = auth_service
        self.refresh_buffer = timedelta(seconds=refresh_buffer_seconds)

        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._lock = Lock()

    def get_access_token(self) -> str:
        with self._lock:
            if self._should_refresh():
                self._refresh()
            return self._access_token

    def _should_refresh(self) -> bool:
        if not self._access_token or not self._expires_at:
            return True

        now = datetime.now(UTC)
        return now >= (self._expires_at - self.refresh_buffer)

    def _refresh(self) -> None:
        token_data = self.auth_service.refresh_access_token()

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 1200)  # default 20 min fallback

        if not access_token:
            raise RuntimeError("No access_token returned from TradeStation")

        self._access_token = access_token
        self._expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))