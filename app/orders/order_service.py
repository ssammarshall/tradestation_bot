from __future__ import annotations

from app.schemas.orders import (
    OrderRequest,
    OrderResponse,
    BracketOrderRequest,
    GroupOrderResponse,
)
from app.broker.tradestation_client import TradeStationClient


class OrderService:
    def __init__(self, client: TradeStationClient):
        self.client = client

    def place_order(self, order: OrderRequest) -> OrderResponse:
        response = self.client.post(
            "/orderexecution/orders",
            json=order.to_dict(),
            timeout=30,
        )
        return OrderResponse.from_dict(response.json())

    def place_bracket_order(self, bracket: BracketOrderRequest) -> GroupOrderResponse:
        response = self.client.post(
            "/orderexecution/ordergroups",
            json=bracket.to_dict(),
            timeout=30,
        )
        return GroupOrderResponse.from_dict(response.json())
