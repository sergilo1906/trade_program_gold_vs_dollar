from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_ablation_force_regime(config_path: Path) -> str:
    try:
        for raw in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            if key.strip() == "ablation_force_regime":
                clean = value.split("#", 1)[0].strip().strip("'\"")
                return clean or "NA"
    except Exception:
        return "NA"
    return "NA"


def _git_commit_or_na(workdir: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=True,
        )
        commit = proc.stdout.strip()
        return commit if commit else "NA"
    except Exception:
        return "NA"


def _list_run_dirs(runs_root: Path) -> list[Path]:
    if not runs_root.exists():
        return []
    return [p for p in runs_root.iterdir() if p.is_dir()]


def _select_created_run(before: list[Path], after: list[Path]) -> Path:
    before_set = {str(p.resolve()) for p in before}
    created = [p for p in after if str(p.resolve()) not in before_set]
    if created:
        return sorted(created, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    if after:
        return sorted(after, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    raise RuntimeError("No runs found in outputs/runs after execution.")


def _serialize_run_error(exc: BaseException | None) -> str:
    if exc is None:
        return ""
    if isinstance(exc, subprocess.CalledProcessError):
        return f"CalledProcessError(returncode={exc.returncode}, cmd={exc.cmd})"
    return f"{exc.__class__.__name__}: {exc}"


def _write_run_meta(
    *,
    run_dir: Path,
    run_id: str,
    data_path: Path,
    config_path: Path,
    postprocess_ok: bool,
    postprocess_error: str,
    process_returncode: int,
) -> Path:
    run_meta: dict[str, Any] = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "data_path": str(data_path),
        "config_path": str(config_path),
        "config_hash": _sha256_file(config_path),
        "ablation_force_regime": _read_ablation_force_regime(config_path),
        "git_commit": _git_commit_or_na(Path.cwd()),
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "postprocess_ok": bool(postprocess_ok),
        "process_returncode": int(process_returncode),
    }
    if not postprocess_ok:
        run_meta["postprocess_error"] = postprocess_error

    run_meta_path = run_dir / "run_meta.json"
    run_meta_path.write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    return run_meta_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backtest and persist run metadata/artifacts.")
    parser.add_argument("--data", required=True, help="Path to input OHLC data CSV.")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    parser.add_argument("--runs-root", default="outputs/runs", help="Runs root directory.")
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    config_path = Path(args.config).resolve()
    runs_root = Path(args.runs_root).resolve()

    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    runs_root.mkdir(parents=True, exist_ok=True)
    before = _list_run_dirs(runs_root)

    cmd = [
        sys.executable,
        "-m",
        "xauusd_bot",
        "run",
        "--data",
        str(data_path),
        "--config",
        str(config_path),
    ]
    print("Executing:", " ".join(cmd))
    run_error: BaseException | None = None
    process_returncode = 0
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        run_error = exc
        process_returncode = int(exc.returncode)
    except Exception as exc:
        run_error = exc
        process_returncode = 1

    after = _list_run_dirs(runs_root)
    try:
        run_dir = _select_created_run(before, after)
    except Exception:
        fallback_run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = runs_root / fallback_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_dir.name

    run_meta_path = _write_run_meta(
        run_dir=run_dir,
        run_id=run_id,
        data_path=data_path,
        config_path=config_path,
        postprocess_ok=(run_error is None),
        postprocess_error=_serialize_run_error(run_error),
        process_returncode=process_returncode,
    )

    config_used_path = run_dir / "config_used.yaml"
    shutil.copyfile(config_path, config_used_path)

    print(f"run_id: {run_id}")
    print(f"run_dir: {run_dir}")
    print(f"run_meta: {run_meta_path}")
    print(f"config_used: {config_used_path}")
    if run_error is not None:
        print(f"WARN: run failed but metadata was written. error={_serialize_run_error(run_error)}")
        return process_returncode if process_returncode != 0 else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
