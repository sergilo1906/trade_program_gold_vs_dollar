from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd


R_CANDIDATES = [
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "pnl_R",
    "pnl_r",
]

TS_CANDIDATES = [
    "entry_time",
    "open_time",
    "entry_ts",
    "timestamp",
    "time",
]

SCENARIOS: list[tuple[str, list[int]]] = [
    ("BASE", []),
    ("EXCL_8_11_14", [8, 11, 14]),
    ("EXCL_0_7", list(range(0, 8))),
    ("EXCL_16_19", [16, 17, 18, 19]),
]


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "(empty)"
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = []
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            vals.append("" if pd.isna(v) else str(v))
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + body)


def _first_present(columns: Iterable[str], candidates: list[str]) -> str | None:
    colset = set(columns)
    for c in candidates:
        if c in colset:
            return c
    return None


def _metrics_from_r(df: pd.DataFrame, r_col: str) -> dict[str, float]:
    if df.empty:
        return {
            "pf": float("nan"),
            "expectancy_R": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
        }
    r = pd.to_numeric(df[r_col], errors="coerce").dropna()
    if r.empty:
        return {
            "pf": float("nan"),
            "expectancy_R": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
        }

    pos_sum = float(r[r > 0].sum())
    neg_abs = float((-r[r < 0]).sum())
    pf = (pos_sum / neg_abs) if neg_abs > 0 else float("nan")
    return {
        "pf": pf,
        "expectancy_R": float(r.mean()),
        "winrate": float((r > 0).mean()),
        "trades": int(len(r)),
    }


def run_ablation(run_dir: Path) -> tuple[Path, Path]:
    trades_path = run_dir / "trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"Missing trades.csv: {trades_path}")

    trades = pd.read_csv(trades_path)
    r_col = _first_present(trades.columns, R_CANDIDATES)
    ts_col = _first_present(trades.columns, TS_CANDIDATES)

    if r_col is None:
        raise ValueError(f"No R column found. Checked: {R_CANDIDATES}")
    if ts_col is None:
        raise ValueError(f"No timestamp column found. Checked: {TS_CANDIDATES}")

    ts = pd.to_datetime(trades[ts_col], errors="coerce", utc=True)
    trades = trades.copy()
    trades["entry_ts_utc"] = ts
    trades = trades.dropna(subset=["entry_ts_utc"])
    trades["hour_utc"] = trades["entry_ts_utc"].dt.hour

    rows: list[dict[str, object]] = []
    for scenario_name, excl_hours in SCENARIOS:
        excl_set = set(excl_hours)
        if excl_set:
            subset = trades[~trades["hour_utc"].isin(excl_set)]
        else:
            subset = trades

        m = _metrics_from_r(subset, r_col)
        rows.append(
            {
                "scenario": scenario_name,
                "excluded_hours_utc": ",".join(str(h) for h in excl_hours) if excl_hours else "",
                "pf": m["pf"],
                "expectancy_R": m["expectancy_R"],
                "winrate": m["winrate"],
                "trades": m["trades"],
            }
        )

    out_df = pd.DataFrame(rows)

    diag_dir = run_dir / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    out_csv = diag_dir / "ABLAT_hours.csv"
    out_df.to_csv(out_csv, index=False)

    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_md = docs_dir / "ABLAT_summary.md"

    md_lines = [
        "# Ablation Hours Summary",
        "",
        f"- run_dir: `{run_dir}`",
        f"- trades source: `{trades_path}`",
        f"- R column detected: `{r_col}`",
        f"- timestamp column detected: `{ts_col}`",
        "",
        "## Results",
        "",
        _markdown_table(out_df),
        "",
        f"- output_csv: `{out_csv}`",
    ]
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    return out_csv, out_md


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablation by excluded UTC hour buckets.")
    parser.add_argument(
        "run_dir",
        nargs="?",
        default="outputs/runs/20260218_161547",
        help="Path to run directory (must contain trades.csv).",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    out_csv, out_md = run_ablation(run_dir)
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
