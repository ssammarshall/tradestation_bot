from __future__ import annotations

from datetime import datetime
from typing import Callable

from app.market_data.stream_manager import StreamManager
from app.schemas.bars import StreamBarEvent
from app.strategies.registry import StrategyRegistry, build_default_registry
from app.strategies.strategy import Strategy
from app.utils.toml_loader import load_strategy_assignments


class StrategyManager:
    def __init__(self, stream_manager: StreamManager, registry: StrategyRegistry = None):
        self._stream_manager = stream_manager
        self._registry = registry if registry is not None else build_default_registry()
        self._strategies: list[Strategy] = []
        self._callbacks: dict[Strategy, Callable[[StreamBarEvent], None]] = {}

    def load(self, path: str) -> None:
        for strategy in load_strategy_assignments(path):
            strategy.setup = self._registry.get_setup(strategy.setup)()
            strategy.entry = self._registry.get_entry(strategy.entry)()
            self._strategies.append(strategy)
            
            callback: Callable[[StreamBarEvent], None] = lambda event, s=strategy: s.evaluate(event)
            self._callbacks[strategy] = callback

    def subscribe_strategy(self, strategy: Strategy) -> None:
        if not strategy._is_subscribed and strategy.stream:
            self._stream_manager.subscribe(strategy.stream, self._callbacks[strategy])
            strategy.startup()

    def unsubscribe_strategy(self, strategy: Strategy) -> None:
        if strategy._is_subscribed and strategy.stream:
            self._stream_manager.unsubscribe(strategy.stream, self._callbacks[strategy])
            strategy.shutdown()

    def update(self) -> None:
        current_time = datetime.now().time()
        
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
        self._stream_manager.shutdown()
