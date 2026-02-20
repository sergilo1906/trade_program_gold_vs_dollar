from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from xauusd_bot.data_loader import load_m5_csv

ROOT = Path(__file__).resolve().parents[1]


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def _now_utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _materialize_smoke_input(data_path: Path, max_bars: int, stamp: str) -> Path:
    # Reuse project loader to support timestamp aliases/headerless OHLC files.
    df = load_m5_csv(data_path)
    if max_bars > 0 and len(df) > max_bars:
        df = df.tail(max_bars).reset_index(drop=True)

    tmp_dir = ROOT / "data" / "tmp_smoke"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out = tmp_dir / f"v4_smoke_input_{stamp}.csv"
    df.to_csv(out, index=False)
    return out


def _resolve_candidate_paths(candidates_arg: list[str], candidates_dir: Path) -> list[Path]:
    out: list[Path] = []
    for raw in candidates_arg:
        token = str(raw).strip()
        if not token:
            continue
        candidate = Path(token)
        if candidate.is_absolute() and candidate.exists():
            out.append(candidate)
            continue
        if candidate.exists():
            out.append((ROOT / candidate) if not candidate.is_absolute() else candidate)
            continue
        name = token if token.lower().endswith(".yaml") else f"{token}.yaml"
        p = candidates_dir / name
        if not p.exists():
            raise FileNotFoundError(f"Candidate not found: {token} (checked {p.as_posix()})")
        out.append(p)
    if not out:
        raise ValueError("No candidate configs resolved for smoke run.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick smoke wrapper for V4 candidates (baseline + 2 candidates).")
    parser.add_argument("--data", default="data/sample_m5.csv")
    parser.add_argument("--candidates-dir", default="configs/v4_candidates")
    parser.add_argument("--candidates", nargs="+", default=["v4a_orb_07", "v4a_orb_03"])
    parser.add_argument("--baseline-config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--max-bars", type=int, default=4000)
    parser.add_argument("--out-dir", default="outputs/v4_smoke_runs")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--resamples", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--snapshot-root", default="docs/_snapshots")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    candidates_dir = _resolve(args.candidates_dir)
    baseline_cfg = _resolve(args.baseline_config)
    out_dir = _resolve(args.out_dir)
    runs_root = _resolve(args.runs_root)
    snapshot_root = _resolve(args.snapshot_root)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if not baseline_cfg.exists():
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")

    stamp = _now_utc_compact()
    smoke_input = _materialize_smoke_input(data_path=data_path, max_bars=int(args.max_bars), stamp=stamp)
    candidate_paths = _resolve_candidate_paths(args.candidates, candidates_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    temp_candidates_dir = out_dir / f"_tmp_candidates_{stamp}"
    temp_candidates_dir.mkdir(parents=True, exist_ok=True)
    for p in candidate_paths:
        shutil.copy2(p, temp_candidates_dir / p.name)

    cmd = [
        sys.executable,
        "scripts/run_v4_candidates.py",
        "--data",
        smoke_input.as_posix(),
        "--candidates-dir",
        temp_candidates_dir.as_posix(),
        "--out-dir",
        out_dir.as_posix(),
        "--runs-root",
        runs_root.as_posix(),
        "--baseline-config",
        baseline_cfg.as_posix(),
        "--resamples",
        str(int(args.resamples)),
        "--seed",
        str(int(args.seed)),
    ]
    proc = _run_cmd(cmd)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise RuntimeError(f"run_v4_candidates.py failed with rc={proc.returncode}")

    score_csv = out_dir / "v4_candidates_scoreboard.csv"
    score_md = out_dir / "v4_candidates_scoreboard.md"
    score_json = out_dir / "v4_candidates_scoreboard_summary.json"
    for p in (score_csv, score_md, score_json):
        if not p.exists():
            raise FileNotFoundError(f"Missing expected artifact: {p.as_posix()}")

    snapshot_dir = snapshot_root / f"v4a_smoke_{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(score_csv, snapshot_dir / "v4_candidates_scoreboard.csv")
    shutil.copy2(score_md, snapshot_dir / "v4_candidates_scoreboard.md")
    shutil.copy2(score_json, snapshot_dir / "v4_candidates_scoreboard_summary.json")

    meta = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "command": " ".join(cmd),
        "data_source": data_path.as_posix(),
        "smoke_input": smoke_input.as_posix(),
        "max_bars": int(args.max_bars),
        "baseline_config": baseline_cfg.as_posix(),
        "candidates": [p.as_posix() for p in candidate_paths],
        "out_dir": out_dir.as_posix(),
        "snapshot_dir": snapshot_dir.as_posix(),
        "runs_root": runs_root.as_posix(),
        "resamples": int(args.resamples),
        "seed": int(args.seed),
    }
    (snapshot_dir / "v4_smoke_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    if not args.keep_temp:
        if smoke_input.exists():
            smoke_input.unlink(missing_ok=True)
        if temp_candidates_dir.exists():
            shutil.rmtree(temp_candidates_dir, ignore_errors=False)

    print(f"SMOKE_STATUS: ok")
    print(f"SMOKE_OUT_DIR: {out_dir.as_posix()}")
    print(f"SMOKE_SNAPSHOT_DIR: {snapshot_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
