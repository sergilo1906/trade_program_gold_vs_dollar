from __future__ import annotations

from typing import Any

import pandas as pd

from xauusd_bot.models import Bias, BiasContext


def evaluate_h1_bias(h1_history: pd.DataFrame, params: dict[str, Any]) -> BiasContext:
    lookback = int(params.get("h1_bias_slope_lookback", 3))
    atr_mult = float(params.get("h1_bias_atr_mult", 0.10))
    min_sep_atr_mult = float(params.get("h1_min_sep_atr_mult", 0.25))

    if len(h1_history) < max(lookback + 1, 5):
        return BiasContext(bias=Bias.NONE, reason="NOT_ENOUGH_BARS")

    required = {"ema50_h1", "ema200_h1", "atr_h1", "close"}
    if not required.issubset(set(h1_history.columns)):
        return BiasContext(bias=Bias.NONE, reason="H1_COLUMNS_MISSING")

    row = h1_history.iloc[-1]
    ema_fast = float(row["ema50_h1"])
    ema_slow = float(row["ema200_h1"])
    close = float(row["close"])
    atr = float(row["atr_h1"]) if pd.notna(row["atr_h1"]) else 0.0
    ema_fast_prev = float(h1_history.iloc[-1 - lookback]["ema50_h1"])
    slope = ema_fast - ema_fast_prev

    if pd.isna(ema_fast) or pd.isna(ema_slow):
        return BiasContext(bias=Bias.NONE, reason="H1_EMA_NA")
    ema_sep = abs(ema_fast - ema_slow)
    if ema_sep < (min_sep_atr_mult * atr):
        return BiasContext(bias=Bias.NONE, reason="H1_BIAS_NONE_FLAT")

    if (ema_fast > ema_slow) and (close > ema_slow + (atr_mult * atr)) and (slope > 0):
        return BiasContext(bias=Bias.LONG, reason="H1_BIAS_LONG")
    if (ema_fast < ema_slow) and (close < ema_slow - (atr_mult * atr)) and (slope < 0):
        return BiasContext(bias=Bias.SHORT, reason="H1_BIAS_SHORT")
    return BiasContext(bias=Bias.NONE, reason="H1_BIAS_NONE")
