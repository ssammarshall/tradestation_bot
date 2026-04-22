from abc import ABC, abstractmethod
from decimal import Decimal


class BaseEntry(ABC):
    def __init__(
        self,
        take_profit: Decimal,
        stop_loss: Decimal,
        target_price: Decimal | None = None,
    ) -> None:
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.target_price = target_price

    @abstractmethod
    def is_valid(self) -> bool: ...
