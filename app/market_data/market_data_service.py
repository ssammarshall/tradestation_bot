from __future__ import annotations

import json

from app.schemas.bars import BarHistoryParams, BarsResponse, StreamBarEvent
from app.schemas.symbols import SymbolDetails, SymbolDetailsResponse
from app.broker.tradestation_client import TradeStationClient


class MarketDataService:
    def __init__(self, client: TradeStationClient):
        self.client = client
        self._symbol_details_cache: dict[str, SymbolDetails] = {}

    def get_symbol_details(self, symbol: str) -> SymbolDetails:
        if symbol in self._symbol_details_cache:
            return self._symbol_details_cache[symbol]
        response = self.client.get(
            f"/marketdata/symbols/@{symbol}",
            timeout=30,
        )
        parsed = SymbolDetailsResponse.from_dict(response.json())
        if not parsed.symbols:
            raise ValueError(f"no symbol details returned for {symbol}")
        details = parsed.symbols[0]
        self._symbol_details_cache[symbol] = details
        return details

    def get_bars(self, params: BarHistoryParams) -> BarsResponse:
        response = self.client.get(
            f"/marketdata/barcharts/@{params.symbol}",
            params=params.to_query_params(),
            timeout=30,
        )
        return BarsResponse.from_dict(response.json())
    
    def stream_bars(self, params: BarHistoryParams):
        response = self.client.get(
            f"/marketdata/stream/barcharts/@{params.symbol}",
            params=params.to_query_params(),
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

                event = StreamBarEvent.from_dict(payload)
                yield event
        finally:
            response.close()