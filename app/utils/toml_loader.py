import tomllib
from app.schemas.bars import BarHistoryParams, BarUnit, SessionTemplate
from app.strategies.strategy import Strategy


def load_strategy_assignments(path: str) -> list[Strategy]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    
    assignments = []
    for item in data.get("assignments", []):
        assignments.append(
            Strategy(
                name=item["name"],
                symbol=item["symbol"],
                setup=item["setup"],
                entry=item["entry"],
                trade_window_start=item["trade_window_start"],
                trade_window_end=item["trade_window_end"],
                max_num_of_trades=item["max_num_of_trades"],
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