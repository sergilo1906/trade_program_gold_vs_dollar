from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
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

RISK_COL_CANDIDATES = ("risk_amount", "risk_usd", "risk", "risk_amt")
PNL_NET_COL_CANDIDATES = ("pnl", "pnl_net", "net_pnl", "profit_net")
PNL_GROSS_COL_CANDIDATES = ("pnl_gross", "gross_pnl", "profit_gross")
TOTAL_COST_COL_CANDIDATES = ("cost_total", "total_cost", "cost_usd", "fees_total")
QTY_COL_CANDIDATES = ("closed_size", "size", "qty", "quantity")
COMPONENT_COST_COL_CANDIDATES = (
    "spread_cost",
    "slippage_cost",
    "commission",
    "commission_cost",
    "swap_cost",
    "fees",
)


def _find_first_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for cand in candidates:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    return None


def _short(text: str, limit: int = 600) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _bootstrap_ci(r_values: np.ndarray, resamples: int, seed: int) -> tuple[float, float, bool]:
    n = int(r_values.size)
    if n == 0:
        return math.nan, math.nan, False
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    for i in range(resamples):
        means[i] = float(rng.choice(r_values, size=n, replace=True).mean())
    ci_low = float(np.quantile(means, 0.025))
    ci_high = float(np.quantile(means, 0.975))
    crosses_zero = bool(ci_low <= 0.0 <= ci_high)
    return ci_low, ci_high, crosses_zero


def _compute_kpis(r_values: np.ndarray) -> dict[str, Any]:
    n = int(r_values.size)
    if n == 0:
        return {
            "pf": math.nan,
            "expectancy_R": math.nan,
            "trades": 0,
            "winrate": math.nan,
        }
    gross_win = float(r_values[r_values > 0].sum())
    gross_loss = float((-r_values[r_values < 0]).sum())
    if gross_loss > 0:
        pf = gross_win / gross_loss
    else:
        pf = float("inf") if gross_win > 0 else math.nan
    return {
        "pf": float(pf),
        "expectancy_R": float(r_values.mean()),
        "trades": n,
        "winrate": float((r_values > 0).mean()),
    }


def _direction_sign(series: pd.Series) -> np.ndarray:
    mapped = (
        series.astype(str)
        .str.upper()
        .str.strip()
        .map(
            {
                "LONG": 1.0,
                "BUY": 1.0,
                "SHORT": -1.0,
                "SELL": -1.0,
            }
        )
    )
    if mapped.isna().any():
        bad_vals = sorted(series[mapped.isna()].astype(str).unique().tolist())
        raise ValueError(f"Unsupported direction values for sign mapping: {bad_vals}")
    return mapped.to_numpy(dtype=float)


