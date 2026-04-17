from config.settings import Settings
from app.broker.tradestation_client import TradeStationClient
from app.orders.order_service import OrderService
from app.schemas.orders import (
    BracketOrderRequest,
    OrderRequest,
    OrderType,
    TimeInForce,
    TimeInForceDuration,
    TradeAction,
)

SYMBOL = "MNQM26"
QUANTITY = "1"

settings = Settings()
client = TradeStationClient(settings)
order_service = OrderService(client)

# ---------------------------------------------------------------------------
# Single market order
# ---------------------------------------------------------------------------

order = OrderRequest(
    account_id=settings.active_account_id,
    symbol=SYMBOL,
    quantity=QUANTITY,
    trade_action=TradeAction.BUY,
    order_type=OrderType.MARKET,
    time_in_force=TimeInForce(duration=TimeInForceDuration.DAY),
)

response = order_service.place_order(order)
for result in response.orders:
    if result.is_error:
        print(f"order error: {result.error}")
    else:
        print(f"order placed: id={result.order_id} msg={result.message}")

# ---------------------------------------------------------------------------
# Bracket order (entry + stop loss + take profit)
# ---------------------------------------------------------------------------

entry = OrderRequest(
    account_id=settings.active_account_id,
    symbol=SYMBOL,
    quantity=QUANTITY,
    trade_action=TradeAction.BUY,
    order_type=OrderType.LIMIT,
    time_in_force=TimeInForce(duration=TimeInForceDuration.DAY),
    limit_price="19000.00",
)

bracket = BracketOrderRequest(
    entry=entry,
    stop_loss_price="18950.00",
    take_profit_price="19100.00",
)