from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "git command failed")
    return res.stdout.strip()


def _safe_git(cmd: list[str], default: str) -> str:
    try:
        out = _git(cmd)
        return out if out else default
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser(description="Update docs/LATEST_COMMIT.md")
    parser.add_argument("--repo-url", default=None)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", default=None)
    parser.add_argument("--out", default="docs/LATEST_COMMIT.md")
    args = parser.parse_args()

    repo_url = args.repo_url or _safe_git(["git", "remote", "get-url", "origin"], "NO_REMOTE_CONFIGURED")
    commit = args.commit or _safe_git(["git", "rev-parse", "--short", "HEAD"], "NO_COMMIT")
    date_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# Latest Commit\n\n"
        f"- repo_url: `{repo_url}`\n"
        f"- branch: `{args.branch}`\n"
        f"- last_commit: `{commit}`\n"
        f"- date: `{date_utc}`\n"
    )
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