def _detect_cost_model(trades: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, dict[str, Any]]:
    """
    Returns:
      - pnl_net_usd
      - pnl_gross_usd
      - cost_usd (gross - net)
      - metadata with formula details
    """
    df = trades.copy()
    cols = set(df.columns)

    pnl_net_col = _find_first_col(df, PNL_NET_COL_CANDIDATES)
    pnl_gross_col = _find_first_col(df, PNL_GROSS_COL_CANDIDATES)
    cost_total_col = _find_first_col(df, TOTAL_COST_COL_CANDIDATES)
    qty_col = _find_first_col(df, QTY_COL_CANDIDATES)

    if pnl_net_col is not None:
        pnl_net = pd.to_numeric(df[pnl_net_col], errors="coerce")
    else:
        pnl_net = pd.Series([math.nan] * len(df), index=df.index)

    # Option A: explicit gross + net.
    if pnl_gross_col is not None and pnl_net_col is not None:
        pnl_gross = pd.to_numeric(df[pnl_gross_col], errors="coerce")
        cost = pnl_gross - pnl_net
        if cost.isna().any():
            raise ValueError(f"NaN values found in gross/net columns: {pnl_gross_col}, {pnl_net_col}")
        if (cost < -1e-9).any():
            raise ValueError("Derived cost has negative values from gross-net; aborting.")
        return pnl_net, pnl_gross, cost, {
            "formula_id": "gross_minus_net_explicit",
            "pnl_net_col": pnl_net_col,
            "pnl_gross_col": pnl_gross_col,
        }

    # Option B: explicit total cost + net.
    if cost_total_col is not None and pnl_net_col is not None:
        cost = pd.to_numeric(df[cost_total_col], errors="coerce")
        if cost.isna().any():
            raise ValueError(f"NaN values found in cost column: {cost_total_col}")
        if (cost < -1e-9).any():
            raise ValueError("Explicit total cost column has negative values; aborting.")
        pnl_gross = pnl_net + cost
        return pnl_net, pnl_gross, cost, {
            "formula_id": "net_plus_explicit_total_cost",
            "pnl_net_col": pnl_net_col,
            "cost_total_col": cost_total_col,
        }

    # Option C: component costs + net.
    component_cols = [c for c in COMPONENT_COST_COL_CANDIDATES if c in cols]
    if component_cols and pnl_net_col is not None:
        cost = pd.Series(0.0, index=df.index, dtype=float)
        for c in component_cols:
            cost = cost + pd.to_numeric(df[c], errors="coerce")
        if cost.isna().any():
            raise ValueError(f"NaN values found in component costs: {component_cols}")
        if (cost < -1e-9).any():
            raise ValueError("Derived component costs include negative values; aborting.")
        pnl_gross = pnl_net + cost
        return pnl_net, pnl_gross, cost, {
            "formula_id": "net_plus_component_costs",
            "pnl_net_col": pnl_net_col,
            "component_cost_cols": component_cols,
        }

    # Option D: derive gross from mid prices and direction.
    required_mid = {"entry_mid", "exit_mid", "direction"}
    if required_mid.issubset(cols) and qty_col is not None and pnl_net_col is not None:
        sign = _direction_sign(df["direction"])
        qty = pd.to_numeric(df[qty_col], errors="coerce")
        entry_mid = pd.to_numeric(df["entry_mid"], errors="coerce")
        exit_mid = pd.to_numeric(df["exit_mid"], errors="coerce")
        pnl_gross = (exit_mid - entry_mid) * sign * qty
        if pnl_gross.isna().any():
            raise ValueError("NaN values found while deriving gross pnl from mid prices.")
        cost = pnl_gross - pnl_net
        if (cost < -1e-9).any():
            raise ValueError("Derived cost from mid/net produced negative values; aborting.")
        return pnl_net, pnl_gross, cost, {
            "formula_id": "gross_from_mid_minus_net",
            "pnl_net_col": pnl_net_col,
            "qty_col": qty_col,
            "required_cols": ["entry_mid", "exit_mid", "direction", qty_col],
        }

    # Option E: derive cost from execution-vs-mid plus optional commission.
    required_exec = {"entry_price", "exit_price", "entry_mid", "exit_mid", "direction"}
    if required_exec.issubset(cols) and qty_col is not None and pnl_net_col is not None:
        sign = _direction_sign(df["direction"])
        qty = pd.to_numeric(df[qty_col], errors="coerce")
        entry_price = pd.to_numeric(df["entry_price"], errors="coerce")
        exit_price = pd.to_numeric(df["exit_price"], errors="coerce")
        entry_mid = pd.to_numeric(df["entry_mid"], errors="coerce")
        exit_mid = pd.to_numeric(df["exit_mid"], errors="coerce")
        pnl_exec = (exit_price - entry_price) * sign * qty
        pnl_gross = (exit_mid - entry_mid) * sign * qty
        cost_price_impact = pnl_gross - pnl_exec
        cost = cost_price_impact.copy()
        commission_cols = [c for c in ("commission", "commission_cost", "fees") if c in cols]
        if commission_cols:
            for c in commission_cols:
                cost = cost + pd.to_numeric(df[c], errors="coerce")
        if cost.isna().any():
            raise ValueError("NaN values found while deriving cost from execution-vs-mid.")
        if (cost < -1e-9).any():
            raise ValueError("Derived cost from execution-vs-mid produced negative values; aborting.")
        return pnl_net, pnl_gross, cost, {
            "formula_id": "cost_from_exec_vs_mid",
            "pnl_net_col": pnl_net_col,
            "qty_col": qty_col,
            "commission_cols": commission_cols,
        }

    raise RuntimeError(
        "Unable to infer post-hoc cost model from trades columns. "
        f"Available columns: {list(df.columns)}"
    )


