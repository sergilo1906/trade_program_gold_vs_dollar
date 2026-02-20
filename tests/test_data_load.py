from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from xauusd_bot.data_loader import load_m5_csv


def test_load_m5_csv_happy_path(tmp_path: Path) -> None:
    csv_path = tmp_path / "ok.csv"
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 00:00:00", "2024-01-01 00:05:00", "2024-01-01 00:10:00"],
            "open": [2000.0, 2000.2, 2000.1],
            "high": [2000.3, 2000.4, 2000.5],
            "low": [1999.9, 2000.0, 1999.8],
            "close": [2000.2, 2000.1, 2000.3],
        }
    )
    df.to_csv(csv_path, index=False)

    out = load_m5_csv(csv_path)
    assert list(out.columns)[:5] == ["timestamp", "open", "high", "low", "close"]
    assert len(out) == 3
    assert out["timestamp"].is_monotonic_increasing


def test_load_m5_csv_missing_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad.csv"
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 00:00:00"],
            "open": [2000.0],
            "high": [2000.3],
            "close": [2000.2],
        }
    )
    df.to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        _ = load_m5_csv(csv_path)
