from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


R_CANDIDATES = [
    "r_multiple",
    "R_net",
    "net_R",
    "pnl_R",
    "pnl_r",
    "r",
]


@dataclass
class ExperimentSummary:
    label: str
    run_id: str
    mode: str
    pf: float
    expectancy_R: float
    winrate: float
    trades: int
    opportunities_denom: float
    session_block_pct: float
    cost_filter_block_pct: float
    shock_block_pct: float
    boot_mean: float
    boot_ci_low: float
    boot_ci_high: float
    boot_crosses_zero: bool
    max_hour_trade_share: float
    top_hours: pd.DataFrame
    worst_hours: pd.DataFrame
    hourly_table: pd.DataFrame


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return "NaN"
        return f"{value:.6f}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_sin datos_"
    headers = [str(col) for col in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)


def _detect_r_col(trades: pd.DataFrame) -> str:
    for col in R_CANDIDATES:
        if col in trades.columns:
            return col
    lowered = {c.lower(): c for c in trades.columns}
    for col in R_CANDIDATES:
        if col.lower() in lowered:
            return lowered[col.lower()]
    raise ValueError(f"No R column found in trades columns={list(trades.columns)}")


def _compute_kpis_from_trades(trades: pd.DataFrame) -> tuple[float, float, float, int]:
    r_col = _detect_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    trades_n = int(r.size)
    if trades_n == 0:
        return np.nan, np.nan, np.nan, 0
    sum_pos = float(r[r > 0].sum())
    sum_neg_abs = float(abs(r[r < 0].sum()))
    pf = (sum_pos / sum_neg_abs) if sum_neg_abs > 0 else np.nan
    expectancy = float(r.mean())
    winrate = float((r > 0).mean())
    return pf, expectancy, winrate, trades_n


def _read_block_pct(e_df: pd.DataFrame, block_type: str) -> float:
    if e_df.empty or "block_type" not in e_df.columns:
        return np.nan
    row = e_df[e_df["block_type"] == block_type]
    if row.empty or "pct_of_opportunities" not in row.columns:
        return np.nan
    return float(pd.to_numeric(row.iloc[0]["pct_of_opportunities"], errors="coerce"))


def _read_opportunities_denom(e_df: pd.DataFrame) -> float:
    if e_df.empty or "opportunities_denom" not in e_df.columns:
        return np.nan
    val = pd.to_numeric(e_df["opportunities_denom"], errors="coerce").dropna()
    return float(val.iloc[0]) if not val.empty else np.nan


def _load_hourly(run_dir: Path) -> pd.DataFrame:
    diag = run_dir / "diagnostics"
    h_path = diag / "H_perf_by_hour_robust.csv"
    c_path = diag / "C_perf_by_hour_utc.csv"
    d_path = diag / "D_costR_percentiles.csv"

    if h_path.exists():
        perf = pd.read_csv(h_path)
    elif c_path.exists():
        perf = pd.read_csv(c_path)
    else:
        return pd.DataFrame(
            columns=["hour_utc", "trades", "pf", "expectancy_R", "winrate", "cost_R_mean"]
        )

    if perf.empty:
        return pd.DataFrame(
            columns=["hour_utc", "trades", "pf", "expectancy_R", "winrate", "cost_R_mean"]
        )

    for col in ["hour_utc", "trades", "pf", "expectancy_R", "winrate"]:
        if col not in perf.columns:
            perf[col] = np.nan
    perf = perf[["hour_utc", "trades", "pf", "expectancy_R", "winrate"]].copy()
    perf["hour_utc"] = pd.to_numeric(perf["hour_utc"], errors="coerce")
    perf["trades"] = pd.to_numeric(perf["trades"], errors="coerce")
    perf = perf.dropna(subset=["hour_utc"]).copy()
    perf["hour_utc"] = perf["hour_utc"].astype(int)

    cost_map = pd.DataFrame(columns=["hour_utc", "cost_R_mean"])
    if d_path.exists():
        d = pd.read_csv(d_path)
        if not d.empty and "hour_utc" in d.columns and "cost_R_mean" in d.columns:
            d = d.copy()
            d["hour_utc"] = pd.to_numeric(d["hour_utc"], errors="coerce")
            d["trades"] = pd.to_numeric(d.get("trades", np.nan), errors="coerce")
            d["cost_R_mean"] = pd.to_numeric(d["cost_R_mean"], errors="coerce")
            d = d.dropna(subset=["hour_utc", "cost_R_mean", "trades"])
            if not d.empty:
                d["hour_utc"] = d["hour_utc"].astype(int)
                grouped = d.groupby("hour_utc", as_index=False).apply(
                    lambda g: pd.Series(
                        {
                            "cost_R_mean": np.average(g["cost_R_mean"], weights=g["trades"])
                            if g["trades"].sum() > 0
                            else np.nan
                        }
                    )
                )
                if isinstance(grouped.index, pd.MultiIndex):
                    grouped = grouped.reset_index(level=0, drop=True).reset_index()
                cost_map = grouped[["hour_utc", "cost_R_mean"]]

    merged = perf.merge(cost_map, on="hour_utc", how="left")
    merged = merged.sort_values(["hour_utc"]).reset_index(drop=True)
    return merged


