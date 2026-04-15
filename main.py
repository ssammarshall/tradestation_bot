from config.settings import Settings
from app.broker.tradestation_client import TradeStationClient
from app.market_data.bar_service import BarService
from app.market_data.stream_service import StreamService
from app.utils.toml_loader import load_stream_params

def main():
    settings = Settings()
    client = TradeStationClient(settings)
    bar_service = BarService(client)
    stream_service = StreamService(client)

    params = load_stream_params("stream_config.toml")
    for param in params:
        for event in stream_service.stream_bars(param):
            print(event)

if __name__ == "__main__":
    main()