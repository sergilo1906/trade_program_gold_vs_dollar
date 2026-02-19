from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "docs" / "UNATTENDED_LOG.md"


def _fmt_ts(v: object) -> str:
    ts = pd.to_datetime(v, errors="coerce")
    if pd.isna(ts):
        return "NA"
    return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _section_for_csv(path: Path, title: str) -> list[str]:
    lines: list[str] = [f"### {title}", ""]
    lines.append(f"- file: `{path.relative_to(ROOT).as_posix()}`")
    if not path.exists():
        lines.append("- status: MISSING")
        lines.append("")
        return lines

    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        min_ts = _fmt_ts(ts.min())
        max_ts = _fmt_ts(ts.max())
    else:
        min_ts = "NA"
        max_ts = "NA"
    lines.append(f"- rows: {len(df)}")
    lines.append(f"- min_timestamp: {min_ts}")
    lines.append(f"- max_timestamp: {max_ts}")
    lines.append("")
    lines.append("First 3 rows:")
    lines.append("")
    lines.append("```")
    lines.append(df.head(3).to_string(index=False))
    lines.append("```")
    lines.append("")
    lines.append("Last 3 rows:")
    lines.append("")
    lines.append("```")
    lines.append(df.tail(3).to_string(index=False))
    lines.append("```")
    lines.append("")
    return lines


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    lines: list[str] = []
    lines.append("")
    lines.append("## Phase 1 - HOLDOUT Split")
    lines.append("")
    lines.append(f"- logged_at_utc: {stamp}")
    lines.append("- command: `python scripts/make_holdout_split.py`")
    lines.append("")

    lines.extend(
        _section_for_csv(ROOT / "data" / "xauusd_m5_backtest_ready.csv", "Validation FULL")
    )
    lines.extend(_section_for_csv(ROOT / "data" / "xauusd_m5_DEV80.csv", "Validation DEV80"))
    lines.extend(_section_for_csv(ROOT / "data" / "xauusd_m5_HOLDOUT20.csv", "Validation HOLDOUT20"))

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Appended: {LOG_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
