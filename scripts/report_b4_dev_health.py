from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
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


def _pf_from_series(r: pd.Series) -> float:
    vals = pd.to_numeric(r, errors="coerce").dropna()
    if vals.empty:
        return float("nan")
    gross_win = float(vals[vals > 0].sum())
    gross_loss = float((-vals[vals < 0]).sum())
    if gross_loss > 0:
        return gross_win / gross_loss
    return float("inf") if gross_win > 0 else float("nan")


def _find_r_col(df: pd.DataFrame) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        found = lowered.get(cand.lower())
        if found is not None:
            return found
    return None


def _safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _resolve_run_id(run_id: str | None, summary_path: Path) -> str:
    if run_id:
        return str(run_id).strip()
    if not summary_path.exists():
        raise RuntimeError(
            "Missing default summary file and --run-id not provided: "
            f"{summary_path.as_posix()}"
        )
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"Unable to parse summary json for default run-id: {summary_path.as_posix()}"
        ) from exc
    baseline = str(payload.get("baseline_run_id", "")).strip()
    if not baseline:
        raise RuntimeError(
            "Summary file does not include baseline_run_id and --run-id was not provided: "
            f"{summary_path.as_posix()}"
        )
    return baseline


def _drawdown_from_r(trades: pd.DataFrame, r_col: str, sort_col: str | None) -> float:
    work = trades.copy()
    if sort_col is not None and sort_col in work.columns:
        work = work.sort_values(sort_col).reset_index(drop=True)
    r = pd.to_numeric(work[r_col], errors="coerce").fillna(0.0)
    cum_r = r.cumsum()
    peak = cum_r.cummax()
    dd = peak - cum_r
    if dd.empty:
        return float("nan")
    return float(dd.max())


def _session_bucket(hour_utc: int) -> str:
    if 0 <= hour_utc < 7:
        return "ASIA"
    if 7 <= hour_utc < 13:
        return "LONDON"
    if 13 <= hour_utc < 21:
        return "NY"
    return "OFF"


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


def _compute_cost_analysis(trades: pd.DataFrame, missing: list[str]) -> tuple[dict[str, Any], pd.DataFrame]:
    needed = {"direction", "entry_mid", "exit_mid", "pnl", "risk_amount"}
    if not needed.issubset(set(trades.columns)):
        missing.append(
            "Cost decomposition unavailable: need columns "
            "`direction, entry_mid, exit_mid, pnl, risk_amount` in trades.csv."
        )
        return {
            "available": False,
            "expectancy_R_net": None,
            "expectancy_R_gross_mid": None,
            "cost_R_mean": None,
            "cost_R_total": None,
            "cost_pnl_total": None,
        }, trades

    work = trades.copy()
    qty = pd.to_numeric(work["closed_size"], errors="coerce")
    if qty.isna().all() and ("size" in work.columns):
        qty = pd.to_numeric(work["size"], errors="coerce")
    risk_amount = pd.to_numeric(work["risk_amount"], errors="coerce")
    pnl_net = pd.to_numeric(work["pnl"], errors="coerce")
    entry_mid = pd.to_numeric(work["entry_mid"], errors="coerce")
    exit_mid = pd.to_numeric(work["exit_mid"], errors="coerce")
    direction = work["direction"].astype(str).str.upper()

    gross_pnl_mid = pd.Series(index=work.index, dtype="float64")
    long_mask = direction == "LONG"
    short_mask = direction == "SHORT"
    gross_pnl_mid.loc[long_mask] = (
        (exit_mid.loc[long_mask] - entry_mid.loc[long_mask]) * qty.loc[long_mask]
    )
    gross_pnl_mid.loc[short_mask] = (
        (entry_mid.loc[short_mask] - exit_mid.loc[short_mask]) * qty.loc[short_mask]
    )

    valid_mask = gross_pnl_mid.notna() & pnl_net.notna() & risk_amount.notna() & (risk_amount > 0)
    if valid_mask.sum() == 0:
        missing.append("Cost decomposition unavailable after coercion (no valid trade rows).")
        return {
            "available": False,
            "expectancy_R_net": None,
            "expectancy_R_gross_mid": None,
            "cost_R_mean": None,
            "cost_R_total": None,
            "cost_pnl_total": None,
        }, trades

    work = work.loc[valid_mask].copy()
    gross_pnl_mid = gross_pnl_mid.loc[valid_mask]
    pnl_net = pnl_net.loc[valid_mask]
    risk_amount = risk_amount.loc[valid_mask]

    work["gross_pnl_mid"] = gross_pnl_mid
    work["cost_pnl"] = gross_pnl_mid - pnl_net
    work["r_gross_mid"] = gross_pnl_mid / risk_amount
    work["cost_r"] = work["r_gross_mid"] - pd.to_numeric(work["r_multiple"], errors="coerce")

    summary = {
        "available": True,
        "expectancy_R_net": _safe_float(pd.to_numeric(work["r_multiple"], errors="coerce").mean()),
        "expectancy_R_gross_mid": _safe_float(pd.to_numeric(work["r_gross_mid"], errors="coerce").mean()),
        "cost_R_mean": _safe_float(pd.to_numeric(work["cost_r"], errors="coerce").mean()),
        "cost_R_total": _safe_float(pd.to_numeric(work["cost_r"], errors="coerce").sum()),
        "cost_pnl_total": _safe_float(pd.to_numeric(work["cost_pnl"], errors="coerce").sum()),
    }
    return summary, work


