from abc import ABC, abstractmethod

from app.schemas.bars import Bar, BarHistoryParams, BarHistoryRequest


class BaseSetup(ABC):
    def __init__(self) -> None:
        self.symbol: str | None = None
        self.pending_request: BarHistoryRequest | None = None

    @abstractmethod
    def history_params(self, symbol: str) -> BarHistoryParams: ...

    @abstractmethod
    def startup(self, bars: list[Bar]) -> None: ...

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...

    def receive_bars(self, bars: list[Bar]) -> None:
        pass
