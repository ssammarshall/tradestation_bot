from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SymbolDetails:
    """Subset of GET /v3/marketdata/symbols/{symbols} response we care about."""
    symbol: str
    point_value: float

    @classmethod
    def from_dict(cls, data: dict) -> SymbolDetails:
        price_format = data.get("PriceFormat", {}) or {}
        return cls(
            symbol=data["Symbol"],
            point_value=float(price_format.get("PointValue", "1")),
        )


@dataclass
class SymbolDetailsResponse:
    symbols: list[SymbolDetails] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> SymbolDetailsResponse:
        return cls(symbols=[SymbolDetails.from_dict(s) for s in data.get("Symbols", [])])
