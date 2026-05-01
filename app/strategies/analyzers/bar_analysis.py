from __future__ import annotations

from dataclasses import dataclass

from app.schemas.bars import Bar


def period_high(bars: list[Bar]) -> float:
    return max(bar.high_f for bar in bars)


def period_low(bars: list[Bar]) -> float:
    return min(bar.low_f for bar in bars)


def period_high_low(bars: list[Bar]) -> tuple[float, float]:
    return period_high(bars), period_low(bars)


@dataclass
class FVG:
    is_bullish = True
    top: float
    bottom: float
    timestamp: str  # timestamp of the last bar


def detect_fvgs(bars: list[Bar]) -> list[FVG]:
    fvgs: list[FVG] = []
    for i in range(1, len(bars) - 1):
        prev_high = bars[i - 1].high_f
        prev_low = bars[i - 1].low_f
        next_high = bars[i + 1].high_f
        next_low = bars[i + 1].low_f

        if next_low > prev_high:
            fvgs.append(FVG(True, next_low, prev_high, bars[i+1].timestamp))
        elif next_high < prev_low:
            fvgs.append(FVG(False, prev_low, next_high, bars[i+1].timestamp))

    return fvgs
