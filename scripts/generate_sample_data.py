from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_sample(rows: int = 620, seed: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2026-01-06 00:05:00", periods=rows, freq="5min")

    closes: list[float] = []
    price = 2620.0
    for i in range(rows):
        if i < 120:
            drift = 0.18
        elif i < 180:
            drift = -0.14
        elif i < 280:
            drift = 0.22
        elif i < 360:
            drift = -0.10
        elif i < 470:
            drift = 0.17
        elif i < 540:
            drift = -0.16
        else:
            drift = 0.20

        wave = 0.45 * np.sin(i / 4.8)
        noise = rng.normal(0.0, 0.04)
        price = price + drift + wave + noise
        closes.append(float(price))

    opens = [closes[0]] + closes[:-1]
    highs = []
    lows = []
    volumes = []
    spreads = []
    bids = []
    asks = []
    for o, c in zip(opens, closes):
        wiggle_high = abs(rng.normal(0.10, 0.03))
        wiggle_low = abs(rng.normal(0.10, 0.03))
        high = max(o, c) + wiggle_high
        low = min(o, c) - wiggle_low

        spread = float(np.clip(rng.normal(0.22, 0.06), 0.05, 0.50))
        bid = c - (spread / 2.0)
        ask = c + (spread / 2.0)

        highs.append(high)
        lows.append(low)
        volumes.append(120)
        spreads.append(spread)
        bids.append(bid)
        asks.append(ask)

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
            "spread": spreads,
            "bid": bids,
            "ask": asks,
        }
    )
    return df


def main() -> None:
    output = Path("data") / "sample_m5.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    df = build_sample()
    tmp_output = output.with_suffix(output.suffix + ".tmp")
    df.to_csv(tmp_output, index=False)
    tmp_output.replace(output)
    print(f"Wrote {len(df)} rows to {output}")


if __name__ == "__main__":
    main()
