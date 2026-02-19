from __future__ import annotations

from typing import Any

import pandas as pd

from xauusd_bot.models import Bias, BiasContext, Confirmation, M15Context


def evaluate_m15_confirmation(
    m15_history: pd.DataFrame,
    bias_context: BiasContext,
    params: dict[str, Any],
) -> M15Context:
    if bias_context.bias == Bias.NONE:
        return M15Context(confirmation=Confirmation.NO, reason="NO_H1_BIAS")

    if len(m15_history) < 4:
        return M15Context(confirmation=Confirmation.NO, reason="NOT_ENOUGH_BARS")
    required = {"close", "ema20_m15", "rsi14_m15", "timestamp"}
    if not required.issubset(set(m15_history.columns)):
        return M15Context(confirmation=Confirmation.NO, reason="M15_COLUMNS_MISSING")

    valid_bars = int(params.get("confirm_valid_m15_bars", 3))
    df = m15_history.reset_index(drop=True)

    pullback_active = False
    pullback_rsi_ok = False
    pullback_start_idx: int | None = None
    confirm_idx: int | None = None
    confirm_time: pd.Timestamp | None = None

    rsi_pullback_long_max = float(params.get("rsi_pullback_long_max", 35.0))
    rsi_recover_long_min = float(params.get("rsi_recover_long_min", 40.0))
    rsi_pullback_short_min = float(params.get("rsi_pullback_short_min", 65.0))
    rsi_recover_short_max = float(params.get("rsi_recover_short_max", 60.0))

    for i, row in df.iterrows():
        close = float(row["close"])
        ema = float(row["ema20_m15"])
        rsi = float(row["rsi14_m15"]) if pd.notna(row["rsi14_m15"]) else float("nan")

        if bias_context.bias == Bias.LONG:
            if close <= ema:
                if not pullback_active:
                    pullback_start_idx = int(i)
                pullback_active = True
                confirm_idx = None
                confirm_time = None
            if pullback_active and pd.notna(rsi) and rsi <= rsi_pullback_long_max:
                pullback_rsi_ok = True
            if (
                pullback_active
                and pullback_rsi_ok
                and close > ema
                and pd.notna(rsi)
                and rsi >= rsi_recover_long_min
            ):
                confirm_idx = int(i)
                confirm_time = pd.Timestamp(row["timestamp"])
                pullback_active = False
                pullback_rsi_ok = False
        else:
            if close >= ema:
                if not pullback_active:
                    pullback_start_idx = int(i)
                pullback_active = True
                confirm_idx = None
                confirm_time = None
            if pullback_active and pd.notna(rsi) and rsi >= rsi_pullback_short_min:
                pullback_rsi_ok = True
            if (
                pullback_active
                and pullback_rsi_ok
                and close < ema
                and pd.notna(rsi)
                and rsi <= rsi_recover_short_max
            ):
                confirm_idx = int(i)
                confirm_time = pd.Timestamp(row["timestamp"])
                pullback_active = False
                pullback_rsi_ok = False

    if confirm_idx is None:
        reason = "M15_CONFIRM_NOT_READY"
        if pullback_start_idx is not None:
            reason = "M15_PULLBACK_RSI_OK" if pullback_rsi_ok else "M15_PULLBACK_STARTED"
        return M15Context(
            confirmation=Confirmation.NO,
            touched_zone=pullback_start_idx is not None,
            pullback_start_time=pd.Timestamp(df.iloc[pullback_start_idx]["timestamp"]).to_pydatetime()
            if pullback_start_idx is not None
            else None,
            reason=reason,
        )

    bars_since_confirm = (len(df) - 1) - confirm_idx
    if bars_since_confirm >= valid_bars:
        return M15Context(
            confirmation=Confirmation.NO,
            touched_zone=True,
            pullback_start_time=pd.Timestamp(df.iloc[pullback_start_idx]["timestamp"]).to_pydatetime()
            if pullback_start_idx is not None
            else None,
            confirmation_time=(confirm_time or pd.Timestamp(df.iloc[confirm_idx]["timestamp"])).to_pydatetime(),
            reason="M15_CONFIRM_EXPIRED",
        )

    return M15Context(
        confirmation=Confirmation.OK,
        touched_zone=True,
        pullback_start_time=pd.Timestamp(df.iloc[pullback_start_idx]["timestamp"]).to_pydatetime()
        if pullback_start_idx is not None
        else None,
        confirmation_time=(confirm_time or pd.Timestamp(df.iloc[confirm_idx]["timestamp"])).to_pydatetime(),
        reason="M15_CONFIRM_OK",
    )
