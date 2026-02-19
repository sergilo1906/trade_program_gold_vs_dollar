from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
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


def _short(text: str, limit: int = 600) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _extract_run_id(output: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", output)
    if not m:
        raise ValueError(f"Unable to parse run_id from output: {_short(output, 300)}")
    return m.group(1)


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    raise ValueError(f"No R column found in trades. columns={list(df.columns)}")


def _compute_trade_kpis(trades_path: Path) -> dict[str, Any]:
    if not trades_path.exists():
        return {
            "pf": math.nan,
            "expectancy_R": math.nan,
            "trades": 0,
            "winrate": math.nan,
            "r_col": "",
        }
    trades = pd.read_csv(trades_path)
    if trades.empty:
        return {
            "pf": math.nan,
            "expectancy_R": math.nan,
            "trades": 0,
            "winrate": math.nan,
            "r_col": "",
        }
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    n = int(r.size)
    if n == 0:
        return {
            "pf": math.nan,
            "expectancy_R": math.nan,
            "trades": 0,
            "winrate": math.nan,
            "r_col": r_col,
        }
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss > 0:
        pf = gross_win / gross_loss
    else:
        pf = float("inf") if gross_win > 0 else math.nan
    return {
        "pf": float(pf),
        "expectancy_R": float(r.mean()),
        "trades": n,
        "winrate": float((r > 0).mean()),
        "r_col": r_col,
    }


def _read_boot_row(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "diagnostics" / "BOOT_expectancy_ci.csv"
    if not p.exists():
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples_file": pd.NA,
        }
    df = pd.read_csv(p)
    if df.empty:
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples_file": pd.NA,
        }
    row = df.iloc[0]
    return {
        "boot_n": row.get("n", pd.NA),
        "boot_mean": row.get("mean", pd.NA),
        "boot_ci_low": row.get("ci_low", pd.NA),
        "boot_ci_high": row.get("ci_high", pd.NA),
        "boot_crosses_zero": row.get("crosses_zero", pd.NA),
        "boot_resamples_file": row.get("resamples", pd.NA),
    }


def _parse_windows(text: str) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    for p in parts:
        if ":" not in p:
            raise ValueError(f"Invalid window spec `{p}`. Expected start:end")
        start_s, end_s = p.split(":", 1)
        start = float(start_s)
        end = float(end_s)
        if not (0.0 <= start < end <= 1.0):
            raise ValueError(f"Invalid window range `{p}`. Must satisfy 0<=start<end<=1")
        out.append((start, end))
    if not out:
        raise ValueError("No windows parsed.")
    return out


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


