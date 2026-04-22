import requests
from config.settings import Settings

settings = Settings()

print(
    "Open this URL in your browser:\n"
    f"{settings.auth_base_url}/authorize"
    f"?response_type=code"
    f"&client_id={settings.client_id}"
    f"&audience=https%3A%2F%2Fapi.tradestation.com"
    f"&redirect_uri={settings.redirect_uri.replace(':', '%3A').replace('/', '%2F')}"
    f"&scope=openid%20offline_access%20profile%20MarketData%20ReadAccount%20Trade"
)

try:
    code = input("Paste returned code: ").strip()

    response = requests.post(
        f"{settings.auth_base_url}/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "code": code,
            "redirect_uri": settings.redirect_uri,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    print("\nSave this REFRESH_TOKEN in your .env:\n")
    print(data["refresh_token"])
except KeyboardInterrupt:
    print("\nShutting down.")