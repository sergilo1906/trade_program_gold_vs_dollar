from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """EMA with SMA(period) initialization."""
    n = max(int(period), 1)
    out = pd.Series(index=series.index, dtype="float64")
    if series.empty:
        return out

    values = series.astype(float).to_list()
    if len(values) < n:
        return out

    k = 2.0 / (n + 1.0)
    sma = sum(values[:n]) / n
    out.iloc[n - 1] = sma
    prev = sma
    for i in range(n, len(values)):
        prev = (values[i] * k) + (prev * (1.0 - k))
        out.iloc[i] = prev
    return out


def true_range(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="float64")

    high = df[high_col].astype(float)
    low = df[low_col].astype(float)
    close = df[close_col].astype(float)
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.astype(float)


def atr_wilder(
    df: pd.DataFrame,
    period: int,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """ATR Wilder with explicit init mean(TR first n)."""
    n = max(int(period), 1)
    tr = true_range(df, high_col=high_col, low_col=low_col, close_col=close_col)
    out = pd.Series(index=tr.index, dtype="float64")
    if tr.empty or len(tr) < n:
        return out

    values = tr.to_list()
    seed = sum(values[:n]) / n
    out.iloc[n - 1] = seed
    prev = seed
    for i in range(n, len(values)):
        prev = ((prev * (n - 1)) + values[i]) / n
        out.iloc[i] = prev
    return out


def atr(
    df: pd.DataFrame,
    period: int,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    return atr_wilder(df=df, period=period, high_col=high_col, low_col=low_col, close_col=close_col)


def rsi_wilder(series: pd.Series, period: int) -> pd.Series:
    n = max(int(period), 1)
    out = pd.Series(index=series.index, dtype="float64")
    if series.empty:
        return out

    values = series.astype(float).to_list()
    if len(values) <= n:
        return out

    gains: list[float] = [0.0]
    losses: list[float] = [0.0]
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains[1 : n + 1]) / n
    avg_loss = sum(losses[1 : n + 1]) / n
    if avg_loss == 0.0:
        out.iloc[n] = 100.0 if avg_gain > 0.0 else 50.0
    else:
        rs = avg_gain / avg_loss
        out.iloc[n] = 100.0 - (100.0 / (1.0 + rs))

    prev_gain = avg_gain
    prev_loss = avg_loss
    for i in range(n + 1, len(values)):
        prev_gain = ((prev_gain * (n - 1)) + gains[i]) / n
        prev_loss = ((prev_loss * (n - 1)) + losses[i]) / n
        if prev_loss == 0.0:
            out.iloc[i] = 100.0 if prev_gain > 0.0 else 50.0
        else:
            rs = prev_gain / prev_loss
            out.iloc[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def rolling_high(series: pd.Series, lookback: int) -> pd.Series:
    n = max(int(lookback), 1)
    return series.astype(float).rolling(window=n, min_periods=n).max()


def rolling_low(series: pd.Series, lookback: int) -> pd.Series:
    n = max(int(lookback), 1)
    return series.astype(float).rolling(window=n, min_periods=n).min()


def detect_swings(df: pd.DataFrame, k: int) -> tuple[pd.Series, pd.Series]:
    if df.empty:
        empty = pd.Series(dtype="bool")
        return empty, empty

    window = 2 * k + 1
    highs = df["high"].astype(float)
    lows = df["low"].astype(float)

    swing_high = highs.eq(highs.rolling(window=window, center=True).max())
    swing_low = lows.eq(lows.rolling(window=window, center=True).min())

    swing_high = swing_high.fillna(False)
    swing_low = swing_low.fillna(False)

    if k > 0 and len(df) > 2 * k:
        swing_high.iloc[:k] = False
        swing_high.iloc[-k:] = False
        swing_low.iloc[:k] = False
        swing_low.iloc[-k:] = False

    return swing_high.astype(bool), swing_low.astype(bool)


def last_swing_index_before(flags: pd.Series, before_idx: int) -> int | None:
    if before_idx <= 0 or flags.empty:
        return None
    candidates = flags.iloc[:before_idx]
    true_idx = candidates[candidates].index
    if len(true_idx) == 0:
        return None
    return int(true_idx[-1])
