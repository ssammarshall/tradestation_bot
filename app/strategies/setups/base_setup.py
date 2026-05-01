from abc import ABC, abstractmethod

from app.schemas.bars import Bar, BarHistoryParams


class BaseSetup(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def history_params(self, symbol: str) -> BarHistoryParams: ...

    @abstractmethod
    def startup(self, bars: list[Bar]) -> None: ...

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...
