from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "xauusd_m5_backtest_ready.csv"
DEV_CSV = ROOT / "data" / "xauusd_m5_DEV80.csv"
HOLDOUT_CSV = ROOT / "data" / "xauusd_m5_HOLDOUT20.csv"
DOC_PATH = ROOT / "docs" / "HOLDOUT_SPLIT.md"


def _fmt_ts(value: pd.Timestamp | str | None) -> str:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return "NA"
    return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _range_row(df: pd.DataFrame, label: str) -> dict[str, object]:
    if df.empty:
        return {
            "dataset": label,
            "rows": 0,
            "start_ts": "NA",
            "end_ts": "NA",
        }
    return {
        "dataset": label,
        "rows": int(len(df)),
        "start_ts": _fmt_ts(df["timestamp"].iloc[0]),
        "end_ts": _fmt_ts(df["timestamp"].iloc[-1]),
    }


def _md_table(rows: list[dict[str, object]]) -> str:
    headers = ["dataset", "rows", "start_ts", "end_ts"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input dataset: {INPUT_CSV.as_posix()}")

    df = pd.read_csv(INPUT_CSV)
    if "timestamp" not in df.columns:
        raise ValueError("Input CSV must include 'timestamp' column.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    n_rows = len(df)
    cut = int(math.floor(0.8 * n_rows))
    dev = df.iloc[:cut].copy()
    holdout = df.iloc[cut:].copy()

    DEV_CSV.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    dev.to_csv(DEV_CSV, index=False)
    holdout.to_csv(HOLDOUT_CSV, index=False)

    rows = [
        {
            "dataset": "FULL",
            "rows": int(n_rows),
            "start_ts": _fmt_ts(df["timestamp"].iloc[0] if n_rows else None),
            "end_ts": _fmt_ts(df["timestamp"].iloc[-1] if n_rows else None),
        },
        _range_row(dev, "DEV80"),
        _range_row(holdout, "HOLDOUT20"),
    ]

    md = "\n".join(
        [
            "# HOLDOUT Split (80/20, Time-Ordered)",
            "",
            "- Input: `data/xauusd_m5_backtest_ready.csv`",
            "- Split rule: `cut = floor(0.8 * n_rows)` after sort by `timestamp` ascending",
            f"- n_rows: `{n_rows}`",
            f"- cut index: `{cut}`",
            f"- DEV output: `{DEV_CSV.relative_to(ROOT).as_posix()}`",
            f"- HOLDOUT output: `{HOLDOUT_CSV.relative_to(ROOT).as_posix()}`",
            "",
            "## Date Ranges",
            "",
            _md_table(rows),
            "",
        ]
    )
    DOC_PATH.write_text(md, encoding="utf-8")

    print(f"Wrote: {DEV_CSV.as_posix()}")
    print(f"Wrote: {HOLDOUT_CSV.as_posix()}")
    print(f"Wrote: {DOC_PATH.as_posix()}")
    print(f"n_rows={n_rows} cut={cut} dev_rows={len(dev)} holdout_rows={len(holdout)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
