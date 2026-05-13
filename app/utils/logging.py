import logging
from contextvars import ContextVar
from typing import Mapping

_LIVE_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
_BACKTEST_FORMAT = "%(bar_time)s - %(levelname)s - %(name)s - %(message)s"

bar_clock: ContextVar[str] = ContextVar("bar_clock", default="")


def configure(
    level: int | str = logging.INFO,
    overrides: Mapping[str, int | str] | None = None,
    backtest: bool = False,
) -> None:
    fmt = _BACKTEST_FORMAT if backtest else _LIVE_FORMAT
    logging.basicConfig(level=level, format=fmt)
    if backtest:
        base_factory = logging.getLogRecordFactory()
        def factory(*args, **kwargs):
            record = base_factory(*args, **kwargs)
            record.bar_time = bar_clock.get()
            return record
        logging.setLogRecordFactory(factory)
    if not overrides: return
    for name, lvl in overrides.items():
        logging.getLogger(name).setLevel(lvl)
