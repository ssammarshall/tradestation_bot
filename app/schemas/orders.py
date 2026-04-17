from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OrderType(str, Enum):
    MARKET = "Market"
    LIMIT = "Limit"
    STOP_MARKET = "StopMarket"
    STOP_LIMIT = "StopLimit"


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_TO_COVER = "BUYTOCOVER"
    SELL_SHORT = "SELLSHORT"


class TimeInForceDuration(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"


class GroupOrderType(str, Enum):
    BRACKET = "BRK"  # entry + stop loss + take profit


# ---------------------------------------------------------------------------
# Request parameters
# ---------------------------------------------------------------------------

@dataclass
class TimeInForce:
    duration: TimeInForceDuration = TimeInForceDuration.DAY
    expiration: Optional[str] = None  # ISO 8601, required when duration=GTD

    def to_dict(self) -> dict:
        d: dict = {"Duration": self.duration.value}
        if self.expiration is not None:
            d["Expiration"] = self.expiration
        return d


@dataclass
class OrderRequest:
    """
    Parameters for POST /v3/orderexecution/orders.

    Prices are passed as strings to preserve decimal precision,
    matching the TradeStation API convention.
    """
    account_id: str
    symbol: str
    quantity: str
    trade_action: TradeAction
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = field(default_factory=TimeInForce)
    limit_price: Optional[str] = None   # required for Limit / StopLimit
    stop_price: Optional[str] = None    # required for StopMarket / StopLimit
    route: str = "Intelligent"

    def to_dict(self) -> dict:
        d: dict = {
            "AccountID": self.account_id,
            "Symbol": self.symbol,
            "Quantity": self.quantity,
            "OrderType": self.order_type.value,
            "TradeAction": self.trade_action.value,
            "TimeInForce": self.time_in_force.to_dict(),
            "Route": self.route,
        }
        if self.limit_price is not None:
            d["LimitPrice"] = self.limit_price
        if self.stop_price is not None:
            d["StopPrice"] = self.stop_price
        return d


@dataclass
class BracketOrderRequest:
    """
    Parameters for POST /v3/orderexecution/ordergroups.

    Sends three legs as a bracket: entry, stop-loss, and take-profit.
    The stop-loss and take-profit legs are built automatically from
    the entry order plus the provided prices.
    """
    entry: OrderRequest
    stop_loss_price: str
    take_profit_price: str

    def _exit_trade_action(self) -> TradeAction:
        if self.entry.trade_action == TradeAction.BUY:
            return TradeAction.SELL
        return TradeAction.BUY_TO_COVER

    def to_dict(self) -> dict:
        exit_action = self._exit_trade_action()
        gtc = TimeInForce(duration=TimeInForceDuration.GTC)

        stop_loss = OrderRequest(
            account_id=self.entry.account_id,
            symbol=self.entry.symbol,
            quantity=self.entry.quantity,
            trade_action=exit_action,
            order_type=OrderType.STOP_MARKET,
            time_in_force=gtc,
            stop_price=self.stop_loss_price,
            route=self.entry.route,
        )

        take_profit = OrderRequest(
            account_id=self.entry.account_id,
            symbol=self.entry.symbol,
            quantity=self.entry.quantity,
            trade_action=exit_action,
            order_type=OrderType.LIMIT,
            time_in_force=gtc,
            limit_price=self.take_profit_price,
            route=self.entry.route,
        )

        return {
            "Type": GroupOrderType.BRACKET.value,
            "Orders": [
                self.entry.to_dict(),
                stop_loss.to_dict(),
                take_profit.to_dict(),
            ],
        }


# ---------------------------------------------------------------------------
# Response objects
# ---------------------------------------------------------------------------

@dataclass
class OrderResult:
    """Result for a single order leg returned by the API."""
    order_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return bool(self.error)

    @classmethod
    def from_dict(cls, data: dict) -> OrderResult:
        return cls(
            order_id=data.get("OrderID"),
            message=data.get("Message"),
            error=data.get("Error"),
        )


@dataclass
class OrderResponse:
    """Parsed response from POST /v3/orderexecution/orders."""
    orders: list[OrderResult] = field(default_factory=list)

    @property
    def order_id(self) -> Optional[str]:
        """Convenience accessor for the first (and usually only) order ID."""
        return self.orders[0].order_id if self.orders else None

    @classmethod
    def from_dict(cls, data: dict) -> OrderResponse:
        results = [OrderResult.from_dict(o) for o in data.get("Orders", [])]
        return cls(orders=results)


@dataclass
class GroupOrderResponse:
    """Parsed response from POST /v3/orderexecution/ordergroups."""
    orders: list[OrderResult] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> GroupOrderResponse:
        results = [OrderResult.from_dict(o) for o in data.get("Orders", [])]
        return cls(orders=results)
