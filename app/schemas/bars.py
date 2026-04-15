from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BarUnit(str, Enum):
    """Aggregation unit for bar requests."""
    MINUTE = "Minute"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"


class SessionTemplate(str, Enum):
    """Trading session filter applied to bar data."""
    DEFAULT = "Default"
    US_EQ_PRE_AND_POST = "USEQPreAndPost"
    US_EQ_PRE = "USEQPre"
    US_EQ_POST = "USEQPost"
    US_EQ_24_HOUR = "USEQ24Hour"


class BarStatus(str, Enum):
    """Whether the bar is still forming or complete."""
    OPEN = "Open"
    CLOSED = "Closed"


# ---------------------------------------------------------------------------
# Request parameters
# ---------------------------------------------------------------------------

@dataclass
class BarHistoryParams:
    """
    Query parameters for GET /v3/marketdata/barcharts/{symbol}
    and GET /v3/marketdata/stream/barcharts/{symbol}.

    Either (barsback) or (firstdate) must be supplied — not both.
    """
    symbol: str
    unit: BarUnit = BarUnit.DAILY
    interval: int = 1
    barsback: Optional[int] = None
    firstdate: Optional[str] = None   # ISO 8601, e.g. "2024-01-01T00:00:00Z"
    lastdate: Optional[str] = None    # ISO 8601; defaults to now when omitted
    session_template: SessionTemplate = SessionTemplate.DEFAULT

    def to_query_params(self) -> dict:
        """Return a dict suitable for use as HTTP query parameters."""
        params: dict = {
            "unit": self.unit.value,
            "interval": self.interval,
            "sessiontemplate": self.session_template.value,
        }
        if self.barsback is not None:
            params["barsback"] = self.barsback
        if self.firstdate is not None:
            params["firstdate"] = self.firstdate
        if self.lastdate is not None:
            params["lastdate"] = self.lastdate
        return params


# ---------------------------------------------------------------------------
# Bar data object
# ---------------------------------------------------------------------------

@dataclass
class Bar:
    """
    A single OHLCV bar returned by the TradeStation market data API.

    All price and volume fields come back as strings from the API to
    preserve decimal precision; use the helper properties to get floats.
    """
    # Core OHLCV
    open: str
    high: str
    low: str
    close: str
    total_volume: str

    # Timing
    timestamp: str          # ISO 8601, e.g. "2024-01-02T09:30:00-05:00"
    epoch: int              # Unix timestamp in milliseconds

    # Optional fields (not always present)
    down_volume: str = "0"
    open_interest: str = "0"
    net_change: str = "0"
    percent_change: str = "0"

    # Status flags
    bar_status: BarStatus = BarStatus.CLOSED
    is_realtime: bool = False
    is_end_of_history: bool = False

    # ------------------------------------------------------------------
    # Float accessors
    # ------------------------------------------------------------------

    @property
    def open_f(self) -> float:
        return float(self.open)

    @property
    def high_f(self) -> float:
        return float(self.high)

    @property
    def low_f(self) -> float:
        return float(self.low)

    @property
    def close_f(self) -> float:
        return float(self.close)

    @property
    def total_volume_f(self) -> float:
        return float(self.total_volume)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> Bar:
        """Parse a bar object from a raw API response dictionary."""
        return cls(
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            total_volume=data.get("TotalVolume", "0"),
            timestamp=data["TimeStamp"],
            epoch=int(data.get("Epoch", 0)),
            down_volume=data.get("DownVolume", "0"),
            open_interest=data.get("OpenInterest", "0"),
            net_change=data.get("NetChange", "0"),
            percent_change=data.get("PercentChange", "0"),
            bar_status=BarStatus(data.get("BarStatus", BarStatus.CLOSED.value)),
            is_realtime=bool(data.get("IsRealtime", False)),
            is_end_of_history=bool(data.get("IsEndOfHistory", False)),
        )


# ---------------------------------------------------------------------------
# Response wrappers
# ---------------------------------------------------------------------------

@dataclass
class BarsResponse:
    """Parsed response from GET /v3/marketdata/barcharts/{symbol}."""
    bars: list[Bar] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> BarsResponse:
        bars = [Bar.from_dict(b) for b in data.get("Bars", [])]
        return cls(bars=bars)


@dataclass
class StreamBarEvent:
    """
    A single event from the streaming bar endpoint.

    The stream sends either a bar update or a heartbeat/status message.
    Check ``is_bar`` before accessing ``bar``.
    """
    raw: dict
    bar: Optional[Bar] = None
    heartbeat: Optional[str] = None   # value of "Heartbeat" field if present
    error: Optional[str] = None       # value of "Error" field if present

    @property
    def is_bar(self) -> bool:
        return self.bar is not None

    @property
    def is_heartbeat(self) -> bool:
        return self.heartbeat is not None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @classmethod
    def from_dict(cls, data: dict) -> StreamBarEvent:
        if "Open" in data:
            return cls(raw=data, bar=Bar.from_dict(data))
        if "Heartbeat" in data:
            return cls(raw=data, heartbeat=str(data["Heartbeat"]))
        if "Error" in data:
            return cls(raw=data, error=str(data["Error"]))
        return cls(raw=data)
