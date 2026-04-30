from datetime import time
from typing import Optional

from app.schemas.bars import BarHistoryParams, StreamBarEvent
from app.strategies.entries.base_entry import BaseEntry
from app.strategies.setups.base_setup import BaseSetup


class Strategy:
    def __init__(
        self,
        name: str,
        symbol: str,
        setup: BaseSetup,
        entry: BaseEntry,
        trade_window_start: time,
        trade_window_end: time,
        max_num_of_trades: int,
        stream: Optional[BarHistoryParams] = None,
    ) -> None:
        self.name = name
        self.symbol = symbol
        self.setup = setup
        self.entry = entry
        self.trade_window_start = trade_window_start
        self.trade_window_end = trade_window_end
        self.max_num_of_trades = max_num_of_trades
        self.stream = stream
        self._setup_confirmed: bool = False
        self._is_subscribed: bool = False

    def evaluate(self, event: StreamBarEvent) -> None:
        if not event.is_bar:
            return
        if not self._setup_confirmed:
            if self.setup.is_valid(event.bar):
                self._setup_confirmed = True
        else:
            self.entry.is_valid(event.bar)