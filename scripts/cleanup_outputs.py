from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


RUN_ID_RE = re.compile(r"\b\d{8}_\d{6}\b")


def _run_dirs(runs_root: Path) -> list[Path]:
    if not runs_root.exists():
        return []
    return sorted([p for p in runs_root.iterdir() if p.is_dir()], key=lambda p: p.name)


def _extract_run_ids_from_tree(root: Path) -> set[str]:
    if not root.exists():
        return set()
    out: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        out.update(RUN_ID_RE.findall(text))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune old run directories to control disk usage.")
    parser.add_argument("--runs-root", default="outputs/runs")
    parser.add_argument("--keep-last", type=int, default=40)
    parser.add_argument("--keep-run-ids", nargs="*", default=[])
    parser.add_argument(
        "--keep-referenced-in",
        default="",
        help="Directory tree to scan and keep run_ids referenced in text files (e.g., docs).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    keep_last = max(0, int(args.keep_last))
    keep_ids = {str(x).strip() for x in args.keep_run_ids if str(x).strip()}
    keep_ref_root = Path(args.keep_referenced_in) if str(args.keep_referenced_in).strip() else None
    keep_from_refs = _extract_run_ids_from_tree(keep_ref_root) if keep_ref_root is not None else set()
    keep_ids |= keep_from_refs

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
    if keep_ref_root is not None:
        print(f"keep_referenced_in: {keep_ref_root.as_posix()}")
        print(f"keep_from_references_count: {len(keep_from_refs)}")
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
