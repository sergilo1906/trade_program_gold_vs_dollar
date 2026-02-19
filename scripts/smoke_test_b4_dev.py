from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


def _extract_run_id(text: str) -> str | None:
    m = re.search(r"run_id:\s*([0-9_]+)", text)
    return m.group(1) if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test run using pivot winner B4 on DEV dataset.")
    parser.add_argument("--data", default="data_local/xauusd_m5_DEV_2021_2023.csv")
    parser.add_argument("--config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--out-dir", default="outputs/smoke_dev_b4")
    args = parser.parse_args()

    data_path = Path(args.data)
    config_path = Path(args.config)
    out_dir = Path(args.out_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path.as_posix()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_cfg = out_dir / "_tmp_smoke_config.yaml"
    cfg_obj = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    cfg_obj["runs_output_dir"] = out_dir.as_posix()
    tmp_cfg.write_text(yaml.safe_dump(cfg_obj, sort_keys=False), encoding="utf-8")

    cmd = [
        sys.executable,
        "scripts/run_and_tag.py",
        "--data",
        data_path.as_posix(),
        "--config",
        tmp_cfg.as_posix(),
        "--runs-root",
        out_dir.as_posix(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if proc.returncode != 0:
        if proc.stdout.strip():
            print(proc.stdout.strip())
        if proc.stderr.strip():
            print(proc.stderr.strip())
        raise RuntimeError(f"run_and_tag failed with rc={proc.returncode}")

    run_id = _extract_run_id(proc.stdout)
    run_dir = out_dir / run_id if run_id else out_dir
    trades_count = "NA"
    if run_id:
        trades_path = run_dir / "trades.csv"
        if trades_path.exists():
            trades_count = str(len(pd.read_csv(trades_path)))

    print("SMOKE_RESULT")
    print(f"status: OK")
    print(f"runs_root: {out_dir.as_posix()}")
    print(f"run_id: {run_id or 'NA'}")
    print(f"run_dir: {run_dir.as_posix()}")
    print(f"trades: {trades_count}")
    print(f"config_used_for_smoke: {tmp_cfg.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
