from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from lib.edge_factory_eval import (
        apply_gates,
        build_score_row,
        config_key,
        data_key,
        load_boot_ci,
        load_cost_stress,
        load_gates_config,
        load_temporal_flags,
        load_trade_kpis,
        merge_metric_payload,
        resolve_stage_config,
    )
except ModuleNotFoundError:
    from scripts.lib.edge_factory_eval import (
        apply_gates,
        build_score_row,
        config_key,
        data_key,
        load_boot_ci,
        load_cost_stress,
        load_gates_config,
        load_temporal_flags,
        load_trade_kpis,
        merge_metric_payload,
        resolve_stage_config,
    )


ROOT = Path(__file__).resolve().parents[1]


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


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
    if not runs_root.exists():
        return out
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


def _load_progress_records(
    progress_jsonl: Path,
    *,
    wanted_data_key: str,
) -> dict[str, dict[str, Any]]:
    latest_by_cfg: dict[str, dict[str, Any]] = {}
    if not progress_jsonl.exists():
        return latest_by_cfg
    for raw in progress_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        cfg = str(rec.get("config", "")).strip()
        dpath = str(rec.get("data_path", "")).strip()
        if not cfg or not dpath:
            continue
        if data_key(dpath) != wanted_data_key:
            continue
        rec_key = config_key(Path(cfg))
        prev = latest_by_cfg.get(rec_key)
        run_id = str(rec.get("run_id", "")).strip()
        if prev is None:
            latest_by_cfg[rec_key] = rec
            continue
        prev_run = str(prev.get("run_id", "")).strip()
        if run_id > prev_run:
            latest_by_cfg[rec_key] = rec
    return latest_by_cfg


def _lookup_from_run_meta(
    *,
    runs_root: Path,
    wanted_data_key: str,
    batch_start_run_id: str,
) -> dict[str, tuple[str, Path]]:
    latest: dict[str, tuple[str, Path]] = {}
    for run_id, meta, run_dir in _iter_run_meta(runs_root):
        if batch_start_run_id and (run_id < batch_start_run_id):
            continue
        cfg_key = config_key(Path(str(meta.get("config_path", ""))))
        d_key = data_key(Path(str(meta.get("data_path", ""))))
        if not cfg_key or d_key != wanted_data_key:
            continue
        prev = latest.get(cfg_key)
        if (prev is None) or (run_id > prev[0]):
            latest[cfg_key] = (run_id, run_dir)
    return latest


def _select_run_for_config(
    *,
    cfg_path: Path,
    runs_root: Path,
    progress_records: dict[str, dict[str, Any]],
    run_meta_latest: dict[str, tuple[str, Path]],
) -> tuple[str, Path | None, str, str]:
    cfg_key = config_key(cfg_path)
    from_progress = progress_records.get(cfg_key)
    if from_progress is not None:
        run_id = str(from_progress.get("run_id", "")).strip()
        note = str(from_progress.get("note", "")).strip()
        status = str(from_progress.get("status", "ok")).strip().lower() or "ok"
        run_dir = runs_root / run_id if run_id else None
        if run_dir is not None and run_dir.exists():
            return run_id, run_dir, status, note
        return run_id, None, "failed", (note or "run from progress not found on disk")

    from_meta = run_meta_latest.get(cfg_key)
    if from_meta is not None:
        run_id, run_dir = from_meta
        return run_id, run_dir, "ok", "resolved from run_meta fallback"

    return "", None, "failed", "run not found in progress/run_meta"


