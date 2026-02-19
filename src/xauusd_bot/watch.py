from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Iterable, Sequence


RELEVANT_EVENT_TYPES = {
    "SIGNAL_DETECTED",
    "PENDING_SET",
    "PENDING_IGNORED",
    "PENDING_CLEARED",
    "TRADE_OPEN",
    "TRADE_CLOSE",
    "FILTER_BLOCKED",
}


def parse_line(line: str, headers: Sequence[str]) -> dict[str, str] | None:
    if not line.strip():
        return None
    values = next(csv.reader([line]))
    if len(values) > len(headers):
        head = values[: len(headers) - 1]
        tail = ",".join(values[len(headers) - 1 :])
        values = head + [tail]
    if len(values) < len(headers):
        values.extend([""] * (len(headers) - len(values)))
    return dict(zip(headers, values))


def filter_event(row: dict[str, str], allowed_event_types: Iterable[str] | None = None) -> bool:
    allowed = set(allowed_event_types or RELEVANT_EVENT_TYPES)
    return row.get("event_type", "") in allowed


def _short_payload(payload: str, limit: int = 140) -> str:
    compact = " ".join(payload.split())
    if not compact:
        return "-"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def format_line(row: dict[str, str]) -> str:
    payload = row.get("payload_json", "")
    payload_short = _short_payload(payload)
    return (
        f"{row.get('ts', '')} | {row.get('event_type', '')} | signal={row.get('signal', '-') or '-'} | "
        f"bias={row.get('bias', '-') or '-'} | m15={row.get('m15_confirmation', '-') or '-'} | "
        f"entry={row.get('entry_price_candidate', '-') or '-'} | outcome={row.get('outcome', '-') or '-'} | "
        f"pnl={row.get('pnl', '-') or '-'} | payload={payload_short}"
    )


def watch_signals(file_path: str | Path, tail: int = 30, once: bool = False, poll_interval: float = 1.0) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Signals file not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as handle:
        header_line = handle.readline()
        if not header_line:
            return 0
        headers = next(csv.reader([header_line]))

        matched_rows: list[dict[str, str]] = []
        for line in handle:
            row = parse_line(line, headers)
            if row is not None and filter_event(row):
                matched_rows.append(row)

        for row in matched_rows[-max(0, int(tail)) :]:
            print(format_line(row))

        if once:
            return 0

        while True:
            position = handle.tell()
            line = handle.readline()
            if not line:
                time.sleep(poll_interval)
                continue
            if not line.endswith("\n"):
                handle.seek(position)
                time.sleep(poll_interval)
                continue

            row = parse_line(line, headers)
            if row is not None and filter_event(row):
                print(format_line(row), flush=True)
