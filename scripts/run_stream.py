from app.broker.tradestation_client import TradeStationClient
from app.market_data.market_data_service import MarketDataService
from app.utils.toml_loader import load_stream_params
from config.settings import Settings

settings = Settings()
client = TradeStationClient(settings)
market_data_service = MarketDataService(client)

params = load_stream_params("stream_config.toml")
try:
    for param in params:
        for event in market_data_service.stream_bars(param):
            if event.is_bar:
                bar = event.bar
                print(
                    f"BAR {bar.timestamp} O={bar.open} H={bar.high} "
                    f"L={bar.low} C={bar.close} RT={bar.is_realtime}"
                )
            elif event.is_heartbeat:
                print("heartbeat: ", event.heartbeat)
            elif event.is_error:
                print("stream error: ", event.error)
                break
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    client.close()