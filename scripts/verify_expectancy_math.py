from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
R_COL_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def _load_scoreboard(primary: Path, fallback: Path) -> tuple[pd.DataFrame, Path]:
    if primary.exists() and primary.stat().st_size > 0:
        return pd.read_csv(primary), primary
    if fallback.exists() and fallback.stat().st_size > 0:
        return pd.read_csv(fallback), fallback
    raise FileNotFoundError(
        "No valid scoreboard found. Checked:\n"
        f"- {primary.as_posix()} (missing or empty)\n"
        f"- {fallback.as_posix()} (missing or empty)"
    )


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        c = lowered.get(cand.lower())
        if c is not None:
            return c
    raise ValueError(f"No R column found. Columns={list(df.columns)}")


def _safe_float(value: Any) -> float:
    try:
        v = float(value)
        return v
    except Exception:
        return math.nan


def _profit_factor(r: pd.Series) -> float:
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss > 0:
        return gross_win / gross_loss
    return float("inf") if gross_win > 0 else math.nan


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
                vals.append(f"{float(v):.8f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify expectancy/PF/trades math from trades.csv vs scoreboard.")
    parser.add_argument("--scoreboard", default="outputs/v4_dev_runs/v4_candidates_scoreboard.csv")
    parser.add_argument(
        "--scoreboard-fallback",
        default="docs/_snapshots/v4_dev_runs_2021_2023/v4_candidates_scoreboard.csv",
    )
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="docs/_snapshots/v4a_expectancy_audit_2021_2023")
    parser.add_argument("--tol-expectancy", type=float, default=1e-6)
    parser.add_argument("--tol-pf", type=float, default=1e-6)
    parser.add_argument("--tol-winrate", type=float, default=1e-6)
    args = parser.parse_args()

    scoreboard_path = _resolve(args.scoreboard)
    scoreboard_fallback = _resolve(args.scoreboard_fallback)
    runs_root = _resolve(args.runs_root)
    out_dir = _resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    score_df, chosen_score_path = _load_scoreboard(scoreboard_path, scoreboard_fallback)
    required = {"candidate", "run_id", "expectancy_R", "pf", "trades", "winrate"}
    missing_required = required - set(score_df.columns)
    if missing_required:
        raise ValueError(f"Scoreboard missing required columns: {sorted(missing_required)}")

    rows: list[dict[str, Any]] = []
    for _, row in score_df.iterrows():
        run_id = str(row.get("run_id", "")).strip()
        if not run_id:
            continue

        run_dir = runs_root / run_id
        trades_path = run_dir / "trades.csv"
        out: dict[str, Any] = {
            "candidate": row.get("candidate", ""),
            "run_id": run_id,
            "run_dir": run_dir.as_posix(),
            "status": "ok",
            "r_col": "",
            "trades_scoreboard": _safe_float(row.get("trades")),
            "expectancy_scoreboard": _safe_float(row.get("expectancy_R")),
            "pf_scoreboard": _safe_float(row.get("pf")),
            "winrate_scoreboard": _safe_float(row.get("winrate")),
            "trades_calc": math.nan,
            "expectancy_calc": math.nan,
            "median_r_calc": math.nan,
            "pf_calc": math.nan,
            "winrate_calc": math.nan,
            "sum_r_calc": math.nan,
            "min_r_calc": math.nan,
            "p05_r_calc": math.nan,
            "p25_r_calc": math.nan,
            "p75_r_calc": math.nan,
            "p95_r_calc": math.nan,
            "max_r_calc": math.nan,
            "delta_expectancy": math.nan,
            "delta_pf": math.nan,
            "delta_trades": math.nan,
            "delta_winrate": math.nan,
            "expectancy_match": False,
            "pf_match": False,
            "trades_match": False,
            "winrate_match": False,
            "pipeline_bug_suspected": False,
            "note": "",
        }

        if not trades_path.exists():
            out["status"] = "missing_trades"
            out["note"] = f"Missing trades.csv: {trades_path.as_posix()}"
            rows.append(out)
            continue

        try:
            trades_df = pd.read_csv(trades_path)
            if trades_df.empty:
                out["status"] = "empty_trades"
                out["note"] = "trades.csv empty"
                rows.append(out)
                continue
            r_col = _find_r_col(trades_df)
            r = pd.to_numeric(trades_df[r_col], errors="coerce").dropna()
            if r.empty:
                out["status"] = "invalid_r"
                out["note"] = f"R column {r_col} has no numeric values"
                rows.append(out)
                continue

            out["r_col"] = r_col
            out["trades_calc"] = float(r.size)
            out["expectancy_calc"] = float(r.mean())
            out["median_r_calc"] = float(r.median())
            out["pf_calc"] = float(_profit_factor(r))
            out["winrate_calc"] = float((r > 0).mean())
            out["sum_r_calc"] = float(r.sum())
            out["min_r_calc"] = float(r.min())
            out["p05_r_calc"] = float(r.quantile(0.05))
            out["p25_r_calc"] = float(r.quantile(0.25))
            out["p75_r_calc"] = float(r.quantile(0.75))
            out["p95_r_calc"] = float(r.quantile(0.95))
            out["max_r_calc"] = float(r.max())

            out["delta_expectancy"] = out["expectancy_calc"] - out["expectancy_scoreboard"]
            out["delta_pf"] = out["pf_calc"] - out["pf_scoreboard"]
            out["delta_trades"] = out["trades_calc"] - out["trades_scoreboard"]
            out["delta_winrate"] = out["winrate_calc"] - out["winrate_scoreboard"]

            out["expectancy_match"] = bool(abs(out["delta_expectancy"]) <= float(args.tol_expectancy))
            out["pf_match"] = bool(abs(out["delta_pf"]) <= float(args.tol_pf))
            out["trades_match"] = bool(abs(out["delta_trades"]) <= 0.0)
            out["winrate_match"] = bool(abs(out["delta_winrate"]) <= float(args.tol_winrate))
            out["pipeline_bug_suspected"] = not (
                out["expectancy_match"] and out["pf_match"] and out["trades_match"] and out["winrate_match"]
            )
        except Exception as exc:
            out["status"] = "error"
            out["note"] = str(exc)
        rows.append(out)

    audit_df = pd.DataFrame(rows)
    if audit_df.empty:
        raise RuntimeError("No rows audited. Scoreboard may be empty.")

    audit_csv = out_dir / "expectancy_audit.csv"
    audit_md = out_dir / "expectancy_audit.md"
    audit_df.to_csv(audit_csv, index=False)

    bug_rows = audit_df[audit_df["pipeline_bug_suspected"] == True]  # noqa: E712
    bug_flag = "YES" if len(bug_rows) > 0 else "NO"
    md_lines: list[str] = []
    md_lines.append("# V4A Expectancy Audit (DEV 2021-2023)")
    md_lines.append("")
    md_lines.append(f"- scoreboard_used: `{chosen_score_path.as_posix()}`")
    md_lines.append(f"- rows_audited: `{len(audit_df)}`")
    md_lines.append(f"- PIPELINE_BUG_SUSPECTED: **{bug_flag}**")
    md_lines.append(
        "- tolerances: "
        f"`expectancy={args.tol_expectancy}`, `pf={args.tol_pf}`, `winrate={args.tol_winrate}`, `trades=exact`"
    )
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append("")
    summary_cols = [
        "candidate",
        "run_id",
        "status",
        "expectancy_scoreboard",
        "expectancy_calc",
        "delta_expectancy",
        "pf_scoreboard",
        "pf_calc",
        "delta_pf",
        "trades_scoreboard",
        "trades_calc",
        "delta_trades",
        "pipeline_bug_suspected",
    ]
    md_lines.append(
        _md_table(
            audit_df[summary_cols],
            float_cols={
                "expectancy_scoreboard",
                "expectancy_calc",
                "delta_expectancy",
                "pf_scoreboard",
                "pf_calc",
                "delta_pf",
                "trades_scoreboard",
                "trades_calc",
                "delta_trades",
            },
        )
    )
    if len(bug_rows) > 0:
        md_lines.append("")
        md_lines.append("## Suspected Rows")
        md_lines.append("")
        md_lines.append(
            _md_table(
                bug_rows[
                    [
                        "candidate",
                        "run_id",
                        "status",
                        "expectancy_match",
                        "pf_match",
                        "trades_match",
                        "winrate_match",
                        "note",
                    ]
                ]
            )
        )
    md_lines.append("")
    md_lines.append(f"- output_csv: `{audit_csv.as_posix()}`")
    audit_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote: {audit_csv.as_posix()}")
    print(f"Wrote: {audit_md.as_posix()}")
    print(f"PIPELINE_BUG_SUSPECTED={bug_flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
