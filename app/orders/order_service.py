from __future__ import annotations

import json

from app.schemas.orders import (
    OrderRequest,
    OrderResponse,
    BracketOrderRequest,
    GroupOrderResponse,
    OrderStatusParams,
    StreamOrderEvent,
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

    def stream_orders(self, params: OrderStatusParams):
        response = self.client.get(
            f"/brokerage/stream/accounts/{params.account_id}/orders",
            stream=True,
            timeout=60,
        )

        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                yield StreamOrderEvent.from_dict(payload)
        finally:
            response.close()
