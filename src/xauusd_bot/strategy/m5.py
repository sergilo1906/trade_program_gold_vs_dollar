from __future__ import annotations

from typing import Any

import pandas as pd

from xauusd_bot.models import Bias, BiasContext, Confirmation, EntrySetup, EntrySignal, M15Context


def evaluate_m5_entry(
    m5_history: pd.DataFrame,
    bias_context: BiasContext,
    m15_context: M15Context,
    params: dict[str, Any],
) -> tuple[EntrySignal, EntrySetup | None]:
    if bias_context.bias == Bias.NONE or m15_context.confirmation != Confirmation.OK:
        return EntrySignal.NONE, None
    if len(m5_history) < 8:
        return EntrySignal.NONE, None

    required = {"open", "high", "low", "close", "ema20_m5", "atr_m5", "timestamp"}
    if not required.issubset(set(m5_history.columns)):
        return EntrySignal.NONE, None

    bos_lookback = int(params.get("bos_lookback", 5))
    body_ratio_min = float(params.get("body_ratio", 0.70))
    wick_ratio_max = float(params.get("wick_ratio_max", 0.20))
    swing_lookback = int(params.get("swing_lookback", 6))
    if len(m5_history) < max(bos_lookback + 1, swing_lookback):
        return EntrySignal.NONE, None

    df = m5_history.reset_index(drop=True)
    last = df.iloc[-1]
    prev_window = df.iloc[-1 - bos_lookback : -1]
    if prev_window.empty:
        return EntrySignal.NONE, None

    hh = float(prev_window["high"].max())
    ll = float(prev_window["low"].min())
    close = float(last["close"])
    open_ = float(last["open"])
    high = float(last["high"])
    low = float(last["low"])
    ema = float(last["ema20_m5"]) if pd.notna(last["ema20_m5"]) else float("nan")
    atr_now = float(last["atr_m5"]) if pd.notna(last["atr_m5"]) else 0.0

    rng = max(high - low, 0.0)
    body = abs(close - open_)
    ratio = (body / rng) if rng > 0 else 0.0
    strong_bull = (close > open_) and (ratio >= body_ratio_min)
    strong_bear = (close < open_) and (ratio >= body_ratio_min)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low
    wick_ok_long = upper_wick <= (wick_ratio_max * rng) if rng > 0 else False
    wick_ok_short = lower_wick <= (wick_ratio_max * rng) if rng > 0 else False

    swing_window = df.iloc[-swing_lookback:]
    swing_high = float(swing_window["high"].max())
    swing_low = float(swing_window["low"].min())
    setup_time = pd.Timestamp(last["timestamp"]).to_pydatetime()
    setup_index = len(df) - 1

    if bias_context.bias == Bias.LONG:
        if pd.notna(ema) and (close > ema) and (close > hh) and strong_bull and wick_ok_long:
            return (
                EntrySignal.BUY,
                EntrySetup(
                    signal=EntrySignal.BUY,
                    trigger_price=close,
                    micro_swing_high=swing_high,
                    micro_swing_low=swing_low,
                    buffer_micro=atr_now,
                    setup_time=setup_time,
                    setup_index=setup_index,
                ),
            )
        return EntrySignal.NONE, None

    if pd.notna(ema) and (close < ema) and (close < ll) and strong_bear and wick_ok_short:
        return (
            EntrySignal.SELL,
            EntrySetup(
                signal=EntrySignal.SELL,
                trigger_price=close,
                micro_swing_high=swing_high,
                micro_swing_low=swing_low,
                buffer_micro=atr_now,
                setup_time=setup_time,
                setup_index=setup_index,
            ),
        )
    return EntrySignal.NONE, None
