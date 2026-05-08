from abc import ABC, abstractmethod
from decimal import Decimal
from logging import Logger, getLogger

from app.schemas.bars import Bar


class BaseEntry(ABC):
    def __init__(
        self,
        take_profit: Decimal = Decimal(0),
        stop_loss: Decimal = Decimal(0),
        target_price: Decimal | None = None,
    ) -> None:
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.log: Logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...
