from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from posthoc_cost_stress import run_posthoc_cost_stress
except ModuleNotFoundError:
    from scripts.posthoc_cost_stress import run_posthoc_cost_stress


def _short(text: str, limit: int = 600) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _load_run_tokens(runs: list[str], runs_file: str | None) -> list[str]:
    tokens = [x.strip() for x in runs if x.strip()]
    if runs_file:
        p = Path(runs_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                t = line.strip()
                if t and not t.startswith("#"):
                    tokens.append(t)
    # Keep order + dedupe.
    out: list[str] = []
    seen: set[str] = set()
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _resolve_run_dir(token: str, runs_root: Path) -> Path:
    token = token.strip()
    if not token:
        raise ValueError("Empty run token.")

    p = Path(token)
    if p.exists() and p.is_dir() and (p / "trades.csv").exists():
        return p

    direct = runs_root / token
    if direct.exists() and (direct / "trades.csv").exists():
        return direct

    # Support short suffix input, e.g. "141728".
    matches = [d for d in runs_root.iterdir() if d.is_dir() and d.name.endswith(token) and (d / "trades.csv").exists()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(x.name for x in sorted(matches, key=lambda z: z.name))
        raise RuntimeError(f"Ambiguous token `{token}`. Matches: {names}")

    raise FileNotFoundError(f"Cannot resolve run token `{token}` under `{runs_root.as_posix()}`.")


def _load_window_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}
    if "run_id" not in df.columns:
        return {}
    key_col = "window" if "window" in df.columns else None
    if key_col is None:
        return {}
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        rid = str(row.get("run_id", "")).strip()
        win = str(row.get(key_col, "")).strip()
        if rid:
            out[rid] = win
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch post-hoc cost stress across multiple runs.")
    parser.add_argument(
        "--runs",
        nargs="+",
        required=True,
        help="List of run_ids or run_dirs (supports short suffix tokens).",
    )
    parser.add_argument("--runs-file", default=None, help="Optional text file with run tokens, one per line.")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--factors", nargs="+", type=float, default=[1.2, 1.5])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument(
        "--window-map-csv",
        default="outputs/rolling_holdout/rolling_holdout_runs.csv",
        help="Optional csv to map run_id -> window.",
    )
    parser.add_argument(
        "--out",
        default="outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv",
        help="Consolidated output CSV.",
    )
    parser.add_argument(
        "--per-trade-dir",
        default="outputs/posthoc_cost_stress/rolling_per_trade",
        help="Directory to save per-trade posthoc files per run.",
    )
    parser.add_argument(
        "--summary-json",
        default="outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_summary.json",
        help="Summary JSON with failures/notes.",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    per_trade_dir = Path(args.per_trade_dir)
    per_trade_dir.mkdir(parents=True, exist_ok=True)
    summary_json = Path(args.summary_json)
    summary_json.parent.mkdir(parents=True, exist_ok=True)

    tokens = _load_run_tokens(args.runs, args.runs_file)
    if not tokens:
        raise RuntimeError("No run tokens provided.")

    window_map = _load_window_map(Path(args.window_map_csv))
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    for token in tokens:
        try:
            run_dir = _resolve_run_dir(token, runs_root)
            run_id = run_dir.name

            limitation_doc = Path("docs") / f"POSTHOC_COST_STRESS_LIMITATION_{run_id}.md"
            summary_df, per_trade_df, _ = run_posthoc_cost_stress(
                run_dir,
                factors=[float(x) for x in args.factors],
                seed=int(args.seed),
                resamples=int(args.resamples),
                limitation_doc=limitation_doc,
            )

            per_trade_path = per_trade_dir / f"{run_id}_posthoc_per_trade.csv"
            per_trade_df.to_csv(per_trade_path, index=False)

            window = window_map.get(run_id, "")
            for _, srow in summary_df.iterrows():
                rows.append(
                    {
                        "run_id": run_id,
                        "window": window,
                        "scenario": srow.get("scenario", ""),
                        "factor": srow.get("factor", pd.NA),
                        "pf": srow.get("pf", pd.NA),
                        "expectancy_R": srow.get("expectancy_R", pd.NA),
                        "trades": srow.get("trades", pd.NA),
                        "winrate": srow.get("winrate", pd.NA),
                        "ci_low": srow.get("ci_low", pd.NA),
                        "ci_high": srow.get("ci_high", pd.NA),
                        "crosses_zero": srow.get("crosses_zero", pd.NA),
                    }
                )
        except Exception as exc:
            failures.append({"token": token, "error": _short(str(exc))})
            continue

    out_df = pd.DataFrame(
        rows,
        columns=[
            "run_id",
            "window",
            "scenario",
            "factor",
            "pf",
            "expectancy_R",
            "trades",
            "winrate",
            "ci_low",
            "ci_high",
            "crosses_zero",
        ],
    )
    out_df.to_csv(out_path, index=False)

    summary = {
        "runs_requested": tokens,
        "rows_written": int(len(out_df)),
        "runs_ok": sorted(out_df["run_id"].dropna().astype(str).unique().tolist()) if not out_df.empty else [],
        "failures": failures,
        "out_csv": out_path.as_posix(),
        "per_trade_dir": per_trade_dir.as_posix(),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote: {out_path.as_posix()}")
    print(f"Wrote: {summary_json.as_posix()}")
    print(f"rows_written: {len(out_df)}")
    if failures:
        print(f"failures: {len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
