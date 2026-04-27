import time

from app.broker.tradestation_client import TradeStationClient
from app.market_data.stream_service import StreamService
from app.market_data.stream_manager import StreamManager
from app.strategies.strategy_manager import StrategyManager
from config.settings import Settings

settings = Settings()
client = TradeStationClient(settings)
stream_service = StreamService(client)
stream_manager = StreamManager(stream_service)
strategy_manager = StrategyManager(stream_manager)

strategy_manager.load("strategy_assignments.toml")
print(f"Loaded {len(strategy_manager.strategies)} strategy assignment(s).")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    strategy_manager.shutdown()
    client.close()
