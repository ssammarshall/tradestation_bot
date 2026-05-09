from __future__ import annotations

from datetime import datetime
from logging import Logger, getLogger
from typing import Callable

from app.strategies.backtest.backtest_market_data_service import BacktestMarketDataService
from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.schemas.bars import StreamBarEvent
from app.strategies.registry import build_default_registry
from app.strategies.strategy import Strategy
from app.utils.toml_loader import load_strategy_assignments


class Backtester:
    """
    Mirrors StrategyManager, but instead of a live bar stream the bars are
    fetched up front and replayed one at a time through the same callback
    path StrategyManager uses for live data. A cursor advanced per replayed
    bar clamps any get_bars() the strategy issues mid-replay (startup,
    pending_request) to data available as of the current tick.
    """

    def __init__(
        self,
        market_data_service: MarketDataService,
        order_service: OrderService,
        days_back: int = 365,
    ) -> None:
        self._market_data = BacktestMarketDataService(market_data_service, days_back)
        self._order_service = order_service
        self._registry = build_default_registry()
        self._strategies: list[Strategy] = []
        self._callbacks: dict[Strategy, Callable[[StreamBarEvent], None]] = {}
        self._trades: dict[Strategy, list[str]] = {}
        self.log: Logger = getLogger(self.__class__.__name__)

    @property
    def trades(self) -> dict[Strategy, list[str]]:
        return {s: list(ts) for s, ts in self._trades.items()}

    @property
    def strategies(self) -> list[Strategy]:
        return list(self._strategies)

    def load(self, path: str) -> None:
        for strategy in load_strategy_assignments(
            path,
            market_data_service=self._market_data,
            order_service=self._order_service,
        ):
            strategy.setup = self._registry.get_setup(strategy.setup)()
            strategy.entry = self._registry.get_entry(strategy.entry)()
            self._strategies.append(strategy)
            self._trades[strategy] = []

            callback: Callable[[StreamBarEvent], None] = lambda event, s=strategy: s.evaluate(event)
            self._callbacks[strategy] = callback

    def run(self) -> None:
        for strategy in self._strategies:
            self.log.info("replaying %s (%s)", strategy.name, strategy.symbol)
            self._simulate(strategy)
            timestamps = self._trades[strategy]
            self.log.info("%s - total trades taken: %d", strategy.name, len(timestamps))
            for i, ts in enumerate(timestamps, start=1):
                self.log.info("%s - %d. %s", strategy.name, i, ts)

    def _simulate(self, strategy: Strategy) -> None:
        bars = self._market_data.prefetch(strategy.stream)
        if not bars:
            self.log.warning("no bars returned for %s; skipping", strategy.symbol)
            return

        ws = strategy.trade_window_start
        we = strategy.trade_window_end
        callback = self._callbacks[strategy]

        for bar in bars:
            self._market_data.cursor_epoch = bar.epoch
            bar_time = datetime.fromisoformat(bar.timestamp).time()
            in_window = ws <= bar_time < we

            if in_window and not strategy._is_subscribed:
                strategy.startup()
            elif not in_window and strategy._is_subscribed:
                strategy.shutdown()

            if strategy._is_subscribed:
                trades_before = strategy._current_num_of_trades
                callback(StreamBarEvent(raw={}, bar=bar))
                if strategy._current_num_of_trades > trades_before:
                    self._trades[strategy].append(bar.timestamp)

        if strategy._is_subscribed:
            strategy.shutdown()
