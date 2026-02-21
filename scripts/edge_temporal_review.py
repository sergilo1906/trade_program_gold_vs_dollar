from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


R_COL_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)

TS_COL_CANDIDATES = (
    "entry_time",
    "open_time",
    "entry_ts",
    "timestamp",
    "time",
    "ts",
)


def _find_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for cand in candidates:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    return None


def _profit_factor(r: pd.Series) -> float:
    r = pd.to_numeric(r, errors="coerce").dropna()
    if r.empty:
        return math.nan
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss <= 0.0:
        return float("inf") if gross_win > 0 else math.nan
    return gross_win / gross_loss


def _review_run(run_id: str, run_dir: Path, segments: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trades_path = run_dir / "trades.csv"
    if not trades_path.exists():
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {"run_id": run_id, "status": "missing_trades"},
        )
    trades = pd.read_csv(trades_path)
    if trades.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {"run_id": run_id, "status": "empty_trades"},
        )

    r_col = _find_col(trades, R_COL_CANDIDATES)
    t_col = _find_col(trades, TS_COL_CANDIDATES)
    if r_col is None:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {"run_id": run_id, "status": "missing_r_col"},
        )
    if t_col is None:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {"run_id": run_id, "status": "missing_time_col"},
        )

    df = trades.copy()
    df[r_col] = pd.to_numeric(df[r_col], errors="coerce")
    df[t_col] = pd.to_datetime(df[t_col], errors="coerce", utc=True)
    df = df.dropna(subset=[r_col, t_col]).sort_values(t_col).reset_index(drop=True)
    if df.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {"run_id": run_id, "status": "empty_after_clean"},
        )

    t0 = df[t_col].min()
    t1 = df[t_col].max()
    sec_total = max(1.0, float((t1 - t0).total_seconds()))

    seg_rows: list[dict[str, Any]] = []
    for seg in range(int(segments)):
        left_ratio = float(seg) / float(segments)
        right_ratio = float(seg + 1) / float(segments)
        left = t0 + pd.Timedelta(seconds=sec_total * left_ratio)
        right = t0 + pd.Timedelta(seconds=sec_total * right_ratio)
        if seg == int(segments) - 1:
            m = (df[t_col] >= left) & (df[t_col] <= right)
        else:
            m = (df[t_col] >= left) & (df[t_col] < right)
        sub = df.loc[m]
        r = sub[r_col]
        seg_rows.append(
            {
                "run_id": run_id,
                "segment": f"S{seg + 1}",
                "start_ts": left.isoformat(),
                "end_ts": right.isoformat(),
                "trades": int(len(sub)),
                "expectancy_R": float(r.mean()) if not r.empty else math.nan,
                "pf": _profit_factor(r),
                "winrate": float((r > 0).mean()) if not r.empty else math.nan,
            }
        )
    seg_df = pd.DataFrame(seg_rows)

    df["year"] = df[t_col].dt.year
    y_rows: list[dict[str, Any]] = []
    for year, sub in df.groupby("year", sort=True):
        r = sub[r_col]
        y_rows.append(
            {
                "run_id": run_id,
                "year": int(year),
                "trades": int(len(sub)),
                "expectancy_R": float(r.mean()) if not r.empty else math.nan,
                "pf": _profit_factor(r),
                "winrate": float((r > 0).mean()) if not r.empty else math.nan,
            }
        )
    year_df = pd.DataFrame(y_rows)

    df["hour_utc"] = df[t_col].dt.hour
    h_rows: list[dict[str, Any]] = []
    for hour, sub in df.groupby("hour_utc", sort=True):
        r = sub[r_col]
        h_rows.append(
            {
                "run_id": run_id,
                "hour_utc": int(hour),
                "trades": int(len(sub)),
                "expectancy_R": float(r.mean()) if not r.empty else math.nan,
                "pf": _profit_factor(r),
                "winrate": float((r > 0).mean()) if not r.empty else math.nan,
            }
        )
    hour_df = pd.DataFrame(h_rows)

    summary = {
        "run_id": run_id,
        "status": "ok",
        "trades": int(len(df)),
        "start_ts": t0.isoformat(),
        "end_ts": t1.isoformat(),
        "segments_negative": int((pd.to_numeric(seg_df["expectancy_R"], errors="coerce") < 0).sum()),
        "years_negative": int((pd.to_numeric(year_df["expectancy_R"], errors="coerce") < 0).sum()),
        "hours_negative_ge10": int(
            (
                (pd.to_numeric(hour_df["expectancy_R"], errors="coerce") < 0)
                & (pd.to_numeric(hour_df["trades"], errors="coerce") >= 10)
            ).sum()
        ),
    }
    return seg_df, year_df, hour_df, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Temporal stability review from run trades.")
    parser.add_argument("--scoreboard", required=True, help="Scoreboard CSV with run_id/status.")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="outputs/edge_discovery_overnight")
    parser.add_argument("--segments", type=int, default=4)
    args = parser.parse_args()

    scoreboard = Path(args.scoreboard)
    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not scoreboard.exists():
        raise FileNotFoundError(f"Missing scoreboard csv: {scoreboard.as_posix()}")
    score = pd.read_csv(scoreboard)
    if score.empty:
        raise RuntimeError("Scoreboard is empty.")
    if "run_id" not in score.columns:
        raise RuntimeError("Scoreboard must include run_id column.")

    ok_mask = score["status"].astype(str).str.lower().eq("ok") if "status" in score.columns else pd.Series([True] * len(score))
    run_ids = score.loc[ok_mask, "run_id"].astype(str).dropna().unique().tolist()

    seg_all: list[pd.DataFrame] = []
    year_all: list[pd.DataFrame] = []
    hour_all: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    for run_id in run_ids:
        run_dir = runs_root / run_id
        seg_df, year_df, hour_df, summary = _review_run(run_id=run_id, run_dir=run_dir, segments=int(args.segments))
        if not seg_df.empty:
            seg_all.append(seg_df)
        if not year_df.empty:
            year_all.append(year_df)
        if not hour_df.empty:
            hour_all.append(hour_df)
        summaries.append(summary)

    seg_out = out_dir / "edge_discovery_temporal_segments.csv"
    year_out = out_dir / "edge_discovery_yearly.csv"
    hour_out = out_dir / "edge_discovery_hourly.csv"
    summary_out = out_dir / "edge_discovery_temporal_summary.json"

    pd.concat(seg_all, ignore_index=True).to_csv(seg_out, index=False) if seg_all else pd.DataFrame().to_csv(seg_out, index=False)
    pd.concat(year_all, ignore_index=True).to_csv(year_out, index=False) if year_all else pd.DataFrame().to_csv(year_out, index=False)
    pd.concat(hour_all, ignore_index=True).to_csv(hour_out, index=False) if hour_all else pd.DataFrame().to_csv(hour_out, index=False)

    payload = {
        "runs_reviewed": run_ids,
        "segments": int(args.segments),
        "rows_segments": 0 if not seg_all else int(sum(len(x) for x in seg_all)),
        "rows_yearly": 0 if not year_all else int(sum(len(x) for x in year_all)),
        "rows_hourly": 0 if not hour_all else int(sum(len(x) for x in hour_all)),
        "summary_by_run": summaries,
        "outputs": {
            "segments_csv": seg_out.as_posix(),
            "yearly_csv": year_out.as_posix(),
            "hourly_csv": hour_out.as_posix(),
        },
    }
    summary_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote: {seg_out.as_posix()}")
    print(f"Wrote: {year_out.as_posix()}")
    print(f"Wrote: {hour_out.as_posix()}")
    print(f"Wrote: {summary_out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
