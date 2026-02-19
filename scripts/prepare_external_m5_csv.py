from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TS_ALIASES = ("timestamp", "time", "datetime", "date", "ts")
REQUIRED = ("open", "high", "low", "close")


def _find_timestamp_column(columns: list[str]) -> str | None:
    lower = {c.lower(): c for c in columns}
    for alias in TS_ALIASES:
        if alias in lower:
            return lower[alias]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize external M5 CSV into backtest-ready format.")
    parser.add_argument("--input", required=True, help="Path to source CSV.")
    parser.add_argument("--output", required=True, help="Path to normalized CSV.")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path.as_posix()}")

    df = pd.read_csv(in_path)
    if df.empty:
        raise RuntimeError("Input CSV is empty.")

    ts_col = _find_timestamp_column(list(df.columns))
    if ts_col is None:
        raise RuntimeError(f"No timestamp-like column found. columns={list(df.columns)}")

    cols_lower = {c.lower(): c for c in df.columns}
    missing = [c for c in REQUIRED if c not in cols_lower]
    if missing:
        raise RuntimeError(f"Missing required OHLC columns: {missing}")

    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(df[ts_col], errors="coerce"),
            "open": pd.to_numeric(df[cols_lower["open"]], errors="coerce"),
            "high": pd.to_numeric(df[cols_lower["high"]], errors="coerce"),
            "low": pd.to_numeric(df[cols_lower["low"]], errors="coerce"),
            "close": pd.to_numeric(df[cols_lower["close"]], errors="coerce"),
        }
    )
    if "volume" in cols_lower:
        out["volume"] = pd.to_numeric(df[cols_lower["volume"]], errors="coerce")
    else:
        out["volume"] = 0.0

    before = len(out)
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"]).copy()
    dropped_na = before - len(out)

    out = out.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
    dropped_dupes = before - dropped_na - len(out)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    min_ts = out["timestamp"].min()
    max_ts = out["timestamp"].max()
    unique_days = int(out["timestamp"].dt.date.nunique())
    median_delta_min = float(out["timestamp"].diff().dropna().dt.total_seconds().median() / 60.0)

    print(f"input: {in_path.as_posix()}")
    print(f"output: {out_path.as_posix()}")
    print(f"rows_out: {len(out)}")
    print(f"min_ts: {min_ts}")
    print(f"max_ts: {max_ts}")
    print(f"unique_days: {unique_days}")
    print(f"median_delta_minutes: {median_delta_min:.2f}")
    print(f"dropped_na_rows: {dropped_na}")
    print(f"dropped_duplicate_timestamps: {dropped_dupes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
