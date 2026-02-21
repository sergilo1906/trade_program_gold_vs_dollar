from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _append(log: list[str], title: str, cp: subprocess.CompletedProcess[str]) -> None:
    log.append(f"[{title}] rc={cp.returncode}")
    if cp.stdout.strip():
        log.append("stdout:")
        log.append(cp.stdout.strip())
    if cp.stderr.strip():
        log.append("stderr:")
        log.append(cp.stderr.strip())
    log.append("")


def _cmd_str(cmd: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command overnight edge discovery run.")
    parser.add_argument("--data", default="data_local/xauusd_m5_DEV_2021_2023.csv")
    parser.add_argument("--candidates-dir", default="configs/edge_discovery_candidates")
    parser.add_argument("--baseline-config", default="configs/config_v3_PIVOT_B4.yaml")
    parser.add_argument("--out-dir", default="outputs/edge_discovery_overnight")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-bars", type=int, default=0)
    parser.add_argument("--snapshot-root", default="docs/_snapshots")
    parser.add_argument("--snapshot-prefix", default="edge_discovery_overnight")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_lines: list[str] = [f"generated_utc={datetime.now(timezone.utc).isoformat()}"]
    notes: list[str] = []

    run_queue_cmd = [
        sys.executable,
        "scripts/run_vtm_candidates.py",
        "--data",
        args.data,
        "--candidates-dir",
        args.candidates_dir,
        "--out-dir",
        args.out_dir,
        "--runs-root",
        args.runs_root,
        "--baseline-config",
        args.baseline_config,
        "--resamples",
        str(int(args.resamples)),
        "--seed",
        str(int(args.seed)),
        "--max-bars",
        str(int(args.max_bars)),
        "--snapshot-root",
        args.snapshot_root,
        "--snapshot-prefix",
        args.snapshot_prefix,
    ]
    log_lines.append("CMD_QUEUE=" + _cmd_str(run_queue_cmd))
    cp_queue = _run(run_queue_cmd)
    _append(log_lines, "run_vtm_candidates", cp_queue)

    scoreboard_csv = out_dir / "vtm_candidates_scoreboard.csv"
    summary_json = out_dir / "vtm_candidates_scoreboard_summary.json"
    if (cp_queue.returncode != 0) or (not summary_json.exists()) or (not scoreboard_csv.exists()):
        notes.append("queue step failed or missing artifacts; orchestration stopped before posthoc/temporal")
        payload = {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "failed_queue",
            "notes": notes,
            "artifacts": {
                "scoreboard_csv": scoreboard_csv.as_posix(),
                "summary_json": summary_json.as_posix(),
            },
        }
        out_status = out_dir / "edge_discovery_orchestration_summary.json"
        out_status.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out_dir / "edge_discovery_orchestration.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        print(f"Wrote: {out_status.as_posix()}")
        print(f"Wrote: {(out_dir / 'edge_discovery_orchestration.log').as_posix()}")
        return 1

    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    run_ids = []
    base_run = str(summary.get("baseline_run_id", "")).strip()
    if base_run:
        run_ids.append(base_run)
    run_ids.extend([str(x).strip() for x in summary.get("run_ids_ok", []) if str(x).strip()])
    # dedupe keep order
    dedup: list[str] = []
    seen: set[str] = set()
    for rid in run_ids:
        if rid not in seen:
            seen.add(rid)
            dedup.append(rid)
    run_ids = dedup

    posthoc_csv = Path("outputs/posthoc_cost_stress/edge_discovery_overnight_posthoc.csv")
    posthoc_summary = Path("outputs/posthoc_cost_stress/edge_discovery_overnight_posthoc_summary.json")
    posthoc_per_trade = Path("outputs/posthoc_cost_stress/edge_discovery_overnight_per_trade")
    posthoc_cmd = [
        sys.executable,
        "scripts/posthoc_cost_stress_batch.py",
        "--runs",
        *run_ids,
        "--runs-root",
        args.runs_root,
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
    log_lines.append("CMD_POSTHOC=" + _cmd_str(posthoc_cmd))
    cp_posthoc = _run(posthoc_cmd)
    _append(log_lines, "posthoc_cost_stress_batch", cp_posthoc)
    if cp_posthoc.returncode != 0:
        notes.append("posthoc batch failed")

    temporal_cmd = [
        sys.executable,
        "scripts/edge_temporal_review.py",
        "--scoreboard",
        scoreboard_csv.as_posix(),
        "--runs-root",
        args.runs_root,
        "--out-dir",
        args.out_dir,
        "--segments",
        "4",
    ]
    log_lines.append("CMD_TEMPORAL=" + _cmd_str(temporal_cmd))
    cp_temporal = _run(temporal_cmd)
    _append(log_lines, "edge_temporal_review", cp_temporal)
    if cp_temporal.returncode != 0:
        notes.append("temporal review failed")

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if (cp_queue.returncode == 0 and cp_posthoc.returncode == 0 and cp_temporal.returncode == 0) else "partial",
        "resamples": int(args.resamples),
        "seed": int(args.seed),
        "run_ids": run_ids,
        "notes": notes,
        "artifacts": {
            "scoreboard_csv": scoreboard_csv.as_posix(),
            "scoreboard_summary_json": summary_json.as_posix(),
            "posthoc_csv": posthoc_csv.as_posix(),
            "posthoc_summary_json": posthoc_summary.as_posix(),
            "temporal_segments_csv": (out_dir / "edge_discovery_temporal_segments.csv").as_posix(),
            "temporal_yearly_csv": (out_dir / "edge_discovery_yearly.csv").as_posix(),
            "temporal_hourly_csv": (out_dir / "edge_discovery_hourly.csv").as_posix(),
            "temporal_summary_json": (out_dir / "edge_discovery_temporal_summary.json").as_posix(),
        },
    }
    out_status = out_dir / "edge_discovery_orchestration_summary.json"
    out_log = out_dir / "edge_discovery_orchestration.log"
    out_status.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print(f"Wrote: {out_status.as_posix()}")
    print(f"Wrote: {out_log.as_posix()}")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
