from app.strategies.backtest.backtester import Backtester
from app.broker.tradestation_client import TradeStationClient
from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.utils.logging import configure
from app.utils.toml_loader import load_logging_config
from config.settings import Settings

level, overrides = load_logging_config("logging.toml")
configure(level=level, overrides=overrides)

settings = Settings()
client = TradeStationClient(settings)
market_data_service = MarketDataService(client)
order_service = OrderService(client)

backtester = Backtester(
    market_data_service=market_data_service,
    order_service=order_service,
    days_back=30,
)

try:
    backtester.load("strategy_assignments.toml")
    print(f"Loaded {len(backtester.strategies)} strategy assignment(s).")
    backtester.run()
finally:
    client.close()
