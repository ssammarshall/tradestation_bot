from __future__ import annotations

import json

from app.schemas.bars import BarHistoryParams, StreamBarEvent
from app.broker.tradestation_client import TradeStationClient


class StreamService:
    def __init__(self, client: TradeStationClient):
        self.client = client

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