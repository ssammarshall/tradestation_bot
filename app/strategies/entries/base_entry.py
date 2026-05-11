from abc import ABC, abstractmethod
from decimal import Decimal
from logging import Logger, getLogger

from app.schemas.bars import Bar


class BaseEntry(ABC):
    def __init__(
        self,
        target_price: Decimal | None = None,
        resistance_level: Decimal | None = None,
        support_level: Decimal | None = None,
    ) -> None:
        self.target_price = target_price
        self.resistance_level = resistance_level
        self.support_level = support_level
        self.log: Logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...
