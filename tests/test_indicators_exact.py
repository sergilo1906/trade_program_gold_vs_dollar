from __future__ import annotations

import pandas as pd

from xauusd_bot.indicators import atr_wilder, ema


def test_ema_uses_sma_initialization() -> None:
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = ema(series, period=3)
    assert pd.isna(out.iloc[0])
    assert pd.isna(out.iloc[1])
    assert out.iloc[2] == 2.0  # SMA(1,2,3)
    assert out.iloc[3] == 3.0  # 0.5*4 + 0.5*2
    assert out.iloc[4] == 4.0  # 0.5*5 + 0.5*3


def test_atr_wilder_matches_expected_small_series() -> None:
    df = pd.DataFrame(
        {
            "high": [10.0, 12.0, 13.0],
            "low": [8.0, 9.0, 11.0],
            "close": [9.0, 11.0, 12.0],
        }
    )
    out = atr_wilder(df, period=2)
    # TR = [2, 3, 2]
    # ATR[1] = (2+3)/2 = 2.5
    # ATR[2] = (2.5*(2-1) + 2)/2 = 2.25
    assert pd.isna(out.iloc[0])
    assert abs(float(out.iloc[1]) - 2.5) < 1e-9
    assert abs(float(out.iloc[2]) - 2.25) < 1e-9