def _to_bool(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Rolling holdout OOS evaluation for one config.")
    parser.add_argument("--data", default="data/xauusd_m5_backtest_ready.csv")
    parser.add_argument("--config", default="configs/config_v3_AUTO_EXP_B.yaml")
    parser.add_argument(
        "--windows",
        default="0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0",
        help="Comma-separated ranges start:end in [0,1].",
    )
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="outputs/rolling_holdout")
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report", default="docs/ROLLING_HOLDOUT.md")
    parser.add_argument("--tmp-dir", default="data/tmp_rolling")
    args = parser.parse_args()

    data_path = Path(args.data)
    config_path = Path(args.config)
    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    report_path = Path(args.report)
    tmp_dir = Path(args.tmp_dir)

    notes: list[str] = []

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path.as_posix()}")

    windows = _parse_windows(args.windows)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(data_path)
    if "timestamp" not in data.columns:
        raise RuntimeError("Input data must include `timestamp` column.")
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    data = data.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    n = len(data)
    if n == 0:
        raise RuntimeError("Input data has 0 valid rows after timestamp parse.")

    rows: list[dict[str, Any]] = []
    for idx, (start, end) in enumerate(windows, start=1):
        label = f"W{idx}"
        i0 = int(math.floor(start * n))
        i1 = int(math.floor(end * n))
        window_df = data.iloc[i0:i1].copy()
        tmp_csv = tmp_dir / f"{label}_{int(start*100)}_{int(end*100)}.csv"
        window_df.to_csv(tmp_csv, index=False)

        row: dict[str, Any] = {
            "window": label,
            "start_pct": start,
            "end_pct": end,
            "rows": int(len(window_df)),
            "start_ts": str(window_df["timestamp"].iloc[0]) if not window_df.empty else "NA",
            "end_ts": str(window_df["timestamp"].iloc[-1]) if not window_df.empty else "NA",
            "data_csv": tmp_csv.as_posix(),
            "run_id": "",
            "status": "pending",
            "note": "",
            "pf": math.nan,
            "expectancy_R": math.nan,
            "trades": 0,
            "winrate": math.nan,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples_used": pd.NA,
        }

        if window_df.empty:
            row["status"] = "failed"
            row["note"] = "Window produced 0 rows."
            notes.append(f"{label}: empty window rows for range {start}:{end}")
            rows.append(row)
            continue

        try:
            run_cmd = [
                sys.executable,
                "scripts/run_and_tag.py",
                "--data",
                tmp_csv.as_posix(),
                "--config",
                config_path.as_posix(),
                "--runs-root",
                runs_root.as_posix(),
            ]
            run_res = _run_cmd(run_cmd)
            if run_res.returncode != 0:
                raise RuntimeError(
                    f"run_and_tag failed rc={run_res.returncode}; stderr={_short(run_res.stderr)}"
                )
            run_id = _extract_run_id(run_res.stdout)
            row["run_id"] = run_id

            run_dir = runs_root / run_id
            diag_cmd = [sys.executable, "scripts/diagnose_run.py", run_dir.as_posix()]
            diag_res = _run_cmd(diag_cmd)
            if diag_res.returncode != 0:
                raise RuntimeError(
                    f"diagnose_run failed rc={diag_res.returncode}; stderr={_short(diag_res.stderr)}"
                )

            boot_cmd = [
                sys.executable,
                "scripts/bootstrap_expectancy.py",
                run_dir.as_posix(),
                "--resamples",
                str(int(args.resamples)),
                "--seed",
                str(int(args.seed)),
            ]
            boot_res = _run_cmd(boot_cmd)
            boot_used = int(args.resamples)
            if boot_res.returncode != 0:
                # Resource fallback requested by instruction.
                fallback_cmd = [
                    sys.executable,
                    "scripts/bootstrap_expectancy.py",
                    run_dir.as_posix(),
                    "--resamples",
                    "2000",
                    "--seed",
                    str(int(args.seed)),
                ]
                fallback_res = _run_cmd(fallback_cmd)
                if fallback_res.returncode != 0:
                    raise RuntimeError(
                        "bootstrap_expectancy failed at requested and fallback resamples; "
                        f"stderr={_short(fallback_res.stderr)}"
                    )
                boot_used = 2000
                row["note"] = "bootstrap fallback to 2000 resamples due prior failure"
                notes.append(
                    f"{label}: bootstrap failed at {args.resamples}, fallback to 2000 applied."
                )

            k = _compute_trade_kpis(run_dir / "trades.csv")
            boot = _read_boot_row(run_dir)
            row.update(
                {
                    "status": "ok",
                    "pf": k["pf"],
                    "expectancy_R": k["expectancy_R"],
                    "trades": k["trades"],
                    "winrate": k["winrate"],
                    "boot_ci_low": boot["boot_ci_low"],
                    "boot_ci_high": boot["boot_ci_high"],
                    "boot_crosses_zero": boot["boot_crosses_zero"],
                    "boot_resamples_used": boot_used,
                }
            )
        except Exception as exc:
            row["status"] = "failed"
            row["note"] = _short(str(exc))
            notes.append(f"{label}: {row['note']}")

        rows.append(row)

    runs_df = pd.DataFrame(rows)
    runs_csv = out_dir / "rolling_holdout_runs.csv"
    runs_df.to_csv(runs_csv, index=False)

    ok_df = runs_df[runs_df["status"] == "ok"].copy()
    pos_exp = int((pd.to_numeric(ok_df["expectancy_R"], errors="coerce") > 0).sum()) if not ok_df.empty else 0
    pf_gt_1 = int((pd.to_numeric(ok_df["pf"], errors="coerce") > 1).sum()) if not ok_df.empty else 0
    crosses = 0
    if not ok_df.empty:
        crosses = int(sum(1 for v in ok_df["boot_crosses_zero"] if _to_bool(v) is True))

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "data": data_path.as_posix(),
        "config": config_path.as_posix(),
        "windows": [{"start": s, "end": e} for s, e in windows],
        "runs_csv": runs_csv.as_posix(),
        "windows_total": int(len(runs_df)),
        "windows_ok": int(len(ok_df)),
        "windows_failed": int((runs_df["status"] != "ok").sum()),
        "positive_expectancy_windows": pos_exp,
        "pf_gt_1_windows": pf_gt_1,
        "ci_crosses_zero_windows": crosses,
        "run_ids_ok": ok_df["run_id"].astype(str).tolist() if not ok_df.empty else [],
        "notes": notes,
    }
    summary_path = out_dir / "rolling_holdout_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    rep_lines: list[str] = []
    rep_lines.append("# Rolling HOLDOUT (OOS) - Winner Config")
    rep_lines.append("")
    rep_lines.append(f"- data: `{data_path.as_posix()}`")
    rep_lines.append(f"- config: `{config_path.as_posix()}`")
    rep_lines.append("- windows: `" + args.windows + "`")
    rep_lines.append("")
    rep_lines.append("## Results by window")
    rep_cols = [
        "window",
        "start_pct",
        "end_pct",
        "rows",
        "start_ts",
        "end_ts",
        "run_id",
        "status",
        "pf",
        "expectancy_R",
        "trades",
        "winrate",
        "boot_ci_low",
        "boot_ci_high",
        "boot_crosses_zero",
        "note",
    ]
    rep_lines.append(
        _md_table(
            runs_df[rep_cols],
            float_cols={
                "start_pct",
                "end_pct",
                "pf",
                "expectancy_R",
                "winrate",
                "boot_ci_low",
                "boot_ci_high",
            },
        )
    )
    rep_lines.append("")
    rep_lines.append("## Stability summary")
    rep_lines.append(f"- windows_ok: `{summary['windows_ok']}/{summary['windows_total']}`")
    rep_lines.append(f"- windows with expectancy_R > 0: `{summary['positive_expectancy_windows']}`")
    rep_lines.append(f"- windows with PF > 1: `{summary['pf_gt_1_windows']}`")
    rep_lines.append(f"- windows with bootstrap CI crossing 0: `{summary['ci_crosses_zero_windows']}`")
    rep_lines.append("")
    rep_lines.append("## Artifacts")
    rep_lines.append(f"- runs_csv: `{runs_csv.as_posix()}`")
    rep_lines.append(f"- summary_json: `{summary_path.as_posix()}`")
    if summary["run_ids_ok"]:
        rep_lines.append("- run_ids_ok: " + ", ".join(f"`{x}`" for x in summary["run_ids_ok"]))
    if notes:
        rep_lines.append("")
        rep_lines.append("## Notes")
        for n in notes:
            rep_lines.append(f"- {n}")
    rep_lines.append("")
    report_path.write_text("\n".join(rep_lines), encoding="utf-8")

    print(f"Wrote: {runs_csv.as_posix()}")
    print(f"Wrote: {summary_path.as_posix()}")
    print(f"Wrote: {report_path.as_posix()}")
    if summary["run_ids_ok"]:
        print("run_ids_ok:", ",".join(summary["run_ids_ok"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
