from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


R_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)

TS_CANDIDATES = (
    "entry_time",
    "open_time",
    "entry_ts",
    "timestamp",
    "time",
    "ts",
)


def _find_first_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for cand in candidates:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    return None


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No data_"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for h in headers:
            v = row[h]
            if pd.isna(v):
                vals.append("")
            elif isinstance(v, float):
                vals.append(f"{v:.6f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def bootstrap_expectancy(
    run_dir: Path,
    resamples: int = 5000,
    seed: int = 42,
) -> tuple[Path, Path]:
    trades_path = run_dir / "trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"Missing trades.csv: {trades_path}")

    trades = pd.read_csv(trades_path)
    r_col = _find_first_col(trades, R_CANDIDATES)
    if r_col is None:
        raise ValueError(f"No R column found in trades.csv. Tried: {R_CANDIDATES}")

    r = pd.to_numeric(trades[r_col], errors="coerce").dropna().to_numpy(dtype=float)
    n = int(r.size)

    if n == 0:
        mean_r = float("nan")
        ci_low = float("nan")
        ci_high = float("nan")
    else:
        rng = np.random.default_rng(seed)
        means = np.empty(resamples, dtype=float)
        for i in range(resamples):
            sample = rng.choice(r, size=n, replace=True)
            means[i] = float(sample.mean())
        mean_r = float(r.mean())
        ci_low = float(np.quantile(means, 0.025))
        ci_high = float(np.quantile(means, 0.975))

    crosses_zero = bool((not pd.isna(ci_low)) and (not pd.isna(ci_high)) and (ci_low <= 0.0 <= ci_high))

    diag_dir = run_dir / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    out_csv = diag_dir / "BOOT_expectancy_ci.csv"
    out_df = pd.DataFrame(
        [
            {
                "run_id": run_dir.name,
                "r_col": r_col,
                "n": n,
                "seed": int(seed),
                "resamples": int(resamples),
                "mean": mean_r,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "crosses_zero": crosses_zero,
            }
        ]
    )
    out_df.to_csv(out_csv, index=False)

    ts_col = _find_first_col(trades, TS_CANDIDATES)
    month_df = pd.DataFrame(columns=["month", "trades"])
    if ts_col is not None:
        ts = pd.to_datetime(trades[ts_col], errors="coerce", utc=True)
        valid = ts.dropna()
        if not valid.empty:
            month_df = (
                valid.dt.to_period("M")
                .astype(str)
                .value_counts()
                .rename_axis("month")
                .reset_index(name="trades")
                .sort_values("month")
                .reset_index(drop=True)
            )

    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_md = docs_dir / "RANGE_EDGE_VALIDATION.md"
    md_parts = [
        "# RANGE Edge Validation",
        "",
        "## Input",
        f"- run_dir: `{run_dir.as_posix()}`",
        f"- trades: `{trades_path.as_posix()}`",
        f"- R column: `{r_col}`",
        f"- resamples: `{resamples}`",
        f"- seed: `{seed}`",
        "",
        "## Bootstrap CI (Expectancy_R)",
        _markdown_table(out_df),
        "",
        "## Decision",
        f"- CI cruza 0: `{'YES' if crosses_zero else 'NO'}`",
        "",
        "## Trades por mes",
        _markdown_table(month_df),
        "",
        f"- output_csv: `{out_csv.as_posix()}`",
    ]
    out_md.write_text("\n".join(md_parts) + "\n", encoding="utf-8")
    return out_csv, out_md


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap confidence interval for expectancy_R from trades.csv.")
    parser.add_argument("run_dir", help="Run directory path.")
    parser.add_argument("--resamples", type=int, default=5000, help="Number of bootstrap resamples.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    out_csv, out_md = bootstrap_expectancy(
        run_dir=Path(args.run_dir),
        resamples=args.resamples,
        seed=args.seed,
    )
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
