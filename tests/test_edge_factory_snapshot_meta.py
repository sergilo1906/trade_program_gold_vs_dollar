from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _write_trade_artifacts(run_dir: Path, r_values: list[float]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = pd.date_range("2025-01-01 00:00:00", periods=len(r_values), freq="5min")
    pd.DataFrame(
        {
            "entry_time": ts,
            "r_multiple": r_values,
            "pnl": [x * 10.0 for x in r_values],
        }
    ).to_csv(run_dir / "trades.csv", index=False)
    diag = run_dir / "diagnostics"
    diag.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "ci_low": -0.02,
                "ci_high": 0.06,
                "crosses_zero": True,
                "resamples": 100,
            }
        ]
    ).to_csv(diag / "BOOT_expectancy_ci.csv", index=False)


def test_edge_factory_rebuild_writes_snapshot_meta(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=30, freq="5min"),
            "open": [1.0] * 30,
            "high": [1.1] * 30,
            "low": [0.9] * 30,
            "close": [1.0] * 30,
        }
    ).to_csv(data_path, index=False)

    candidates_dir = tmp_path / "cands"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    baseline_cfg = tmp_path / "baseline.yaml"
    baseline_cfg.write_text("strategy_family: V3_CLASSIC\n", encoding="utf-8")
    cand_cfg = candidates_dir / "cand.yaml"
    cand_cfg.write_text("strategy_family: VTM_VOL_MR\n", encoding="utf-8")

    runs_root = tmp_path / "runs"
    run_base = runs_root / "20260101_000001"
    run_cand = runs_root / "20260101_000101"
    _write_trade_artifacts(run_base, [0.1, -0.05, 0.08, 0.01])
    _write_trade_artifacts(run_cand, [0.06, 0.02, -0.01, 0.03])

    progress = tmp_path / "out" / "edge_factory_progress.jsonl"
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "candidate": "__baseline__",
                        "config": baseline_cfg.as_posix(),
                        "data_path": data_path.as_posix(),
                        "run_id": run_base.name,
                        "status": "ok",
                    }
                ),
                json.dumps(
                    {
                        "candidate": cand_cfg.stem,
                        "config": cand_cfg.as_posix(),
                        "data_path": data_path.as_posix(),
                        "run_id": run_cand.name,
                        "status": "ok",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    gates_cfg = tmp_path / "gates.yaml"
    gates_cfg.write_text(
        "\n".join(
            [
                "version: 1",
                "default_stage: smoke",
                "stages:",
                "  smoke:",
                "    min_trades: 1",
                "    min_pf: null",
                "    min_expectancy_r: null",
                "    require_ci_non_crossing_zero: false",
                "    min_retention_vs_baseline_pct: null",
                "    require_cost_stress_survival_p20: false",
                "    require_cost_stress_survival_p50: false",
                "    require_temporal_stability: false",
                "    max_drawdown_r: null",
                "    min_years_active: null",
                "    min_months_with_trades: null",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    snapshot_root = tmp_path / "snapshots"
    out_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "scripts/run_edge_factory_batch.py",
        "--data",
        str(data_path),
        "--candidates-dir",
        str(candidates_dir),
        "--baseline-config",
        str(baseline_cfg),
        "--out-dir",
        str(out_dir),
        "--runs-root",
        str(runs_root),
        "--resamples",
        "100",
        "--seed",
        "7",
        "--gates-config",
        str(gates_cfg),
        "--stage",
        "smoke",
        "--snapshot-root",
        str(snapshot_root),
        "--snapshot-prefix",
        "edge_factory_pytest",
        "--rebuild-only",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    snapshots = sorted(snapshot_root.glob("edge_factory_pytest_*"))
    assert snapshots, "snapshot folder not created"
    latest = snapshots[-1]
    meta_path = latest / "meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert "command" in meta and "run_edge_factory_batch.py" in meta["command"]
    assert str(meta.get("used_data_path", "")).endswith("data.csv")
    assert int(meta.get("seed", -1)) == 7
    assert int(meta.get("resamples", -1)) == 100

