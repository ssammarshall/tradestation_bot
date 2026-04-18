from __future__ import annotations

from typing import Optional

from app.schemas.accounts import (
    AccountsResponse,
    BalancesResponse,
    BODBalancesResponse,
    AccountOrdersResponse,
)
from app.broker.tradestation_client import TradeStationClient


class AccountService:
    def __init__(self, client: TradeStationClient):
        self.client = client

    def get_accounts(self) -> AccountsResponse:
        response = self.client.get("/brokerage/accounts")
        return AccountsResponse.from_dict(response.json())

    def get_balance(self, account_id: str) -> BalancesResponse:
        response = self.client.get(f"/brokerage/accounts/{account_id}/balances")
        return BalancesResponse.from_dict(response.json())

    def get_bod_balance(self, account_id: str) -> BODBalancesResponse:
        response = self.client.get(f"/brokerage/accounts/{account_id}/bodbalances")
        return BODBalancesResponse.from_dict(response.json())

    def get_orders(self, account_id: str) -> AccountOrdersResponse:
        response = self.client.get(f"/brokerage/accounts/{account_id}/orders")
        return AccountOrdersResponse.from_dict(response.json())

    def get_historical_orders(
        self, account_id: str, since: Optional[str] = None
    ) -> AccountOrdersResponse:
        params = {}
        if since is not None:
            params["since"] = since
        response = self.client.get(
            f"/brokerage/accounts/{account_id}/historicalorders",
            params=params,
        )
        return AccountOrdersResponse.from_dict(response.json())
