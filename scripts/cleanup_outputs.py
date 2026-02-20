from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _run_dirs(runs_root: Path) -> list[Path]:
    if not runs_root.exists():
        return []
    return sorted([p for p in runs_root.iterdir() if p.is_dir()], key=lambda p: p.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune old run directories to control disk usage.")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--keep-last", type=int, default=40)
    parser.add_argument("--keep-run-ids", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    keep_last = max(0, int(args.keep_last))
    keep_ids = {str(x).strip() for x in args.keep_run_ids if str(x).strip()}

    dirs = _run_dirs(runs_root)
    if not dirs:
        print(f"No runs found under: {runs_root.as_posix()}")
        return 0

    keep_by_age = {p.name for p in dirs[-keep_last:]} if keep_last > 0 else set()
    keep = keep_by_age | keep_ids
    drop = [p for p in dirs if p.name not in keep]

    print(f"runs_root: {runs_root.as_posix()}")
    print(f"total_runs: {len(dirs)}")
    print(f"keep_last: {keep_last}")
    print(f"keep_explicit: {sorted(keep_ids)}")
    print(f"to_delete: {len(drop)}")

    for p in drop:
        print(f"- {p.as_posix()}")

    if args.dry_run:
        print("Dry run only; nothing deleted.")
        return 0

    for p in drop:
        shutil.rmtree(p, ignore_errors=False)
    print(f"Deleted {len(drop)} run directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
