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
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        resistance_level: Decimal | None = None,
        support_level: Decimal | None = None,
    ) -> None:
        self.symbol: str = symbol
        self.is_bullish = is_bullish
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.resistance_level = resistance_level
        self.support_level = support_level
        self.invalidated: bool = False
        self.log: Logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...

    def apply_signal(self, signal: EntrySignal) -> None:
        self.is_bullish = signal.is_bullish
        self.target_price = signal.target_price
        self.stop_loss = signal.stop_loss
        self.take_profit = signal.take_profit
        self.resistance_level = signal.resistance_level
        self.support_level = signal.support_level
        self.invalidated = False

    def clear_signal(self) -> None:
        self.is_bullish = None
        self.target_price = None
        self.stop_loss = None
        self.take_profit = None
        self.resistance_level = None
        self.support_level = None
        self.invalidated = False
