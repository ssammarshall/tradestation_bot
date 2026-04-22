from __future__ import annotations

from app.market_data.stream_manager import StreamManager
from app.strategies.registry import StrategyRegistry, build_default_registry
from app.strategies.strategy import Strategy
from app.utils.toml_loader import load_strategy_assignments


class StrategyManager:
    def __init__(self, stream_manager: StreamManager, registry: StrategyRegistry = None):
        self._stream_manager = stream_manager
        self._registry = registry if registry is not None else build_default_registry()
        self._strategies: list[Strategy] = []

    def load(self, path: str) -> None:
        for strategy in load_strategy_assignments(path):
            self._strategies.append(strategy)
            self._stream_manager.subscribe(
                strategy.stream,
                lambda _, s=strategy: s.evaluate(),
            )

    @property
    def strategies(self) -> list[Strategy]:
        return list(self._strategies)

    def shutdown(self) -> None:
        self._stream_manager.shutdown()
