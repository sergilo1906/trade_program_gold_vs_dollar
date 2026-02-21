from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from build_edge_factory_scoreboard_from_runs import build_edge_factory_scoreboard
except ModuleNotFoundError:
    from scripts.build_edge_factory_scoreboard_from_runs import build_edge_factory_scoreboard


ROOT = Path(__file__).resolve().parents[1]


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


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


def _short(text: str, limit: int = 800) -> str:
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _extract_run_id(output: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", output)
    if not m:
        return ""
    return m.group(1)


def _append_progress(progress_path: Path, payload: dict[str, Any]) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _materialize_input(data_path: Path, max_bars: int, stamp: str) -> Path:
    if max_bars <= 0:
        return data_path
    df = pd.read_csv(data_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "timestamp" not in df.columns and len(df.columns) >= 5:
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
    tmp_dir = ROOT / "data" / "tmp_edge_factory"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out = tmp_dir / f"edge_factory_input_{stamp}.csv"
    df.to_csv(out, index=False)
    return out


def _execute_candidate(
    *,
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
        "note": "",
        "boot_resamples_used": int(resamples),
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
        fallback = _run_cmd(fallback_cmd)
        log_lines.append(f"{cfg_path.stem}: bootstrap rc={boot_res.returncode} fallback_rc={fallback.returncode}")
        if fallback.returncode != 0:
            row["status"] = "failed"
            row["note"] = _short(fallback.stderr or fallback.stdout)
            return row
        row["boot_resamples_used"] = 2000
        row["note"] = "bootstrap fallback to 2000 resamples"
    else:
        log_lines.append(f"{cfg_path.stem}: bootstrap rc=0 resamples={resamples}")

    return row


def _read_manifest_used_data(manifest_path: Path) -> Path | None:
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    used = str(payload.get("used_data_path", "")).strip()
    if not used:
        return None
    p = _resolve(used)
    return p if p.exists() else None


def _collect_run_ids_from_progress(progress_path: Path, data_path: Path) -> list[str]:
    if not progress_path.exists():
        return []
    out: list[str] = []
    seen: set[str] = set()
    data_key = str(data_path).replace("\\", "/").lower()
    for raw in progress_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if str(rec.get("data_path", "")).replace("\\", "/").lower() != data_key:
            continue
        if str(rec.get("status", "")).lower() != "ok":
            continue
        rid = str(rec.get("run_id", "")).strip()
        if rid and (rid not in seen):
            seen.add(rid)
            out.append(rid)
    return out


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic Edge Factory batch runner with gates, rebuild and snapshots.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--candidates-dir", required=True)
    parser.add_argument("--baseline-config", default="")
    parser.add_argument("--out-dir", default="outputs/edge_factory_batch")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-bars", type=int, default=0)
    parser.add_argument("--gates-config", default="configs/research_gates/default_edge_factory.yaml")
    parser.add_argument("--stage", choices=["smoke", "dev_fast", "dev_robust"], default="dev_fast")
    parser.add_argument("--snapshot-root", default="docs/_snapshots")
    parser.add_argument("--snapshot-prefix", default="edge_factory_batch")
    parser.add_argument("--rebuild-only", action="store_true")
    parser.add_argument("--with-posthoc", dest="with_posthoc", action="store_true")
    parser.add_argument("--no-posthoc", dest="with_posthoc", action="store_false")
    parser.set_defaults(with_posthoc=None)
    parser.add_argument("--with-temporal", dest="with_temporal", action="store_true")
    parser.add_argument("--no-temporal", dest="with_temporal", action="store_false")
    parser.set_defaults(with_temporal=None)
    args = parser.parse_args()

    stage = str(args.stage)
    with_posthoc = bool(args.with_posthoc) if args.with_posthoc is not None else bool(stage == "dev_robust")
    with_temporal = bool(args.with_temporal) if args.with_temporal is not None else bool(stage == "dev_robust")

    data_path = _resolve(args.data)
    candidates_dir = _resolve(args.candidates_dir)
    baseline_cfg = _resolve(args.baseline_config) if str(args.baseline_config).strip() else None
    out_dir = _resolve(args.out_dir)
    runs_root = _resolve(args.runs_root)
    gates_cfg = _resolve(args.gates_config)
    snapshot_root = _resolve(args.snapshot_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.as_posix()}")
    if not candidates_dir.exists():
        raise FileNotFoundError(f"Missing candidates dir: {candidates_dir.as_posix()}")
    if baseline_cfg is not None and (not baseline_cfg.exists()):
        raise FileNotFoundError(f"Missing baseline config: {baseline_cfg.as_posix()}")
    if not gates_cfg.exists():
        raise FileNotFoundError(f"Missing gates config: {gates_cfg.as_posix()}")

    candidates = sorted([p.resolve() for p in candidates_dir.glob("*.yaml") if p.is_file()])
    if not candidates:
        raise RuntimeError(f"No YAML candidates found in {candidates_dir.as_posix()}")

    stamp = _now_utc_compact()
    manifest_path = out_dir / "edge_factory_manifest.json"
    progress_path = out_dir / "edge_factory_progress.jsonl"
    run_log_path = out_dir / "edge_factory_run.log"
    batch_start_run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if args.rebuild_only:
        used_data = _read_manifest_used_data(manifest_path) or data_path
        run_log_lines: list[str] = [
            f"generated_utc={datetime.now(timezone.utc).isoformat()}",
            "mode=rebuild_only",
            f"data={used_data.as_posix()}",
        ]
    else:
        used_data = _materialize_input(data_path=data_path, max_bars=int(args.max_bars), stamp=stamp)
        run_log_lines = [
            f"generated_utc={datetime.now(timezone.utc).isoformat()}",
            "mode=run",
            f"data={used_data.as_posix()}",
        ]

    manifest_payload: dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "running" if not args.rebuild_only else "rebuilding",
        "stage": stage,
        "rebuild_only": bool(args.rebuild_only),
        "data_source_path": data_path.as_posix(),
        "used_data_path": used_data.as_posix(),
        "candidates_dir": candidates_dir.as_posix(),
        "baseline_config": baseline_cfg.as_posix() if baseline_cfg is not None else "",
        "gates_config": gates_cfg.as_posix(),
        "runs_root": runs_root.as_posix(),
        "out_dir": out_dir.as_posix(),
        "resamples": int(args.resamples),
        "seed": int(args.seed),
        "max_bars": int(args.max_bars),
        "with_posthoc": bool(with_posthoc),
        "with_temporal": bool(with_temporal),
        "batch_start_run_id": batch_start_run_id,
        "progress_jsonl": progress_path.as_posix(),
        "candidate_configs": [p.as_posix() for p in candidates],
        "notes": [],
    }
    _write_json(manifest_path, manifest_payload)

    executed_rows: list[dict[str, Any]] = []
    if not args.rebuild_only:
        if baseline_cfg is not None:
            baseline_row = _execute_candidate(
                cfg_path=baseline_cfg,
                data_path=used_data,
                runs_root=runs_root,
                resamples=int(args.resamples),
                seed=int(args.seed),
                log_lines=run_log_lines,
            )
            baseline_row["candidate"] = "__baseline__"
            executed_rows.append(baseline_row)
            _append_progress(
                progress_path,
                {
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    "stage": stage,
                    "candidate": "__baseline__",
                    "config": baseline_cfg.as_posix(),
                    "data_path": used_data.as_posix(),
                    "run_id": baseline_row.get("run_id", ""),
                    "status": baseline_row.get("status", "failed"),
                    "note": baseline_row.get("note", ""),
                },
            )
        for cfg in candidates:
            row = _execute_candidate(
                cfg_path=cfg,
                data_path=used_data,
                runs_root=runs_root,
                resamples=int(args.resamples),
                seed=int(args.seed),
                log_lines=run_log_lines,
            )
            executed_rows.append(row)
            _append_progress(
                progress_path,
                {
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    "stage": stage,
                    "candidate": cfg.stem,
                    "config": cfg.as_posix(),
                    "data_path": used_data.as_posix(),
                    "run_id": row.get("run_id", ""),
                    "status": row.get("status", "failed"),
                    "note": row.get("note", ""),
                },
            )
    else:
        run_log_lines.append("skip run/diagnose/bootstrap; rebuilding from existing artifacts")

    run_ids_ok = _collect_run_ids_from_progress(progress_path=progress_path, data_path=used_data)
    posthoc_csv: Path | None = None
    posthoc_summary: Path | None = None
    temporal_summary: Path | None = None

    if with_posthoc and run_ids_ok:
        posthoc_csv = out_dir / "edge_factory_posthoc.csv"
        posthoc_summary = out_dir / "edge_factory_posthoc_summary.json"
        posthoc_per_trade = out_dir / "edge_factory_posthoc_per_trade"
        posthoc_cmd = [
            sys.executable,
            "scripts/posthoc_cost_stress_batch.py",
            "--runs",
            *run_ids_ok,
            "--runs-root",
            runs_root.as_posix(),
            "--factors",
            "1.2",
            "1.5",
            "--seed",
            str(int(args.seed)),
            "--resamples",
            str(int(args.resamples)),
            "--out",
            posthoc_csv.as_posix(),
            "--summary-json",
            posthoc_summary.as_posix(),
            "--per-trade-dir",
            posthoc_per_trade.as_posix(),
        ]
        run_log_lines.append("CMD_POSTHOC=" + " ".join(posthoc_cmd))
        posthoc_res = _run_cmd(posthoc_cmd)
        run_log_lines.append(f"posthoc rc={posthoc_res.returncode}")
        if posthoc_res.returncode != 0:
            manifest_payload["notes"].append("posthoc failed")
            posthoc_csv = None
            posthoc_summary = None
    elif with_posthoc and (not run_ids_ok):
        manifest_payload["notes"].append("posthoc skipped: no successful run_ids")

    if with_temporal and run_ids_ok:
        temporal_input = out_dir / "edge_factory_runs_input.csv"
        pd.DataFrame([{"run_id": rid, "status": "ok"} for rid in run_ids_ok]).to_csv(temporal_input, index=False)
        temporal_cmd = [
            sys.executable,
            "scripts/edge_temporal_review.py",
            "--scoreboard",
            temporal_input.as_posix(),
            "--runs-root",
            runs_root.as_posix(),
            "--out-dir",
            out_dir.as_posix(),
            "--segments",
            "4",
        ]
        run_log_lines.append("CMD_TEMPORAL=" + " ".join(temporal_cmd))
        temporal_res = _run_cmd(temporal_cmd)
        run_log_lines.append(f"temporal rc={temporal_res.returncode}")
        if temporal_res.returncode == 0:
            temporal_summary = out_dir / "edge_discovery_temporal_summary.json"
        else:
            manifest_payload["notes"].append("temporal review failed")
            temporal_summary = None
    elif with_temporal and (not run_ids_ok):
        manifest_payload["notes"].append("temporal skipped: no successful run_ids")

    build_note = "rebuild-only from existing artifacts" if args.rebuild_only else "built from current batch artifacts"
    built = build_edge_factory_scoreboard(
        data_path=used_data,
        candidates_dir=candidates_dir,
        baseline_config=baseline_cfg,
        runs_root=runs_root,
        out_dir=out_dir,
        gates_config_path=gates_cfg,
        stage=stage,
        progress_jsonl=progress_path if progress_path.exists() else None,
        posthoc_csv=posthoc_csv,
        temporal_summary_json=temporal_summary,
        note=build_note,
        manifest_path=manifest_path,
        batch_start_run_id=batch_start_run_id,
    )

    run_log_path.write_text("\n".join(run_log_lines) + "\n", encoding="utf-8")

    snapshot_dir = snapshot_root / f"{args.snapshot_prefix}_{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for src in [
        built["scoreboard_csv"],
        built["scoreboard_md"],
        built["scoreboard_summary_json"],
        run_log_path,
        manifest_path,
        progress_path,
    ]:
        if Path(src).exists():
            shutil.copy2(src, snapshot_dir / Path(src).name)
    optional_artifacts = [
        posthoc_csv,
        posthoc_summary,
        out_dir / "edge_discovery_temporal_segments.csv",
        out_dir / "edge_discovery_yearly.csv",
        out_dir / "edge_discovery_hourly.csv",
        temporal_summary,
    ]
    for p in optional_artifacts:
        if p is not None and Path(p).exists():
            shutil.copy2(p, snapshot_dir / Path(p).name)

    command_used = "python scripts/run_edge_factory_batch.py " + " ".join(sys.argv[1:])
    meta = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "command": command_used,
        "stage": stage,
        "rebuild_only": bool(args.rebuild_only),
        "data_source_path": data_path.as_posix(),
        "used_data_path": used_data.as_posix(),
        "baseline_config": baseline_cfg.as_posix() if baseline_cfg is not None else "",
        "candidates_dir": candidates_dir.as_posix(),
        "resamples": int(args.resamples),
        "seed": int(args.seed),
        "max_bars": int(args.max_bars),
        "with_posthoc": bool(with_posthoc),
        "with_temporal": bool(with_temporal),
        "run_ids_ok": run_ids_ok,
        "scoreboard_csv": built["scoreboard_csv"].as_posix(),
        "scoreboard_summary_json": built["scoreboard_summary_json"].as_posix(),
        "snapshot_dir": snapshot_dir.as_posix(),
    }
    _write_json(snapshot_dir / "meta.json", meta)

    manifest_payload.update(
        {
            "status": "ok",
            "completed_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "run_ids_ok": run_ids_ok,
            "artifacts": {
                "scoreboard_csv": built["scoreboard_csv"].as_posix(),
                "scoreboard_md": built["scoreboard_md"].as_posix(),
                "scoreboard_summary_json": built["scoreboard_summary_json"].as_posix(),
                "snapshot_dir": snapshot_dir.as_posix(),
                "posthoc_csv": posthoc_csv.as_posix() if posthoc_csv is not None else "",
                "temporal_summary_json": temporal_summary.as_posix() if temporal_summary is not None else "",
            },
        }
    )
    _write_json(manifest_path, manifest_payload)

    print(f"Wrote: {built['scoreboard_csv'].as_posix()}")
    print(f"Wrote: {built['scoreboard_md'].as_posix()}")
    print(f"Wrote: {built['scoreboard_summary_json'].as_posix()}")
    print(f"Wrote: {run_log_path.as_posix()}")
    print(f"Snapshot: {snapshot_dir.as_posix()}")
    print(f"pass_count: {built['summary']['pass_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

