from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml


RUNS = [
    "20260218_210540",  # V3 RANGE
    "20260218_211849",  # V3 TREND
    "20260218_213339",  # V3 AUTO
]

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


def _parse_windows(windows: list[str]) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for window in windows:
        start_raw, end_raw = window.split("-", 1)
        start = _hhmm_to_min(start_raw)
        end = _hhmm_to_min(end_raw)
        out.append((start, end, window))
    return out


def _in_window(minute: int, start: int, end: int) -> bool:
    if start < end:
        return start <= minute < end
    return (minute >= start) or (minute < end)


def _session_key(ts: pd.Timestamp, mode: str, trend_ws: list[tuple[int, int, str]], range_ws: list[tuple[int, int, str]]) -> str:
    minute = int(ts.hour) * 60 + int(ts.minute)
    windows = trend_ws if mode == "TREND" else range_ws
    label = "NO_WINDOW"
    for start, end, raw in windows:
        if _in_window(minute, start, end):
            label = raw
            break
    return f"{ts.date().isoformat()}|{label}"


def main() -> int:
    for run_id in RUNS:
        run_dir = Path("outputs/runs") / run_id
        diag_dir = run_dir / "diagnostics"
        missing = [name for name in REQUIRED_DIAG if not (diag_dir / name).exists()]

        events = pd.read_csv(run_dir / "events.csv")
        trades = pd.read_csv(run_dir / "trades.csv")

        v3_events = events[events["event_type"].astype(str).str.startswith("V3_")]["event_type"].value_counts().to_dict()

        signal_targets: set[str] = set()
        signal_events = events[events["event_type"].isin(["V3_SIGNAL_TREND_BREAKOUT", "V3_SIGNAL_RANGE_RSI"])]
        for _, row in signal_events.iterrows():
            details_raw = row.get("details_json", "")
            try:
                details = json.loads(details_raw) if isinstance(details_raw, str) else {}
            except Exception:
                details = {}
            target = details.get("entry_ts_t1")
            if isinstance(target, str) and target:
                ts_target = pd.to_datetime(target, errors="coerce", utc=True)
                if pd.notna(ts_target):
                    signal_targets.add(pd.Timestamp(ts_target).isoformat())

        entry_events = events[events["event_type"] == "V3_ENTRY"].copy()
        entry_events["timestamp"] = pd.to_datetime(entry_events["timestamp"], errors="coerce", utc=True)
        matched = 0
        total_entries = int(entry_events["timestamp"].notna().sum())
        for ts in entry_events["timestamp"].dropna():
            if pd.Timestamp(ts).isoformat() in signal_targets:
                matched += 1

        cfg = yaml.safe_load((run_dir / "config_used.yaml").read_text(encoding="utf-8"))
        trend_ws = _parse_windows(cfg.get("trend_sessions", []))
        range_ws = _parse_windows(cfg.get("range_sessions", []))
        max_trades_per_session = int(cfg.get("max_trades_per_session", 1))

        trades["entry_time"] = pd.to_datetime(trades["entry_time"], errors="coerce", utc=True)
        valid = trades.dropna(subset=["entry_time"]).copy()
        keys = [
            _session_key(row["entry_time"], str(row.get("mode", "")), trend_ws, range_ws)
            for _, row in valid.iterrows()
        ]
        counts = pd.Series(keys).value_counts() if keys else pd.Series(dtype="int64")
        max_seen = int(counts.max()) if not counts.empty else 0

        print(f"=== {run_id} ===")
        print(f"diag_missing: {'none' if not missing else missing}")
        print(f"v3_event_types: {v3_events}")
        print(f"next_open_matches: {matched}/{total_entries}")
        print(
            f"max_trades_per_session_seen: {max_seen} "
            f"(allowed={max_trades_per_session}, ok={max_seen <= max_trades_per_session})"
        )
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
