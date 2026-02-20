from __future__ import annotations

import argparse
import json
import math
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


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def _short(text: str, limit: int = 700) -> str:
    s = " ".join(str(text).split())
    return s if len(s) <= limit else (s[: limit - 3] + "...")


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
            out.append((run_dir.name, meta, run_dir))
        except Exception:
            continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild V4 scoreboard from completed run_meta/trades/boot artifacts.")
    parser.add_argument("--data", default="data_local/xauusd_m5_DEV_2021_2023.csv")
    parser.add_argument("--baseline-config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--candidates-dir", default="configs/v4_candidates2")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="outputs/v4_dev_runs2")
    parser.add_argument("--note", default="reconstructed from outputs/runs after wrapper timeout/log interruption")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    baseline_cfg = _resolve(args.baseline_config)
    candidates_dir = _resolve(args.candidates_dir)
    runs_root = _resolve(args.runs_root)
    out_dir = _resolve(args.out_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not baseline_cfg.exists():
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if not runs_root.exists():
        raise FileNotFoundError(f"Missing runs root: {runs_root.as_posix()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = sorted([p.resolve() for p in candidates_dir.glob("*.yaml") if p.is_file()])
    if not candidates:
        raise RuntimeError(f"No candidate YAML files found under: {candidates_dir.as_posix()}")

    meta_rows = _iter_run_meta(runs_root)
    data_key = data_path.as_posix().lower().replace("\\", "/")

    by_cfg_latest: dict[str, tuple[str, Path]] = {}
    for run_id, meta, run_dir in meta_rows:
        cfg_key = str(meta.get("config_path", "")).lower().replace("\\", "/")
        d_key = str(meta.get("data_path", "")).lower().replace("\\", "/")
        if d_key != data_key:
            continue
        prev = by_cfg_latest.get(cfg_key)
        if (prev is None) or (run_id > prev[0]):
            by_cfg_latest[cfg_key] = (run_id, run_dir)

    baseline_key = baseline_cfg.as_posix().lower().replace("\\", "/")
    baseline_rec = by_cfg_latest.get(baseline_key)
    baseline_run_id = ""
    baseline_trades = 0
    notes: list[str] = [args.note]
    if baseline_rec is not None:
        baseline_run_id, baseline_run_dir = baseline_rec
        baseline_trades = int(_compute_trade_kpis(baseline_run_dir / "trades.csv")["trades"])
    else:
        notes.append(f"baseline missing run_meta match for {baseline_cfg.as_posix()}")

    rows: list[dict[str, Any]] = []
    for cfg_path in candidates:
        cfg_key = cfg_path.as_posix().lower().replace("\\", "/")
        row: dict[str, Any] = {
            "candidate": cfg_path.stem,
            "config": cfg_path.as_posix(),
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
        rec = by_cfg_latest.get(cfg_key)
        if rec is None:
            rows.append(row)
            continue
        run_id, run_dir = rec
        try:
            k = _compute_trade_kpis(run_dir / "trades.csv")
            b = _read_boot_row(run_dir)
            row.update(
                {
                    "run_id": run_id,
                    "status": "ok",
                    "pf": k["pf"],
                    "expectancy_R": k["expectancy_R"],
                    "trades": k["trades"],
                    "winrate": k["winrate"],
                    "ci_low": b["ci_low"],
                    "ci_high": b["ci_high"],
                    "crosses_zero": b["crosses_zero"],
                    "boot_resamples_used": b["boot_resamples_used"],
                    "note": "",
                }
            )
        except Exception as exc:
            row["run_id"] = run_id
            row["status"] = "failed"
            row["note"] = _short(exc)
        rows.append(row)

    df = pd.DataFrame(rows)
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
        df["gate_retention_gt_90"] = (pd.to_numeric(df["retention_vs_b4_pct"], errors="coerce") >= 90.0) & (
            df["status"] == "ok"
        )
        df["gate_all"] = (
            df["gate_pf_gt_1"] & df["gate_exp_gt_0"] & df["gate_ci_not_cross_zero"] & df["gate_retention_gt_90"]
        )
        df = df.sort_values(
            ["gate_all", "gate_pf_gt_1", "gate_exp_gt_0", "expectancy_R", "pf", "trades"],
            ascending=[False, False, False, False, False, False],
        ).reset_index(drop=True)

    out_csv = out_dir / "v4_candidates_scoreboard.csv"
    out_md = out_dir / "v4_candidates_scoreboard.md"
    out_json = out_dir / "v4_candidates_scoreboard_summary.json"

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
        "reconstructed": True,
        "reconstruct_reason": args.note,
        "data": data_path.as_posix(),
        "baseline_config": baseline_cfg.as_posix(),
        "baseline_run_id": baseline_run_id,
        "baseline_trades": baseline_trades,
        "candidates_dir": candidates_dir.as_posix(),
        "rows_written": int(len(df)),
        "run_ids_ok": df.loc[df["status"] == "ok", "run_id"].astype(str).tolist() if not df.empty else [],
        "notes": notes,
        "scoreboard_csv": out_csv.as_posix(),
    }
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# V4 Candidates DEV Scoreboard (Reconstructed)")
    md_lines.append("")
    md_lines.append(f"- data: `{data_path.as_posix()}`")
    md_lines.append(f"- baseline_config: `{baseline_cfg.as_posix()}`")
    md_lines.append(f"- baseline_run_id: `{baseline_run_id}`")
    md_lines.append(f"- baseline_trades: `{baseline_trades}`")
    md_lines.append(f"- reconstructed_reason: `{args.note}`")
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
    print(f"Wrote: {out_md.as_posix()}")
    print(f"Wrote: {out_json.as_posix()}")
    print("run_ids_ok:", ",".join(summary["run_ids_ok"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