def _order_scoreboard(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    baseline_df = df[df["is_baseline"] == True].copy()  # noqa: E712
    cand_df = df[df["is_baseline"] != True].copy()  # noqa: E712
    if not cand_df.empty:
        cand_df["sort_gate_all"] = cand_df["gate_all"].fillna(False).astype(bool)
        cand_df = cand_df.sort_values(
            ["sort_gate_all", "expectancy_R", "pf", "trades"],
            ascending=[False, False, False, False],
        ).drop(columns=["sort_gate_all"])
    return pd.concat([baseline_df, cand_df], ignore_index=True)


def build_edge_factory_scoreboard(
    *,
    data_path: Path,
    candidates_dir: Path,
    baseline_config: Path | None,
    runs_root: Path,
    out_dir: Path,
    gates_config_path: Path,
    stage: str,
    progress_jsonl: Path | None = None,
    posthoc_csv: Path | None = None,
    temporal_summary_json: Path | None = None,
    note: str = "",
    manifest_path: Path | None = None,
    batch_start_run_id: str = "",
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = sorted([p.resolve() for p in candidates_dir.glob("*.yaml") if p.is_file()])
    if not candidates:
        raise RuntimeError(f"No candidate YAMLs found under: {candidates_dir.as_posix()}")

    data_k = data_key(data_path)
    progress_records = (
        _load_progress_records(progress_jsonl, wanted_data_key=data_k) if progress_jsonl is not None else {}
    )
    run_meta_latest = _lookup_from_run_meta(
        runs_root=runs_root,
        wanted_data_key=data_k,
        batch_start_run_id=batch_start_run_id,
    )

    gates_cfg = load_gates_config(gates_config_path)
    stage_cfg = resolve_stage_config(gates_cfg, stage)

    baseline_run_id = ""
    baseline_trades = 0
    baseline_row: dict[str, Any] | None = None

    rows: list[dict[str, Any]] = []
    if baseline_config is not None:
        b_run_id, b_run_dir, b_status, b_note = _select_run_for_config(
            cfg_path=baseline_config.resolve(),
            runs_root=runs_root,
            progress_records=progress_records,
            run_meta_latest=run_meta_latest,
        )
        if b_run_dir is not None:
            tk = load_trade_kpis(b_run_dir)
            bk = load_boot_ci(b_run_dir)
            merged = merge_metric_payload(
                trade_kpis=tk,
                boot_kpis=bk,
                cost_kpis={"cost_survives_1p2": None, "cost_survives_1p5": None},
                temporal_kpis={"temporal_pass": None},
                baseline_trades=0,
            )
            baseline_trades = int(merged.get("trades", 0) or 0)
            baseline_run_id = b_run_id
            if tk.get("trade_status") != "ok":
                b_status = "failed"
                if b_note:
                    b_note = f"{b_note}; trade_status={tk.get('trade_status')}"
                else:
                    b_note = f"trade_status={tk.get('trade_status')}"
            baseline_row = build_score_row(
                candidate="__baseline__",
                config_path=baseline_config.resolve(),
                run_id=b_run_id,
                status=b_status,
                is_baseline=True,
                metrics=merged,
                gate_result=None,
                note=b_note,
            )
        else:
            baseline_row = build_score_row(
                candidate="__baseline__",
                config_path=baseline_config.resolve(),
                run_id=b_run_id,
                status="failed",
                is_baseline=True,
                metrics={},
                gate_result=None,
                note=b_note,
            )

    if baseline_row is not None:
        rows.append(baseline_row)

    for cfg in candidates:
        run_id, run_dir, status, row_note = _select_run_for_config(
            cfg_path=cfg,
            runs_root=runs_root,
            progress_records=progress_records,
            run_meta_latest=run_meta_latest,
        )
        if run_dir is None:
            rows.append(
                build_score_row(
                    candidate=cfg.stem,
                    config_path=cfg,
                    run_id=run_id,
                    status="failed",
                    is_baseline=False,
                    metrics={},
                    gate_result={
                        "gate_all": False,
                        "gate_flags": {},
                        "fail_reasons": ["candidate run not found"],
                        "pending_metrics": [],
                    },
                    note=row_note,
                )
            )
            continue

        trade_kpis = load_trade_kpis(run_dir)
        boot_kpis = load_boot_ci(run_dir)
        cost_kpis = load_cost_stress(posthoc_csv, run_id)
        temporal_kpis = load_temporal_flags(temporal_summary_json, run_id)
        merged = merge_metric_payload(
            trade_kpis=trade_kpis,
            boot_kpis=boot_kpis,
            cost_kpis=cost_kpis,
            temporal_kpis=temporal_kpis,
            baseline_trades=baseline_trades,
        )

        if trade_kpis.get("trade_status") != "ok":
            status = "failed"
            if row_note:
                row_note = f"{row_note}; trade_status={trade_kpis.get('trade_status')}"
            else:
                row_note = f"trade_status={trade_kpis.get('trade_status')}"

        gate_result = apply_gates(
            metrics=merged,
            stage_cfg=stage_cfg,
            baseline_trades=baseline_trades,
            stage_name=stage,
        )
        if status != "ok":
            gate_result["gate_all"] = False
            gate_result["fail_reasons"] = list(gate_result.get("fail_reasons", [])) + [f"status={status}"]
        rows.append(
            build_score_row(
                candidate=cfg.stem,
                config_path=cfg,
                run_id=run_id,
                status=status,
                is_baseline=False,
                metrics=merged,
                gate_result=gate_result,
                note=row_note,
            )
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = _order_scoreboard(df)

    out_csv = out_dir / "edge_factory_scoreboard.csv"
    out_md = out_dir / "edge_factory_scoreboard.md"
    out_summary = out_dir / "edge_factory_scoreboard_summary.json"
    df.to_csv(out_csv, index=False)

    candidates_df = df[df["is_baseline"] != True].copy() if not df.empty else pd.DataFrame()  # noqa: E712
    pass_count = int((candidates_df["gate_all"] == True).sum()) if not candidates_df.empty else 0  # noqa: E712
    run_ids_ok = (
        candidates_df.loc[candidates_df["status"] == "ok", "run_id"].astype(str).tolist()
        if not candidates_df.empty
        else []
    )

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reconstructed": True,
        "stage": stage,
        "data": data_path.as_posix(),
        "baseline_config": baseline_config.as_posix() if baseline_config is not None else "",
        "baseline_run_id": baseline_run_id,
        "baseline_trades": int(baseline_trades),
        "candidates_dir": candidates_dir.as_posix(),
        "rows_written": int(len(df)),
        "candidate_rows": int(len(candidates_df)) if not candidates_df.empty else 0,
        "pass_count": pass_count,
        "run_ids_ok": run_ids_ok,
        "posthoc_csv": posthoc_csv.as_posix() if posthoc_csv is not None else "",
        "temporal_summary_json": temporal_summary_json.as_posix() if temporal_summary_json is not None else "",
        "progress_jsonl": progress_jsonl.as_posix() if progress_jsonl is not None else "",
        "manifest_path": manifest_path.as_posix() if manifest_path is not None else "",
        "batch_start_run_id": batch_start_run_id,
        "notes": [x for x in [note] if x],
        "scoreboard_csv": out_csv.as_posix(),
    }
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# Edge Factory Scoreboard")
    md_lines.append("")
    md_lines.append(f"- stage: `{stage}`")
    md_lines.append(f"- data: `{data_path.as_posix()}`")
    md_lines.append(f"- baseline_run_id: `{baseline_run_id}`")
    md_lines.append(f"- baseline_trades: `{baseline_trades}`")
    md_lines.append(f"- pass_count(gate_all): `{pass_count}`")
    md_lines.append("")
    if baseline_row is not None:
        md_lines.append("## Baseline")
        md_lines.append("")
        baseline_md = df[df["is_baseline"] == True][["candidate", "run_id", "status", "trades", "pf", "expectancy_R", "note"]]  # noqa: E712
        md_lines.append(_md_table(baseline_md, float_cols={"pf", "expectancy_R"}))
        md_lines.append("")

    md_lines.append("## Candidates")
    md_lines.append("")
    if candidates_df.empty:
        md_lines.append("_No candidates_")
    else:
        md_lines.append(
            _md_table(
                candidates_df[
                    [
                        "candidate",
                        "run_id",
                        "status",
                        "trades",
                        "pf",
                        "expectancy_R",
                        "ci_low",
                        "ci_high",
                        "crosses_zero",
                        "retention_vs_b4_pct",
                        "gate_all",
                        "fail_reasons",
                        "pending_metrics",
                        "note",
                    ]
                ],
                float_cols={"pf", "expectancy_R", "ci_low", "ci_high", "retention_vs_b4_pct"},
            )
        )
    md_lines.append("")
    md_lines.append("## Artifacts")
    md_lines.append("")
    md_lines.append(f"- scoreboard_csv: `{out_csv.as_posix()}`")
    md_lines.append(f"- summary_json: `{out_summary.as_posix()}`")
    if posthoc_csv is not None:
        md_lines.append(f"- posthoc_csv: `{posthoc_csv.as_posix()}`")
    if temporal_summary_json is not None:
        md_lines.append(f"- temporal_summary_json: `{temporal_summary_json.as_posix()}`")
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {
        "df": df,
        "summary": summary,
        "scoreboard_csv": out_csv,
        "scoreboard_md": out_md,
        "scoreboard_summary_json": out_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Edge Factory scoreboard from progress/run_meta artifacts.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--candidates-dir", required=True)
    parser.add_argument("--baseline-config", default="")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--out-dir", default="outputs/edge_factory_batch")
    parser.add_argument("--gates-config", default="configs/research_gates/default_edge_factory.yaml")
    parser.add_argument("--stage", default="dev_fast")
    parser.add_argument("--progress-jsonl", default="")
    parser.add_argument("--posthoc-csv", default="")
    parser.add_argument("--temporal-summary-json", default="")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--batch-start-run-id", default="")
    parser.add_argument("--note", default="reconstructed from progress/run_meta")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    candidates_dir = _resolve(args.candidates_dir)
    runs_root = _resolve(args.runs_root)
    out_dir = _resolve(args.out_dir)
    gates_config = _resolve(args.gates_config)
    baseline_cfg = _resolve(args.baseline_config) if str(args.baseline_config).strip() else None
    progress_jsonl = _resolve(args.progress_jsonl) if str(args.progress_jsonl).strip() else (out_dir / "edge_factory_progress.jsonl")
    posthoc_csv = _resolve(args.posthoc_csv) if str(args.posthoc_csv).strip() else (out_dir / "edge_factory_posthoc.csv")
    temporal_summary_json = (
        _resolve(args.temporal_summary_json)
        if str(args.temporal_summary_json).strip()
        else (out_dir / "edge_discovery_temporal_summary.json")
    )
    manifest = _resolve(args.manifest) if str(args.manifest).strip() else (out_dir / "edge_factory_manifest.json")

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data path: {data_path.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if baseline_cfg is not None and (not baseline_cfg.exists()):
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")
    if not runs_root.exists():
        raise FileNotFoundError(f"Missing runs root: {runs_root.as_posix()}")

    built = build_edge_factory_scoreboard(
        data_path=data_path,
        candidates_dir=candidates_dir,
        baseline_config=baseline_cfg,
        runs_root=runs_root,
        out_dir=out_dir,
        gates_config_path=gates_config,
        stage=str(args.stage),
        progress_jsonl=progress_jsonl if progress_jsonl.exists() else None,
        posthoc_csv=posthoc_csv if posthoc_csv.exists() else None,
        temporal_summary_json=temporal_summary_json if temporal_summary_json.exists() else None,
        note=str(args.note),
        manifest_path=manifest if manifest.exists() else None,
        batch_start_run_id=str(args.batch_start_run_id),
    )
    print(f"Wrote: {built['scoreboard_csv'].as_posix()}")
    print(f"Wrote: {built['scoreboard_md'].as_posix()}")
    print(f"Wrote: {built['scoreboard_summary_json'].as_posix()}")
    print(f"pass_count: {built['summary']['pass_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

