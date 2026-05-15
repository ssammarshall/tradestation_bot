from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from app.market_data.market_data_service import MarketDataService
from app.market_data.market_data_stream_manager import MarketDataStreamManager
from app.orders.order_service import OrderService
from app.orders.order_stream_manager import OrderStreamManager
from app.schemas.bars import StreamBarEvent
from app.schemas.orders import StreamOrderEvent
from app.strategies.registry import build_default_registry
from app.strategies.strategy import Strategy
from app.utils.toml_loader import load_strategy_assignments


class StrategyManager:
    def __init__(
        self,
        market_data_service: MarketDataService,
        order_service: OrderService,
    ):
        self._market_data = market_data_service
        self._market_data_stream_manager = MarketDataStreamManager(market_data_service)
        self._order_service = order_service
        self._order_stream_manager = OrderStreamManager(order_service)
        self._registry = build_default_registry()
        self._strategies: list[Strategy] = []
        self._callbacks: dict[Strategy, Callable[[StreamBarEvent], None]] = {}
        self._order_callbacks: dict[Strategy, Callable[[StreamOrderEvent], None]] = {}

    def load(self, path: str) -> None:
        for strategy in load_strategy_assignments(
            path,
            market_data_service=self._market_data,
            order_service=self._order_service,
        ):
            strategy.setup = self._registry.get_setup(strategy.setup)(symbol=strategy.symbol)
            strategy.entry = self._registry.get_entry(strategy.entry)(symbol=strategy.symbol)
            self._strategies.append(strategy)

            callback: Callable[[StreamBarEvent], None] = lambda event, s=strategy: s.evaluate(event)
            self._callbacks[strategy] = callback

            order_callback: Callable[[StreamOrderEvent], None] = lambda event, s=strategy: s.on_order_event(event)
            self._order_callbacks[strategy] = order_callback

    def subscribe_strategy(self, strategy: Strategy) -> None:
        if not strategy._is_subscribed and strategy.stream:
            strategy.startup()
            self._market_data_stream_manager.subscribe(strategy.stream, self._callbacks[strategy])
            self._order_stream_manager.subscribe(strategy.account_id, self._order_callbacks[strategy])

    def unsubscribe_strategy(self, strategy: Strategy) -> None:
        if strategy._is_subscribed and strategy.stream:
            self._order_stream_manager.unsubscribe(strategy.account_id, self._order_callbacks[strategy])
            self._market_data_stream_manager.unsubscribe(strategy.stream, self._callbacks[strategy])
            strategy.shutdown()

    def update(self) -> None:
        current_time = datetime.now(timezone.utc).time()
        
        for strategy in self._strategies:
            in_window = strategy.trade_window_start <= current_time < strategy.trade_window_end
            
            if in_window and not strategy._is_subscribed:
                self.subscribe_strategy(strategy)
            elif not in_window and strategy._is_subscribed:
                self.unsubscribe_strategy(strategy)

    @property
    def strategies(self) -> list[Strategy]:
        return list(self._strategies)

    def shutdown(self) -> None:
        for strategy in self._strategies:
            if strategy._is_subscribed:
                self.unsubscribe_strategy(strategy)
        self._market_data_stream_manager.shutdown()
        self._order_stream_manager.shutdown()
