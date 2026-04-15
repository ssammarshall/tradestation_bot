from __future__ import annotations

from app.schemas.bars import BarHistoryParams, BarsResponse
from app.broker.tradestation_client import TradeStationClient


class BarService:
    def __init__(self, client: TradeStationClient):
        self.client = client

    def get_bars(self, params: BarHistoryParams) -> BarsResponse:
        response = self.client.get(
            f"/marketdata/barcharts/{params.symbol}",
            params=params.to_query_params(),
            timeout=30,
        )
        return BarsResponse.from_dict(response.json())