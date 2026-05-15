from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from logging import Logger, getLogger

from app.schemas.bars import Bar
from app.schemas.orders import (
    BracketOrderRequest,
    GroupOrderResponse,
    OrderRequest,
    OrderResponse,
    OrderResult,
    OrderUpdate,
    StreamOrderEvent,
    TradeAction,
)


@dataclass
class BacktestTrade:
    symbol: str
    is_long: bool
    quantity: float
    entry_price: float
    exit_price: float
    entry_timestamp: str
    exit_timestamp: str
    exit_reason: str  # "stop" | "take_profit"

    @property
    def pnl(self) -> float:
        diff = self.exit_price - self.entry_price if self.is_long else self.entry_price - self.exit_price
        return diff * self.quantity


@dataclass
class _PendingBracket:
    symbol: str
    is_long: bool
    quantity: float
    stop_price: float
    take_profit_price: float
    entry_order_id: str
    stop_order_id: str
    take_profit_order_id: str
    place_epoch: int
    state: str  # "PENDING_ENTRY" | "ACTIVE" | "DONE"
    entry_price: float | None = None
    entry_timestamp: str | None = None


class BacktestOrderService:
    """
    In-memory stand-in for OrderService used by the backtester.

    place_bracket_order records a bracket; tick(bar) advances each pending
    bracket against the bar being replayed and returns synthetic
    StreamOrderEvents that mirror the live order-stream shape, so
    Strategy.on_order_event runs unchanged in backtest.
    """

    def __init__(self) -> None:
        self._brackets: list[_PendingBracket] = []
        self._completed: list[BacktestTrade] = []
        self._id_counter = count(1)
        # Set by the backtester before each bar is dispatched. Used so an
        # entry market order does not fill on the same bar that placed it.
        self.cursor_epoch: int = 0
        self.log: Logger = getLogger(self.__class__.__name__)

    def consume_completed_trades(self) -> list[BacktestTrade]:
        trades = self._completed
        self._completed = []
        return trades

    def reset(self) -> None:
        self._brackets.clear()
        self._completed.clear()

    def _next_id(self, suffix: str) -> str:
        return f"BT-{next(self._id_counter)}-{suffix}"

    def place_order(self, order: OrderRequest) -> OrderResponse:
        return OrderResponse(orders=[OrderResult(order_id=self._next_id("OP"))])

    def place_bracket_order(self, bracket: BracketOrderRequest) -> GroupOrderResponse:
        entry_id = self._next_id("ENT")
        stop_id = self._next_id("SL")
        tp_id = self._next_id("TP")

        is_long = bracket.entry.trade_action == TradeAction.BUY
        self._brackets.append(
            _PendingBracket(
                symbol=bracket.entry.symbol,
                is_long=is_long,
                quantity=float(bracket.entry.quantity),
                stop_price=float(bracket.stop_loss_price),
                take_profit_price=float(bracket.take_profit_price),
                entry_order_id=entry_id,
                stop_order_id=stop_id,
                take_profit_order_id=tp_id,
                place_epoch=self.cursor_epoch,
                state="PENDING_ENTRY",
            )
        )
        return GroupOrderResponse(
            orders=[
                OrderResult(order_id=entry_id),
                OrderResult(order_id=stop_id),
                OrderResult(order_id=tp_id),
            ]
        )

    def tick(self, bar: Bar) -> list[StreamOrderEvent]:
        events: list[StreamOrderEvent] = []
        for br in self._brackets:
            if br.state == "PENDING_ENTRY":
                # Market entry fills at the first bar strictly after placement.
                if bar.epoch <= br.place_epoch:
                    continue
                br.entry_price = bar.open_f
                br.entry_timestamp = bar.timestamp
                events.append(_fill(br.entry_order_id, br.symbol))
                br.state = "ACTIVE"
                self._evaluate_exit(br, bar, events)
            elif br.state == "ACTIVE":
                self._evaluate_exit(br, bar, events)

        self._brackets = [b for b in self._brackets if b.state != "DONE"]
        return events

    def _evaluate_exit(self, br: _PendingBracket, bar: Bar, events: list[StreamOrderEvent]) -> None:
        if br.is_long:
            hit_stop = bar.low_f <= br.stop_price
            hit_tp = bar.high_f >= br.take_profit_price
        else:
            hit_stop = bar.high_f >= br.stop_price
            hit_tp = bar.low_f <= br.take_profit_price

        # If a single bar wicks through both levels, assume the stop fills first.
        if hit_stop:
            events.append(_fill(br.stop_order_id, br.symbol))
            events.append(_cancel(br.take_profit_order_id, br.symbol))
            self._record_trade(br, bar, exit_price=br.stop_price, exit_reason="stop")
            br.state = "DONE"
        elif hit_tp:
            events.append(_fill(br.take_profit_order_id, br.symbol))
            events.append(_cancel(br.stop_order_id, br.symbol))
            self._record_trade(br, bar, exit_price=br.take_profit_price, exit_reason="take_profit")
            br.state = "DONE"

    def _record_trade(self, br: _PendingBracket, bar: Bar, exit_price: float, exit_reason: str) -> None:
        if br.entry_price is None or br.entry_timestamp is None:
            return
        self._completed.append(
            BacktestTrade(
                symbol=br.symbol,
                is_long=br.is_long,
                quantity=br.quantity,
                entry_price=br.entry_price,
                exit_price=exit_price,
                entry_timestamp=br.entry_timestamp,
                exit_timestamp=bar.timestamp,
                exit_reason=exit_reason,
            )
        )


def _fill(order_id: str, symbol: str) -> StreamOrderEvent:
    return StreamOrderEvent(
        raw={},
        order=OrderUpdate(order_id=order_id, status="FLL", symbol=symbol),
    )


def _cancel(order_id: str, symbol: str) -> StreamOrderEvent:
    return StreamOrderEvent(
        raw={},
        order=OrderUpdate(order_id=order_id, status="CAN", symbol=symbol),
    )
