from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import pandas as pd


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


def _scan_factor_cols(df: pd.DataFrame) -> dict[float, str]:
    mapping: dict[float, str] = {}
    pat = re.compile(r"^r_multiple_posthoc_f(.+)$")
    for c in df.columns:
        m = pat.match(c)
        if not m:
            continue
        raw = m.group(1)
        txt = raw.replace("_", ".")
        try:
            f = float(txt)
        except Exception:
            continue
        mapping[f] = c
    return mapping


def _pick_factor_col(mapping: dict[float, str], target: float, tol: float = 1e-9) -> str:
    for f, c in mapping.items():
        if abs(float(f) - float(target)) <= tol:
            return c
    available = ", ".join(str(k) for k in sorted(mapping.keys()))
    raise KeyError(f"Missing factor {target} in per-trade file. Available factors: {available}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cost sensitivity attribution report from per-trade posthoc CSV.")
    parser.add_argument(
        "--per-trade",
        default="outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv",
        help="Per-trade posthoc CSV path.",
    )
    parser.add_argument("--output", default="docs/COST_SENSITIVITY_ATTRIBUTION.md")
    parser.add_argument(
        "--out-prefix",
        default="outputs/posthoc_cost_stress/cost_sensitivity",
        help="Prefix for auxiliary CSV outputs.",
    )
    args = parser.parse_args()

    per_trade_path = Path(args.per_trade)
    if not per_trade_path.exists():
        raise FileNotFoundError(f"Missing per-trade CSV: {per_trade_path.as_posix()}")

    df = pd.read_csv(per_trade_path)
    if df.empty:
        raise RuntimeError(f"Empty per-trade CSV: {per_trade_path.as_posix()}")

    factor_cols = _scan_factor_cols(df)
    c_base = _pick_factor_col(factor_cols, 1.0)
    c_20 = _pick_factor_col(factor_cols, 1.2)
    c_50 = _pick_factor_col(factor_cols, 1.5)

    r_base = pd.to_numeric(df[c_base], errors="coerce")
    r_20 = pd.to_numeric(df[c_20], errors="coerce")
    r_50 = pd.to_numeric(df[c_50], errors="coerce")
    if r_base.isna().any() or r_20.isna().any() or r_50.isna().any():
        raise RuntimeError("NaN values detected in required R columns for attribution.")

    work = df.copy()
    work["r_base"] = r_base
    work["r_p20"] = r_20
    work["r_p50"] = r_50
    work["delta_R_20"] = work["r_p20"] - work["r_base"]
    work["delta_R_50"] = work["r_p50"] - work["r_base"]

    # Top 10 by R deterioration (most negative deltas).
    top_cols = [
        "trade_id",
        "entry_time",
        "mode",
        "regime_at_entry",
        "direction",
        "exit_reason",
        "r_base",
        "r_p20",
        "delta_R_20",
        "r_p50",
        "delta_R_50",
    ]
    available_top_cols = [c for c in top_cols if c in work.columns]
    top20 = work.sort_values("delta_R_20", ascending=True).head(10)[available_top_cols].reset_index(drop=True)
    top50 = work.sort_values("delta_R_50", ascending=True).head(10)[available_top_cols].reset_index(drop=True)

    # Aggregate by mode/regime/exit_reason.
    group_keys = [c for c in ("mode", "regime_at_entry", "exit_reason") if c in work.columns]
    if not group_keys:
        raise RuntimeError("No grouping columns available among mode/regime_at_entry/exit_reason.")
    grouped = (
        work.groupby(group_keys, dropna=False)
        .agg(
            trades=("trade_id" if "trade_id" in work.columns else "r_base", "count"),
            exp_R_base=("r_base", "mean"),
            exp_R_p20=("r_p20", "mean"),
            exp_R_p50=("r_p50", "mean"),
        )
        .reset_index()
    )
    grouped["delta_R_20"] = grouped["exp_R_p20"] - grouped["exp_R_base"]
    grouped["delta_R_50"] = grouped["exp_R_p50"] - grouped["exp_R_base"]
    grouped = grouped.sort_values(["delta_R_20", "trades"], ascending=[True, False]).reset_index(drop=True)

    # Aggregate by entry hour when derivable.
    by_hour = pd.DataFrame(
        columns=["hour_utc", "trades", "exp_R_base", "exp_R_p20", "exp_R_p50", "delta_R_20", "delta_R_50"]
    )
    hour_note = "entry_time not available or not parseable."
    if "entry_time" in work.columns:
        ts = pd.to_datetime(work["entry_time"], errors="coerce", utc=False)
        if ts.notna().any():
            tmp = work.loc[ts.notna()].copy()
            tmp["hour_utc"] = ts[ts.notna()].dt.hour.astype(int)
            by_hour = (
                tmp.groupby("hour_utc", dropna=False)
                .agg(
                    trades=("trade_id" if "trade_id" in tmp.columns else "r_base", "count"),
                    exp_R_base=("r_base", "mean"),
                    exp_R_p20=("r_p20", "mean"),
                    exp_R_p50=("r_p50", "mean"),
                )
                .reset_index()
            )
            by_hour["delta_R_20"] = by_hour["exp_R_p20"] - by_hour["exp_R_base"]
            by_hour["delta_R_50"] = by_hour["exp_R_p50"] - by_hour["exp_R_base"]
            by_hour = by_hour.sort_values(["delta_R_20", "trades"], ascending=[True, False]).reset_index(drop=True)
            hour_note = "entry_time parsed and hour_utc derived."

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    top20.to_csv(Path(f"{out_prefix.as_posix()}_top10_delta20.csv"), index=False)
    top50.to_csv(Path(f"{out_prefix.as_posix()}_top10_delta50.csv"), index=False)
    grouped.to_csv(Path(f"{out_prefix.as_posix()}_by_mode_regime_exit.csv"), index=False)
    by_hour.to_csv(Path(f"{out_prefix.as_posix()}_by_hour.csv"), index=False)

    # Build markdown report.
    out_md = Path(args.output)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Cost Sensitivity Attribution")
    lines.append("")
    lines.append("- source_per_trade: `" + per_trade_path.as_posix() + "`")
    lines.append("- method: post-hoc trade-set fixed attribution (factors 1.0, 1.2, 1.5)")
    lines.append("")
    lines.append("## Top 10 trades by R loss (1.0 -> 1.2)")
    lines.append(_md_table(top20, float_cols={"r_base", "r_p20", "delta_R_20", "r_p50", "delta_R_50"}))
    lines.append("")
    lines.append("## Top 10 trades by R loss (1.0 -> 1.5)")
    lines.append(_md_table(top50, float_cols={"r_base", "r_p20", "delta_R_20", "r_p50", "delta_R_50"}))
    lines.append("")
    lines.append("## Aggregation by mode / regime_at_entry / exit_reason")
    lines.append(
        _md_table(
            grouped,
            float_cols={"exp_R_base", "exp_R_p20", "exp_R_p50", "delta_R_20", "delta_R_50"},
        )
    )
    lines.append("")
    lines.append("## Aggregation by hour (derived from entry_time)")
    lines.append(f"- note: {hour_note}")
    lines.append(
        _md_table(
            by_hour,
            float_cols={"exp_R_base", "exp_R_p20", "exp_R_p50", "delta_R_20", "delta_R_50"},
        )
    )
    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- `{out_prefix.as_posix()}_top10_delta20.csv`")
    lines.append(f"- `{out_prefix.as_posix()}_top10_delta50.csv`")
    lines.append(f"- `{out_prefix.as_posix()}_by_mode_regime_exit.csv`")
    lines.append(f"- `{out_prefix.as_posix()}_by_hour.csv`")
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {out_md.as_posix()}")
    print(f"Wrote: {out_prefix.as_posix()}_top10_delta20.csv")
    print(f"Wrote: {out_prefix.as_posix()}_top10_delta50.csv")
    print(f"Wrote: {out_prefix.as_posix()}_by_mode_regime_exit.csv")
    print(f"Wrote: {out_prefix.as_posix()}_by_hour.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
