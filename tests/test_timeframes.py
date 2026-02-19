from __future__ import annotations

import pandas as pd

from xauusd_bot.timeframes import resample_from_m5


def test_resample_m5_to_m15_and_h1_counts() -> None:
    timestamps = pd.date_range("2026-01-01 00:05:00", periods=24, freq="5min")
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [1.0] * 24,
            "high": [2.0] * 24,
            "low": [0.5] * 24,
            "close": [1.5] * 24,
            "volume": [10] * 24,
        }
    )

    m15 = resample_from_m5(df, "15min")
    h1 = resample_from_m5(df, "1h")

    assert len(m15) == 8
    assert len(h1) == 2
