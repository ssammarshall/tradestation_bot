from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

@dataclass
class Account:
    account_id: str
    account_type: Optional[str] = None
    alias: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Account:
        return cls(
            account_id=data.get("AccountID", ""),
            account_type=data.get("AccountType"),
            alias=data.get("Alias"),
            currency=data.get("Currency"),
            status=data.get("Status"),
            name=data.get("Name"),
        )


@dataclass
class AccountsResponse:
    accounts: list[Account] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> AccountsResponse:
        return cls(accounts=[Account.from_dict(a) for a in data.get("Accounts", [])])


# ---------------------------------------------------------------------------
# Balances
# ---------------------------------------------------------------------------

@dataclass
class Balance:
    account_id: str
    cash_balance: Optional[str] = None
    buying_power: Optional[str] = None
    equity: Optional[str] = None
    market_value: Optional[str] = None
    todays_profit_loss: Optional[str] = None
    unrealized_profit_loss: Optional[str] = None
    realized_profit_loss: Optional[str] = None
    commission: Optional[str] = None
    required_margin: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Balance:
        return cls(
            account_id=data.get("AccountID", ""),
            cash_balance=data.get("CashBalance"),
            buying_power=data.get("BuyingPower"),
            equity=data.get("Equity"),
            market_value=data.get("MarketValue"),
            todays_profit_loss=data.get("TodaysProfitLoss"),
            unrealized_profit_loss=data.get("UnrealizedProfitLoss"),
            realized_profit_loss=data.get("RealizedProfitLoss"),
            commission=data.get("Commission"),
            required_margin=data.get("RequiredMargin"),
        )


@dataclass
class BalancesResponse:
    balances: list[Balance] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> BalancesResponse:
        return cls(balances=[Balance.from_dict(b) for b in data.get("Balances", [])])


# ---------------------------------------------------------------------------
# Beginning-of-day balances
# ---------------------------------------------------------------------------

@dataclass
class BODBalance:
    account_id: str
    cash_balance: Optional[str] = None
    buying_power: Optional[str] = None
    equity: Optional[str] = None
    net_cash: Optional[str] = None
    open_trade_equity: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> BODBalance:
        return cls(
            account_id=data.get("AccountID", ""),
            cash_balance=data.get("CashBalance"),
            buying_power=data.get("BuyingPower"),
            equity=data.get("Equity"),
            net_cash=data.get("NetCash"),
            open_trade_equity=data.get("OpenTradeEquity"),
        )


@dataclass
class BODBalancesResponse:
    balances: list[BODBalance] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> BODBalancesResponse:
        return cls(balances=[BODBalance.from_dict(b) for b in data.get("BODBalances", [])])


# ---------------------------------------------------------------------------
# Account Orders
# ---------------------------------------------------------------------------

@dataclass
class AccountOrder:
    order_id: Optional[str] = None
    account_id: Optional[str] = None
    symbol: Optional[str] = None
    order_type: Optional[str] = None
    trade_action: Optional[str] = None
    quantity: Optional[str] = None
    filled_quantity: Optional[str] = None
    status: Optional[str] = None
    limit_price: Optional[str] = None
    stop_price: Optional[str] = None
    opened_date_time: Optional[str] = None
    closed_date_time: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> AccountOrder:
        return cls(
            order_id=data.get("OrderID"),
            account_id=data.get("AccountID"),
            symbol=data.get("Symbol"),
            order_type=data.get("OrderType"),
            trade_action=data.get("TradeAction"),
            quantity=data.get("Quantity"),
            filled_quantity=data.get("FilledQuantity"),
            status=data.get("Status"),
            limit_price=data.get("LimitPrice"),
            stop_price=data.get("StopPrice"),
            opened_date_time=data.get("OpenedDateTime"),
            closed_date_time=data.get("ClosedDateTime"),
        )


@dataclass
class AccountOrdersResponse:
    orders: list[AccountOrder] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> AccountOrdersResponse:
        return cls(orders=[AccountOrder.from_dict(o) for o in data.get("Orders", [])])
