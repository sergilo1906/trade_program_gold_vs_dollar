from __future__ import annotations

from pathlib import Path

import pandas as pd

from xauusd_bot.configuration import load_config
from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger
from xauusd_bot.models import EntrySignal


def _build_engine(tmp_path: Path) -> SimulationEngine:
    cfg = load_config("configs/config_smoke_baseline.yaml")
    cfg["output_dir"] = str(tmp_path / "output")
    cfg["runs_output_dir"] = str(tmp_path / "runs")
    cfg["strategy_family"] = "VTM_VOL_MR"
    cfg["enable_strategy_v3"] = False
    cfg["vtm_vol_mr"].update(
        {
            "signal_model": "shock_session",
            "atr_period": 14,
            "ma_period": 30,
            "shock_threshold": 2.5,
            "threshold_range": 2.5,
            "stop_atr": 1.0,
            "target_atr": 1.0,
            "holding_bars": 8,
            "close_extreme_pct": 0.10,
            "close_extreme_frac": 0.10,
            "entry_windows": ["07:00-08:00"],
            "excluded_windows": [],
            "spread_max_usd": 10.0,
            "vol_filter_min": 0.0,
            "slope_threshold": 0.0,
        }
    )
    logger = CsvLogger(output_dir=Path(cfg["output_dir"]), reset=True)
    return SimulationEngine(config=cfg, logger=logger)


def test_vtm_shock_session_direction_logic(tmp_path: Path) -> None:
    engine = _build_engine(tmp_path)

    long_row = pd.Series(
        {
            "high": 100.0,
            "low": 99.0,
            "close": 99.02,
            "atr_vtm": 0.30,
            "spread": 0.40,
        }
    )
    signal, event_type, payload = engine._evaluate_vtm_entry_signal(
        row=long_row,
        signal_ts=pd.Timestamp("2024-03-04 07:30:00"),
    )
    assert signal == EntrySignal.BUY
    assert event_type == "VTM_SIGNAL_SHOCK_MR"
    assert payload is not None
    assert float(payload["target_dist"]) > 0.0
    assert payload["setup_reason"] == "VTM_SHOCK_MR_LONG"

    short_row = pd.Series(
        {
            "high": 100.0,
            "low": 99.0,
            "close": 99.98,
            "atr_vtm": 0.30,
            "spread": 0.40,
        }
    )
    signal, event_type, payload = engine._evaluate_vtm_entry_signal(
        row=short_row,
        signal_ts=pd.Timestamp("2024-03-04 07:35:00"),
    )
    assert signal == EntrySignal.SELL
    assert event_type == "VTM_SIGNAL_SHOCK_MR"
    assert payload is not None
    assert payload["setup_reason"] == "VTM_SHOCK_MR_SHORT"


def test_vtm_shock_session_blocks_outside_window(tmp_path: Path) -> None:
    engine = _build_engine(tmp_path)
    row = pd.Series(
        {
            "high": 100.0,
            "low": 99.0,
            "close": 99.02,
            "atr_vtm": 0.30,
            "spread": 0.40,
        }
    )
    signal, event_type, payload = engine._evaluate_vtm_entry_signal(
        row=row,
        signal_ts=pd.Timestamp("2024-03-04 09:00:00"),
    )
    assert signal == EntrySignal.NONE
    assert event_type == "VTM_BLOCK_OUTSIDE_ENTRY_WINDOW"
    assert payload is None

