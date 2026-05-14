from abc import ABC, abstractmethod
from decimal import Decimal
from logging import Logger, getLogger

from app.schemas.bars import Bar
from app.schemas.signals import EntrySignal


class BaseEntry(ABC):
    def __init__(
        self,
        symbol: str,
        is_bullish: bool | None = None,
        target_price: Decimal | None = None,
        resistance_level: Decimal | None = None,
        support_level: Decimal | None = None,
    ) -> None:
        self.symbol: str = symbol
        self.is_bullish = is_bullish
        self.target_price = target_price
        self.resistance_level = resistance_level
        self.support_level = support_level
        self.invalidated: bool = False
        self.log: Logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...

    def apply_signal(self, signal: EntrySignal) -> None:
        self.is_bullish = signal.is_bullish
        self.target_price = signal.target_price
        self.resistance_level = signal.resistance_level
        self.support_level = signal.support_level
        self.invalidated = False

    def clear_signal(self) -> None:
        self.is_bullish = None
        self.target_price = None
        self.resistance_level = None
        self.support_level = None
        self.invalidated = False
