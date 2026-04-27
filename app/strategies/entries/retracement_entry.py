from decimal import Decimal

from app.strategies.entries.base_entry import BaseEntry

class RetracementEntry(BaseEntry):
    def __init__(
        self,
        take_profit: Decimal = Decimal(0),
        stop_loss: Decimal = Decimal(0),
        target_price: Decimal | None = None,
    ) -> None:
        super().__init__(take_profit, stop_loss, target_price)

    def is_valid(self) -> bool:
        # Implement the validation logic for the RetracementEntry
        pass