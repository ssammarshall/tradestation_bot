from decimal import Decimal

from app.schemas.bars import Bar
from app.schemas.signals import EntrySignal
from app.strategies.analyzers.bar_analysis import is_impulsive_bar
from app.strategies.entries.base_entry import BaseEntry


class RetracementEntry(BaseEntry):
    def __init__(
        self,
        symbol: str,
        is_bullish: bool | None = None,
        target_price: Decimal | None = None,
        resistance_level: Decimal | None = None,
        support_level: Decimal | None = None,
    ) -> None:
        super().__init__(symbol, is_bullish, target_price, resistance_level, support_level)
        self._has_retraced: bool = False

    def apply_signal(self, signal: EntrySignal) -> None:
        super().apply_signal(signal)
        if self.is_bullish is None:
            self.log.error("is_bullish is not set")
            raise ValueError("RetracementEntry requires is_bullish to be set")
        if self.target_price is None:
            self.log.error("target_price is not set")
            raise ValueError("RetracementEntry requires target_price to be set")
        if self.is_bullish and self.support_level is None:
            self.log.error("bullish signal missing support_level")
            raise ValueError("RetracementEntry bullish signal requires support_level")
        if not self.is_bullish and self.resistance_level is None:
            self.log.error("bearish signal missing resistance_level")
            raise ValueError("RetracementEntry bearish signal requires resistance_level")
        self._has_retraced = False

    def clear_signal(self) -> None:
        super().clear_signal()
        self._has_retraced = False

    def is_valid(self, bar: Bar) -> bool:
        target = float(self.target_price)

        if self.is_bullish:
            level = float(self.support_level)
            if bar.close_f < level:
                self.log.debug("price broke below support %s, invalidating", level)
                self.invalidated = True
                return False
            if not self._has_retraced:
                if bar.close_f > level:
                    self._has_retraced = True
                else:
                    return False
        else:
            level = float(self.resistance_level)
            if bar.close_f > level:
                self.log.debug("price broke above resistance %s, invalidating", level)
                self.invalidated = True
                return False
            if not self._has_retraced:
                if bar.close_f < level:
                    self._has_retraced = True
                else:
                    return False

        wicked_target = bar.low_f <= target <= bar.high_f
        if wicked_target and not is_impulsive_bar(bar):
            self.log.info("retracement entry valid at %s, target=%s", bar.timestamp, target)
            return True
        return False
