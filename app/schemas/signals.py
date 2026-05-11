from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class EntrySignal:
    """Setup-emitted trade signal consumed by an entry."""
    is_bullish: bool
    target_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    resistance_level: Decimal | None = None
    support_level: Decimal | None = None
