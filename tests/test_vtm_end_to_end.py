from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _extract_run_id(text: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", text)
    return m.group(1) if m else ""


def test_vtm_end_to_end_generates_artifacts(tmp_path: Path) -> None:
    data_path = ROOT / "data" / "sample_m5.csv"
    assert data_path.exists()

    runs_root = tmp_path / "runs"
    out_dir = tmp_path / "output"
    cfg_path = tmp_path / "vtm_test.yaml"

    cfg = {
        "output_dir": str(out_dir),
        "runs_output_dir": str(runs_root),
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
            "threshold_range": 0.9,
            "stop_atr": 0.8,
            "holding_bars": 8,
            "close_extreme_frac": 0.4,
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
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    cmd_run = [
        sys.executable,
        "scripts/run_and_tag.py",
        "--data",
        str(data_path),
        "--config",
        str(cfg_path),
        "--runs-root",
        str(runs_root),
    ]
    run = subprocess.run(cmd_run, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, f"stdout={run.stdout}\nstderr={run.stderr}"
    run_id = _extract_run_id(run.stdout + "\n" + run.stderr)
    assert run_id
    run_dir = runs_root / run_id

    cmd_diag = [sys.executable, "scripts/diagnose_run.py", str(run_dir)]
    diag = subprocess.run(cmd_diag, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert diag.returncode == 0, f"stdout={diag.stdout}\nstderr={diag.stderr}"

    cmd_boot = [
        sys.executable,
        "scripts/bootstrap_expectancy.py",
        str(run_dir),
        "--resamples",
        "200",
        "--seed",
        "42",
    ]
    boot = subprocess.run(cmd_boot, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert boot.returncode == 0, f"stdout={boot.stdout}\nstderr={boot.stderr}"

    trades = pd.read_csv(run_dir / "trades.csv")
    assert len(trades) > 0
    assert (run_dir / "diagnostics" / "BOOT_expectancy_ci.csv").exists()
