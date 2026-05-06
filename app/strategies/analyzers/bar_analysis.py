from __future__ import annotations

from dataclasses import dataclass

from app.schemas.bars import Bar


def period_high(bars: list[Bar]) -> float:
    return max(bar.high_f for bar in bars)


def period_low(bars: list[Bar]) -> float:
    return min(bar.low_f for bar in bars)


def period_high_low(bars: list[Bar]) -> tuple[float | None, float | None]:
    if not bars:
        return None, None
    return period_high(bars), period_low(bars)


def is_bullish_bar(bar: Bar) -> bool:
    return bar.close_f > bar.open_f


def is_impulsive_bar(bar: Bar, threshold: float = 0.6) -> bool:
    bar_range = bar.high_f - bar.low_f
    if bar_range <= 0:
        return False
    body = abs(bar.close_f - bar.open_f)
    return body / bar_range >= threshold


@dataclass
class FVG:
    is_bullish: bool
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


def detect_ifvg(fvg: FVG, bar: Bar) -> bool:
    if fvg.timestamp == bar.timestamp:
        # Bar that formed the FVG cannot be the one to fill it
        return False
    
    if fvg.is_bullish:
        return (
            not is_bullish_bar(bar)
            and fvg.top < bar.open_f
            and fvg.bottom > bar.close_f
        )
    return (
        is_bullish_bar(bar)
        and fvg.bottom > bar.open_f
        and fvg.top < bar.close_f
    )
