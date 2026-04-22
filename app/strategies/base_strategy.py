from time import time

from app.strategies.entries.base_entry import BaseEntry
from app.strategies.setups.base_setup import BaseSetup


class BaseStrategy:
    def __init__(
        self,
        symbol: str,
        setup: BaseSetup,
        entry: BaseEntry,
        trade_window_start: time,
        trade_window_end: time,
        max_num_of_trades: int,
    ) -> None:
        self.symbol = symbol
        self.setup = setup
        self.entry = entry
        self.trade_window_start = trade_window_start
        self.trade_window_end = trade_window_end
        self.max_num_of_trades = max_num_of_trades
        self._setup_confirmed: bool = False

    def evaluate(self) -> None:
        if not self._setup_confirmed:
            if self.setup.is_valid():
                self._setup_confirmed = True
        else:
            self.entry.is_valid()