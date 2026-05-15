from __future__ import annotations

from datetime import datetime
from logging import Logger, getLogger
from typing import Callable

from app.strategies.backtest.backtest_market_data_service import BacktestMarketDataService
from app.strategies.backtest.backtest_order_service import BacktestOrderService, BacktestTrade
from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.schemas.bars import StreamBarEvent
from app.strategies.registry import build_default_registry
from app.strategies.strategy import Strategy
from app.utils.logging import bar_clock
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
        self._order_service = BacktestOrderService()
        self._registry = build_default_registry()
        self._strategies: list[Strategy] = []
        self._callbacks: dict[Strategy, Callable[[StreamBarEvent], None]] = {}
        self._trades: dict[Strategy, list[BacktestTrade]] = {}
        self.log: Logger = getLogger(self.__class__.__name__)

    @property
    def trades(self) -> dict[Strategy, list[BacktestTrade]]:
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
            strategy.setup = self._registry.get_setup(strategy.setup)(symbol=strategy.symbol)
            strategy.entry = self._registry.get_entry(strategy.entry)(symbol=strategy.symbol)
            self._strategies.append(strategy)
            self._trades[strategy] = []

            callback: Callable[[StreamBarEvent], None] = lambda event, s=strategy: s.evaluate(event)
            self._callbacks[strategy] = callback

    def run(self) -> None:
        grand_total_pnl = 0.0
        grand_total_trades = 0
        for strategy in self._strategies:
            self.log.info("replaying %s (%s)", strategy.name, strategy.symbol)
            self._simulate(strategy)
            trades = self._trades[strategy]
            self.log.info("%s - total trades taken: %d", strategy.name, len(trades))
            for i, t in enumerate(trades, start=1):
                dollar_pnl = t.pnl * strategy.point_value
                self.log.info(
                    "%s - %d. %s %s entry=%.4f@%s exit=%.4f@%s (%s) pnl=$%+.2f",
                    strategy.name,
                    i,
                    "LONG" if t.is_long else "SHORT",
                    t.symbol,
                    t.entry_price,
                    t.entry_timestamp,
                    t.exit_price,
                    t.exit_timestamp,
                    t.exit_reason,
                    dollar_pnl,
                )
            total_pnl = sum(t.pnl * strategy.point_value for t in trades)
            wins = sum(1 for t in trades if t.pnl > 0)
            losses = sum(1 for t in trades if t.pnl < 0)
            self.log.info(
                "%s - total pnl=$%+.2f, wins=%d, losses=%d",
                strategy.name,
                total_pnl,
                wins,
                losses,
            )
            grand_total_pnl += total_pnl
            grand_total_trades += len(trades)

        self.log.info(
            "backtest complete - strategies=%d, trades=%d, total pnl=$%+.2f",
            len(self._strategies),
            grand_total_trades,
            grand_total_pnl,
        )

    def _simulate(self, strategy: Strategy) -> None:
        self._order_service.reset()
        bars = self._market_data.prefetch(strategy.stream)
        if not bars:
            self.log.warning("no bars returned for %s; skipping", strategy.symbol)
            return

        ws = strategy.trade_window_start
        we = strategy.trade_window_end
        callback = self._callbacks[strategy]

        for bar in bars:
            self._market_data.cursor_epoch = bar.epoch
            self._order_service.cursor_epoch = bar.epoch
            bar_clock.set(bar.timestamp)
            bar_time = datetime.fromisoformat(bar.timestamp).time()
            in_window = ws <= bar_time < we

            if in_window and not strategy._is_subscribed:
                strategy.startup()
            elif not in_window and strategy._is_subscribed and not strategy.has_active_order:
                strategy.shutdown()

            if strategy._is_subscribed and in_window:
                callback(StreamBarEvent(raw={}, bar=bar))

            for evt in self._order_service.tick(bar):
                strategy.on_order_event(evt)

            self._trades[strategy].extend(self._order_service.consume_completed_trades())

        if strategy._is_subscribed:
            strategy.shutdown()
