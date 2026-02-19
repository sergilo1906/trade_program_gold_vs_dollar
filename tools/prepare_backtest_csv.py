from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED = ["timestamp", "open", "high", "low", "close"]
OPTIONAL_ORDER = ["volume", "spread", "bid", "ask"]
TIMESTAMP_ALIASES = {"timestamp", "time", "datetime", "date", "ts"}


def _norm(name: object) -> str:
    return str(name).strip().lower()


def _find_timestamp_col(columns: list[object]) -> str | None:
    for col in columns:
        if _norm(col) in TIMESTAMP_ALIASES:
            return str(col)
    return None


def _read_any_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if _find_timestamp_col(list(df.columns)) is not None:
        return df

    # Headerless fallback: assume first six columns are OHLCV.
    df_no_header = pd.read_csv(path, header=None)
    base = ["timestamp", "open", "high", "low", "close", "volume"]
    if df_no_header.shape[1] <= len(base):
        df_no_header.columns = base[: df_no_header.shape[1]]
    else:
        extras = [f"col_{i}" for i in range(len(base), df_no_header.shape[1])]
        df_no_header.columns = base + extras
    return df_no_header


def prepare_csv(input_path: Path, output_path: Path) -> int:
    df = _read_any_csv(input_path)
    df.columns = [_norm(c) for c in df.columns]

    if "timestamp" not in df.columns:
        raise ValueError("No timestamp column found after normalization.")

    # Parse and clean timestamp.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    # Parse numeric price/volume columns.
    for col in [c for c in REQUIRED[1:] + OPTIONAL_ORDER if c in df.columns]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Enforce required OHLC.
    missing_required = [c for c in REQUIRED if c not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")
    df = df.dropna(subset=["open", "high", "low", "close"]).copy()

    if "volume" not in df.columns:
        df["volume"] = 0.0

    # Canonical ordering and dedupe.
    ordered_cols = REQUIRED + [c for c in OPTIONAL_ORDER if c in df.columns and c not in REQUIRED]
    df = df[ordered_cols]
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print("PREPARE CSV SUMMARY")
    print(f"input: {input_path.resolve()}")
    print(f"output: {output_path.resolve()}")
    print(f"rows: {len(df)}")
    print(f"min_ts: {df['timestamp'].min()}")
    print(f"max_ts: {df['timestamp'].max()}")
    print(f"unique_days: {int(df['timestamp'].dt.date.nunique())}")
    print(f"columns: {list(df.columns)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize M5 CSV into backtest-ready canonical format.")
    parser.add_argument("--csv", required=True, help="Input CSV path")
    parser.add_argument("--out", required=True, help="Output CSV path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    in_path = Path(args.csv)
    if not in_path.exists():
        print(f"ERROR: input CSV not found: {in_path}")
        return 2
    return prepare_csv(in_path, Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
