from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.build_edge_factory_scoreboard_from_runs import build_edge_factory_scoreboard


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
    diag_dir = run_dir / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "ci_low": -0.01,
                "ci_high": 0.08,
                "crosses_zero": True,
                "resamples": 200,
            }
        ]
    ).to_csv(diag_dir / "BOOT_expectancy_ci.csv", index=False)


def test_rebuild_scoreboard_from_progress_and_runs(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=20, freq="5min"),
            "open": [1.0] * 20,
            "high": [1.1] * 20,
            "low": [0.9] * 20,
            "close": [1.0] * 20,
        }
    ).to_csv(data_path, index=False)

    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    cfg1 = candidates_dir / "cand_a.yaml"
    cfg2 = candidates_dir / "cand_b.yaml"
    cfg1.write_text("strategy_family: VTM_VOL_MR\n", encoding="utf-8")
    cfg2.write_text("strategy_family: VTM_VOL_MR\n", encoding="utf-8")
    baseline_cfg = tmp_path / "baseline.yaml"
    baseline_cfg.write_text("strategy_family: V3_CLASSIC\n", encoding="utf-8")

    runs_root = tmp_path / "runs"
    run_base = runs_root / "20260101_000001"
    run_a = runs_root / "20260101_000101"
    run_b = runs_root / "20260101_000201"
    _write_trade_artifacts(run_base, [0.1, -0.05, 0.08, 0.03])
    _write_trade_artifacts(run_a, [0.2, 0.1, -0.1, 0.05, 0.05])
    _write_trade_artifacts(run_b, [-0.1, -0.05, 0.02, -0.02])

    progress_path = tmp_path / "edge_factory_progress.jsonl"
    lines = [
        {
            "candidate": "__baseline__",
            "config": baseline_cfg.as_posix(),
            "data_path": data_path.as_posix(),
            "run_id": run_base.name,
            "status": "ok",
            "note": "",
        },
        {
            "candidate": cfg1.stem,
            "config": cfg1.as_posix(),
            "data_path": data_path.as_posix(),
            "run_id": run_a.name,
            "status": "ok",
            "note": "",
        },
        {
            "candidate": cfg2.stem,
            "config": cfg2.as_posix(),
            "data_path": data_path.as_posix(),
            "run_id": run_b.name,
            "status": "ok",
            "note": "",
        },
    ]
    progress_path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")

    gates_cfg = tmp_path / "gates.yaml"
    gates_cfg.write_text(
        "\n".join(
            [
                "version: 1",
                "default_stage: dev_fast",
                "stages:",
                "  dev_fast:",
                "    min_trades: 1",
                "    min_pf: 0.8",
                "    min_expectancy_r: -1.0",
                "    require_ci_non_crossing_zero: false",
                "    min_retention_vs_baseline_pct: 0.0",
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

    out_dir = tmp_path / "out"
    built = build_edge_factory_scoreboard(
        data_path=data_path,
        candidates_dir=candidates_dir,
        baseline_config=baseline_cfg,
        runs_root=runs_root,
        out_dir=out_dir,
        gates_config_path=gates_cfg,
        stage="dev_fast",
        progress_jsonl=progress_path,
        note="pytest rebuild check",
    )

    assert built["scoreboard_csv"].exists()
    assert built["scoreboard_md"].exists()
    assert built["scoreboard_summary_json"].exists()
    summary = json.loads(built["scoreboard_summary_json"].read_text(encoding="utf-8"))
    assert summary["rows_written"] == 3
    assert summary["baseline_run_id"] == run_base.name

