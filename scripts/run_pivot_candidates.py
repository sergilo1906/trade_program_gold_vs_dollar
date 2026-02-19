from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = [
    "configs/config_v3_PIVOT_B1.yaml",
    "configs/config_v3_PIVOT_B2.yaml",
    "configs/config_v3_PIVOT_B3.yaml",
    "configs/config_v3_PIVOT_B4.yaml",
]


def _short(text: str, limit: int = 700) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _md_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data_"
    float_cols = float_cols or set()
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for c in cols:
            v = row[c]
            if pd.isna(v):
                vals.append("")
            elif c in float_cols:
                vals.append(f"{float(v):.6f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _read_baseline_trade_count(path: Path) -> int:
    if not path.exists():
        return 0
    df = pd.read_csv(path)
    if df.empty:
        return 0
    base = df[pd.to_numeric(df["factor"], errors="coerce") == 1.0]
    return int(pd.to_numeric(base["trades"], errors="coerce").fillna(0).sum())


def _compute_profitability(
    runs_csv: Path,
    runs_root: Path,
    equity_start: float,
) -> dict[str, Any]:
    if not runs_csv.exists():
        return {
            "total_pnl": math.nan,
            "total_return": math.nan,
            "days": math.nan,
            "annualized": math.nan,
            "monthly_equiv": math.nan,
            "trades_per_month": math.nan,
        }
    runs = pd.read_csv(runs_csv)
    if runs.empty:
        return {
            "total_pnl": math.nan,
            "total_return": math.nan,
            "days": math.nan,
            "annualized": math.nan,
            "monthly_equiv": math.nan,
            "trades_per_month": math.nan,
        }

    total_pnl = 0.0
    total_trades = 0
    for rid in runs["run_id"].astype(str):
        tpath = runs_root / rid / "trades.csv"
        if not tpath.exists():
            continue
        tdf = pd.read_csv(tpath)
        pnl = pd.to_numeric(tdf.get("pnl"), errors="coerce").dropna()
        total_pnl += float(pnl.sum()) if not pnl.empty else 0.0
        total_trades += int(len(tdf))

    start_ts = pd.to_datetime(runs["start_ts"], errors="coerce")
    end_ts = pd.to_datetime(runs["end_ts"], errors="coerce")
    if start_ts.notna().any() and end_ts.notna().any():
        days = float((end_ts.max() - start_ts.min()).total_seconds() / 86400.0)
    else:
        days = math.nan

    total_return = (total_pnl / equity_start) if equity_start > 0 else math.nan
    if pd.isna(days) or days <= 0 or pd.isna(total_return) or total_return <= -1.0:
        annualized = math.nan
        monthly_equiv = math.nan
        trades_per_month = math.nan
    else:
        annualized = float((1.0 + total_return) ** (365.0 / days) - 1.0)
        monthly_equiv = float((1.0 + annualized) ** (1.0 / 12.0) - 1.0)
        trades_per_month = float(total_trades / (days / 30.44))

    return {
        "total_pnl": total_pnl,
        "total_return": total_return,
        "days": days,
        "annualized": annualized,
        "monthly_equiv": monthly_equiv,
        "trades_per_month": trades_per_month,
    }


def _evaluate_candidate(
    cfg_path: Path,
    windows: str,
    data_path: Path,
    runs_root: Path,
    resamples: int,
    seed: int,
    baseline_total_trades: int,
    baseline_w4_trades: int,
    equity_start: float,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    cand_name = cfg_path.stem
    out_dir = ROOT / "outputs" / "rolling_holdout_pivot" / cand_name
    report_path = ROOT / "docs" / f"ROLLING_HOLDOUT_{cand_name}.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    row: dict[str, Any] = {
        "candidate": cand_name,
        "config": cfg_path.as_posix(),
        "status": "ok",
        "windows_pass_1p2": 0,
        "windows_pass_1p5": 0,
        "w4_pf_1p0": math.nan,
        "w4_exp_1p0": math.nan,
        "w4_trades_1p0": 0,
        "w4_pf_1p2": math.nan,
        "w4_exp_1p2": math.nan,
        "w4_trades_1p2": 0,
        "w4_pf_1p5": math.nan,
        "w4_exp_1p5": math.nan,
        "w4_trades_1p5": 0,
        "w4_pass_1p2": False,
        "w4_pass_1p5": False,
        "total_trades_1p0": 0,
        "global_trade_retention_pct": math.nan,
        "global_trade_loss_pct": math.nan,
        "overfilter_gt35pct": False,
        "w4_trade_retention_vs44_pct": math.nan,
        "run_ids": "",
        "rolling_runs_csv": (out_dir / "rolling_holdout_runs.csv").as_posix(),
        "posthoc_csv": (ROOT / "outputs" / "posthoc_cost_stress" / f"rolling_posthoc_cost_stress_{cand_name}.csv").as_posix(),
        "total_return": math.nan,
        "annualized": math.nan,
        "monthly_equiv": math.nan,
        "expectancy_R_oos_mean": math.nan,
        "trades_per_month_est": math.nan,
    }

    roll_cmd = [
        sys.executable,
        "scripts/rolling_holdout_eval.py",
        "--data",
        data_path.as_posix(),
        "--config",
        cfg_path.as_posix(),
        "--windows",
        windows,
        "--runs-root",
        runs_root.as_posix(),
        "--out-dir",
        out_dir.as_posix(),
        "--report",
        report_path.as_posix(),
        "--resamples",
        str(int(resamples)),
        "--seed",
        str(int(seed)),
    ]
    roll_res = _run_cmd(roll_cmd)
    if roll_res.returncode != 0:
        row["status"] = "failed_rolling"
        notes.append(f"{cand_name}: rolling failed: {_short(roll_res.stderr)}")
        return row, notes

    runs_csv = out_dir / "rolling_holdout_runs.csv"
    if not runs_csv.exists():
        row["status"] = "failed_rolling_missing_csv"
        notes.append(f"{cand_name}: missing rolling csv {runs_csv.as_posix()}")
        return row, notes
    r_df = pd.read_csv(runs_csv)
    ok = r_df[r_df["status"] == "ok"].copy() if "status" in r_df.columns else r_df.copy()
    run_ids = ok["run_id"].astype(str).tolist() if not ok.empty else []
    row["run_ids"] = ",".join(run_ids)
    if not run_ids:
        row["status"] = "failed_no_run_ids"
        notes.append(f"{cand_name}: no successful rolling run_ids")
        return row, notes

    posthoc_csv = ROOT / "outputs" / "posthoc_cost_stress" / f"rolling_posthoc_cost_stress_{cand_name}.csv"
    posthoc_cmd = [
        sys.executable,
        "scripts/posthoc_cost_stress_batch.py",
        "--runs",
        *run_ids,
        "--window-map-csv",
        runs_csv.as_posix(),
        "--factors",
        "1.2",
        "1.5",
        "--seed",
        str(int(seed)),
        "--resamples",
        str(int(resamples)),
        "--out",
        posthoc_csv.as_posix(),
    ]
    posthoc_res = _run_cmd(posthoc_cmd)
    if posthoc_res.returncode != 0:
        row["status"] = "failed_posthoc"
        notes.append(f"{cand_name}: posthoc batch failed: {_short(posthoc_res.stderr)}")
        return row, notes
    if not posthoc_csv.exists():
        row["status"] = "failed_posthoc_missing_csv"
        notes.append(f"{cand_name}: missing posthoc csv {posthoc_csv.as_posix()}")
        return row, notes

    p_df = pd.read_csv(posthoc_csv)
    if p_df.empty:
        row["status"] = "failed_empty_posthoc"
        notes.append(f"{cand_name}: empty posthoc csv")
        return row, notes

    p_df["factor"] = pd.to_numeric(p_df["factor"], errors="coerce")
    p_df["pf"] = pd.to_numeric(p_df["pf"], errors="coerce")
    p_df["expectancy_R"] = pd.to_numeric(p_df["expectancy_R"], errors="coerce")
    p_df["trades"] = pd.to_numeric(p_df["trades"], errors="coerce")

    for factor, out_col in ((1.2, "windows_pass_1p2"), (1.5, "windows_pass_1p5")):
        sub = p_df[p_df["factor"] == factor].copy()
        pass_mask = (sub["pf"] > 1.0) & (sub["expectancy_R"] > 0.0)
        row[out_col] = int(pass_mask.sum())

    for factor, suffix in ((1.0, "1p0"), (1.2, "1p2"), (1.5, "1p5")):
        sub = p_df[(p_df["factor"] == factor) & (p_df["window"] == "W4")]
        if not sub.empty:
            x = sub.iloc[0]
            row[f"w4_pf_{suffix}"] = float(x["pf"])
            row[f"w4_exp_{suffix}"] = float(x["expectancy_R"])
            row[f"w4_trades_{suffix}"] = int(x["trades"])
        row[f"w4_pass_{suffix}"] = bool(
            (not pd.isna(row[f"w4_pf_{suffix}"]))
            and (not pd.isna(row[f"w4_exp_{suffix}"]))
            and (float(row[f"w4_pf_{suffix}"]) > 1.0)
            and (float(row[f"w4_exp_{suffix}"]) > 0.0)
        )

    base = p_df[p_df["factor"] == 1.0].copy()
    row["total_trades_1p0"] = int(pd.to_numeric(base["trades"], errors="coerce").fillna(0).sum())
    row["expectancy_R_oos_mean"] = float(pd.to_numeric(base["expectancy_R"], errors="coerce").mean())
    if baseline_total_trades > 0:
        row["global_trade_retention_pct"] = 100.0 * float(row["total_trades_1p0"]) / float(baseline_total_trades)
        row["global_trade_loss_pct"] = 100.0 - float(row["global_trade_retention_pct"])
        row["overfilter_gt35pct"] = bool(float(row["global_trade_loss_pct"]) > 35.0)
    if baseline_w4_trades > 0 and row["w4_trades_1p0"] > 0:
        row["w4_trade_retention_vs44_pct"] = 100.0 * float(row["w4_trades_1p0"]) / float(baseline_w4_trades)

    prof = _compute_profitability(runs_csv=runs_csv, runs_root=runs_root, equity_start=equity_start)
    row["total_return"] = prof["total_return"]
    row["annualized"] = prof["annualized"]
    row["monthly_equiv"] = prof["monthly_equiv"]
    row["trades_per_month_est"] = prof["trades_per_month"]

    return row, notes


def _pick_top_candidates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    base = df.copy()
    base["windows_pass_1p2"] = pd.to_numeric(base["windows_pass_1p2"], errors="coerce")
    base["windows_pass_1p5"] = pd.to_numeric(base["windows_pass_1p5"], errors="coerce")
    base["w4_pf_1p2"] = pd.to_numeric(base["w4_pf_1p2"], errors="coerce")
    base["w4_exp_1p2"] = pd.to_numeric(base["w4_exp_1p2"], errors="coerce")
    base["annualized"] = pd.to_numeric(base["annualized"], errors="coerce")
    base["w4_pass_1p2"] = base["w4_pass_1p2"].astype(bool)
    base["overfilter_gt35pct"] = base["overfilter_gt35pct"].astype(bool)

    # Acceptance tier enforces the non-negotiable +20 gate and trade-loss control.
    base["accept_gate_1p2"] = (
        (base["windows_pass_1p2"] >= 4)
        & base["w4_pass_1p2"]
        & (~base["overfilter_gt35pct"])
    )
    base["penalty_overfilter"] = base["overfilter_gt35pct"].astype(int)
    ranked = base.sort_values(
        [
            "accept_gate_1p2",
            "penalty_overfilter",
            "w4_pass_1p2",
            "windows_pass_1p2",
            "windows_pass_1p5",
            "w4_pf_1p2",
            "w4_exp_1p2",
            "annualized",
        ],
        ascending=[False, True, False, False, False, False, False, False],
    ).reset_index(drop=True)
    return ranked


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Route B pivot candidates and build scoreboard.")
    parser.add_argument("--candidates", nargs="+", default=DEFAULT_CANDIDATES)
    parser.add_argument("--data", default="data/xauusd_m5_backtest_ready.csv")
    parser.add_argument("--windows", default="0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--equity-start", type=float, default=10000.0)
    parser.add_argument(
        "--baseline-posthoc",
        default="outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv",
    )
    parser.add_argument("--baseline-w4-trades", type=int, default=44)
    parser.add_argument("--out-csv", default="outputs/rolling_holdout_pivot/pivot_scoreboard.csv")
    parser.add_argument("--out-json", default="outputs/rolling_holdout_pivot/pivot_scoreboard_summary.json")
    parser.add_argument("--out-md", default="docs/PIVOT_SCOREBOARD.md")
    args = parser.parse_args()

    data_path = (ROOT / args.data) if not Path(args.data).is_absolute() else Path(args.data)
    runs_root = (ROOT / args.runs_root) if not Path(args.runs_root).is_absolute() else Path(args.runs_root)

    baseline_path = (ROOT / args.baseline_posthoc) if not Path(args.baseline_posthoc).is_absolute() else Path(args.baseline_posthoc)
    baseline_total_trades = _read_baseline_trade_count(baseline_path)
    if baseline_total_trades <= 0:
        baseline_total_trades = 168

    rows: list[dict[str, Any]] = []
    notes: list[str] = []

    for cand in args.candidates:
        cfg = (ROOT / cand) if not Path(cand).is_absolute() else Path(cand)
        if not cfg.exists():
            rows.append(
                {
                    "candidate": cfg.stem,
                    "config": cfg.as_posix(),
                    "status": "missing_config",
                }
            )
            notes.append(f"{cfg.stem}: missing config `{cfg.as_posix()}`")
            continue
        row, n = _evaluate_candidate(
            cfg_path=cfg,
            windows=args.windows,
            data_path=data_path,
            runs_root=runs_root,
            resamples=int(args.resamples),
            seed=int(args.seed),
            baseline_total_trades=int(baseline_total_trades),
            baseline_w4_trades=int(args.baseline_w4_trades),
            equity_start=float(args.equity_start),
        )
        rows.append(row)
        notes.extend(n)

    out_df = pd.DataFrame(rows)
    ranked = _pick_top_candidates(out_df)

    out_csv = ROOT / args.out_csv
    out_json = ROOT / args.out_json
    out_md = ROOT / args.out_md
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    ranked.to_csv(out_csv, index=False)

    winner: dict[str, Any] | None = None
    if not ranked.empty:
        winner_row = ranked.iloc[0]
        winner = {k: _to_jsonable(winner_row[k]) for k in ranked.columns}

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "baseline_total_trades": int(baseline_total_trades),
        "baseline_w4_trades": int(args.baseline_w4_trades),
        "candidates": [str(c) for c in args.candidates],
        "winner": winner,
        "notes": notes,
        "scoreboard_csv": out_csv.as_posix(),
    }
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    table_cols = [
        "candidate",
        "status",
        "windows_pass_1p2",
        "windows_pass_1p5",
        "w4_pf_1p2",
        "w4_exp_1p2",
        "w4_trades_1p0",
        "global_trade_retention_pct",
        "overfilter_gt35pct",
        "monthly_equiv",
        "annualized",
    ]
    table = ranked[[c for c in table_cols if c in ranked.columns]].copy() if not ranked.empty else ranked

    lines: list[str] = []
    lines.append("# Pivot Scoreboard (Route B)")
    lines.append("")
    lines.append(f"- generated_utc: {summary['generated_utc']}")
    lines.append(f"- baseline_total_trades: `{baseline_total_trades}`")
    lines.append(f"- baseline_w4_trades: `{args.baseline_w4_trades}`")
    lines.append("")
    lines.append("## Candidate summary")
    lines.append(
        _md_table(
            table,
            float_cols={
                "w4_pf_1p2",
                "w4_exp_1p2",
                "global_trade_retention_pct",
                "monthly_equiv",
                "annualized",
            },
        )
    )
    lines.append("")
    lines.append("## Winner")
    if winner is None:
        lines.append("- winner: `NA`")
    else:
        lines.append(f"- winner_candidate: `{winner.get('candidate')}`")
        lines.append(f"- status: `{winner.get('status')}`")
        lines.append(
            f"- windows_pass_1p2: `{winner.get('windows_pass_1p2')}` / 4, "
            f"windows_pass_1p5: `{winner.get('windows_pass_1p5')}` / 4"
        )
        lines.append(
            f"- W4 +20%: PF `{winner.get('w4_pf_1p2')}`, expectancy_R `{winner.get('w4_exp_1p2')}`, "
            f"trades `{winner.get('w4_trades_1p2')}`"
        )
        lines.append(
            f"- trade retention global: `{winner.get('global_trade_retention_pct')}`%, "
            f"overfilter_gt35pct: `{winner.get('overfilter_gt35pct')}`"
        )
        lines.append(
            f"- profitability approx: monthly_equiv `{winner.get('monthly_equiv')}`, annualized `{winner.get('annualized')}`"
        )
    if notes:
        lines.append("")
        lines.append("## Notes")
        for n in notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- scoreboard_csv: `{out_csv.as_posix()}`")
    lines.append(f"- scoreboard_json: `{out_json.as_posix()}`")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {out_csv.as_posix()}")
    print(f"Wrote: {out_json.as_posix()}")
    print(f"Wrote: {out_md.as_posix()}")
    if winner is not None:
        print(f"winner_candidate: {winner.get('candidate')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
