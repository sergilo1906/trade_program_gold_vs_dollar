from __future__ import annotations

import argparse
from pathlib import Path

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


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    raise ValueError(f"No R column found. columns={list(df.columns)}")


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


def build_holdout_report(run_id: str, output: Path) -> None:
    run_dir = Path("outputs/runs") / run_id
    diag_dir = run_dir / "diagnostics"
    trades_path = run_dir / "trades.csv"
    boot_path = diag_dir / "BOOT_expectancy_ci.csv"
    blocks_path = diag_dir / "E_blocks.csv"
    hour_path = diag_dir / "H_perf_by_hour_robust.csv"

    trades = pd.read_csv(trades_path)
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    gross_win = float(r[r > 0].sum()) if not r.empty else 0.0
    gross_loss = float((-r[r < 0]).sum()) if not r.empty else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else (float("inf") if gross_win > 0 else float("nan"))
    expectancy = float(r.mean()) if not r.empty else float("nan")
    winrate = float((r > 0).mean()) if not r.empty else float("nan")
    kpi_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "pf": pf,
                "expectancy_R": expectancy,
                "trades": int(r.size),
                "winrate": winrate,
            }
        ]
    )

    boot_df = pd.read_csv(boot_path) if boot_path.exists() else pd.DataFrame()
    if boot_df.empty:
        boot_df = pd.DataFrame(
            [
                {
                    "run_id": run_id,
                    "n": pd.NA,
                    "mean": pd.NA,
                    "ci_low": pd.NA,
                    "ci_high": pd.NA,
                    "crosses_zero": pd.NA,
                    "resamples": pd.NA,
                }
            ]
        )
    else:
        keep_cols = ["run_id", "n", "mean", "ci_low", "ci_high", "crosses_zero", "resamples"]
        for c in keep_cols:
            if c not in boot_df.columns:
                boot_df[c] = pd.NA
        boot_df = boot_df[keep_cols]

    blocks_df = pd.read_csv(blocks_path) if blocks_path.exists() else pd.DataFrame()
    if not blocks_df.empty:
        blocks_df = blocks_df[
            ["block_type", "count", "pct_of_opportunities", "opportunities_denom", "denominator_source"]
        ].copy()

    hour_df = pd.read_csv(hour_path) if hour_path.exists() else pd.DataFrame()
    if not hour_df.empty:
        hour_df["hour_utc"] = pd.to_numeric(hour_df["hour_utc"], errors="coerce")
        hour_df["trades"] = pd.to_numeric(hour_df["trades"], errors="coerce")
        hour_df["expectancy_R"] = pd.to_numeric(hour_df["expectancy_R"], errors="coerce")
        hour_df["pf"] = pd.to_numeric(hour_df["pf"], errors="coerce")
        hour_df["winrate"] = pd.to_numeric(hour_df["winrate"], errors="coerce")
        hour_df = hour_df.dropna(subset=["hour_utc"]).copy()
        hour_df["hour_utc"] = hour_df["hour_utc"].astype(int)

    neg_hours = pd.DataFrame(columns=["hour_utc", "trades", "expectancy_R", "pf", "winrate"])
    top_hours = pd.DataFrame(columns=["hour_utc", "trades", "expectancy_R", "pf", "winrate"])
    if not hour_df.empty:
        neg_hours = (
            hour_df[(hour_df["trades"] >= 10) & (hour_df["expectancy_R"] < 0)]
            .sort_values(["expectancy_R", "trades"], ascending=[True, False])[
                ["hour_utc", "trades", "expectancy_R", "pf", "winrate"]
            ]
            .reset_index(drop=True)
        )
        top_hours = (
            hour_df[hour_df["trades"] > 0]
            .sort_values(["expectancy_R", "trades"], ascending=[False, False])[
                ["hour_utc", "trades", "expectancy_R", "pf", "winrate"]
            ]
            .head(5)
            .reset_index(drop=True)
        )

    lines: list[str] = []
    lines.append("# HOLDOUT Report")
    lines.append("")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- run_dir: `{run_dir.as_posix()}`")
    lines.append("")
    lines.append("## KPIs")
    lines.append(_md_table(kpi_df, float_cols={"pf", "expectancy_R", "winrate"}))
    lines.append("")
    lines.append("## Bootstrap CI")
    lines.append(_md_table(boot_df, float_cols={"mean", "ci_low", "ci_high"}))
    lines.append("")
    lines.append("## Blocks (session/cost/shock/max_trades)")
    lines.append(_md_table(blocks_df, float_cols={"pct_of_opportunities"}))
    lines.append("")
    lines.append("## Hour Stability Summary")
    lines.append("Negative expectancy hours with trades >= 10:")
    lines.append(_md_table(neg_hours, float_cols={"expectancy_R", "pf", "winrate"}))
    lines.append("")
    lines.append("Top hours by expectancy_R:")
    lines.append(_md_table(top_hours, float_cols={"expectancy_R", "pf", "winrate"}))
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HOLDOUT report for a run.")
    parser.add_argument("run_id", help="Run ID under outputs/runs.")
    parser.add_argument("--output", default="docs/HOLDOUT_REPORT.md", help="Output markdown path.")
    args = parser.parse_args()

    build_holdout_report(args.run_id, Path(args.output))
    print(f"Wrote: {Path(args.output).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
