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


def atr(bars: list[Bar], period: int = 14) -> float | None:
    if len(bars) < period + 1:
        return None
    true_ranges: list[float] = []
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close_f
        high = bars[i].high_f
        low = bars[i].low_f
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return sum(true_ranges[-period:]) / period


@dataclass
class FVG:
    is_bullish: bool
    bar_1: Bar
    bar_2: Bar
    bar_3: Bar
    range_f: float


def detect_fvgs(bars: list[Bar]) -> list[FVG]:
    fvgs: list[FVG] = []
    for i in range(1, len(bars) - 1):
        prev_bar = bars[i - 1]
        mid_bar = bars[i]
        next_bar = bars[i + 1]

        if next_bar.low_f > prev_bar.high_f:
            fvgs.append(FVG(True, prev_bar, mid_bar, next_bar, next_bar.low_f - prev_bar.high_f))
        elif next_bar.high_f < prev_bar.low_f:
            fvgs.append(FVG(False, prev_bar, mid_bar, next_bar, prev_bar.low_f - next_bar.high_f))

    return fvgs


def detect_ifvg(fvg: FVG, bar: Bar) -> bool:
    if bar.timestamp in (fvg.bar_1.timestamp, fvg.bar_2.timestamp, fvg.bar_3.timestamp):
        # Bars that formed the FVG cannot be the one to invert it
        return False

    if fvg.is_bullish:
        return (
            not is_bullish_bar(bar)
            and fvg.bar_3.low_f < bar.open_f
            and fvg.bar_1.high_f > bar.close_f
        )
    return (
        is_bullish_bar(bar)
        and fvg.bar_3.high_f > bar.open_f
        and fvg.bar_1.low_f < bar.close_f
    )
