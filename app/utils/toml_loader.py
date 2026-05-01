import tomllib
from datetime import datetime

from app.market_data.market_data_service import MarketDataService
from app.orders.order_service import OrderService
from app.schemas.bars import BarHistoryParams, BarUnit, SessionTemplate
from app.strategies.strategy import Strategy


def _parse_time(time_str: str) -> datetime.time:
    """Convert 'HH:MM' string to datetime.time object"""
    return datetime.strptime(time_str, "%H:%M").time()

def load_strategy_assignments(
    path: str,
    market_data_service: MarketDataService,
    order_service: OrderService,
) -> list[Strategy]:
    with open(path, "rb") as f:
        data = tomllib.load(f)

    assignments = []
    for item in data.get("assignments", []):
        stream = BarHistoryParams(
            symbol=item["symbol"],
            unit=BarUnit(item.get("unit", "Minute")),
            interval=item.get("interval", 1),
            barsback=item.get("barsback"),
            session_template=SessionTemplate(item.get("session_template", "Default")),
        )
        assignments.append(
            Strategy(
                name=item["name"],
                symbol=item["symbol"],
                setup=item["setup"],
                entry=item["entry"],
                trade_window_start=_parse_time(item["trade_window_start"]),
                trade_window_end=_parse_time(item["trade_window_end"]),
                max_num_of_trades=item["max_num_of_trades"],
                market_data_service=market_data_service,
                order_service=order_service,
                stream=stream,
            )
        )

    return assignments

def load_stream_params(path: str) -> list[BarHistoryParams]:
    with open(path, "rb") as f:
        data = tomllib.load(f)

    params_list = []
    for item in data.get("streams", []):
        params_list.append(
            BarHistoryParams(
                symbol=item["symbol"],
                unit=BarUnit(item.get("unit", "Minute")),
                interval=item.get("interval", 1),
                barsback=item.get("barsback"),
                firstdate=item.get("firstdate"),
                lastdate=item.get("lastdate"),
                session_template=SessionTemplate(
                    item.get("session_template", "Default")
                ),
            )
        )

    return params_list