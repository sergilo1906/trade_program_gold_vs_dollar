from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _build_dataset(path: Path, bars: int = 720) -> None:
    ts = pd.date_range("2024-03-04 00:00:00", periods=bars, freq="5min")
    closes: list[float] = []
    for i, t in enumerate(ts):
        day = (t.normalize() - ts[0].normalize()).days
        minute = int(t.hour) * 60 + int(t.minute)
        base = 2050.0 + day * 0.8
        if minute <= 30:
            close = base + (i % 4) * 0.02
        elif minute < 12 * 60:
            close = base + 1.2 + (minute - 35) * 0.002
        else:
            close = base - 1.1 - (minute - 12 * 60) * 0.0015
        closes.append(float(close))
    opens = [closes[0]] + closes[:-1]
    highs = [max(o, c) + 0.07 for o, c in zip(opens, closes)]
    lows = [min(o, c) - 0.07 for o, c in zip(opens, closes)]
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [100.0] * len(ts),
        }
    )
    df.to_csv(path, index=False)


def test_smoke_pipeline_generates_artifacts(tmp_path: Path) -> None:
    data_path = tmp_path / "smoke_data.csv"
    _build_dataset(data_path)

    runs_root = tmp_path / "runs"
    out_dir = tmp_path / "smoke_runs"
    snapshot_root = tmp_path / "snapshots"
    decision_doc = tmp_path / "SMOKE_DECISION.md"

    cmd = [
        sys.executable,
        "scripts/run_smoke.py",
        "--data",
        str(data_path),
        "--config",
        "configs/config_smoke_baseline.yaml",
        "--runs-root",
        str(runs_root),
        "--out-dir",
        str(out_dir),
        "--snapshot-root",
        str(snapshot_root),
        "--decision-doc",
        str(decision_doc),
        "--max-bars",
        "600",
        "--resamples",
        "200",
        "--seed",
        "42",
        "--keep-temp",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    score_csv = out_dir / "smoke_scoreboard.csv"
    score_md = out_dir / "smoke_scoreboard.md"
    score_json = out_dir / "smoke_scoreboard_summary.json"
    assert score_csv.exists()
    assert score_md.exists()
    assert score_json.exists()
    assert decision_doc.exists()

    summary = json.loads(score_json.read_text(encoding="utf-8"))
    assert summary.get("pipeline_ok") is True
    run_id = str(summary.get("run_id", "")).strip()
    assert run_id
    assert int(summary.get("trades", 0)) > 0
    assert (runs_root / run_id / "trades.csv").exists()
