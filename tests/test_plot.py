from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_plot_script_generates_png(tmp_path: Path) -> None:
    data_path = tmp_path / "sample_m5.csv"
    signals_path = tmp_path / "signals.csv"
    output_path = tmp_path / "last_chart.png"

    market = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01 00:05:00", periods=50, freq="5min"),
            "close": [2600 + (i * 0.1) for i in range(50)],
        }
    )
    market.to_csv(data_path, index=False)

    signals = pd.DataFrame(
        {
            "ts": [
                "2026-01-01 01:00:00",
                "2026-01-01 01:05:00",
                "2026-01-01 01:30:00",
            ],
            "event_type": ["SIGNAL_DETECTED", "TRADE_OPEN", "TRADE_CLOSE"],
            "signal": ["BUY", "BUY", "BUY"],
            "entry_price_candidate": ["2601.20", "2601.30", ""],
            "outcome": ["", "", "TP_HIT"],
            "payload_json": ["{}", "{}", '{"exit_price": 2602.10}'],
        }
    )
    signals.to_csv(signals_path, index=False)

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "plot_signals.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--data",
            str(data_path),
            "--signals",
            str(signals_path),
            "--output",
            str(output_path),
            "--bars",
            "50",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Wrote chart to" in result.stdout
    assert output_path.exists()
    assert output_path.stat().st_size > 0
