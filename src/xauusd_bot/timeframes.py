from __future__ import annotations

import pandas as pd


def resample_from_m5(m5_df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if m5_df.empty:
        return m5_df.copy()

    df = m5_df.copy()
    df = df.set_index("timestamp")

    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    for optional in ("bid", "ask", "spread"):
        if optional in df.columns:
            agg[optional] = "mean"

    resampled = (
        df.resample(rule, label="right", closed="right")
        .agg(agg)
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return resampled


def closed_bars_count_up_to(resampled_df: pd.DataFrame, current_ts: pd.Timestamp) -> int:
    if resampled_df.empty:
        return 0
    ts_arr = resampled_df["timestamp"].to_numpy()
    end = 0
    while end < len(ts_arr) and pd.Timestamp(ts_arr[end]) <= current_ts:
        end += 1
    return end
