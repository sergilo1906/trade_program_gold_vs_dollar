from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


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
    raise ValueError(f"No R column in trades. columns={list(df.columns)}")


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


def _scenario_row(label: str, run_id: str) -> dict[str, Any]:
    run_dir = Path("outputs/runs") / run_id
    trades = pd.read_csv(run_dir / "trades.csv")
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    gross_win = float(r[r > 0].sum()) if not r.empty else 0.0
    gross_loss = float((-r[r < 0]).sum()) if not r.empty else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else (float("inf") if gross_win > 0 else float("nan"))
    exp = float(r.mean()) if not r.empty else float("nan")

    boot_path = run_dir / "diagnostics" / "BOOT_expectancy_ci.csv"
    if boot_path.exists():
        boot = pd.read_csv(boot_path).iloc[0]
        ci_low = boot.get("ci_low", pd.NA)
        ci_high = boot.get("ci_high", pd.NA)
        crosses_zero = boot.get("crosses_zero", pd.NA)
    else:
        ci_low = pd.NA
        ci_high = pd.NA
        crosses_zero = pd.NA

    cfg = yaml.safe_load((run_dir / "config_used.yaml").read_text(encoding="utf-8")) or {}
    spread = cfg.get("spread_usd", pd.NA)
    slippage = cfg.get("slippage_usd", pd.NA)

    return {
        "scenario": label,
        "run_id": run_id,
        "spread_usd": spread,
        "slippage_usd": slippage,
        "pf": pf,
        "expectancy_R": exp,
        "trades": int(r.size),
        "boot_ci_low": ci_low,
        "boot_ci_high": ci_high,
        "boot_crosses_zero": crosses_zero,
    }


def build_report(base_run: str, p20_run: str, p50_run: str, output: Path) -> None:
    rows = [
        _scenario_row("BASE", base_run),
        _scenario_row("+20% COST", p20_run),
        _scenario_row("+50% COST", p50_run),
    ]
    df = pd.DataFrame(rows)

    lines: list[str] = []
    lines.append("# Cost Stress (HOLDOUT20)")
    lines.append("")
    lines.append("- Simple cost knob used: `spread_usd` and `slippage_usd` scaled from winner config.")
    lines.append("- Winner config base: `configs/config_v3_AUTO_EXP_B.yaml`")
    lines.append("- Stress configs: `configs/config_v3_AUTO_EXP_B_COSTP20.yaml`, `configs/config_v3_AUTO_EXP_B_COSTP50.yaml`")
    lines.append("")
    lines.append("## Stress Table")
    lines.append(
        _md_table(
            df,
            float_cols={"spread_usd", "slippage_usd", "pf", "expectancy_R", "boot_ci_low", "boot_ci_high"},
        )
    )
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cost stress markdown report.")
    parser.add_argument("--base-run", required=True)
    parser.add_argument("--p20-run", required=True)
    parser.add_argument("--p50-run", required=True)
    parser.add_argument("--output", default="docs/COST_STRESS.md")
    args = parser.parse_args()

    build_report(args.base_run, args.p20_run, args.p50_run, Path(args.output))
    print(f"Wrote: {Path(args.output).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
