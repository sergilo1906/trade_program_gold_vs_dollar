from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TS_ALIASES = ("timestamp", "time", "datetime", "date", "ts")


def _find_ts_col(columns: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for alias in TS_ALIASES:
        if alias in lowered:
            return lowered[alias]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DEV dataset from FULL history by start date.")
    parser.add_argument("--input", required=True, help="Input FULL CSV path.")
    parser.add_argument("--output", required=True, help="Output DEV CSV path.")
    parser.add_argument("--start", required=True, help="Inclusive start date, e.g. 2021-01-01.")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    start_ts = pd.to_datetime(args.start, errors="raise")

    if not in_path.exists():
        raise FileNotFoundError(f"Missing input CSV: {in_path.as_posix()}")

    df = pd.read_csv(in_path)
    if df.empty:
        raise RuntimeError("Input CSV is empty.")

    df.columns = [str(c).strip().lower() for c in df.columns]
    ts_col = _find_ts_col(list(df.columns))
    if ts_col is None:
        raise RuntimeError(f"No timestamp-like column found. columns={list(df.columns)}")
    if ts_col != "timestamp":
        df = df.rename(columns={ts_col: "timestamp"})

    rows_before = len(df)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    nat_count = int(df["timestamp"].isna().sum())
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df = df[df["timestamp"] >= start_ts].reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    pct_nat = (100.0 * nat_count / rows_before) if rows_before > 0 else 0.0
    min_ts = df["timestamp"].min() if not df.empty else pd.NaT
    max_ts = df["timestamp"].max() if not df.empty else pd.NaT

    print(f"input: {in_path.as_posix()}")
    print(f"output: {out_path.as_posix()}")
    print(f"rows_before: {rows_before}")
    print(f"rows_after: {len(df)}")
    print(f"start_filter: {start_ts}")
    print(f"min_ts: {min_ts}")
    print(f"max_ts: {max_ts}")
    print(f"nat_removed: {nat_count} ({pct_nat:.4f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