def main() -> int:
    parser = argparse.ArgumentParser(description="Build baseline B4 DEV health report from an existing run.")
    parser.add_argument("--run-id", default=None, help="Run id under outputs/runs. Optional if summary has baseline_run_id.")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument(
        "--summary-json-default",
        default="outputs/v4_dev_runs/v4_candidates_scoreboard_summary.json",
    )
    parser.add_argument("--out-dir", default="outputs/b4_dev_health")
    args = parser.parse_args()

    summary_default = Path(args.summary_json_default)
    run_id = _resolve_run_id(args.run_id, summary_default)
    run_dir = Path(args.runs_root) / run_id
    trades_path = run_dir / "trades.csv"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_summary = out_dir / "b4_dev_health_summary.json"
    out_monthly = out_dir / "b4_dev_health_monthly.csv"
    out_md = out_dir / "b4_dev_health.md"

    missing_data: list[str] = []
    if not run_dir.exists():
        missing_data.append(f"Run directory not found: {run_dir.as_posix()}")
    if not trades_path.exists():
        missing_data.append(f"Missing trades.csv: {trades_path.as_posix()}")

    if missing_data:
        payload = {
            "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "run_id": run_id,
            "run_dir": run_dir.as_posix(),
            "status": "incomplete_missing_data",
            "missing_data": missing_data,
        }
        out_summary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        pd.DataFrame(columns=["month", "trades", "expectancy_R", "pf", "winrate", "avg_R", "median_R"]).to_csv(
            out_monthly, index=False
        )
        md_lines = [
            "# B4 DEV Health Report",
            "",
            f"- run_id: `{run_id}`",
            f"- run_dir: `{run_dir.as_posix()}`",
            "",
            "## MISSING DATA",
        ]
        md_lines.extend([f"- {item}" for item in missing_data])
        md_lines.append("")
        out_md.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"Wrote: {out_summary.as_posix()}")
        print(f"Wrote: {out_monthly.as_posix()}")
        print(f"Wrote: {out_md.as_posix()}")
        return 0

    trades = pd.read_csv(trades_path)
    if trades.empty:
        missing_data.append("trades.csv has 0 rows.")

    r_col = _find_r_col(trades)
    if r_col is None:
        missing_data.append(
            "No R column found in trades.csv. Expected one of: "
            + ", ".join(R_COL_CANDIDATES)
        )
        trades["r_multiple"] = pd.NA
        r_col = "r_multiple"

    entry_ts_col = None
    if "entry_time" in trades.columns:
        trades["entry_ts"] = pd.to_datetime(trades["entry_time"], errors="coerce")
        if trades["entry_ts"].notna().any():
            entry_ts_col = "entry_ts"
        else:
            missing_data.append("entry_time present but not parseable to datetime.")
    else:
        missing_data.append("entry_time missing in trades.csv (monthly/hourly breakdown limited).")

    exit_ts_col = None
    if "exit_time" in trades.columns:
        trades["exit_ts"] = pd.to_datetime(trades["exit_time"], errors="coerce")
        if trades["exit_ts"].notna().any():
            exit_ts_col = "exit_ts"

    if exit_ts_col is not None:
        sort_col = exit_ts_col
    elif entry_ts_col is not None:
        sort_col = entry_ts_col
    else:
        sort_col = None
        missing_data.append("No usable timestamp in trades.csv. Drawdown uses file row order.")

    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    trades_count = int(r.size)
    winrate = float((r > 0).mean()) if trades_count > 0 else float("nan")
    expectancy_r = float(r.mean()) if trades_count > 0 else float("nan")
    pf = _pf_from_series(r) if trades_count > 0 else float("nan")
    avg_r = expectancy_r
    median_r = float(r.median()) if trades_count > 0 else float("nan")
    mdd_r = _drawdown_from_r(trades, r_col, sort_col) if trades_count > 0 else float("nan")

    monthly_df = pd.DataFrame(
        columns=["month", "trades", "expectancy_R", "pf", "winrate", "avg_R", "median_R"]
    )
    if entry_ts_col is not None and trades_count > 0:
        work = trades.copy()
        work["r_val"] = pd.to_numeric(work[r_col], errors="coerce")
        work = work.dropna(subset=["entry_ts", "r_val"]).copy()
        if not work.empty:
            work["month"] = work["entry_ts"].dt.to_period("M").astype(str)
            monthly_rows: list[dict[str, Any]] = []
            for month, grp in work.groupby("month"):
                rvals = pd.to_numeric(grp["r_val"], errors="coerce").dropna()
                monthly_rows.append(
                    {
                        "month": str(month),
                        "trades": int(rvals.size),
                        "expectancy_R": float(rvals.mean()) if not rvals.empty else float("nan"),
                        "pf": _pf_from_series(rvals),
                        "winrate": float((rvals > 0).mean()) if not rvals.empty else float("nan"),
                        "avg_R": float(rvals.mean()) if not rvals.empty else float("nan"),
                        "median_R": float(rvals.median()) if not rvals.empty else float("nan"),
                    }
                )
            monthly_df = pd.DataFrame(monthly_rows).sort_values("month").reset_index(drop=True)
    else:
        missing_data.append("Monthly breakdown unavailable (no parseable entry_time).")

    by_hour_df = pd.DataFrame(columns=["hour_utc", "trades", "expectancy_R", "pf", "winrate"])
    by_session_df = pd.DataFrame(columns=["session", "trades", "expectancy_R", "pf", "winrate"])
    if entry_ts_col is not None and trades_count > 0:
        work = trades.copy()
        work["r_val"] = pd.to_numeric(work[r_col], errors="coerce")
        work = work.dropna(subset=["entry_ts", "r_val"]).copy()
        if not work.empty:
            work["hour_utc"] = work["entry_ts"].dt.hour.astype(int)
            hour_rows: list[dict[str, Any]] = []
            for hour, grp in work.groupby("hour_utc"):
                rvals = pd.to_numeric(grp["r_val"], errors="coerce").dropna()
                hour_rows.append(
                    {
                        "hour_utc": int(hour),
                        "trades": int(rvals.size),
                        "expectancy_R": float(rvals.mean()) if not rvals.empty else float("nan"),
                        "pf": _pf_from_series(rvals),
                        "winrate": float((rvals > 0).mean()) if not rvals.empty else float("nan"),
                    }
                )
            by_hour_df = pd.DataFrame(hour_rows).sort_values("hour_utc").reset_index(drop=True)

            work["session"] = work["hour_utc"].apply(_session_bucket)
            session_rows: list[dict[str, Any]] = []
            for session, grp in work.groupby("session"):
                rvals = pd.to_numeric(grp["r_val"], errors="coerce").dropna()
                session_rows.append(
                    {
                        "session": str(session),
                        "trades": int(rvals.size),
                        "expectancy_R": float(rvals.mean()) if not rvals.empty else float("nan"),
                        "pf": _pf_from_series(rvals),
                        "winrate": float((rvals > 0).mean()) if not rvals.empty else float("nan"),
                    }
                )
            by_session_df = pd.DataFrame(session_rows).sort_values("session").reset_index(drop=True)
    else:
        missing_data.append("Hourly/session breakdown unavailable (no parseable entry_time).")

    cost_summary, trades_with_cost = _compute_cost_analysis(trades, missing_data)

    monthly_df.to_csv(out_monthly, index=False)

    summary_payload = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "run_dir": run_dir.as_posix(),
        "data_sources": {
            "trades_csv": trades_path.as_posix(),
            "summary_default": summary_default.as_posix(),
        },
        "metrics": {
            "trades": trades_count,
            "winrate": winrate,
            "expectancy_R": expectancy_r,
            "pf": pf,
            "avg_R": avg_r,
            "median_R": median_r,
            "max_drawdown_R": mdd_r,
            "drawdown_method": (
                f"cumulative R ordered by `{sort_col}`"
                if sort_col is not None
                else "cumulative R in file row order (timestamp unavailable)"
            ),
        },
        "cost_analysis": cost_summary,
        "monthly_rows": int(len(monthly_df)),
        "hourly_rows": int(len(by_hour_df)),
        "session_rows": int(len(by_session_df)),
        "missing_data": missing_data,
    }
    out_summary.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    core_df = pd.DataFrame(
        [
            {
                "trades": trades_count,
                "winrate": winrate,
                "expectancy_R": expectancy_r,
                "pf": pf,
                "avg_R": avg_r,
                "median_R": median_r,
                "max_drawdown_R": mdd_r,
            }
        ]
    )
    cost_df = pd.DataFrame([cost_summary])

    md_lines: list[str] = []
    md_lines.append("# B4 DEV Health Report")
    md_lines.append("")
    md_lines.append(f"- run_id: `{run_id}`")
    md_lines.append(f"- run_dir: `{run_dir.as_posix()}`")
    md_lines.append("")
    md_lines.append("## Core Metrics")
    md_lines.append("")
    md_lines.append(
        _md_table(
            core_df,
            float_cols={"winrate", "expectancy_R", "pf", "avg_R", "median_R", "max_drawdown_R"},
        )
    )
    md_lines.append("")
    md_lines.append("## Cost Analysis (Before/After)")
    md_lines.append("")
    md_lines.append(
        _md_table(
            cost_df[
                [
                    "available",
                    "expectancy_R_net",
                    "expectancy_R_gross_mid",
                    "cost_R_mean",
                    "cost_R_total",
                    "cost_pnl_total",
                ]
            ],
            float_cols={
                "expectancy_R_net",
                "expectancy_R_gross_mid",
                "cost_R_mean",
                "cost_R_total",
                "cost_pnl_total",
            },
        )
    )
    md_lines.append("")
    md_lines.append("## Monthly Breakdown")
    md_lines.append("")
    md_lines.append(
        _md_table(
            monthly_df,
            float_cols={"expectancy_R", "pf", "winrate", "avg_R", "median_R"},
        )
    )
    md_lines.append("")
    md_lines.append("## Hourly Breakdown (entry_time UTC)")
    md_lines.append("")
    md_lines.append(
        _md_table(
            by_hour_df,
            float_cols={"expectancy_R", "pf", "winrate"},
        )
    )
    md_lines.append("")
    md_lines.append("## Session Breakdown (derived from entry hour)")
    md_lines.append("")
    md_lines.append(
        _md_table(
            by_session_df,
            float_cols={"expectancy_R", "pf", "winrate"},
        )
    )
    md_lines.append("")
    md_lines.append("## MISSING DATA")
    if missing_data:
        md_lines.extend([f"- {item}" for item in missing_data])
    else:
        md_lines.append("- none")
    md_lines.append("")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote: {out_summary.as_posix()}")
    print(f"Wrote: {out_monthly.as_posix()}")
    print(f"Wrote: {out_md.as_posix()}")
    print(
        "Decision quicklook | "
        f"run_id={run_id} | trades={trades_count} | PF={pf:.6f} | expectancy_R={expectancy_r:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
