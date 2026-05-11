from decimal import Decimal

from app.schemas.bars import Bar
from app.strategies.entries.base_entry import BaseEntry

class RetracementEntry(BaseEntry):
    def __init__(
        self,
        target_price: Decimal | None = None,
        resistance_level: Decimal | None = None,
        support_level: Decimal | None = None,
    ) -> None:
        super().__init__(target_price, resistance_level, support_level)

    def is_valid(self, bar: Bar) -> bool:
        return True  # Placeholder implementation; replace with actual logic