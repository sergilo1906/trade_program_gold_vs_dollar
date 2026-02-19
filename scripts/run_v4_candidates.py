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


def _short(text: str, limit: int = 700) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _extract_run_id(output: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", output)
    if not m:
        raise RuntimeError(f"Unable to parse run_id from output: {_short(output, 300)}")
    return m.group(1)


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        c = lowered.get(cand.lower())
        if c is not None:
            return c
    raise RuntimeError(f"No R column found in trades.csv. columns={list(df.columns)}")


def _compute_trade_kpis(trades_path: Path) -> dict[str, Any]:
    if not trades_path.exists():
        return {"pf": math.nan, "expectancy_R": math.nan, "trades": 0, "winrate": math.nan}
    trades = pd.read_csv(trades_path)
    if trades.empty:
        return {"pf": math.nan, "expectancy_R": math.nan, "trades": 0, "winrate": math.nan}
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    if r.empty:
        return {"pf": math.nan, "expectancy_R": math.nan, "trades": 0, "winrate": math.nan}
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss > 0:
        pf = gross_win / gross_loss
    else:
        pf = float("inf") if gross_win > 0 else math.nan
    return {
        "pf": float(pf),
        "expectancy_R": float(r.mean()),
        "trades": int(r.size),
        "winrate": float((r > 0).mean()),
    }


def _read_boot_row(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "diagnostics" / "BOOT_expectancy_ci.csv"
    if not p.exists():
        return {"ci_low": pd.NA, "ci_high": pd.NA, "crosses_zero": pd.NA, "boot_resamples_used": pd.NA}
    df = pd.read_csv(p)
    if df.empty:
        return {"ci_low": pd.NA, "ci_high": pd.NA, "crosses_zero": pd.NA, "boot_resamples_used": pd.NA}
    row = df.iloc[0]
    return {
        "ci_low": row.get("ci_low", pd.NA),
        "ci_high": row.get("ci_high", pd.NA),
        "crosses_zero": row.get("crosses_zero", pd.NA),
        "boot_resamples_used": row.get("resamples", pd.NA),
    }


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


def _resolve_abs(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def _evaluate_config(
    cfg_path: Path,
    data_path: Path,
    runs_root: Path,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate": cfg_path.stem,
        "config": cfg_path.as_posix(),
        "run_id": "",
        "status": "ok",
        "pf": math.nan,
        "expectancy_R": math.nan,
        "trades": 0,
        "winrate": math.nan,
        "ci_low": pd.NA,
        "ci_high": pd.NA,
        "crosses_zero": pd.NA,
        "boot_resamples_used": pd.NA,
        "note": "",
    }
    try:
        run_cmd = [
            sys.executable,
            "scripts/run_and_tag.py",
            "--data",
            data_path.as_posix(),
            "--config",
            cfg_path.as_posix(),
            "--runs-root",
            runs_root.as_posix(),
        ]
        run_res = _run_cmd(run_cmd)
        if run_res.returncode != 0:
            raise RuntimeError(f"run_and_tag failed rc={run_res.returncode}; stderr={_short(run_res.stderr)}")
        run_id = _extract_run_id(run_res.stdout)
        row["run_id"] = run_id
        run_dir = runs_root / run_id

        diag_cmd = [sys.executable, "scripts/diagnose_run.py", run_dir.as_posix()]
        diag_res = _run_cmd(diag_cmd)
        if diag_res.returncode != 0:
            raise RuntimeError(f"diagnose_run failed rc={diag_res.returncode}; stderr={_short(diag_res.stderr)}")

        boot_cmd = [
            sys.executable,
            "scripts/bootstrap_expectancy.py",
            run_dir.as_posix(),
            "--resamples",
            str(int(resamples)),
            "--seed",
            str(int(seed)),
        ]
        boot_res = _run_cmd(boot_cmd)
        boot_used = int(resamples)
        if boot_res.returncode != 0:
            fallback_cmd = [
                sys.executable,
                "scripts/bootstrap_expectancy.py",
                run_dir.as_posix(),
                "--resamples",
                "2000",
                "--seed",
                str(int(seed)),
            ]
            fb_res = _run_cmd(fallback_cmd)
            if fb_res.returncode != 0:
                raise RuntimeError(
                    "bootstrap_expectancy failed at requested and fallback resamples; "
                    f"stderr={_short(fb_res.stderr)}"
                )
            boot_used = 2000
            row["note"] = "bootstrap fallback to 2000 resamples"

        k = _compute_trade_kpis(run_dir / "trades.csv")
        boot = _read_boot_row(run_dir)
        row.update(
            {
                "pf": k["pf"],
                "expectancy_R": k["expectancy_R"],
                "trades": k["trades"],
                "winrate": k["winrate"],
                "ci_low": boot["ci_low"],
                "ci_high": boot["ci_high"],
                "crosses_zero": boot["crosses_zero"],
                "boot_resamples_used": boot_used,
            }
        )
    except Exception as exc:
        row["status"] = "failed"
        row["note"] = _short(str(exc))
    return row


def _truthy_bool(value: Any) -> bool | None:
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
    parser = argparse.ArgumentParser(description="Run V4-A candidate queue on one dataset and build mini-scoreboard.")
    parser.add_argument("--data", default="data_local/xauusd_m5_DEV_2021_2023.csv")
    parser.add_argument("--candidates-dir", default="configs/v4_candidates")
    parser.add_argument("--out-dir", default="outputs/v4_dev_runs")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--baseline-config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_path = _resolve_abs(args.data)
    candidates_dir = _resolve_abs(args.candidates_dir)
    out_dir = _resolve_abs(args.out_dir)
    runs_root = _resolve_abs(args.runs_root)
    baseline_cfg = _resolve_abs(args.baseline_config)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if not baseline_cfg.exists():
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []
    candidates = sorted([p for p in candidates_dir.glob("*.yaml") if p.is_file()])
    if not candidates:
        raise RuntimeError(f"No candidate YAML files found under: {candidates_dir.as_posix()}")

    baseline_row = _evaluate_config(
        cfg_path=baseline_cfg,
        data_path=data_path,
        runs_root=runs_root,
        resamples=int(args.resamples),
        seed=int(args.seed),
    )
    baseline_trades = int(baseline_row.get("trades", 0) or 0) if baseline_row.get("status") == "ok" else 0
    if baseline_row.get("status") != "ok":
        notes.append(f"baseline failed: {baseline_row.get('note', '')}")

    rows: list[dict[str, Any]] = []
    for cfg_path in candidates:
        row = _evaluate_config(
            cfg_path=cfg_path,
            data_path=data_path,
            runs_root=runs_root,
            resamples=int(args.resamples),
            seed=int(args.seed),
        )
        trades = int(row.get("trades", 0) or 0)
        retention = (100.0 * trades / baseline_trades) if baseline_trades > 0 else math.nan
        gate_pf = (not pd.isna(row["pf"])) and float(row["pf"]) > 1.0
        gate_exp = (not pd.isna(row["expectancy_R"])) and float(row["expectancy_R"]) > 0.0
        cz = _truthy_bool(row.get("crosses_zero", pd.NA))
        gate_ci = (cz is False)
        gate_ret = (not pd.isna(retention)) and float(retention) >= 90.0
        row["retention_vs_b4_pct"] = retention
        row["gate_pf_gt_1"] = gate_pf
        row["gate_exp_gt_0"] = gate_exp
        row["gate_ci_not_cross_zero"] = gate_ci
        row["gate_retention_gt_90"] = gate_ret
        row["gate_all"] = bool(gate_pf and gate_exp and gate_ci and gate_ret)
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["pf"] = pd.to_numeric(df["pf"], errors="coerce")
        df["expectancy_R"] = pd.to_numeric(df["expectancy_R"], errors="coerce")
        df["retention_vs_b4_pct"] = pd.to_numeric(df["retention_vs_b4_pct"], errors="coerce")
        df = df.sort_values(
            ["gate_all", "gate_pf_gt_1", "gate_exp_gt_0", "expectancy_R", "pf", "trades"],
            ascending=[False, False, False, False, False, False],
        ).reset_index(drop=True)

    out_csv = out_dir / "v4_candidates_scoreboard.csv"
    out_json = out_dir / "v4_candidates_scoreboard_summary.json"
    out_md = out_dir / "v4_candidates_scoreboard.md"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    cols = [
        "candidate",
        "run_id",
        "status",
        "pf",
        "expectancy_R",
        "trades",
        "winrate",
        "ci_low",
        "ci_high",
        "crosses_zero",
        "retention_vs_b4_pct",
        "gate_pf_gt_1",
        "gate_exp_gt_0",
        "gate_ci_not_cross_zero",
        "gate_retention_gt_90",
        "gate_all",
        "note",
        "config",
    ]
    df = df.reindex(columns=cols)
    df.to_csv(out_csv, index=False)

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "data": data_path.as_posix(),
        "baseline_config": baseline_cfg.as_posix(),
        "baseline_run_id": baseline_row.get("run_id", ""),
        "baseline_trades": baseline_trades,
        "candidates_dir": candidates_dir.as_posix(),
        "rows_written": int(len(df)),
        "run_ids_ok": df.loc[df["status"] == "ok", "run_id"].astype(str).tolist() if not df.empty else [],
        "notes": notes,
        "scoreboard_csv": out_csv.as_posix(),
    }
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# V4 Candidates DEV Scoreboard")
    md_lines.append("")
    md_lines.append(f"- data: `{data_path.as_posix()}`")
    md_lines.append(f"- baseline_config: `{baseline_cfg.as_posix()}`")
    md_lines.append(f"- baseline_run_id: `{summary['baseline_run_id']}`")
    md_lines.append(f"- baseline_trades: `{baseline_trades}`")
    md_lines.append("")
    md_lines.append("## Candidate results")
    md_lines.append(
        _md_table(
            df[
                [
                    "candidate",
                    "run_id",
                    "status",
                    "pf",
                    "expectancy_R",
                    "trades",
                    "retention_vs_b4_pct",
                    "gate_pf_gt_1",
                    "gate_exp_gt_0",
                    "gate_ci_not_cross_zero",
                    "gate_retention_gt_90",
                    "gate_all",
                    "note",
                ]
            ]
            if not df.empty
            else df,
            float_cols={"pf", "expectancy_R", "retention_vs_b4_pct"},
        )
    )
    md_lines.append("")
    md_lines.append("## Artifacts")
    md_lines.append(f"- csv: `{out_csv.as_posix()}`")
    md_lines.append(f"- json: `{out_json.as_posix()}`")
    if notes:
        md_lines.append("")
        md_lines.append("## Notes")
        for note in notes:
            md_lines.append(f"- {note}")
    md_lines.append("")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote: {out_csv.as_posix()}")
    print(f"Wrote: {out_json.as_posix()}")
    print(f"Wrote: {out_md.as_posix()}")
    if summary["run_ids_ok"]:
        print("run_ids_ok:", ",".join(summary["run_ids_ok"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
