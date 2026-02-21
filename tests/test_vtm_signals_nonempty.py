from __future__ import annotations

from pathlib import Path

import pandas as pd

from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger


ROOT = Path(__file__).resolve().parents[1]


def test_vtm_generates_signals_and_trades(tmp_path: Path) -> None:
    data_path = ROOT / "data" / "sample_m5.csv"
    assert data_path.exists()
    data = pd.read_csv(data_path)
    data.columns = [str(c).strip().lower() for c in data.columns]
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    data = data.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    cfg = {
        "output_dir": str(tmp_path / "output"),
        "runs_output_dir": str(tmp_path / "runs"),
        "starting_balance": 10000.0,
        "risk_per_trade_pct": 0.005,
        "strategy_family": "VTM_VOL_MR",
        "enable_strategy_v3": False,
        "max_trades_per_day": 8,
        "trend_sessions": ["00:00-23:59"],
        "range_sessions": ["00:00-23:59"],
        "blocked_windows": [],
        "spread_usd": 0.41,
        "slippage_usd": 0.05,
        "cost_max_atr_mult": 4.0,
        "cost_max_sl_frac": 5.0,
        "cost_max_tp_frac_range": 0.9,
        "progress_every_days": 0,
        "vtm_vol_mr": {
            "atr_period": 10,
            "ma_period": 20,
            "threshold_range": 0.8,
            "stop_atr": 0.6,
            "holding_bars": 8,
            "close_extreme_frac": 0.45,
            "vol_filter_min": 0.0,
            "slope_lookback": 6,
            "slope_threshold": 0.0,
            "spread_max_usd": 10.0,
            "exit_on_sma_cross": True,
            "be_trigger_atr": 0.2,
            "entry_windows": ["00:00-23:59"],
            "excluded_windows": [],
        },
    }

    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = SimulationEngine(config=cfg, logger=logger)
    summary = engine.run(data)
    assert summary["closed_trades"] > 0

    events = pd.read_csv(Path(cfg["output_dir"]) / "events.csv")
    trades = pd.read_csv(Path(cfg["output_dir"]) / "trades.csv")
    assert len(trades) > 0
    assert (events["event_type"].astype(str) == "VTM_SIGNAL_MEAN_REVERSION").any()
