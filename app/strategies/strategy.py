from datetime import time
from typing import Optional

from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
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
        market_data_service: MarketDataService,
        order_service: OrderService,
        stream: BarHistoryParams,
    ) -> None:
        self.name = name
        self.symbol = symbol
        self.setup = setup
        self.entry = entry
        self.trade_window_start = trade_window_start
        self.trade_window_end = trade_window_end
        self.max_num_of_trades = max_num_of_trades
        self.market_data_service = market_data_service
        self.order_service = order_service
        self.stream = stream
        self._setup_confirmed: bool = False
        self._is_subscribed: bool = False

    def startup(self) -> None:
        params = self.setup.history_params(self.symbol)
        if params:
            bars = self.market_data_service.get_bars(params).bars
            self.setup.startup(bars)
        self._is_subscribed = True

    def shutdown(self) -> None:
        self._is_subscribed = False

    def evaluate(self, event: StreamBarEvent) -> None:
        if not event.is_bar:
            return
        if not self._setup_confirmed:
            if self.setup.is_valid(event.bar):
                self._setup_confirmed = True
        else:
            self.entry.is_valid(event.bar)