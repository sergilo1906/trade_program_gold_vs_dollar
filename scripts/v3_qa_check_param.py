from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


REQUIRED_DIAG = [
    "A_perf_by_mode.csv",
    "B_perf_by_session_bucket.csv",
    "C_perf_by_hour_utc.csv",
    "D_costR_percentiles.csv",
    "E_blocks.csv",
    "F_blocks_by_hour_utc.csv",
    "G_signals_by_hour_utc.csv",
    "H_perf_by_hour_robust.csv",
    "I_perf_by_regime_at_entry.csv",
    "J_signals_state_counts.csv",
    "K_regime_event_counts.csv",
    "L_regime_segments.csv",
    "M_regime_time_share.csv",
    "N_signals_by_regime.csv",
    "diagnostics.md",
]


def _hhmm_to_min(value: str) -> int:
    hh, mm = value.split(":")
    return int(hh) * 60 + int(mm)


def _parse_windows(windows: Iterable[str]) -> list[tuple[int, int, str]]:
    parsed: list[tuple[int, int, str]] = []
    for raw in windows:
        start_raw, end_raw = str(raw).split("-", 1)
        start = _hhmm_to_min(start_raw)
        end = _hhmm_to_min(end_raw)
        parsed.append((start, end, str(raw)))
    return parsed


def _in_window(minute: int, start: int, end: int) -> bool:
    if start < end:
        return start <= minute < end
    return (minute >= start) or (minute < end)


def _session_label(ts: pd.Timestamp, windows: list[tuple[int, int, str]]) -> str:
    minute = int(ts.hour) * 60 + int(ts.minute)
    for start, end, raw in windows:
        if _in_window(minute, start, end):
            return raw
    return "NO_WINDOW"


def _normalize_ts(value: str | pd.Timestamp) -> str | None:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).isoformat()


def _extract_signal_targets(events: pd.DataFrame) -> set[str]:
    targets: set[str] = set()
    mask = events["event_type"].astype(str).str.startswith("V3_SIGNAL_")
    for details_raw in events.loc[mask, "details_json"]:
        if not isinstance(details_raw, str):
            continue
        try:
            details = json.loads(details_raw)
        except Exception:
            continue
        target = details.get("entry_ts_t1")
        normalized = _normalize_ts(target) if isinstance(target, str) else None
        if normalized:
            targets.add(normalized)
    return targets


def _infer_mode(row: pd.Series) -> str:
    mode = str(row.get("mode", "")).upper()
    if mode in {"TREND", "RANGE"}:
        return mode
    regime = str(row.get("regime_at_entry", "")).upper()
    if regime in {"TREND", "RANGE"}:
        return regime
    return "TREND"


def _max_trades_per_session(
    trades: pd.DataFrame,
    trend_windows: list[tuple[int, int, str]],
    range_windows: list[tuple[int, int, str]],
) -> int:
    if trades.empty or "entry_time" not in trades.columns:
        return 0
    local = trades.copy()
    local["entry_time"] = pd.to_datetime(local["entry_time"], errors="coerce", utc=True)
    local = local.dropna(subset=["entry_time"])
    if local.empty:
        return 0

    session_keys: list[str] = []
    for _, row in local.iterrows():
        ts = row["entry_time"]
        mode = _infer_mode(row)
        windows = trend_windows if mode == "TREND" else range_windows
        label = _session_label(ts, windows)
        session_keys.append(f"{ts.date().isoformat()}|{mode}|{label}")

    if not session_keys:
        return 0
    return int(pd.Series(session_keys).value_counts().max())


def check_run(run_id: str) -> dict[str, object]:
    run_dir = Path("outputs/runs") / run_id
    diag_dir = run_dir / "diagnostics"
    result: dict[str, object] = {"run_id": run_id}

    missing_diag = [name for name in REQUIRED_DIAG if not (diag_dir / name).exists()]
    result["diag_ok"] = not missing_diag
    result["missing_diag"] = ",".join(missing_diag)

    events_path = run_dir / "events.csv"
    trades_path = run_dir / "trades.csv"
    cfg_path = run_dir / "config_used.yaml"
    if not events_path.exists() or not trades_path.exists() or not cfg_path.exists():
        result.update(
            {
                "v3_events_ok": False,
                "next_open_ok": False,
                "session_limit_ok": False,
                "matched_entries": 0,
                "total_entries": 0,
                "max_trades_seen": 0,
                "max_trades_allowed": 0,
                "event_types_v3": "",
                "overall_ok": False,
            }
        )
        return result

    events = pd.read_csv(events_path)
    trades = pd.read_csv(trades_path)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    v3_events = events[events["event_type"].astype(str).str.startswith("V3_")]
    v3_types = v3_events["event_type"].astype(str).value_counts().to_dict()
    has_signal = any(t.startswith("V3_SIGNAL_") for t in v3_types)
    has_entry = "V3_ENTRY" in v3_types
    has_exit = any(t.startswith("V3_EXIT_") for t in v3_types)
    v3_events_ok = has_signal and has_entry and has_exit

    signal_targets = _extract_signal_targets(events)
    entry_rows = events.loc[events["event_type"] == "V3_ENTRY"].copy()
    entry_rows["timestamp"] = pd.to_datetime(entry_rows["timestamp"], errors="coerce", utc=True)
    total_entries = int(entry_rows["timestamp"].notna().sum())
    matched_entries = 0
    for ts in entry_rows["timestamp"].dropna():
        if pd.Timestamp(ts).isoformat() in signal_targets:
            matched_entries += 1
    next_open_ok = (total_entries > 0) and (matched_entries == total_entries)

    trend_windows = _parse_windows(cfg.get("trend_sessions", []))
    range_windows = _parse_windows(cfg.get("range_sessions", []))
    max_allowed = int(cfg.get("max_trades_per_session", 1))
    max_seen = _max_trades_per_session(trades, trend_windows, range_windows)
    session_limit_ok = max_seen <= max_allowed

    overall_ok = bool(result["diag_ok"]) and v3_events_ok and next_open_ok and session_limit_ok

    result.update(
        {
            "v3_events_ok": v3_events_ok,
            "next_open_ok": next_open_ok,
            "session_limit_ok": session_limit_ok,
            "matched_entries": matched_entries,
            "total_entries": total_entries,
            "max_trades_seen": max_seen,
            "max_trades_allowed": max_allowed,
            "event_types_v3": ",".join(sorted(v3_types.keys())),
            "overall_ok": overall_ok,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="QA checks for v3 runs.")
    parser.add_argument("run_ids", nargs="+", help="Run IDs to validate.")
    parser.add_argument(
        "--output",
        help="Optional CSV output path for QA summary.",
    )
    args = parser.parse_args()

    rows = [check_run(run_id) for run_id in args.run_ids]
    df = pd.DataFrame(rows)
    with pd.option_context("display.max_colwidth", 200):
        print(df.to_string(index=False))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"\nWrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