def _find_risk_series(trades: pd.DataFrame, pnl_net: pd.Series, r_col: str | None) -> tuple[pd.Series, str]:
    risk_col = _find_first_col(trades, RISK_COL_CANDIDATES)
    if risk_col is not None:
        risk = pd.to_numeric(trades[risk_col], errors="coerce")
        if risk.isna().any() or (risk <= 0).any():
            raise ValueError(f"Invalid risk values in `{risk_col}` (NaN or <= 0).")
        return risk, risk_col

    if r_col is not None:
        r = pd.to_numeric(trades[r_col], errors="coerce")
        safe = r.abs() > 1e-12
        risk = pd.Series([math.nan] * len(trades), index=trades.index, dtype=float)
        risk.loc[safe] = pnl_net.loc[safe] / r.loc[safe]
        if risk.isna().any() or (risk <= 0).any():
            raise ValueError("Could not infer stable positive risk per trade from pnl/r.")
        return risk, f"derived_from_{r_col}"

    raise RuntimeError("No risk column found and no R column available for risk inference.")


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


def _write_limitation_doc(path: Path, run_dir: Path, error_text: str, columns: list[str]) -> None:
    lines = [
        "# Post-hoc Cost Stress Limitation",
        "",
        "No se pudo construir el stress post-hoc ideal (trade-set fijo) con los artefactos actuales.",
        "",
        f"- run_dir: `{run_dir.as_posix()}`",
        f"- error: `{_short(error_text)}`",
        "- columnas detectadas en trades.csv:",
        f"  - {', '.join(columns)}",
        "",
        "## Columna minima faltante sugerida",
        "- Se requiere al menos una forma explicita de coste por trade (`cost_total` o `pnl_gross` junto con `pnl_net`).",
        "- Alternativamente, deben existir suficientes columnas para derivar gross/net de forma inequivoca.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_posthoc_cost_stress(
    run_dir: Path,
    *,
    factors: list[float] | None = None,
    seed: int = 42,
    resamples: int = 5000,
    limitation_doc: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trades_path = run_dir / "trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"Missing trades.csv: {trades_path.as_posix()}")

    trades = pd.read_csv(trades_path)
    if trades.empty:
        raise RuntimeError(f"Empty trades.csv: {trades_path.as_posix()}")

    r_col = _find_first_col(trades, R_COL_CANDIDATES)

    try:
        pnl_net, pnl_gross, cost, model_meta = _detect_cost_model(trades)
        risk, risk_source = _find_risk_series(trades, pnl_net, r_col)
    except Exception as exc:
        if limitation_doc is not None:
            _write_limitation_doc(limitation_doc, run_dir, str(exc), list(trades.columns))
            hint = f" See `{limitation_doc.as_posix()}`."
        else:
            hint = ""
        raise RuntimeError(
            f"Unable to compute ideal post-hoc stress.{hint} Root cause: {_short(str(exc))}"
        ) from exc

    if pnl_net.isna().any() or pnl_gross.isna().any() or cost.isna().any() or risk.isna().any():
        raise RuntimeError("Detected NaN values in required series (pnl_net/pnl_gross/cost/risk).")
    if (risk <= 0).any():
        raise RuntimeError("Risk values must be positive for R recomputation.")
    if (cost < -1e-9).any():
        raise RuntimeError("Negative costs detected after model inference.")

    factors = factors or [1.2, 1.5]
    factor_values = [1.0] + [float(f) for f in factors]
    seen: set[float] = set()
    uniq_factors: list[float] = []
    for f in factor_values:
        if f not in seen:
            seen.add(f)
            uniq_factors.append(f)
    factor_values = uniq_factors

    per_trade = trades.copy()
    per_trade["pnl_net_base"] = pnl_net
    per_trade["pnl_gross_base"] = pnl_gross
    per_trade["cost_base"] = cost
    per_trade["risk_used"] = risk

    rows: list[dict[str, Any]] = []
    for factor in factor_values:
        pnl_net_post = pnl_gross - (cost * factor)
        r_post = pnl_net_post / risk
        if r_post.isna().any():
            raise RuntimeError(f"NaN values in post-hoc R for factor={factor}")

        r_np = r_post.to_numpy(dtype=float)
        kpis = _compute_kpis(r_np)
        ci_low, ci_high, crosses_zero = _bootstrap_ci(r_np, resamples=int(resamples), seed=int(seed))

        label = "BASE" if abs(factor - 1.0) < 1e-12 else f"+{int(round((factor - 1.0) * 100))}% COST"
        rows.append(
            {
                "scenario": label,
                "factor": factor,
                "pf": kpis["pf"],
                "expectancy_R": kpis["expectancy_R"],
                "trades": kpis["trades"],
                "winrate": kpis["winrate"],
                "ci_low": ci_low,
                "ci_high": ci_high,
                "crosses_zero": crosses_zero,
                "seed": int(seed),
                "resamples": int(resamples),
            }
        )

        suffix = str(factor).replace(".", "_")
        per_trade[f"pnl_net_posthoc_f{suffix}"] = pnl_net_post
        per_trade[f"r_multiple_posthoc_f{suffix}"] = r_post

    summary = pd.DataFrame(rows)
    meta = {
        "run_dir": run_dir.as_posix(),
        "trades": int(len(trades)),
        "r_col": r_col,
        "risk_source": risk_source,
        "cost_model": model_meta,
        "factors": factor_values,
    }
    return summary, per_trade, meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Ideal post-hoc cost stress with fixed trade set.")
    parser.add_argument("--run-dir", required=True, help="Run directory path, e.g. outputs/runs/<run_id>")
    parser.add_argument("--factors", nargs="+", type=float, default=[1.2, 1.5], help="Cost multipliers")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument(
        "--out",
        default="outputs/posthoc_cost_stress/posthoc_cost_stress.csv",
        help="Output summary CSV path",
    )
    parser.add_argument(
        "--report",
        default="docs/POSTHOC_COST_STRESS.md",
        help="Output markdown report path",
    )
    parser.add_argument(
        "--limitation-doc",
        default="docs/POSTHOC_COST_STRESS_LIMITATION.md",
        help="Limitation doc path if ideal post-hoc cannot be inferred",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    out_path = Path(args.out)
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    summary, per_trade, meta = run_posthoc_cost_stress(
        run_dir,
        factors=[float(x) for x in args.factors],
        seed=int(args.seed),
        resamples=int(args.resamples),
        limitation_doc=Path(args.limitation_doc),
    )

    summary.to_csv(out_path, index=False)
    per_trade_path = out_dir / "posthoc_cost_stress_per_trade.csv"
    per_trade.to_csv(per_trade_path, index=False)

    meta = {
        **meta,
        "summary_csv": out_path.as_posix(),
        "per_trade_csv": per_trade_path.as_posix(),
    }
    meta_path = out_dir / "posthoc_cost_stress_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Post-hoc Cost Stress (Trade-set fixed)")
    lines.append("")
    lines.append("Este stress es **post-hoc** con **mismo set de trades** del run base (sin re-simular).")
    lines.append("")
    lines.append(f"- run_dir: `{run_dir.as_posix()}`")
    lines.append(f"- trades (fixed): `{meta.get('trades', 'NA')}`")
    lines.append(f"- cost_model_formula: `{meta.get('cost_model', {}).get('formula_id', 'NA')}`")
    lines.append(f"- risk_source: `{meta.get('risk_source', 'NA')}`")
    lines.append(f"- summary_csv: `{out_path.as_posix()}`")
    lines.append(f"- per_trade_csv: `{per_trade_path.as_posix()}`")
    lines.append("")
    lines.append("## Stress Table")
    lines.append(
        _md_table(
            summary[
                [
                    "scenario",
                    "factor",
                    "pf",
                    "expectancy_R",
                    "trades",
                    "winrate",
                    "ci_low",
                    "ci_high",
                    "crosses_zero",
                ]
            ],
            float_cols={"factor", "pf", "expectancy_R", "winrate", "ci_low", "ci_high"},
        )
    )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {out_path.as_posix()}")
    print(f"Wrote: {per_trade_path.as_posix()}")
    print(f"Wrote: {meta_path.as_posix()}")
    print(f"Wrote: {report_path.as_posix()}")
    print(f"cost_model_formula: {meta.get('cost_model', {}).get('formula_id', 'NA')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
