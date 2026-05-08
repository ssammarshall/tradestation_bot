import logging
from typing import Mapping

_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

def configure(level: int | str = logging.INFO, overrides: Mapping[str, int | str] | None = None) -> None:
    logging.basicConfig(level=level, format=_FORMAT)
    if not overrides: return
    for name, lvl in overrides.items():
        logging.getLogger(name).setLevel(lvl)