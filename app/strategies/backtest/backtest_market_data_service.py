from __future__ import annotations

import bisect
from datetime import datetime, timezone
from typing import Optional

from app.market_data.market_data_service import MarketDataService
from app.schemas.bars import Bar, BarHistoryParams, BarsResponse


# TradeStation caps barsback per request; stay safely under.
_TS_MAX_BARSBACK = 57000


def _bars_per_day(params: BarHistoryParams) -> int:
    if params.unit.value == "Minute":
        return max(1, (24 * 60) // params.interval)
    return 1


def _fetch_history(
    service: MarketDataService,
    template: BarHistoryParams,
    days_back: int,
) -> list[Bar]:
    total_needed = _bars_per_day(template) * days_back
    collected: list[Bar] = []
    lastdate: Optional[str] = None

    while len(collected) < total_needed:
        page_size = min(_TS_MAX_BARSBACK, total_needed - len(collected))
        params = BarHistoryParams(
            symbol=template.symbol,
            unit=template.unit,
            interval=template.interval,
            barsback=page_size,
            lastdate=lastdate,
            session_template=template.session_template,
        )
        page = service.get_bars(params).bars
        if not page:
            break
        collected = page + collected
        earliest_ms = page[0].epoch
        lastdate = (
            datetime.fromtimestamp((earliest_ms - 1) / 1000, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    seen: set[int] = set()
    unique: list[Bar] = []
    for b in collected:
        if b.epoch in seen:
            continue
        seen.add(b.epoch)
        unique.append(b)
    unique.sort(key=lambda b: b.epoch)
    return unique


class BacktestMarketDataService:
    """
    Duck-typed proxy around MarketDataService for backtest replay. Caches
    each (symbol, unit, interval) series the first time it is requested,
    then serves every get_bars() call by slicing the cache to bars with
    epoch <= cursor_epoch — so a strategy mid-replay only sees data
    available as of the bar currently being replayed.
    """

    def __init__(self, real: MarketDataService, days_back: int) -> None:
        self._real = real
        self._days_back = days_back
        self._series: dict[tuple[str, str, int], list[Bar]] = {}
        self._epochs: dict[tuple[str, str, int], list[int]] = {}
        self.cursor_epoch: int = 0

    @staticmethod
    def _key(params: BarHistoryParams) -> tuple[str, str, int]:
        return (params.symbol, params.unit.value, params.interval)

    def prefetch(self, template: BarHistoryParams) -> list[Bar]:
        key = self._key(template)
        if key not in self._series:
            bars = _fetch_history(self._real, template, self._days_back)
            self._series[key] = bars
            self._epochs[key] = [b.epoch for b in bars]
        return self._series[key]

    def get_bars(self, params: BarHistoryParams) -> BarsResponse:
        self.prefetch(params)
        key = self._key(params)
        epochs = self._epochs[key]
        idx = bisect.bisect_right(epochs, self.cursor_epoch)
        visible = self._series[key][:idx]
        if params.barsback is not None:
            visible = visible[-params.barsback:]
        return BarsResponse(bars=list(visible))
