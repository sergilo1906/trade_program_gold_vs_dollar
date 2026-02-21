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


def _now_utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _short(text: str, limit: int = 700) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    return clean if len(clean) <= limit else (clean[: limit - 3] + "...")


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


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
        return ""
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
    pf = (gross_win / gross_loss) if gross_loss > 0 else (float("inf") if gross_win > 0 else math.nan)
    return {
        "pf": float(pf),
        "expectancy_R": float(r.mean()),
        "trades": int(r.size),
        "winrate": float((r > 0).mean()),
    }


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


def _materialize_input(data_path: Path, max_bars: int, stamp: str) -> Path:
    if max_bars <= 0:
        return data_path
    df = pd.read_csv(data_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "timestamp" not in df.columns and len(df.columns) >= 5:
        # Some local test datasets are headerless. Retry with canonical OHLCV names.
        raw = pd.read_csv(data_path, header=None)
        if raw.shape[1] >= 5:
            cols = ["timestamp", "open", "high", "low", "close", "volume", "spread", "bid", "ask"]
            raw.columns = cols[: raw.shape[1]]
            df = raw.copy()
            df.columns = [str(c).strip().lower() for c in df.columns]
    if "timestamp" not in df.columns:
        raise ValueError("Input data must contain timestamp column.")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if len(df) > max_bars:
        df = df.tail(max_bars).reset_index(drop=True)
    tmp_dir = ROOT / "data" / "tmp_vtm"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out = tmp_dir / f"vtm_input_{stamp}.csv"
    df.to_csv(out, index=False)
    return out


def _iter_run_meta(runs_root: Path) -> list[tuple[str, dict[str, Any], Path]]:
    out: list[tuple[str, dict[str, Any], Path]] = []
    for run_dir in runs_root.iterdir():
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "run_meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append((run_dir.name, meta, run_dir))
    return out


def _latest_runs_by_config_for_data(runs_root: Path, data_path: Path) -> dict[str, tuple[str, Path]]:
    data_key = data_path.as_posix().lower().replace("\\", "/")
    latest: dict[str, tuple[str, Path]] = {}
    for run_id, meta, run_dir in _iter_run_meta(runs_root):
        cfg_key = str(meta.get("config_path", "")).lower().replace("\\", "/")
        d_key = str(meta.get("data_path", "")).lower().replace("\\", "/")
        if d_key != data_key:
            continue
        prev = latest.get(cfg_key)
        if (prev is None) or (run_id > prev[0]):
            latest[cfg_key] = (run_id, run_dir)
    return latest


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


def _evaluate_config(
    cfg_path: Path,
    data_path: Path,
    runs_root: Path,
    resamples: int,
    seed: int,
    log_lines: list[str],
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
    rid = _extract_run_id(f"{run_res.stdout}\n{run_res.stderr}")
    row["run_id"] = rid
    log_lines.append(f"{cfg_path.stem}: run_and_tag rc={run_res.returncode} run_id={rid}")
    if run_res.returncode != 0:
        row["status"] = "failed"
        row["note"] = _short(run_res.stderr or run_res.stdout)
        return row
    if not rid:
        row["status"] = "failed"
        row["note"] = "run_and_tag finished but run_id missing in output"
        return row

    run_dir = runs_root / rid
    diag_cmd = [sys.executable, "scripts/diagnose_run.py", run_dir.as_posix()]
    diag_res = _run_cmd(diag_cmd)
    log_lines.append(f"{cfg_path.stem}: diagnose rc={diag_res.returncode}")
    if diag_res.returncode != 0:
        row["status"] = "failed"
        row["note"] = _short(diag_res.stderr or diag_res.stdout)
        return row

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
        fb = _run_cmd(fallback_cmd)
        log_lines.append(f"{cfg_path.stem}: bootstrap rc={boot_res.returncode} fallback_rc={fb.returncode}")
        if fb.returncode != 0:
            row["status"] = "failed"
            row["note"] = _short(fb.stderr or fb.stdout)
            return row
        boot_used = 2000
        row["note"] = "bootstrap fallback to 2000 resamples"
    else:
        log_lines.append(f"{cfg_path.stem}: bootstrap rc=0 resamples={resamples}")

    k = _compute_trade_kpis(run_dir / "trades.csv")
    b = _read_boot_row(run_dir)
    row.update(
        {
            "pf": k["pf"],
            "expectancy_R": k["expectancy_R"],
            "trades": k["trades"],
            "winrate": k["winrate"],
            "ci_low": b["ci_low"],
            "ci_high": b["ci_high"],
            "crosses_zero": b["crosses_zero"],
            "boot_resamples_used": boot_used,
        }
    )
    return row


def _build_scoreboard(
    *,
    baseline_row: dict[str, Any],
    rows: list[dict[str, Any]],
    out_dir: Path,
    data_path: Path,
    baseline_config: Path,
    candidates_dir: Path,
    notes: list[str],
    reconstructed: bool,
) -> dict[str, Any]:
    df = pd.DataFrame(rows)
    baseline_trades = int(baseline_row.get("trades", 0) or 0) if baseline_row.get("status") == "ok" else 0
    if not df.empty:
        df["pf"] = pd.to_numeric(df["pf"], errors="coerce")
        df["expectancy_R"] = pd.to_numeric(df["expectancy_R"], errors="coerce")
        trades = pd.to_numeric(df["trades"], errors="coerce").fillna(0)
        df["retention_vs_b4_pct"] = (100.0 * trades / baseline_trades) if baseline_trades > 0 else math.nan
        df["gate_pf_gt_1"] = (pd.to_numeric(df["pf"], errors="coerce") > 1.0) & (df["status"] == "ok")
        df["gate_exp_gt_0"] = (pd.to_numeric(df["expectancy_R"], errors="coerce") > 0.0) & (df["status"] == "ok")
        gate_ci: list[bool] = []
        for _, r in df.iterrows():
            cz = _truthy_bool(r.get("crosses_zero", pd.NA))
            gate_ci.append(bool(cz is False))
        df["gate_ci_not_cross_zero"] = gate_ci
        df["gate_trades_ge_100"] = (pd.to_numeric(df["trades"], errors="coerce") >= 100) & (df["status"] == "ok")
        df["gate_all"] = df["gate_exp_gt_0"] & df["gate_ci_not_cross_zero"] & df["gate_trades_ge_100"]
        df = df.sort_values(
            ["gate_all", "expectancy_R", "pf", "trades"],
            ascending=[False, False, False, False],
        ).reset_index(drop=True)

    out_csv = out_dir / "vtm_candidates_scoreboard.csv"
    out_md = out_dir / "vtm_candidates_scoreboard.md"
    out_json = out_dir / "vtm_candidates_scoreboard_summary.json"

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
        "gate_trades_ge_100",
        "gate_all",
        "note",
        "config",
    ]
    df = df.reindex(columns=cols)
    df.to_csv(out_csv, index=False)

    pass_count = int((df["gate_all"] == True).sum()) if not df.empty else 0  # noqa: E712
    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reconstructed": reconstructed,
        "data": data_path.as_posix(),
        "baseline_config": baseline_config.as_posix(),
        "baseline_run_id": baseline_row.get("run_id", ""),
        "baseline_trades": baseline_trades,
        "candidates_dir": candidates_dir.as_posix(),
        "rows_written": int(len(df)),
        "pass_count": pass_count,
        "run_ids_ok": df.loc[df["status"] == "ok", "run_id"].astype(str).tolist() if not df.empty else [],
        "notes": notes,
        "scoreboard_csv": out_csv.as_posix(),
    }
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# VTM Candidates DEV Scoreboard")
    md_lines.append("")
    md_lines.append(f"- data: `{data_path.as_posix()}`")
    md_lines.append(f"- baseline_config: `{baseline_config.as_posix()}`")
    md_lines.append(f"- baseline_run_id: `{summary['baseline_run_id']}`")
    md_lines.append(f"- baseline_trades: `{baseline_trades}`")
    md_lines.append(f"- pass_count(gate_all): `{pass_count}`")
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
                    "crosses_zero",
                    "gate_exp_gt_0",
                    "gate_ci_not_cross_zero",
                    "gate_trades_ge_100",
                    "gate_all",
                    "note",
                ]
            ]
            if not df.empty
            else df,
            float_cols={"pf", "expectancy_R"},
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

    return {"df": df, "summary": summary, "csv": out_csv, "md": out_md, "json": out_json}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VTM candidate queue and build scoreboard.")
    parser.add_argument("--data", default="data_local/xauusd_m5_DEV_2021_2023.csv")
    parser.add_argument("--candidates-dir", default="configs/vtm_candidates")
    parser.add_argument("--out-dir", default="outputs/vtm_dev_runs")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--baseline-config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-bars", type=int, default=0)
    parser.add_argument("--snapshot-root", default="docs/_snapshots")
    parser.add_argument("--snapshot-prefix", default="vtm_dev_2021_2023")
    parser.add_argument("--rebuild-only", action="store_true")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    candidates_dir = _resolve(args.candidates_dir)
    out_dir = _resolve(args.out_dir)
    runs_root = _resolve(args.runs_root)
    baseline_cfg = _resolve(args.baseline_config)
    snapshot_root = _resolve(args.snapshot_root)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if not baseline_cfg.exists():
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    stamp = _now_utc_compact()
    used_data = _materialize_input(data_path=data_path, max_bars=int(args.max_bars), stamp=stamp)
    candidates = sorted([p for p in candidates_dir.glob("*.yaml") if p.is_file()])
    if not candidates:
        raise RuntimeError(f"No candidate YAML files found under: {candidates_dir.as_posix()}")

    notes: list[str] = []
    log_lines: list[str] = [f"generated_utc={datetime.now(timezone.utc).isoformat()}", f"data={used_data.as_posix()}"]

    if args.rebuild_only:
        notes.append("scoreboard rebuilt from run_meta/trades/boot artifacts")
        by_cfg = _latest_runs_by_config_for_data(runs_root, used_data)
        baseline_key = baseline_cfg.as_posix().lower().replace("\\", "/")
        baseline_row = {
            "run_id": "",
            "status": "failed",
            "trades": 0,
            "note": "baseline not found in run_meta for selected data",
        }
        b = by_cfg.get(baseline_key)
        if b is not None:
            b_run_id, b_run_dir = b
            b_k = _compute_trade_kpis(b_run_dir / "trades.csv")
            b_boot = _read_boot_row(b_run_dir)
            baseline_row = {
                "run_id": b_run_id,
                "status": "ok",
                "trades": b_k["trades"],
                "pf": b_k["pf"],
                "expectancy_R": b_k["expectancy_R"],
                "winrate": b_k["winrate"],
                "ci_low": b_boot["ci_low"],
                "ci_high": b_boot["ci_high"],
                "crosses_zero": b_boot["crosses_zero"],
            }
        rows: list[dict[str, Any]] = []
        for cfg in candidates:
            cfg_key = cfg.as_posix().lower().replace("\\", "/")
            rec = by_cfg.get(cfg_key)
            row = {
                "candidate": cfg.stem,
                "config": cfg.as_posix(),
                "run_id": "",
                "status": "failed",
                "pf": math.nan,
                "expectancy_R": math.nan,
                "trades": 0,
                "winrate": math.nan,
                "ci_low": pd.NA,
                "ci_high": pd.NA,
                "crosses_zero": pd.NA,
                "boot_resamples_used": pd.NA,
                "note": "run_meta not found for this config/data",
            }
            if rec is not None:
                run_id, run_dir = rec
                k = _compute_trade_kpis(run_dir / "trades.csv")
                b_row = _read_boot_row(run_dir)
                row.update(
                    {
                        "run_id": run_id,
                        "status": "ok",
                        "pf": k["pf"],
                        "expectancy_R": k["expectancy_R"],
                        "trades": k["trades"],
                        "winrate": k["winrate"],
                        "ci_low": b_row["ci_low"],
                        "ci_high": b_row["ci_high"],
                        "crosses_zero": b_row["crosses_zero"],
                        "boot_resamples_used": b_row["boot_resamples_used"],
                        "note": "",
                    }
                )
            rows.append(row)
        built = _build_scoreboard(
            baseline_row=baseline_row,
            rows=rows,
            out_dir=out_dir,
            data_path=used_data,
            baseline_config=baseline_cfg,
            candidates_dir=candidates_dir,
            notes=notes,
            reconstructed=True,
        )
    else:
        baseline_row = _evaluate_config(
            cfg_path=baseline_cfg,
            data_path=used_data,
            runs_root=runs_root,
            resamples=int(args.resamples),
            seed=int(args.seed),
            log_lines=log_lines,
        )
        if baseline_row.get("status") != "ok":
            notes.append(f"baseline failed: {baseline_row.get('note', '')}")
        rows = []
        for cfg in candidates:
            row = _evaluate_config(
                cfg_path=cfg,
                data_path=used_data,
                runs_root=runs_root,
                resamples=int(args.resamples),
                seed=int(args.seed),
                log_lines=log_lines,
            )
            rows.append(row)
        built = _build_scoreboard(
            baseline_row=baseline_row,
            rows=rows,
            out_dir=out_dir,
            data_path=used_data,
            baseline_config=baseline_cfg,
            candidates_dir=candidates_dir,
            notes=notes,
            reconstructed=False,
        )

    run_log = out_dir / "run.log"
    run_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    snapshot_dir = snapshot_root / f"{args.snapshot_prefix}_{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for src in [built["csv"], built["md"], built["json"]]:
        (snapshot_dir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    (snapshot_dir / "run.log").write_text(run_log.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Wrote: {built['csv'].as_posix()}")
    print(f"Wrote: {built['md'].as_posix()}")
    print(f"Wrote: {built['json'].as_posix()}")
    print(f"Wrote: {run_log.as_posix()}")
    print(f"Snapshot: {snapshot_dir.as_posix()}")
    print("pass_count:", built["summary"]["pass_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
