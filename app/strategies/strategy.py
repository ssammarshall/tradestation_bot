from datetime import time
from logging import Logger, getLogger

from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.schemas.bars import BarStatus, BarHistoryParams, StreamBarEvent
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
        self._current_num_of_trades = 0
        self._setup_confirmed: bool = False
        self._is_subscribed: bool = False
        self.log: Logger = getLogger(f"{self.name}")

    def startup(self) -> None:
        self.setup.symbol = self.symbol
        params = self.setup.history_params(self.symbol)
        if params:
            bars = self.market_data_service.get_bars(params).bars
            self.setup.startup(bars)
        self._is_subscribed = True

    def shutdown(self) -> None:
        self._is_subscribed = False
        self._current_num_of_trades = 0

    def reset(self) -> None:
        self._setup_confirmed = False
        self.setup.reset()

    def evaluate(self, event: StreamBarEvent) -> None:
        if not event.is_bar:
            return

        bar = event.bar

        if bar.bar_status != BarStatus.CLOSED:
            return

        # Setup
        while True:
            if self._setup_confirmed:
                break
            
            is_valid_setup = self.setup.is_valid(bar)
            if is_valid_setup:
                self._setup_confirmed = True
                break
            
            if self.setup.pending_request is None:
                break
            request = self.setup.pending_request
            self.setup.pending_request = None
            bars = self.market_data_service.get_bars(request.params).bars
            self.setup.receive_bars(bars)


        if not self._setup_confirmed:
            return
        
        # Entry
        valid_entry = self.entry.is_valid(bar)
        if valid_entry:
            self._current_num_of_trades += 1

            # TODO: execute trade via order service

            self.log.info("entry at %s (trades today=%d)", bar.timestamp, self._current_num_of_trades)
            if self._current_num_of_trades >= self.max_num_of_trades:
                self.log.info("max trades reached, shutting down")
                self.shutdown()