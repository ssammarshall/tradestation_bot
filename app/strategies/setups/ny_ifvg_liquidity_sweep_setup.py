from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import assert_never

from app.schemas.bars import Bar, BarHistoryParams, BarHistoryRequest, BarUnit
from app.schemas.signals import EntrySignal
from app.strategies.analyzers.bar_analysis import FVG, atr, is_bullish_bar, is_impulsive_bar, period_high_low, detect_fvgs, detect_ifvg
from app.strategies.setups.base_setup import BaseSetup


class Phase(str, Enum):
    SCANNING = "scanning"               # Waiting for a sweep of any level
    DETECTING_IFVG = "detecting_ifvg"   # Bars received, IFVG detection
    CONFIRMED = "confirmed"             # Setup confirmed, waiting for entry trigger


class NYIFVGLiquiditySweepSetup(BaseSetup):
    def __init__(self, symbol: str, risk_reward_ratio: float = 1.5) -> None:
        super().__init__(symbol, risk_reward_ratio)

        # (high, low) for the previous day, Asia session, and London session.
        # A side is set to None once it has been swept by a later session.
        self.previous_day: tuple[float | None, float | None] = (None, None)
        self.asia: tuple[float | None, float | None] = (None, None)
        self.london: tuple[float | None, float | None] = (None, None)
        self.current_session: tuple[float | None, float | None] = (None, None)
        # (high_valid, low_valid) - a current_session side only counts as a
        # sweep target once it has surpassed a previous session level.
        self.current_session_valid: tuple[bool, bool] = (False, False)
        self.current_day: date | None = None

        self.entered_liquidity_timestamp: datetime | None = None
        self.is_bullish_sweep: bool | None = None
        self.grace_period_start: datetime | None = None
        self.grace_period: timedelta = timedelta(minutes=10)
        self.bars_since_sweep: list[Bar] | None = None
        self.phase: Phase = Phase.SCANNING

        self.atr_period: int = 20
        self.min_atr: float = 28.0
        self.min_gap_ratio: float = 0.15

    def history_params(self) -> BarHistoryParams:
        now = datetime.now(timezone.utc)
        start = datetime.combine(
            now.date() - timedelta(days=1), time(0, 0), tzinfo=timezone.utc
        )
        minutes_back = int((now - start).total_seconds() // 60) + 1
        return BarHistoryParams(
            symbol=self.symbol,
            unit=BarUnit.MINUTE,
            interval=1,
            barsback=minutes_back
        )

    def startup(self, bars: list[Bar]) -> None:
        self.previous_day = (None, None)
        self.asia = (None, None)
        self.london = (None, None)
        self.current_session = (None, None)
        self.current_session_valid = (False, False)

        if not bars:
            return
        self.log.debug("history returned %d bars, first=%s, last=%s", len(bars), bars[0].timestamp, bars[-1].timestamp)
        last_ts = datetime.fromisoformat(bars[-1].timestamp).astimezone(timezone.utc)
        today = last_ts.date()
        prev_day = today - timedelta(days=1)

        prev_day_bars: list[Bar] = []
        asia_bars: list[Bar] = []
        london_bars: list[Bar] = []

        for bar in bars:
            ts = datetime.fromisoformat(bar.timestamp).astimezone(timezone.utc)
            if ts.date() == prev_day:
                prev_day_bars.append(bar)
            elif ts.date() == today:
                if time(0, 0) <= ts.time() < time(8, 0):
                    asia_bars.append(bar)
                elif time(8, 0) <= ts.time() < time(13, 0):
                    london_bars.append(bar)

        if prev_day_bars:
            self.log.debug("received %d previous day bars", len(prev_day_bars))
            self.previous_day = period_high_low(prev_day_bars)
        if asia_bars:
            self.log.debug("received %d Asia session bars", len(asia_bars))
            self.asia = period_high_low(asia_bars)
        if london_bars:
            self.log.debug("received %d London session bars", len(london_bars))
            self.london = period_high_low(london_bars)

        self._discard_swept_levels()
        self.current_day = today

        self.log.debug("previous day high/low: %s", self.previous_day)
        self.log.debug("asia session high/low: %s", self.asia)
        self.log.debug("london session high/low: %s", self.london)

    def is_valid(self, bar: Bar) -> bool:
        # Snapshot before updating so sweep checks compare the bar's close
        # against the session high/low up to (but not including) this bar.
        # Mask out current_session sides that have not yet surpassed a prior
        # session level - those are internal range, not sweepable liquidity.
        cur_high, cur_low = self.current_session
        high_valid, low_valid = self.current_session_valid
        prev_session = (
            cur_high if high_valid else None,
            cur_low if low_valid else None,
        )
        self._update_current_session(bar)

        match self.phase:
            case Phase.SCANNING:
                self.log.debug("scanning - bar=%s O:%s H:%s L:%s C:%s", bar.timestamp, bar.open_f, bar.high_f, bar.low_f, bar.close_f)
                return self._scan(bar, prev_session)
            case Phase.DETECTING_IFVG:
                self.log.debug("detecting ifvg - bar=%s O:%s H:%s L:%s C:%s", bar.timestamp, bar.open_f, bar.high_f, bar.low_f, bar.close_f)
                return self._detect(bar)
            case _:
                assert_never(self.phase)

    def receive_bars(self, bars: list[Bar]) -> None:
        self.bars_since_sweep = bars

    def reset(self) -> None:
        super().reset()
        self.phase = Phase.SCANNING
        self.entered_liquidity_timestamp = None
        self.is_bullish_sweep = None
        self.grace_period_start = None
        self.bars_since_sweep = None

    # In SCANNING, we wait for a sweep of any level. Once we see a sweep, we request bars for IFVG detection.
    def _scan(self, bar: Bar, prev_session: tuple[float | None, float | None]) -> bool:
        bar_time = datetime.fromisoformat(bar.timestamp).astimezone(timezone.utc)
        sessions = (self.previous_day, self.asia, self.london, prev_session)
        swept_high, swept_low = self._check_sweeps(sessions, bar.close_f)

        # Check if the bar sweeps any of the key levels
        if swept_high or swept_low:
            self.grace_period_start = None
            if swept_high: self.log.debug("swept high")
            if swept_low: self.log.debug("swept low")
            # If we've entered liquidity, record the sweep and it's direction
            if self.entered_liquidity_timestamp is None:
                self.log.debug("entered liquidity, recording sweep")
                self.entered_liquidity_timestamp = bar_time
                self.is_bullish_sweep = swept_high
        elif self.entered_liquidity_timestamp is not None:
            # If we've exited liquidity, check the grace period
            if self.grace_period_start is None:
                # Start the grace period timer and continue
                self.log.debug("start grace period")
                self.grace_period_start = bar_time
            else:
                # If grace period has expired, reset everything and return False
                if bar_time - self.grace_period_start >= self.grace_period:
                    self.log.debug("grace period expired, resetting")
                    self.reset()
                    return False
        else:
            # If we aren't in liquidity and have no grace period, discard swept levels and return
            self._discard_swept_levels()
            self.log.debug("no sweep detected, discard swept levels and return")
            return False

        # Inverse fair value gaps must be formed by impulsive bars
        if not is_impulsive_bar(bar):
            self.log.debug("bar is not impulsive, return")
            return False

        # The impulsive bar must be in the opposite direction of the sweep
        if is_bullish_bar(bar) == self.is_bullish_sweep:
            self.log.debug("bar is in the same direction of the sweep, return")
            return False

        # Request bars from the sweep entry through the current bar for IFVG detection
        minutes_back = int(
            (bar_time - self.entered_liquidity_timestamp).total_seconds() // 60
        ) + 1
        if minutes_back < 3:
            self.log.debug("not enough bars since sweep entry for ifvg detection (minutes_back=%d)", minutes_back)
            return False
        # Guarantee enough bars for an accurate ATR calc at the current bar
        minutes_back = max(minutes_back, self.atr_period + 1)
        
        self._emit_history_request(minutes_back)
        self.phase = Phase.DETECTING_IFVG
        return False

    # In DETECTING_IFVG, we scan bars_since_sweep for the IFVG pattern
    def _detect(self, bar: Bar) -> bool:
        assert self.bars_since_sweep is not None
        atr_value = atr(self.bars_since_sweep, period=self.atr_period)
        if atr_value is None or atr_value < self.min_atr:
            self.log.debug("atr volatility floor not met (atr=%s, min=%s), resetting", atr_value, self.min_atr)
            self.reset()
            return False
        fvgs = detect_fvgs(self.bars_since_sweep)
        for fvg in fvgs:
            if fvg.is_bullish != self.is_bullish_sweep:
                continue
            if fvg.gap_ratio < self.min_gap_ratio:
                self.log.debug("fvg gap ratio %.3f below min %.3f, skipping", fvg.gap_ratio, self.min_gap_ratio)
                continue
            if detect_ifvg(fvg, bar):
                self.log.info("confirmed ifvg at %s, fvg inverted: %s", bar.timestamp, fvg.bar_3.timestamp)
                signal = self._build_signal(fvg, bar)
                self.log.debug("emitting entry signal: target_price=%s, stop_loss=%s, take_profit=%s", signal.target_price, signal.stop_loss, signal.take_profit)
                self.pending_signal = signal
                self.phase = Phase.CONFIRMED
                return True
        self.log.debug("no ifvg detected, resetting")
        self.reset()
        return False

    def _build_signal(self, fvg: FVG, bar: Bar) -> EntrySignal:
        target_price = Decimal(fvg.bar_2.open)
        resistance_level: Decimal | None = None
        support_level: Decimal | None = None
        ratio = Decimal(str(self.risk_reward_ratio))
        if fvg.is_bullish:
            resistance_level = Decimal(bar.open)
            stop_loss = Decimal(fvg.bar_3.high)
            take_profit = target_price - (stop_loss - target_price) * ratio
        else:
            support_level = Decimal(bar.open)
            stop_loss = Decimal(fvg.bar_3.low)
            take_profit = target_price + (target_price - stop_loss) * ratio

        return EntrySignal(
            is_bullish=not self.is_bullish_sweep,
            target_price=target_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            resistance_level=resistance_level,
            support_level=support_level,
        )

    def _emit_history_request(self, minutes_back: int) -> None:
        self.log.debug("emitting history request for %d minutes of bars since sweep entry", minutes_back)
        self.pending_request = BarHistoryRequest(
            params=BarHistoryParams(
                symbol=self.symbol,
                unit=BarUnit.MINUTE,
                interval=1,
                barsback=minutes_back,
            )
        )

    def _check_sweeps(
        self,
        sessions: tuple[tuple[float | None, float | None], ...],
        close: float,
    ) -> tuple[bool, bool]:
        swept_high = any(h is not None and close > h for h, _ in sessions)
        swept_low = any(l is not None and close < l for _, l in sessions)
        return swept_high, swept_low

    def _discard_swept_levels(self) -> None:
        # Earlier sessions get their high/low cleared if a later session swept it.
        sessions = ["previous_day", "asia", "london", "current_session"]
        for i, earlier in enumerate(sessions):
            high, low = getattr(self, earlier)
            for later in sessions[i + 1:]:
                later_high, later_low = getattr(self, later)
                if high is not None and later_high is not None and later_high > high:
                    high = None
                if low is not None and later_low is not None and later_low < low:
                    low = None
            setattr(self, earlier, (high, low))

    def _update_current_session(self, bar: Bar) -> None:
        bar_date = datetime.fromisoformat(bar.timestamp).astimezone(timezone.utc).date()
        if self.current_day is not None and bar_date != self.current_day:
            self._rollover_day()
        self.current_day = bar_date
        cur_high, cur_low = self.current_session
        new_high = bar.high_f if cur_high is None else max(cur_high, bar.high_f)
        new_low = bar.low_f if cur_low is None else min(cur_low, bar.low_f)
        self.current_session = (new_high, new_low)

        # A current_session side becomes a valid sweep target once it has
        # surpassed a previous session high/low. The flag is sticky for the
        # rest of the session - a level that swept liquidity stays sweepable
        # even after that prior level is discarded by _discard_swept_levels.
        prior = (self.previous_day, self.asia, self.london)
        high_valid, low_valid = self.current_session_valid
        if not high_valid and any(h is not None and new_high > h for h, _ in prior):
            high_valid = True
        if not low_valid and any(l is not None and new_low < l for _, l in prior):
            low_valid = True
        self.current_session_valid = (high_valid, low_valid)

    def _rollover_day(self) -> None:
        # Collapse yesterday's asia/london/NY ranges into previous_day, then clear
        # today's sessions so current_session starts fresh for the new day.
        self.log.debug("day rollover from %s", self.current_day)
        sessions = (self.asia, self.london, self.current_session)
        highs = [h for h, _ in sessions if h is not None]
        lows = [l for _, l in sessions if l is not None]
        self.previous_day = (
            max(highs) if highs else None,
            min(lows) if lows else None,
        )
        self.asia = (None, None)
        self.london = (None, None)
        self.current_session = (None, None)
        self.current_session_valid = (False, False)