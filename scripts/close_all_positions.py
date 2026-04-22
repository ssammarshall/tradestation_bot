from config.settings import Settings
from app.broker.tradestation_client import TradeStationClient
from app.account.account_service import AccountService

settings = Settings()
client = TradeStationClient(settings)
account_service = AccountService(client)

account_id = settings.active_account_id
print(f"=== Close All Positions ({settings.environment}) ===")
print(f"  account_id={account_id}\n")

positions_response = account_service.get_positions(account_id)
positions = positions_response.positions

if not positions:
    print("No open positions found.")
else:
    print(f"Found {len(positions)} open position(s):")
    for p in positions:
        print(f"  {p.symbol}  {p.long_short}  qty={p.quantity}  avg_price={p.average_price}  unrealized_pnl={p.unrealized_profit_loss}")

    print()

    results = account_service.close_all_positions(account_id)

    print("=== Close Orders ===")
    for result_response in results:
        for order in result_response.orders:
            if order.is_error:
                print(f"  error: {order.error}")
            else:
                print(f"  order placed: id={order.order_id} msg={order.message}")
