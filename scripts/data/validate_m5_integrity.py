from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLS = ("timestamp", "open", "high", "low", "close")


def _emit(tag: str, message: str) -> None:
    print(f"[{tag}] {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate M5 CSV integrity and print PASS/WARN/FAIL summary.")
    parser.add_argument("--input", required=True, help="CSV path to validate.")
    parser.add_argument("--expected_tf_minutes", type=int, default=5)
    parser.add_argument("--max_report_rows", type=int, default=20)
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        _emit("FAIL", f"missing input file: {in_path.as_posix()}")
        print("SUMMARY: FAIL")
        return 1

    df = pd.read_csv(in_path)
    if df.empty:
        _emit("FAIL", "input csv is empty")
        print("SUMMARY: FAIL")
        return 1

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        _emit("FAIL", f"missing required columns: {missing}")
        print("SUMMARY: FAIL")
        return 1

    warn_count = 0
    fail_count = 0

    ts_raw = pd.to_datetime(df["timestamp"], errors="coerce")
    nat_count = int(ts_raw.isna().sum())
    if nat_count > 0:
        warn_count += 1
        _emit("WARN", f"NaT timestamps: {nat_count}")
    else:
        _emit("PASS", "NaT timestamps: 0")

    working = df.copy()
    working["timestamp"] = ts_raw
    working = working.dropna(subset=["timestamp"]).copy()
    if working.empty:
        _emit("FAIL", "all timestamps became NaT after parse")
        print("SUMMARY: FAIL")
        return 1

    dup = (
        working.groupby("timestamp", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .query("count > 1")
        .sort_values(["count", "timestamp"], ascending=[False, True])
    )
    dup_count = int(dup["count"].sum() - len(dup)) if not dup.empty else 0
    if dup_count > 0:
        warn_count += 1
        _emit("WARN", f"duplicate timestamp rows: {dup_count}")
        _emit("WARN", "duplicate samples:")
        print(dup.head(int(args.max_report_rows)).to_string(index=False))
    else:
        _emit("PASS", "duplicate timestamp rows: 0")

    chrono_ok = working["timestamp"].is_monotonic_increasing
    if chrono_ok:
        _emit("PASS", "chronological order: increasing")
    else:
        warn_count += 1
        _emit("WARN", "chronological order: not monotonic increasing")

    sorted_ts = working["timestamp"].sort_values().drop_duplicates()
    diffs = sorted_ts.diff().dropna().dt.total_seconds().div(60.0)
    dominant_delta = float(diffs.mode().iloc[0]) if not diffs.empty else float("nan")
    if diffs.empty:
        warn_count += 1
        _emit("WARN", "unable to compute deltas (not enough rows)")
    else:
        _emit("PASS", f"dominant delta minutes: {dominant_delta:.2f}")
        if round(dominant_delta) != int(args.expected_tf_minutes):
            fail_count += 1
            _emit("FAIL", f"dominant delta != expected ({args.expected_tf_minutes})")

    gap_df = pd.DataFrame(
        {
            "timestamp": sorted_ts.iloc[1:].values if len(sorted_ts) > 1 else [],
            "gap_minutes": diffs.values if not diffs.empty else [],
        }
    )
    big_gaps = gap_df[gap_df["gap_minutes"] > 60.0].sort_values("gap_minutes", ascending=False)
    if big_gaps.empty:
        _emit("PASS", "gaps > 60 minutes: 0")
    else:
        warn_count += 1
        _emit("WARN", f"gaps > 60 minutes: {len(big_gaps)}")
        print(big_gaps.head(int(args.max_report_rows)).to_string(index=False))

    for col in ("open", "high", "low", "close"):
        working[col] = pd.to_numeric(working[col], errors="coerce")
    nan_ohlc = int(working[["open", "high", "low", "close"]].isna().any(axis=1).sum())
    if nan_ohlc > 0:
        warn_count += 1
        _emit("WARN", f"rows with non-numeric OHLC values: {nan_ohlc}")
    else:
        _emit("PASS", "rows with non-numeric OHLC values: 0")

    sane_mask = (
        (working["high"] >= working[["open", "close"]].max(axis=1))
        & (working["low"] <= working[["open", "close"]].min(axis=1))
        & (working["high"] >= working["low"])
    )
    bad_ohlc = working[~sane_mask].copy()
    if bad_ohlc.empty:
        _emit("PASS", "OHLC sanity violations: 0")
    else:
        fail_count += 1
        _emit("FAIL", f"OHLC sanity violations: {len(bad_ohlc)}")
        cols = ["timestamp", "open", "high", "low", "close"]
        print(bad_ohlc[cols].head(int(args.max_report_rows)).to_string(index=False))

    _emit("PASS", f"rows_checked: {len(working)}")
    _emit("PASS", f"range: {working['timestamp'].min()} -> {working['timestamp'].max()}")

    if fail_count > 0:
        summary = "FAIL"
        code = 1
    elif warn_count > 0:
        summary = "WARN"
        code = 0
    else:
        summary = "PASS"
        code = 0

    print(f"SUMMARY: {summary}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
