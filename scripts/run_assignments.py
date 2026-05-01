import time

from app.broker.tradestation_client import TradeStationClient
from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.strategies.strategy_manager import StrategyManager
from config.settings import Settings

settings = Settings()
client = TradeStationClient(settings)
market_data_service = MarketDataService(client)
order_service = OrderService(client)
strategy_manager = StrategyManager(
    market_data_service=market_data_service,
    order_service=order_service,
)

strategy_manager.load("strategy_assignments.toml")
print(f"Loaded {len(strategy_manager.strategies)} strategy assignment(s).")

try:
    while True:
        strategy_manager.update()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    strategy_manager.shutdown()
    client.close()
