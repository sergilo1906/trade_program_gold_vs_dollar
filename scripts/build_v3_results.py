from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass
class RunSpec:
    label: str
    version: str
    run_id: str


RUNS = [
    RunSpec("BASELINE_RANGE", "v2", "20260218_200211"),
    RunSpec("BASELINE_TREND", "v2", "20260218_200726"),
    RunSpec("BASELINE_AUTO", "v2", "20260218_202210"),
    RunSpec("V3_RANGE", "v3", "20260218_210540"),
    RunSpec("V3_TREND", "v3", "20260218_211849"),
    RunSpec("V3_AUTO", "v3", "20260218_213339"),
]

V3_RUNS = {"20260218_210540", "20260218_211849", "20260218_213339"}

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


def _md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No data_"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for c in cols:
            v = row[c]
            if pd.isna(v):
                vals.append("")
            elif isinstance(v, float):
                vals.append(f"{v:.6f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _hhmm_to_min(value: str) -> int:
    hh, mm = value.split(":")
    return int(hh) * 60 + int(mm)


def _parse_windows(windows: list[str]) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for window in windows:
        start_raw, end_raw = window.split("-", 1)
        out.append((_hhmm_to_min(start_raw), _hhmm_to_min(end_raw), window))
    return out


def _in_window(minute: int, start: int, end: int) -> bool:
    if start < end:
        return start <= minute < end
    return minute >= start or minute < end


def _session_key(ts: pd.Timestamp, mode: str, trend_ws: list[tuple[int, int, str]], range_ws: list[tuple[int, int, str]]) -> str:
    minute = int(ts.hour) * 60 + int(ts.minute)
    windows = trend_ws if mode == "TREND" else range_ws
    label = "NO_WINDOW"
    for start, end, raw in windows:
        if _in_window(minute, start, end):
            label = raw
            break
    return f"{ts.date().isoformat()}|{label}"


def _read_boot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if df.empty:
        return {}
    row = df.iloc[0].to_dict()
    return row


def _read_a(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def _block_count(df: pd.DataFrame, block_type: str) -> tuple[int, float]:
    row = df[df["block_type"] == block_type]
    if row.empty:
        return 0, float("nan")
    return int(row.iloc[0]["count"]), float(row.iloc[0]["pct_of_opportunities"])


def build_results() -> tuple[pd.DataFrame, pd.DataFrame]:
    kpi_rows: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []

    for spec in RUNS:
        run_dir = Path("outputs/runs") / spec.run_id
        diag_dir = run_dir / "diagnostics"
        a = _read_a(diag_dir / "A_perf_by_mode.csv")
        e = pd.read_csv(diag_dir / "E_blocks.csv") if (diag_dir / "E_blocks.csv").exists() else pd.DataFrame()
        boot = _read_boot(diag_dir / "BOOT_expectancy_ci.csv")

        opp_denom = int(pd.to_numeric(e.get("opportunities_denom", pd.Series(dtype="float64")), errors="coerce").max()) if not e.empty else 0
        s_count, s_pct = _block_count(e, "SESSION_BLOCK") if not e.empty else (0, float("nan"))
        c_count, c_pct = _block_count(e, "COST_FILTER_BLOCK") if not e.empty else (0, float("nan"))
        h_count, h_pct = _block_count(e, "SHOCK_BLOCK") if not e.empty else (0, float("nan"))

        kpi_rows.append(
            {
                "label": spec.label,
                "version": spec.version,
                "run_id": spec.run_id,
                "mode": a.get("mode", ""),
                "pf": a.get("pf", pd.NA),
                "expectancy_R": a.get("expectancy_R", pd.NA),
                "winrate": a.get("winrate", pd.NA),
                "trades": a.get("trades", pd.NA),
                "opportunities_denom": opp_denom,
                "session_block": f"{s_count} ({s_pct:.4f})" if pd.notna(s_pct) else str(s_count),
                "cost_filter_block": f"{c_count} ({c_pct:.4f})" if pd.notna(c_pct) else str(c_count),
                "shock_block": f"{h_count} ({h_pct:.4f})" if pd.notna(h_pct) else str(h_count),
                "boot_n": boot.get("n", pd.NA),
                "boot_mean": boot.get("mean", pd.NA),
                "boot_ci_low": boot.get("ci_low", pd.NA),
                "boot_ci_high": boot.get("ci_high", pd.NA),
                "boot_crosses_zero": boot.get("crosses_zero", pd.NA),
                "report_path": f"outputs/runs/{spec.run_id}/report.md",
                "diagnostics_path": f"outputs/runs/{spec.run_id}/diagnostics/diagnostics.md",
            }
        )

        if spec.run_id in V3_RUNS:
            missing = [name for name in REQUIRED_DIAG if not (diag_dir / name).exists()]
            events = pd.read_csv(run_dir / "events.csv")
            trades = pd.read_csv(run_dir / "trades.csv")
            v3_events = events["event_type"].astype(str)
            has_v3_signal = int(v3_events.str.contains(r"^V3_SIGNAL_", regex=True).sum()) > 0
            has_v3_entry_exit = (
                int((v3_events == "V3_ENTRY").sum()) > 0
                and int(v3_events.str.startswith("V3_EXIT_").sum()) > 0
            )

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
                    parsed = pd.to_datetime(target, errors="coerce", utc=True)
                    if pd.notna(parsed):
                        signal_targets.add(pd.Timestamp(parsed).isoformat())

            entries = events[events["event_type"] == "V3_ENTRY"].copy()
            entries["timestamp"] = pd.to_datetime(entries["timestamp"], errors="coerce", utc=True)
            total_entries = int(entries["timestamp"].notna().sum())
            next_open_matches = sum(1 for ts in entries["timestamp"].dropna() if pd.Timestamp(ts).isoformat() in signal_targets)

            cfg = yaml.safe_load((run_dir / "config_used.yaml").read_text(encoding="utf-8"))
            trend_ws = _parse_windows(cfg.get("trend_sessions", []))
            range_ws = _parse_windows(cfg.get("range_sessions", []))
            allowed = int(cfg.get("max_trades_per_session", 1))
            trades["entry_time"] = pd.to_datetime(trades["entry_time"], errors="coerce", utc=True)
            valid = trades.dropna(subset=["entry_time"])
            keys = [_session_key(row["entry_time"], str(row.get("mode", "")), trend_ws, range_ws) for _, row in valid.iterrows()]
            counts = pd.Series(keys).value_counts() if keys else pd.Series(dtype="int64")
            max_seen = int(counts.max()) if not counts.empty else 0

            qa_rows.append(
                {
                    "run_id": spec.run_id,
                    "diag_A_to_N": "OK" if not missing else "FAIL",
                    "has_v3_signal_events": "OK" if has_v3_signal else "FAIL",
                    "has_v3_entry_exit_events": "OK" if has_v3_entry_exit else "FAIL",
                    "next_open_match": f"{next_open_matches}/{total_entries}",
                    "next_open_ok": "OK" if (total_entries > 0 and next_open_matches == total_entries) else "FAIL",
                    "max_trades_per_session_seen": max_seen,
                    "max_trades_per_session_allowed": allowed,
                    "session_limit_ok": "OK" if max_seen <= allowed else "FAIL",
                }
            )

    return pd.DataFrame(kpi_rows), pd.DataFrame(qa_rows)


def main() -> int:
    kpi_df, qa_df = build_results()

    docs_path = Path("docs/V3_RESULTS.md")
    lines = [
        "# V3 Results",
        "",
        "## Context",
        "- OHLC-only, M5, next-open.",
        "- `enable_strategy_v3=true` activo en runs V3.",
        "- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.",
        "",
        "## KPI Comparison (v2 baselines vs v3)",
        _md_table(
            kpi_df[
                [
                    "label",
                    "version",
                    "run_id",
                    "mode",
                    "pf",
                    "expectancy_R",
                    "winrate",
                    "trades",
                    "opportunities_denom",
                    "session_block",
                    "cost_filter_block",
                    "shock_block",
                    "boot_n",
                    "boot_mean",
                    "boot_ci_low",
                    "boot_ci_high",
                    "boot_crosses_zero",
                ]
            ]
        ),
        "",
        "## QA v3",
        _md_table(qa_df),
        "",
        "## Paths",
        _md_table(kpi_df[["label", "run_id", "report_path", "diagnostics_path"]]),
    ]
    docs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote: {docs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
