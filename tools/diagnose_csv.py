from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


TIMESTAMP_ALIASES = {"timestamp", "time", "datetime", "date", "ts"}
HUGE_GAP_THRESHOLD = pd.Timedelta(hours=6)


@dataclass
class CsvInspection:
    path: Path
    df: pd.DataFrame
    timestamp_col: str
    header_mode: str


def _normalize_col(name: object) -> str:
    return str(name).strip().lower()


def _find_timestamp_col(columns: list[object]) -> str | None:
    for col in columns:
        if _normalize_col(col) in TIMESTAMP_ALIASES:
            return str(col)
    return None


def _read_csv_for_inspection(csv_path: Path) -> CsvInspection:
    # First attempt: regular CSV with headers.
    df_default = pd.read_csv(csv_path)
    timestamp_col = _find_timestamp_col(list(df_default.columns))
    if timestamp_col is not None:
        return CsvInspection(path=csv_path, df=df_default, timestamp_col=timestamp_col, header_mode="header")

    # Fallback: headerless OHLCV-style CSV where first column is timestamp.
    df_no_header = pd.read_csv(csv_path, header=None)
    if df_no_header.shape[1] == 0:
        raise ValueError("CSV has no columns.")

    ts_probe = pd.to_datetime(df_no_header.iloc[:, 0], errors="coerce")
    parse_ratio = float(ts_probe.notna().mean()) if len(ts_probe) else 0.0
    if parse_ratio < 0.5:
        raise ValueError(
            "Timestamp column not found and headerless fallback failed "
            f"(first-column parse ratio={parse_ratio:.3f})."
        )

    col_names = ["timestamp", "open", "high", "low", "close", "volume"]
    if df_no_header.shape[1] > len(col_names):
        extra = [f"col_{i}" for i in range(len(col_names), df_no_header.shape[1])]
        col_names.extend(extra)
    df_no_header.columns = col_names[: df_no_header.shape[1]]
    return CsvInspection(path=csv_path, df=df_no_header, timestamp_col="timestamp", header_mode="headerless")


def _format_ts(value: object) -> str:
    if pd.isna(value):
        return "NaT"
    return str(pd.Timestamp(value))


def diagnose_csv(csv_path: Path) -> int:
    inspection = _read_csv_for_inspection(csv_path)
    df = inspection.df.copy()

    ts = pd.to_datetime(df[inspection.timestamp_col], errors="coerce")
    valid_ts = ts.dropna()

    rows = len(df)
    cols = [str(c) for c in df.columns]
    invalid_ts = int(ts.isna().sum())
    min_ts = valid_ts.min() if not valid_ts.empty else pd.NaT
    max_ts = valid_ts.max() if not valid_ts.empty else pd.NaT
    unique_days = int(valid_ts.dt.date.nunique()) if not valid_ts.empty else 0

    duplicated_ts = int(valid_ts.duplicated().sum())
    deltas_in_file_order = valid_ts.diff()
    out_of_order = int((deltas_in_file_order < pd.Timedelta(0)).sum())

    ts_sorted = valid_ts.sort_values().reset_index(drop=True)
    sorted_deltas = ts_sorted.diff().dropna()
    max_gap = sorted_deltas.max() if not sorted_deltas.empty else pd.Timedelta(0)
    huge_gap_count = int((sorted_deltas > HUGE_GAP_THRESHOLD).sum()) if not sorted_deltas.empty else 0
    non_m5_gap_count = int((sorted_deltas != pd.Timedelta(minutes=5)).sum()) if not sorted_deltas.empty else 0

    print("CSV DIAGNOSIS")
    print(f"path_abs: {inspection.path.resolve()}")
    print(f"header_mode: {inspection.header_mode}")
    print(f"rows: {rows}")
    print(f"columns: {cols}")
    print(f"timestamp_col: {inspection.timestamp_col}")
    print(f"timestamp_invalid: {invalid_ts}")
    print(f"min_ts: {_format_ts(min_ts)}")
    print(f"max_ts: {_format_ts(max_ts)}")
    print(f"unique_days: {unique_days}")
    print(f"duplicated_timestamps: {duplicated_ts}")
    print(f"out_of_order_timestamps: {out_of_order}")
    print(f"non_5m_gaps: {non_m5_gap_count}")
    print(f"huge_gaps_gt_6h: {huge_gap_count}")
    print(f"max_gap: {max_gap}")

    if huge_gap_count > 0 and not ts_sorted.empty:
        print("largest_gaps:")
        gaps_df = pd.DataFrame(
            {
                "prev": ts_sorted.shift(1),
                "curr": ts_sorted,
                "gap": ts_sorted.diff(),
            }
        ).dropna(subset=["gap"])
        top_gaps = gaps_df.sort_values("gap", ascending=False).head(5)
        for _, row in top_gaps.iterrows():
            print(f"  - {_format_ts(row['prev'])} -> {_format_ts(row['curr'])} | gap={row['gap']}")

    if inspection.timestamp_col not in df.columns:
        print("ERROR: timestamp column missing after inspection.")
        return 2
    if len(valid_ts) == 0:
        print("ERROR: no valid timestamps parsed.")
        return 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose an M5 CSV for timestamp/data integrity.")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}")
        return 2
    return diagnose_csv(csv_path)


if __name__ == "__main__":
    raise SystemExit(main())
