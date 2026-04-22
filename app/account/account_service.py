from __future__ import annotations

from typing import Optional

from app.schemas.accounts import (
    AccountsResponse,
    BalancesResponse,
    BODBalancesResponse,
    AccountOrdersResponse,
    PositionsResponse,
)
from app.schemas.orders import OrderRequest, OrderResponse, TradeAction
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

    def get_positions(self, account_id: str) -> PositionsResponse:
        response = self.client.get(f"/brokerage/accounts/{account_id}/positions")
        return PositionsResponse.from_dict(response.json())

    def close_all_positions(self, account_id: str) -> list[OrderResponse]:
        positions = self.get_positions(account_id).positions
        results = []
        for position in positions:
            if not position.symbol or not position.quantity:
                continue
            qty = float(position.quantity)
            if qty == 0:
                continue
            trade_action = (
                TradeAction.SELL if position.long_short == "Long" else TradeAction.BUY_TO_COVER
            )
            order = OrderRequest(
                account_id=account_id,
                symbol=position.symbol,
                quantity=position.quantity.lstrip("-"),
                trade_action=trade_action,
            )
            response = self.client.post(
                "/orderexecution/orders", json=order.to_dict(), timeout=30
            )
            results.append(OrderResponse.from_dict(response.json()))
        return results
