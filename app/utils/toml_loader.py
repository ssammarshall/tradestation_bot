import tomllib
from app.schemas.bars import BarHistoryParams, BarUnit, SessionTemplate


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