def _load_summary(label: str, run_id: str) -> ExperimentSummary:
    run_dir = Path("outputs/runs") / run_id
    diag = run_dir / "diagnostics"

    a_df = pd.read_csv(diag / "A_perf_by_mode.csv")
    e_df = pd.read_csv(diag / "E_blocks.csv")
    boot_df = pd.read_csv(diag / "BOOT_expectancy_ci.csv")
    trades = pd.read_csv(run_dir / "trades.csv")

    modes = ",".join(sorted(a_df["mode"].dropna().astype(str).unique())) if "mode" in a_df.columns else "NA"
    pf, expectancy, winrate, trades_n = _compute_kpis_from_trades(trades)

    boot_row = boot_df.iloc[0] if not boot_df.empty else {}
    boot_mean = float(pd.to_numeric(boot_row.get("mean", np.nan), errors="coerce"))
    boot_low = float(pd.to_numeric(boot_row.get("ci_low", np.nan), errors="coerce"))
    boot_high = float(pd.to_numeric(boot_row.get("ci_high", np.nan), errors="coerce"))
    boot_cross = bool(boot_row.get("crosses_zero", True))

    hourly = _load_hourly(run_dir)
    hourly_valid = hourly[hourly["trades"].fillna(0) > 0].copy()
    max_hour_share = (
        float(hourly_valid["trades"].max() / hourly_valid["trades"].sum())
        if not hourly_valid.empty and float(hourly_valid["trades"].sum()) > 0
        else np.nan
    )
    top_hours = hourly_valid.sort_values(["expectancy_R", "trades"], ascending=[False, False]).head(3)
    worst_hours = hourly_valid.sort_values(["expectancy_R", "trades"], ascending=[True, False]).head(3)

    return ExperimentSummary(
        label=label,
        run_id=run_id,
        mode=modes,
        pf=pf,
        expectancy_R=expectancy,
        winrate=winrate,
        trades=trades_n,
        opportunities_denom=_read_opportunities_denom(e_df),
        session_block_pct=_read_block_pct(e_df, "SESSION_BLOCK"),
        cost_filter_block_pct=_read_block_pct(e_df, "COST_FILTER_BLOCK"),
        shock_block_pct=_read_block_pct(e_df, "SHOCK_BLOCK"),
        boot_mean=boot_mean,
        boot_ci_low=boot_low,
        boot_ci_high=boot_high,
        boot_crosses_zero=boot_cross,
        max_hour_trade_share=max_hour_share,
        top_hours=top_hours,
        worst_hours=worst_hours,
        hourly_table=hourly,
    )


def _parse_experiments(values: list[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Expected LABEL=RUN_ID format, got: {raw}")
        label, run_id = raw.split("=", 1)
        parsed.append((label.strip(), run_id.strip()))
    return parsed


def _build_kpi_table(rows: list[ExperimentSummary]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "label": row.label,
                "run_id": row.run_id,
                "mode": row.mode,
                "pf": row.pf,
                "expectancy_R": row.expectancy_R,
                "winrate": row.winrate,
                "trades": row.trades,
                "opportunities_denom": row.opportunities_denom,
                "session_block_pct": row.session_block_pct,
                "cost_filter_block_pct": row.cost_filter_block_pct,
                "shock_block_pct": row.shock_block_pct,
                "boot_mean": row.boot_mean,
                "boot_ci_low": row.boot_ci_low,
                "boot_ci_high": row.boot_ci_high,
                "boot_crosses_zero": row.boot_crosses_zero,
            }
            for row in rows
        ]
    )
    return frame


def _build_ranking(rows: list[ExperimentSummary]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "label": row.label,
                "run_id": row.run_id,
                "expectancy_R": row.expectancy_R,
                "boot_ci_low": row.boot_ci_low,
                "pf": row.pf,
                "trades": row.trades,
                "hour_dependency": row.max_hour_trade_share,
                "shock_block_pct": row.shock_block_pct,
            }
            for row in rows
        ]
    )
    frame = frame.sort_values(
        by=[
            "expectancy_R",
            "boot_ci_low",
            "pf",
            "trades",
            "hour_dependency",
            "shock_block_pct",
        ],
        ascending=[False, False, False, False, True, True],
    ).reset_index(drop=True)
    frame.insert(0, "rank", np.arange(1, len(frame) + 1))
    return frame


