from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


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


def _now_utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _extract_run_id(text: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", text)
    if not m:
        raise RuntimeError(f"Unable to parse run_id from output: {text[-600:]}")
    return m.group(1)


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        c = lowered.get(cand.lower())
        if c is not None:
            return c
    raise RuntimeError(f"No R column found in trades.csv. columns={list(df.columns)}")


def _kpis_from_trades(trades_path: Path) -> dict[str, Any]:
    if not trades_path.exists():
        return {"trades": 0, "winrate": math.nan, "expectancy_R": math.nan, "pf": math.nan}
    trades = pd.read_csv(trades_path)
    if trades.empty:
        return {"trades": 0, "winrate": math.nan, "expectancy_R": math.nan, "pf": math.nan}
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    if r.empty:
        return {"trades": 0, "winrate": math.nan, "expectancy_R": math.nan, "pf": math.nan}
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss > 0:
        pf = gross_win / gross_loss
    else:
        pf = float("inf") if gross_win > 0 else math.nan
    return {
        "trades": int(r.size),
        "winrate": float((r > 0).mean()),
        "expectancy_R": float(r.mean()),
        "pf": float(pf),
    }


def _read_boot_ci(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "diagnostics" / "BOOT_expectancy_ci.csv"
    if not p.exists():
        return {"ci_low": pd.NA, "ci_high": pd.NA, "crosses_zero": pd.NA, "resamples_used": pd.NA}
    df = pd.read_csv(p)
    if df.empty:
        return {"ci_low": pd.NA, "ci_high": pd.NA, "crosses_zero": pd.NA, "resamples_used": pd.NA}
    row = df.iloc[0]
    return {
        "ci_low": row.get("ci_low", pd.NA),
        "ci_high": row.get("ci_high", pd.NA),
        "crosses_zero": row.get("crosses_zero", pd.NA),
        "resamples_used": row.get("resamples", pd.NA),
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


def _materialize_smoke_input(data_path: Path, max_bars: int, stamp: str) -> Path:
    df = pd.read_csv(data_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "timestamp" not in df.columns:
        raise ValueError("Smoke input must contain timestamp column.")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    dropped_nat = before - len(df)
    if max_bars > 0 and len(df) > max_bars:
        df = df.tail(max_bars).reset_index(drop=True)

    tmp_dir = ROOT / "data" / "tmp_smoke"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out = tmp_dir / f"smoke_input_{stamp}.csv"
    df.to_csv(out, index=False)
    print(
        "SMOKE_INPUT | "
        f"path={out.as_posix()} | rows={len(df)} | dropped_nat={dropped_nat} | "
        f"min_ts={df['timestamp'].min()} | max_ts={df['timestamp'].max()}"
    )
    return out


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def _write_smoke_decision(
    decision_doc: Path,
    row: dict[str, Any],
    command_used: str,
    snapshot_dir: Path,
    smoke_input_path: Path,
) -> None:
    status = "funciona" if bool(row.get("pipeline_ok", False)) else "no funciona"
    lines: list[str] = []
    lines.append("# Smoke Decision")
    lines.append("")
    lines.append("## Resultado")
    lines.append("")
    lines.append(f"- decision: **{status}**")
    lines.append(f"- run_id: `{row.get('run_id', '')}`")
    lines.append(f"- pipeline_ok: `{bool(row.get('pipeline_ok', False))}`")
    lines.append(f"- trades: `{row.get('trades', 0)}`")
    lines.append(f"- expectancy_R: `{row.get('expectancy_R')}`")
    lines.append(f"- pf: `{row.get('pf')}`")
    lines.append(f"- winrate: `{row.get('winrate')}`")
    lines.append(f"- ci_low/ci_high: `{row.get('ci_low')}` / `{row.get('ci_high')}`")
    lines.append(f"- crosses_zero: `{row.get('crosses_zero')}`")
    lines.append("")
    lines.append("## Comando Unico")
    lines.append("")
    lines.append(f"```powershell\n{command_used}\n```")
    lines.append("")
    lines.append("## Artefactos")
    lines.append("")
    lines.append(f"- runs_root run: `outputs/runs/{row.get('run_id', '')}`")
    lines.append("- scoreboard csv: `outputs/smoke_runs/smoke_scoreboard.csv`")
    lines.append("- scoreboard md: `outputs/smoke_runs/smoke_scoreboard.md`")
    lines.append("- scoreboard summary: `outputs/smoke_runs/smoke_scoreboard_summary.json`")
    lines.append(f"- snapshot dir: `{snapshot_dir.as_posix()}`")
    lines.append(f"- input materializado: `{smoke_input_path.as_posix()}`")
    lines.append("")
    lines.append("## Notas")
    lines.append("")
    lines.append("- Smoke orientado a plumbing/reproducibilidad; no implica edge productivo.")
    lines.append("- Estrategia baseline smoke: `strategy_family=V4_SESSION_ORB` con parametros permisivos.")
    lines.append("")
    decision_doc.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-command smoke pipeline (run + diagnostics + bootstrap + snapshot).")
    parser.add_argument("--data", default="data/sample_m5.csv")
    parser.add_argument("--config", default="configs/config_smoke_baseline.yaml")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="outputs/smoke_runs")
    parser.add_argument("--snapshot-root", default="docs/_snapshots")
    parser.add_argument("--decision-doc", default="docs/SMOKE_DECISION.md")
    parser.add_argument("--max-bars", type=int, default=1200)
    parser.add_argument("--resamples", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    cfg_path = _resolve(args.config)
    runs_root = _resolve(args.runs_root)
    out_dir = _resolve(args.out_dir)
    snapshot_root = _resolve(args.snapshot_root)
    decision_doc = _resolve(args.decision_doc)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing config file: {cfg_path.as_posix()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    snapshot_root.mkdir(parents=True, exist_ok=True)
    decision_doc.parent.mkdir(parents=True, exist_ok=True)

    stamp = _now_utc_compact()
    smoke_input = _materialize_smoke_input(data_path=data_path, max_bars=int(args.max_bars), stamp=stamp)

    tmp_cfg = out_dir / "_tmp_smoke_config.yaml"
    cfg_obj = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg_obj["runs_output_dir"] = runs_root.as_posix()
    tmp_cfg.write_text(yaml.safe_dump(cfg_obj, sort_keys=False), encoding="utf-8")

    row: dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "ok",
        "run_id": "",
        "run_dir": "",
        "data_source": data_path.as_posix(),
        "smoke_input": smoke_input.as_posix(),
        "config": cfg_path.as_posix(),
        "config_used_for_run": tmp_cfg.as_posix(),
        "trades": 0,
        "winrate": math.nan,
        "expectancy_R": math.nan,
        "pf": math.nan,
        "ci_low": pd.NA,
        "ci_high": pd.NA,
        "crosses_zero": pd.NA,
        "boot_resamples_used": pd.NA,
        "pipeline_ok": False,
        "note": "",
    }

    try:
        run_cmd = [
            sys.executable,
            "scripts/run_and_tag.py",
            "--data",
            smoke_input.as_posix(),
            "--config",
            tmp_cfg.as_posix(),
            "--runs-root",
            runs_root.as_posix(),
        ]
        run_res = _run_cmd(run_cmd)
        if run_res.returncode != 0:
            raise RuntimeError(f"run_and_tag failed rc={run_res.returncode}: {run_res.stderr.strip()}")
        run_id = _extract_run_id(run_res.stdout)
        run_dir = runs_root / run_id
        row["run_id"] = run_id
        row["run_dir"] = run_dir.as_posix()

        diag_cmd = [sys.executable, "scripts/diagnose_run.py", run_dir.as_posix()]
        diag_res = _run_cmd(diag_cmd)
        if diag_res.returncode != 0:
            raise RuntimeError(f"diagnose_run failed rc={diag_res.returncode}: {diag_res.stderr.strip()}")

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
            fallback_cmd = [
                sys.executable,
                "scripts/bootstrap_expectancy.py",
                run_dir.as_posix(),
                "--resamples",
                "2000",
                "--seed",
                str(int(args.seed)),
            ]
            fb_res = _run_cmd(fallback_cmd)
            if fb_res.returncode != 0:
                raise RuntimeError(
                    "bootstrap_expectancy failed at requested and fallback resamples: "
                    f"{fb_res.stderr.strip()}"
                )
            boot_used = 2000
            row["note"] = "bootstrap fallback to 2000 resamples"

        k = _kpis_from_trades(run_dir / "trades.csv")
        b = _read_boot_ci(run_dir)
        row.update(k)
        row["ci_low"] = b["ci_low"]
        row["ci_high"] = b["ci_high"]
        row["crosses_zero"] = b["crosses_zero"]
        row["boot_resamples_used"] = boot_used
        row["pipeline_ok"] = bool(k["trades"] > 0 and run_dir.exists())
    except Exception as exc:
        row["status"] = "failed"
        row["note"] = str(exc)
        row["pipeline_ok"] = False

    score_df = pd.DataFrame([row])
    score_csv = out_dir / "smoke_scoreboard.csv"
    score_md = out_dir / "smoke_scoreboard.md"
    score_json = out_dir / "smoke_scoreboard_summary.json"

    score_df.to_csv(score_csv, index=False)
    score_md.write_text(
        "\n".join(
            [
                "# Smoke Scoreboard",
                "",
                _md_table(
                    score_df[
                        [
                            "generated_utc",
                            "status",
                            "pipeline_ok",
                            "run_id",
                            "trades",
                            "winrate",
                            "expectancy_R",
                            "pf",
                            "ci_low",
                            "ci_high",
                            "crosses_zero",
                            "boot_resamples_used",
                            "note",
                        ]
                    ],
                    float_cols={"winrate", "expectancy_R", "pf", "ci_low", "ci_high"},
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = {
        "generated_utc": row["generated_utc"],
        "status": row["status"],
        "pipeline_ok": bool(row["pipeline_ok"]),
        "run_id": row["run_id"],
        "run_dir": row["run_dir"],
        "trades": int(row["trades"]) if pd.notna(row["trades"]) else 0,
        "expectancy_R": row["expectancy_R"],
        "pf": row["pf"],
        "winrate": row["winrate"],
        "ci_low": row["ci_low"],
        "ci_high": row["ci_high"],
        "crosses_zero": row["crosses_zero"],
        "scoreboard_csv": score_csv.as_posix(),
        "scoreboard_md": score_md.as_posix(),
        "note": row["note"],
    }
    score_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    snapshot_dir = snapshot_root / f"smoke_{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(score_csv, snapshot_dir / "smoke_scoreboard.csv")
    shutil.copy2(score_md, snapshot_dir / "smoke_scoreboard.md")
    shutil.copy2(score_json, snapshot_dir / "smoke_scoreboard_summary.json")

    command_used = (
        f"python scripts/run_smoke.py --data {args.data} --config {args.config} "
        f"--max-bars {int(args.max_bars)} --resamples {int(args.resamples)} --seed {int(args.seed)}"
    )
    _write_smoke_decision(
        decision_doc=decision_doc,
        row=row,
        command_used=command_used,
        snapshot_dir=snapshot_dir,
        smoke_input_path=smoke_input,
    )

    if (not args.keep_temp) and smoke_input.exists():
        smoke_input.unlink(missing_ok=True)
    if (not args.keep_temp) and tmp_cfg.exists():
        tmp_cfg.unlink(missing_ok=True)

    print(f"SMOKE_STATUS: {row['status']}")
    print(f"SMOKE_PIPELINE_OK: {bool(row['pipeline_ok'])}")
    print(f"SMOKE_RUN_ID: {row['run_id']}")
    print(f"SMOKE_RUN_DIR: {row['run_dir']}")
    print(f"SMOKE_TRADES: {row['trades']}")
    print(f"SMOKE_SCOREBOARD: {score_csv.as_posix()}")
    print(f"SMOKE_SNAPSHOT_DIR: {snapshot_dir.as_posix()}")
    print(f"SMOKE_DECISION_DOC: {decision_doc.as_posix()}")
    return 0 if bool(row["pipeline_ok"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
