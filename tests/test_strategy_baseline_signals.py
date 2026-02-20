from __future__ import annotations

from pathlib import Path

import pandas as pd

from xauusd_bot.configuration import load_config
from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger


def _build_orb_friendly_data(days: int = 4) -> pd.DataFrame:
    ts = pd.date_range("2024-01-08 00:00:00", periods=days * 24 * 12, freq="5min")
    closes: list[float] = []
    for t in ts:
        day_base = 2000.0 + float((t.normalize() - ts[0].normalize()).days) * 1.5
        minute = int(t.hour) * 60 + int(t.minute)
        if minute <= 30:
            close = day_base + ((minute / 5.0) % 3) * 0.02
        elif minute < 12 * 60:
            close = day_base + 1.8 + (minute - 35) * 0.004
        else:
            close = day_base - 1.6 - (minute - 12 * 60) * 0.003
        closes.append(float(close))

    opens = [closes[0]] + closes[:-1]
    highs = [max(o, c) + 0.08 for o, c in zip(opens, closes)]
    lows = [min(o, c) - 0.08 for o, c in zip(opens, closes)]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [100.0] * len(ts),
        }
    )


def test_baseline_smoke_strategy_generates_signals_and_trades(tmp_path: Path) -> None:
    cfg = load_config("configs/config_smoke_baseline.yaml")
    cfg["output_dir"] = str(tmp_path / "output")
    cfg["runs_output_dir"] = str(tmp_path / "runs")

    logger = CsvLogger(output_dir=cfg["output_dir"], reset=True)
    engine = SimulationEngine(config=cfg, logger=logger)
    summary = engine.run(_build_orb_friendly_data())

    events = pd.read_csv(Path(summary["events_path"]))
    trades = pd.read_csv(Path(summary["trades_path"]))

    assert len(events) > 0
    assert (events["event_type"].astype(str).str.contains("V4_SIGNAL_ORB_BREAKOUT", regex=False)).any()
    assert len(trades) > 0