def _build_observations(rows: list[ExperimentSummary]) -> list[str]:
    observations: list[str] = []
    by_expectancy = sorted(rows, key=lambda r: r.expectancy_R, reverse=True)
    best = by_expectancy[0]
    worst = by_expectancy[-1]
    observations.append(
        f"Expectancy_R sube desde {worst.label} ({worst.expectancy_R:.4f}) hasta "
        f"{best.label} ({best.expectancy_R:.4f})."
    )

    negatives = []
    for row in rows:
        negative_hours = int((row.hourly_table["expectancy_R"].fillna(0) < 0).sum())
        negatives.append((row.label, negative_hours))
    observations.append(
        "Horas con expectancy_R negativo por experimento: "
        + ", ".join(f"{label}={count}" for label, count in negatives)
        + "."
    )

    ci_order = sorted(rows, key=lambda r: r.boot_ci_low, reverse=True)
    observations.append(
        "Bootstrap ci_low (mejor a peor): "
        + " > ".join(f"{r.label}({r.boot_ci_low:.4f})" for r in ci_order)
        + "."
    )

    dep = []
    for row in rows:
        dep.append(f"{row.label}={row.max_hour_trade_share:.2%}")
    observations.append(
        "Dependencia de una sola hora (max_trade_share): " + ", ".join(dep) + "."
    )
    return observations


def build_report(experiments: list[tuple[str, str]], output_path: Path) -> tuple[pd.DataFrame, list[ExperimentSummary], pd.DataFrame]:
    rows = [_load_summary(label, run_id) for label, run_id in experiments]
    kpi_table = _build_kpi_table(rows)
    ranking = _build_ranking(rows)
    observations = _build_observations(rows)

    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines: list[str] = []
    lines.append("# Session Window Experiments (V3_AUTO)")
    lines.append("")
    lines.append(f"- generated_utc: {ts}")
    lines.append("- timezone: UTC")
    lines.append("")
    lines.append("## Run map")
    for row in rows:
        lines.append(f"- {row.label}: `outputs/runs/{row.run_id}`")
    lines.append("")
    lines.append("## KPI")
    lines.append(_df_to_markdown(kpi_table))
    lines.append("")
    lines.append("## Hourly stability")
    for row in rows:
        lines.append(f"### {row.label} ({row.run_id})")
        lines.append(
            _df_to_markdown(
                row.hourly_table[
                    ["hour_utc", "trades", "pf", "expectancy_R", "winrate", "cost_R_mean"]
                ]
            )
        )
        lines.append("")
    lines.append("## Automatic observations")
    for obs in observations:
        lines.append(f"- {obs}")
    lines.append("")
    lines.append("## Ranking")
    lines.append(_df_to_markdown(ranking))
    lines.append("")
    lines.append("## Top/Bottom hours")
    for row in rows:
        lines.append(f"### {row.label}")
        lines.append("Top 3 by expectancy_R:")
        lines.append(_df_to_markdown(row.top_hours[["hour_utc", "trades", "expectancy_R", "pf", "winrate"]]))
        lines.append("")
        lines.append("Worst 3 by expectancy_R:")
        lines.append(_df_to_markdown(row.worst_hours[["hour_utc", "trades", "expectancy_R", "pf", "winrate"]]))
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return kpi_table, rows, ranking


def main() -> int:
    parser = argparse.ArgumentParser(description="Build comparative report for session window experiments.")
    parser.add_argument(
        "--exp",
        action="append",
        required=True,
        help="Experiment in LABEL=RUN_ID format. Repeat for each run.",
    )
    parser.add_argument(
        "--output",
        default="docs/SESSION_WINDOW_EXPERIMENTS.md",
        help="Output markdown path.",
    )
    args = parser.parse_args()

    experiments = _parse_experiments(args.exp)
    output_path = Path(args.output)
    kpi, rows, ranking = build_report(experiments, output_path)
    print(f"Wrote: {output_path}")
    print("\nKPI:")
    print(kpi.to_string(index=False))
    print("\nRanking:")
    print(ranking.to_string(index=False))
    for row in rows:
        print(f"\n{row.label} top_hours:")
        print(row.top_hours[["hour_utc", "trades", "expectancy_R", "pf", "winrate"]].to_string(index=False))
        print(f"{row.label} worst_hours:")
        print(row.worst_hours[["hour_utc", "trades", "expectancy_R", "pf", "winrate"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
