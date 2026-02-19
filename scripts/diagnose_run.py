from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_RUN_DIR = Path("outputs/runs/20260218_161547")

SESSION_RULES = (
    ("ASIA", 0, 7),
    ("MODE_SESSION", 7, 17),
    ("OFF_SESSION", 17, 24),
)

R_COL_CANDIDATES = (
    "r_multiple",
    "net_r",
    "net_R",
    "pnl_r",
    "pnl_R",
    "expectancy_r",
    "expectancy_R",
)

MODE_COL_CANDIDATES = (
    "mode",
    "regime_at_entry",
    "regime",
)

ENTRY_TS_CANDIDATES = (
    "entry_time",
    "open_time",
    "entry_ts",
    "timestamp",
    "ts",
)

SIGNALS_TS_CANDIDATES = (
    "timestamp",
    "time",
    "ts",
    "event_time",
    "created_at",
)

EVENTS_TS_CANDIDATES = (
    "timestamp",
    "event_time",
    "time",
    "ts",
    "created_at",
)

SESSION_BUCKET_COL_CANDIDATES = (
    "session_bucket",
    "session",
    "bucket",
    "trading_session",
)

RISK_COL_CANDIDATES = (
    "risk_usd",
    "risk_amount",
)

ENTRY_PRICE_COL_CANDIDATES = (
    "entry_mid",
    "entry_price",
    "open_price",
)

SL_PRICE_COL_CANDIDATES = (
    "sl_mid",
    "sl_price",
    "sl",
    "stop_loss",
)

EVENT_TYPE_CANDIDATES = (
    "event_type",
    "reason",
    "code",
    "event",
    "event_code",
    "block_reason",
)

ENTRY_ATTEMPT_FLAG_CANDIDATES = (
    "entry_attempt",
    "is_entry_attempt",
    "attempt_entry",
)

SIGNALS_STATE_CANDIDATES = (
    "state",
    "signal_state",
    "regime_state",
)

BLOCK_TARGETS = ("COST_FILTER_BLOCK", "SESSION_BLOCK", "SHOCK_BLOCK", "MAX_TRADES")
RULE_TARGETS = ("HOUR_BLACKLIST", "HOUR_NOT_IN_WHITELIST", "COST_GATE_OVERRIDE_HOUR")


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _find_first_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    return None


def _profit_factor_from_r(r: pd.Series) -> float:
    s = _to_num(r).dropna()
    if s.empty:
        return 0.0
    gross_win = float(s[s > 0].sum())
    gross_loss = float((-s[s < 0]).sum())
    if gross_loss <= 0:
        return float("inf") if gross_win > 0 else 0.0
    return gross_win / gross_loss


def _format_float(value: Any, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _markdown_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data_"
    float_cols = float_cols or set()
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for h in headers:
            v = row[h]
            if h in float_cols:
                vals.append(_format_float(v, digits=4))
            else:
                vals.append("" if pd.isna(v) else str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _parse_ts_series_to_utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True)


def _prepare_hourly_base(
    df: pd.DataFrame,
    ts_candidates: tuple[str, ...],
    label: str,
    warnings: list[str],
) -> tuple[pd.DataFrame, str | None]:
    out = df.copy()
    ts_col = _find_first_col(out, ts_candidates)
    if ts_col is None:
        out["_ts_utc"] = pd.NaT
        out["_hour_utc"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        warnings.append(f"{label}: missing timestamp column. Tried: {ts_candidates}.")
        return out, None

    out["_ts_utc"] = _parse_ts_series_to_utc(out[ts_col])
    out["_hour_utc"] = pd.to_numeric(out["_ts_utc"].dt.hour, errors="coerce").astype("Int64")
    if int(out["_ts_utc"].notna().sum()) == 0:
        warnings.append(f"{label}: timestamp column `{ts_col}` parsed to all-NaT.")
    return out, ts_col


def _hourly_counts_0_23(series_with_hours: pd.Series) -> pd.DataFrame:
    base = pd.DataFrame({"hour_utc": list(range(24))})
    s = pd.to_numeric(series_with_hours, errors="coerce").dropna()
    if s.empty:
        base["count"] = 0
        return base
    counts = (
        s.astype(int)
        .value_counts()
        .sort_index()
        .rename_axis("hour_utc")
        .reset_index(name="count")
    )
    out = base.merge(counts, on="hour_utc", how="left")
    out["count"] = pd.to_numeric(out["count"], errors="coerce").fillna(0).astype(int)
    return out


def _derive_session_bucket(hour_utc: float | int | None) -> str:
    if hour_utc is None or pd.isna(hour_utc):
        return "UNKNOWN"
    h = int(hour_utc)
    for name, start, end in SESSION_RULES:
        if start <= h < end:
            return name
    return "UNKNOWN"


def _as_text_series(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].fillna("").astype(str)


def _extract_block_counts(events: pd.DataFrame, event_col: str | None) -> dict[str, int]:
    out = {k: 0 for k in BLOCK_TARGETS}
    if events.empty or event_col is None:
        return out
    texts = _as_text_series(events, event_col).str.upper()
    for txt in texts:
        if "COST_FILTER_BLOCK" in txt:
            out["COST_FILTER_BLOCK"] += 1
        if "SESSION_BLOCK" in txt:
            out["SESSION_BLOCK"] += 1
        if "SHOCK_BLOCK" in txt:
            out["SHOCK_BLOCK"] += 1
        if ("MAX_TRADES_BLOCK" in txt) or ("BLOCKED_MAX_TRADES_DAY" in txt) or ("MAX_TRADES" in txt):
            out["MAX_TRADES"] += 1
    return out


def _extract_rule_counts(events: pd.DataFrame, event_col: str | None) -> dict[str, int]:
    out = {k: 0 for k in RULE_TARGETS}
    if events.empty or event_col is None:
        return out
    texts = _as_text_series(events, event_col).str.upper()
    for txt in texts:
        if "HOUR_NOT_IN_WHITELIST" in txt:
            out["HOUR_NOT_IN_WHITELIST"] += 1
        if "HOUR_BLACKLIST" in txt:
            out["HOUR_BLACKLIST"] += 1
        if ("COST_GATE_OVERRIDE_HOUR" in txt) or ("COST_FILTER_BLOCK_OVERRIDE_HOUR" in txt):
            out["COST_GATE_OVERRIDE_HOUR"] += 1
    return out


def _build_rules_by_hour(
    events_hourly: pd.DataFrame,
    event_col: str | None,
    warnings: list[str],
) -> pd.DataFrame:
    cols = [
        "hour_utc",
        "total_blocks",
        "HOUR_BLACKLIST_count",
        "HOUR_NOT_IN_WHITELIST_count",
        "COST_GATE_OVERRIDE_HOUR_count",
    ]
    if event_col is None:
        warnings.append("Cannot build P_rules_by_hour_utc: missing event_type-like column in events.")
        return pd.DataFrame(columns=cols)
    if events_hourly.empty:
        warnings.append("Cannot build P_rules_by_hour_utc: events dataframe is empty.")
        return pd.DataFrame(columns=cols)

    text = _as_text_series(events_hourly, event_col).str.upper()
    hours = pd.to_numeric(events_hourly["_hour_utc"], errors="coerce")
    temp = pd.DataFrame({"hour_utc": hours, "_event_text": text}).dropna(subset=["hour_utc"])
    if temp.empty:
        return pd.DataFrame(columns=cols)
    temp["hour_utc"] = temp["hour_utc"].astype(int)

    matchers = {
        "HOUR_BLACKLIST_count": lambda s: s.str.contains("HOUR_BLACKLIST", regex=False),
        "HOUR_NOT_IN_WHITELIST_count": lambda s: s.str.contains("HOUR_NOT_IN_WHITELIST", regex=False),
        "COST_GATE_OVERRIDE_HOUR_count": lambda s: (
            s.str.contains("COST_GATE_OVERRIDE_HOUR", regex=False)
            | s.str.contains("COST_FILTER_BLOCK_OVERRIDE_HOUR", regex=False)
        ),
    }
    base = pd.DataFrame({"hour_utc": list(range(24))})
    for out_col, matcher in matchers.items():
        mask = matcher(temp["_event_text"])
        counted = (
            temp[mask]["hour_utc"]
            .value_counts()
            .sort_index()
            .rename_axis("hour_utc")
            .reset_index(name=out_col)
        )
        merged = pd.DataFrame({"hour_utc": list(range(24))}).merge(counted, on="hour_utc", how="left")
        merged[out_col] = pd.to_numeric(merged[out_col], errors="coerce").fillna(0).astype(int)
        base = base.merge(merged, on="hour_utc", how="left")
        base[out_col] = pd.to_numeric(base[out_col], errors="coerce").fillna(0).astype(int)

    base["total_blocks"] = (
        base["HOUR_BLACKLIST_count"]
        + base["HOUR_NOT_IN_WHITELIST_count"]
        + base["COST_GATE_OVERRIDE_HOUR_count"]
    )
    return base[cols]


def _detect_opportunities(signals: pd.DataFrame, events: pd.DataFrame) -> tuple[int, str]:
    if not signals.empty:
        for col in ENTRY_ATTEMPT_FLAG_CANDIDATES:
            if col in signals.columns:
                s = signals[col]
                if s.dtype == bool:
                    return int(s.sum()), f"signals.{col}=True"
                num = _to_num(s)
                if num.notna().any():
                    return int((num.fillna(0) > 0).sum()), f"signals.{col}>0"
                txt = s.fillna("").astype(str).str.lower()
                return int(txt.isin({"1", "true", "yes", "y"}).sum()), f"signals.{col} in {{1,true,yes}}"

    if not signals.empty and "event_type" in signals.columns:
        et = _as_text_series(signals, "event_type").str.upper()
        entry_mask = et.str.contains("ENTRY_ATTEMPT", regex=False) | et.str.contains("ENTRY_CHECK", regex=False)
        n_entry = int(entry_mask.sum())
        if n_entry > 0:
            return n_entry, "signals.event_type contains ENTRY_ATTEMPT/ENTRY_CHECK"

        sig_mask = et.str.contains("SIGNAL_DETECTED", regex=False)
        n_sig = int(sig_mask.sum())
        if n_sig > 0:
            return n_sig, "signals.event_type == SIGNAL_DETECTED"

        sig_fallback = et.str.contains("SIGNAL_CHECK", regex=False) | et.str.contains("SIGNAL_TRIGGER", regex=False)
        n_sig_fb = int(sig_fallback.sum())
        if n_sig_fb > 0:
            return n_sig_fb, "signals.event_type contains SIGNAL_CHECK/SIGNAL_TRIGGER"

        generic_sig = et.str.contains("SIGNAL", regex=False)
        n_generic = int(generic_sig.sum())
        if n_generic > 0:
            return n_generic, "signals.event_type contains SIGNAL"

    if not events.empty:
        ev_col = _find_first_col(events, EVENT_TYPE_CANDIDATES)
        if ev_col is not None:
            et = _as_text_series(events, ev_col).str.upper()
            mask = (
                et.str.contains("ENTRY_ATTEMPT", regex=False)
                | et.str.contains("ENTRY_CHECK", regex=False)
                | et.str.contains("SIGNAL", regex=False)
            )
            n = int(mask.sum())
            if n > 0:
                return n, f"events.{ev_col} contains ENTRY_/SIGNAL"

    if not signals.empty:
        return int(len(signals)), "len(signals)"
    if not events.empty:
        return int(len(events)), "len(events)"
    return 0, "no_data"


def _build_perf_table(df: pd.DataFrame, group_cols: list[str], r_col: str) -> pd.DataFrame:
    if df.empty:
        cols = group_cols + ["pf", "expectancy_R", "winrate", "avg_R", "trades"]
        return pd.DataFrame(columns=cols)

    rows: list[dict[str, Any]] = []
    for keys, sub in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        r = _to_num(sub[r_col]).dropna()
        key_dict = {group_cols[i]: keys[i] for i in range(len(group_cols))}
        row = {
            **key_dict,
            "pf": _profit_factor_from_r(r),
            "expectancy_R": float(r.mean()) if not r.empty else 0.0,
            "winrate": float((r > 0).mean()) if not r.empty else 0.0,
            "avg_R": float(r.mean()) if not r.empty else 0.0,
            "trades": int(len(r)),
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    sort_cols = [c for c in group_cols if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    return out


def _prepare_trade_base(trades: pd.DataFrame, warnings: list[str]) -> tuple[pd.DataFrame, dict[str, str | None]]:
    df = trades.copy()
    found: dict[str, str | None] = {
        "r_col": _find_first_col(df, R_COL_CANDIDATES),
        "mode_col": _find_first_col(df, MODE_COL_CANDIDATES),
        "entry_ts_col": _find_first_col(df, ENTRY_TS_CANDIDATES),
        "session_col": _find_first_col(df, SESSION_BUCKET_COL_CANDIDATES),
        "risk_col": _find_first_col(df, RISK_COL_CANDIDATES),
        "entry_price_col": _find_first_col(df, ENTRY_PRICE_COL_CANDIDATES),
        "sl_price_col": _find_first_col(df, SL_PRICE_COL_CANDIDATES),
    }

    if found["r_col"] is None:
        warnings.append(f"Missing R column. Tried: {R_COL_CANDIDATES}.")
        df["_R"] = pd.Series(dtype="float64")
    else:
        df["_R"] = _to_num(df[found["r_col"]])

    if found["mode_col"] is None:
        warnings.append(f"Missing mode/regime column. Tried: {MODE_COL_CANDIDATES}. Using UNKNOWN.")
        df["_mode"] = "UNKNOWN"
    else:
        df["_mode"] = _as_text_series(df, found["mode_col"]).replace("", "UNKNOWN")

    if found["entry_ts_col"] is None:
        warnings.append(f"Missing entry timestamp column. Tried: {ENTRY_TS_CANDIDATES}.")
        df["_entry_ts_utc"] = pd.NaT
        df["_hour_utc"] = pd.NA
    else:
        df["_entry_ts_utc"] = _parse_ts_series_to_utc(df[found["entry_ts_col"]])
        df["_hour_utc"] = df["_entry_ts_utc"].dt.hour

    if found["session_col"] is not None:
        session_vals = _as_text_series(df, found["session_col"]).str.upper().str.strip()
        valid = {"ASIA", "MODE_SESSION", "OFF_SESSION"}
        df["_session_bucket"] = session_vals.where(session_vals.isin(valid), "UNKNOWN")
    else:
        df["_session_bucket"] = df["_hour_utc"].apply(_derive_session_bucket)

    return df, found


def _build_cost_r(
    trades_prepared: pd.DataFrame,
    fills: pd.DataFrame,
    found: dict[str, str | None],
    warnings: list[str],
) -> pd.DataFrame:
    df = trades_prepared.copy()
    if "trade_id" not in df.columns:
        warnings.append("Missing trade_id in trades. Cost_R per trade cannot be aligned.")
        df["_cost_r"] = pd.NA
        return df

    df["trade_id"] = pd.to_numeric(df["trade_id"], errors="coerce")

    cost_usd_by_trade = pd.Series(dtype="float64")
    if not fills.empty and {"trade_id", "spread_usd", "slippage_usd"}.issubset(set(fills.columns)):
        f = fills.copy()
        f["trade_id"] = pd.to_numeric(f["trade_id"], errors="coerce")
        f["spread_usd"] = _to_num(f["spread_usd"]).fillna(0.0)
        f["slippage_usd"] = _to_num(f["slippage_usd"]).fillna(0.0)
        if "cost_multiplier" in f.columns:
            f["cost_multiplier"] = _to_num(f["cost_multiplier"]).fillna(1.0)
        else:
            f["cost_multiplier"] = 1.0
        f["_cost_component_usd"] = (f["spread_usd"] + f["slippage_usd"]) * f["cost_multiplier"]
        cost_usd_by_trade = f.groupby("trade_id")["_cost_component_usd"].sum()
    elif {"spread", "cost_multiplier"}.issubset(set(df.columns)):
        spread = _to_num(df["spread"]).fillna(0.0)
        multiplier = _to_num(df["cost_multiplier"]).fillna(1.0)
        df["_trade_cost_usd"] = spread * multiplier
    else:
        warnings.append(
            "Missing columns for cost_usd. Need fills.(trade_id,spread_usd,slippage_usd) "
            "or trades.(spread,cost_multiplier)."
        )

    if not cost_usd_by_trade.empty:
        df = df.merge(
            cost_usd_by_trade.rename("_trade_cost_usd").reset_index(),
            how="left",
            on="trade_id",
        )
    if "_trade_cost_usd" not in df.columns:
        df["_trade_cost_usd"] = pd.NA

    denom = pd.Series(float("nan"), index=df.index, dtype="float64")
    if found["risk_col"] is not None:
        denom = _to_num(df[found["risk_col"]]).abs()
    elif (found["entry_price_col"] is not None) and (found["sl_price_col"] is not None):
        denom = (_to_num(df[found["entry_price_col"]]) - _to_num(df[found["sl_price_col"]])).abs()
        warnings.append(
            "risk_usd column not found; using abs(entry-sl) as denominator for Cost_R."
        )
    else:
        warnings.append(
            f"Cannot compute Cost_R denominator. Missing risk cols {RISK_COL_CANDIDATES} "
            f"and price/SL pairs {ENTRY_PRICE_COL_CANDIDATES} + {SL_PRICE_COL_CANDIDATES}."
        )

    df["_cost_r"] = _to_num(df["_trade_cost_usd"]) / denom.replace(0, pd.NA)
    return df


def _build_cost_percentiles_table(
    trades_with_cost: pd.DataFrame,
    include_hour: bool = True,
) -> pd.DataFrame:
    base = trades_with_cost.copy()
    base["_cost_r"] = _to_num(base["_cost_r"])
    base = base.dropna(subset=["_cost_r"])
    if base.empty:
        return pd.DataFrame(
            columns=[
                "scope",
                "mode",
                "session_bucket",
                "hour_utc",
                "trades",
                "cost_R_mean",
                "cost_R_p50",
                "cost_R_p75",
                "cost_R_p90",
            ]
        )

    rows: list[dict[str, Any]] = []
    group_specs: list[tuple[str, list[str]]] = [("mode_session_bucket", ["_mode", "_session_bucket"])]
    if include_hour:
        group_specs.append(("mode_session_bucket_hour", ["_mode", "_session_bucket", "_hour_utc"]))

    for scope, cols in group_specs:
        for keys, sub in base.groupby(cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            m = keys[0] if len(keys) > 0 else ""
            b = keys[1] if len(keys) > 1 else ""
            h = keys[2] if len(keys) > 2 else pd.NA
            c = sub["_cost_r"]
            rows.append(
                {
                    "scope": scope,
                    "mode": m,
                    "session_bucket": b,
                    "hour_utc": h,
                    "trades": int(len(c)),
                    "cost_R_mean": float(c.mean()),
                    "cost_R_p50": float(c.quantile(0.50)),
                    "cost_R_p75": float(c.quantile(0.75)),
                    "cost_R_p90": float(c.quantile(0.90)),
                }
            )

    out = pd.DataFrame(rows)
    out = out.sort_values(["scope", "mode", "session_bucket", "hour_utc"], na_position="last").reset_index(drop=True)
    return out


def _build_signals_by_hour(
    signals_hourly: pd.DataFrame,
    events_hourly: pd.DataFrame,
    signals_event_col: str | None,
    events_event_col: str | None,
    warnings: list[str],
) -> tuple[pd.DataFrame, str]:
    out_cols = ["hour_utc", "opportunities"]
    if signals_event_col is None and events_event_col is None:
        warnings.append("Cannot build G_signals_by_hour_utc: missing event_type-like column in both signals/events.")
        return pd.DataFrame(columns=out_cols), "no_event_type_column"

    if signals_event_col is not None:
        s_evt = _as_text_series(signals_hourly, signals_event_col).str.upper()
        s_sig = signals_hourly[s_evt == "SIGNAL_DETECTED"].copy()
        s_counts = _hourly_counts_0_23(s_sig["_hour_utc"])
        if int(s_sig["_hour_utc"].notna().sum()) > 0:
            return s_counts.rename(columns={"count": "opportunities"}), f"signals.{signals_event_col} == SIGNAL_DETECTED"

    if events_event_col is not None:
        warnings.append("Signals timestamp unavailable/invalid for SIGNAL_DETECTED; fallback to events for hourly opportunities.")
        e_evt = _as_text_series(events_hourly, events_event_col).str.upper()
        e_sig = events_hourly[e_evt == "SIGNAL_DETECTED"].copy()
        e_counts = _hourly_counts_0_23(e_sig["_hour_utc"])
        if int(e_sig["_hour_utc"].notna().sum()) > 0:
            return e_counts.rename(columns={"count": "opportunities"}), f"events.{events_event_col} == SIGNAL_DETECTED"

    warnings.append("No valid hourly SIGNAL_DETECTED rows found for G_signals_by_hour_utc.")
    return pd.DataFrame(columns=out_cols), "no_hourly_signal_detected"


def _build_blocks_by_hour(
    events_hourly: pd.DataFrame,
    event_col: str | None,
    opportunities_by_hour: pd.DataFrame,
    warnings: list[str],
) -> pd.DataFrame:
    out_cols = [
        "hour_utc",
        "opportunities",
        "SESSION_BLOCK_count",
        "SESSION_BLOCK_pct",
        "COST_FILTER_BLOCK_count",
        "COST_FILTER_BLOCK_pct",
        "SHOCK_BLOCK_count",
        "SHOCK_BLOCK_pct",
        "MAX_TRADES_count",
        "MAX_TRADES_pct",
    ]
    if event_col is None:
        warnings.append("Cannot build F_blocks_by_hour_utc: missing event_type-like column in events.")
        return pd.DataFrame(columns=out_cols)

    if events_hourly.empty:
        warnings.append("Cannot build F_blocks_by_hour_utc: events dataframe is empty.")
        return pd.DataFrame(columns=out_cols)

    base = pd.DataFrame({"hour_utc": list(range(24))})
    if opportunities_by_hour.empty:
        base["opportunities"] = 0
    else:
        base = base.merge(opportunities_by_hour[["hour_utc", "opportunities"]], on="hour_utc", how="left")
        base["opportunities"] = pd.to_numeric(base["opportunities"], errors="coerce").fillna(0).astype(int)

    text = _as_text_series(events_hourly, event_col).str.upper()
    hours = pd.to_numeric(events_hourly["_hour_utc"], errors="coerce")
    temp = pd.DataFrame({"hour_utc": hours, "_event_text": text}).dropna(subset=["hour_utc"])
    temp["hour_utc"] = temp["hour_utc"].astype(int)

    block_matchers = {
        "SESSION_BLOCK": lambda s: s.str.contains("SESSION_BLOCK", regex=False),
        "COST_FILTER_BLOCK": lambda s: s.str.contains("COST_FILTER_BLOCK", regex=False),
        "SHOCK_BLOCK": lambda s: s.str.contains("SHOCK_BLOCK", regex=False),
        "MAX_TRADES": lambda s: (
            s.str.contains("MAX_TRADES_BLOCK", regex=False)
            | s.str.contains("BLOCKED_MAX_TRADES_DAY", regex=False)
            | s.str.contains("MAX_TRADES", regex=False)
        ),
    }

    for block_name, matcher in block_matchers.items():
        if temp.empty:
            counts = pd.DataFrame({"hour_utc": list(range(24)), f"{block_name}_count": [0] * 24})
        else:
            mask = matcher(temp["_event_text"])
            counted = (
                temp[mask]["hour_utc"]
                .value_counts()
                .sort_index()
                .rename_axis("hour_utc")
                .reset_index(name=f"{block_name}_count")
            )
            counts = pd.DataFrame({"hour_utc": list(range(24))}).merge(counted, on="hour_utc", how="left")
            counts[f"{block_name}_count"] = (
                pd.to_numeric(counts[f"{block_name}_count"], errors="coerce").fillna(0).astype(int)
            )
        base = base.merge(counts, on="hour_utc", how="left")
        base[f"{block_name}_count"] = pd.to_numeric(base[f"{block_name}_count"], errors="coerce").fillna(0).astype(int)
        denom = base["opportunities"].replace(0, pd.NA)
        base[f"{block_name}_pct"] = base[f"{block_name}_count"] / denom

    return base[out_cols]


def _build_hour_robust_perf(trades_prepared: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "hour_utc",
        "trades",
        "wins",
        "losses",
        "sum_R_pos",
        "sum_R_neg_abs",
        "pf",
        "expectancy_R",
        "winrate",
    ]
    if trades_prepared.empty:
        return pd.DataFrame(columns=cols)

    base = trades_prepared.copy()
    base["_hour_utc"] = pd.to_numeric(base["_hour_utc"], errors="coerce")
    base["_R"] = _to_num(base["_R"])
    base = base.dropna(subset=["_hour_utc", "_R"])
    if base.empty:
        return pd.DataFrame(columns=cols)
    base["_hour_utc"] = base["_hour_utc"].astype(int)

    rows: list[dict[str, Any]] = []
    for hour, sub in base.groupby("_hour_utc", dropna=False):
        r = _to_num(sub["_R"]).dropna()
        wins = int((r > 0).sum())
        losses = int((r < 0).sum())
        sum_r_pos = float(r[r > 0].sum())
        sum_r_neg_abs = float(abs(r[r < 0].sum()))
        pf = (sum_r_pos / sum_r_neg_abs) if sum_r_neg_abs > 0 else pd.NA
        expectancy = float(r.mean()) if not r.empty else pd.NA
        winrate = (wins / len(r)) if len(r) > 0 else pd.NA
        rows.append(
            {
                "hour_utc": int(hour),
                "trades": int(len(r)),
                "wins": wins,
                "losses": losses,
                "sum_R_pos": sum_r_pos,
                "sum_R_neg_abs": sum_r_neg_abs,
                "pf": pf,
                "expectancy_R": expectancy,
                "winrate": winrate,
            }
        )

    out = pd.DataFrame(rows, columns=cols).sort_values("hour_utc").reset_index(drop=True)
    return out


def _build_signals_state_counts(
    signals_hourly: pd.DataFrame,
    state_col: str | None,
    warnings: list[str],
) -> pd.DataFrame:
    cols = ["scope", "hour_utc", "state", "count"]
    if state_col is None:
        warnings.append(
            f"Cannot build J_signals_state_counts: missing state column. Tried: {SIGNALS_STATE_CANDIDATES}."
        )
        return pd.DataFrame(columns=cols)

    state_series = _as_text_series(signals_hourly, state_col).replace("", "UNKNOWN")
    global_counts = (
        state_series.value_counts(dropna=False)
        .rename_axis("state")
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    global_df = global_counts.copy()
    global_df["scope"] = "global"
    global_df["hour_utc"] = pd.NA
    global_df = global_df[["scope", "hour_utc", "state", "count"]]

    hourly_df = pd.DataFrame(columns=cols)
    hour_series = pd.to_numeric(signals_hourly.get("_hour_utc", pd.Series(dtype="float64")), errors="coerce")
    if int(hour_series.notna().sum()) > 0:
        temp = pd.DataFrame(
            {
                "hour_utc": hour_series,
                "state": state_series,
            }
        ).dropna(subset=["hour_utc"])
        if not temp.empty:
            temp["hour_utc"] = temp["hour_utc"].astype(int)
            hourly_counts = (
                temp.groupby(["hour_utc", "state"], dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values(["hour_utc", "count", "state"], ascending=[True, False, True])
                .reset_index(drop=True)
            )
            hourly_df = hourly_counts.copy()
            hourly_df["scope"] = "hourly"
            hourly_df = hourly_df[["scope", "hour_utc", "state", "count"]]
    else:
        warnings.append("J_signals_state_counts: no valid hourly timestamps in signals; hourly state rows omitted.")

    if global_df.empty and hourly_df.empty:
        out = pd.DataFrame(columns=cols)
    elif global_df.empty:
        out = hourly_df.copy()
    elif hourly_df.empty:
        out = global_df.copy()
    else:
        out = pd.concat([global_df, hourly_df], ignore_index=True)
    if "hour_utc" in out.columns:
        out["hour_utc"] = pd.to_numeric(out["hour_utc"], errors="coerce").astype("Int64")
    out["count"] = pd.to_numeric(out["count"], errors="coerce").fillna(0).astype(int)
    return out[cols]


def _build_regime_event_counts(
    events_hourly: pd.DataFrame,
    event_col: str | None,
    warnings: list[str],
) -> pd.DataFrame:
    cols = ["scope", "hour_utc", "event_type", "count"]
    if event_col is None:
        warnings.append("Cannot build K_regime_event_counts: missing event_type-like column in events.")
        return pd.DataFrame(columns=cols)

    event_values = _as_text_series(events_hourly, event_col)
    regime_mask = event_values.str.upper().str.contains("REGIME", regex=False)
    regime_df = events_hourly[regime_mask].copy()
    if regime_df.empty:
        warnings.append("K_regime_event_counts: no REGIME events found in events.")
        return pd.DataFrame(columns=cols)

    regime_df["_event_type_norm"] = event_values[regime_mask].values
    global_counts = (
        regime_df["_event_type_norm"]
        .value_counts(dropna=False)
        .rename_axis("event_type")
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    global_df = global_counts.copy()
    global_df["scope"] = "global"
    global_df["hour_utc"] = pd.NA
    global_df = global_df[["scope", "hour_utc", "event_type", "count"]]

    hourly_df = pd.DataFrame(columns=cols)
    hour_series = pd.to_numeric(regime_df.get("_hour_utc", pd.Series(dtype="float64")), errors="coerce")
    if int(hour_series.notna().sum()) > 0:
        temp = pd.DataFrame(
            {
                "hour_utc": hour_series,
                "event_type": regime_df["_event_type_norm"],
            }
        ).dropna(subset=["hour_utc"])
        if not temp.empty:
            temp["hour_utc"] = temp["hour_utc"].astype(int)
            hourly_counts = (
                temp.groupby(["hour_utc", "event_type"], dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values(["hour_utc", "count", "event_type"], ascending=[True, False, True])
                .reset_index(drop=True)
            )
            hourly_df = hourly_counts.copy()
            hourly_df["scope"] = "hourly"
            hourly_df = hourly_df[["scope", "hour_utc", "event_type", "count"]]
    else:
        warnings.append("K_regime_event_counts: no valid hourly timestamps in events; hourly regime rows omitted.")

    if global_df.empty and hourly_df.empty:
        out = pd.DataFrame(columns=cols)
    elif global_df.empty:
        out = hourly_df.copy()
    elif hourly_df.empty:
        out = global_df.copy()
    else:
        out = pd.concat([global_df, hourly_df], ignore_index=True)
    if "hour_utc" in out.columns:
        out["hour_utc"] = pd.to_numeric(out["hour_utc"], errors="coerce").astype("Int64")
    out["count"] = pd.to_numeric(out["count"], errors="coerce").fillna(0).astype(int)
    return out[cols]


def _extract_regime_enter_events(
    events_hourly: pd.DataFrame,
    event_col: str | None,
    warnings: list[str],
) -> pd.DataFrame:
    cols = ["ts_utc", "hour_utc", "event_type", "regime"]
    if event_col is None:
        warnings.append("Cannot extract regime enter events: missing event_type-like column in events.")
        return pd.DataFrame(columns=cols)
    if events_hourly.empty:
        warnings.append("Cannot extract regime enter events: events dataframe is empty.")
        return pd.DataFrame(columns=cols)

    event_text_upper = _as_text_series(events_hourly, event_col).str.upper().str.strip()
    enter_mask = event_text_upper.str.startswith("REGIME_") & event_text_upper.str.endswith("_ENTER")
    enter_df = events_hourly[enter_mask].copy()
    if enter_df.empty:
        warnings.append("No `REGIME_*_ENTER` events found in events for L/M/N.")
        return pd.DataFrame(columns=cols)

    enter_df["event_type"] = _as_text_series(events_hourly, event_col)[enter_mask].values
    enter_df["_event_type_upper"] = event_text_upper[enter_mask].values
    before_drop = len(enter_df)
    enter_df = enter_df.dropna(subset=["_ts_utc"]).copy()
    dropped = before_drop - len(enter_df)
    if dropped > 0:
        warnings.append(f"Regime enter events: omitted {dropped} rows with invalid timestamp (NaT).")
    if enter_df.empty:
        return pd.DataFrame(columns=cols)

    enter_df["regime"] = enter_df["_event_type_upper"].str.extract(r"^REGIME_(.+)_ENTER$")[0].fillna("UNKNOWN")
    enter_df["hour_utc"] = pd.to_numeric(enter_df["_hour_utc"], errors="coerce").astype("Int64")
    out = (
        enter_df.rename(columns={"_ts_utc": "ts_utc"})[["ts_utc", "hour_utc", "event_type", "regime"]]
        .sort_values("ts_utc")
        .reset_index(drop=True)
    )
    return out


def _resolve_regime_segment_end_ts(
    run_dir: Path,
    signals_hourly: pd.DataFrame,
    events_hourly: pd.DataFrame,
    warnings: list[str],
) -> tuple[pd.Timestamp | None, str]:
    if "_ts_utc" in signals_hourly.columns:
        s_max = pd.to_datetime(signals_hourly["_ts_utc"], errors="coerce", utc=True).max()
        if pd.notna(s_max):
            return pd.Timestamp(s_max), "signals_max_ts"

    if "_ts_utc" in events_hourly.columns:
        e_max = pd.to_datetime(events_hourly["_ts_utc"], errors="coerce", utc=True).max()
        if pd.notna(e_max):
            return pd.Timestamp(e_max), "events_max_ts"

    run_meta = run_dir / "run_meta.json"
    if run_meta.exists():
        try:
            meta = json.loads(run_meta.read_text(encoding="utf-8"))
            data_path_raw = meta.get("data_path")
            if isinstance(data_path_raw, str) and data_path_raw.strip():
                data_path = Path(data_path_raw)
                if not data_path.is_absolute():
                    data_path = (run_dir.parent.parent.parent / data_path).resolve()
                if data_path.exists():
                    probe = pd.read_csv(data_path, nrows=5)
                    ts_col = _find_first_col(
                        probe,
                        (
                            "timestamp",
                            "time",
                            "ts",
                            "datetime",
                            "date",
                            "event_time",
                            "created_at",
                        ),
                    )
                    if ts_col is not None:
                        data_full = pd.read_csv(data_path, usecols=[ts_col])
                        d_max = pd.to_datetime(data_full[ts_col], errors="coerce", utc=True).max()
                        if pd.notna(d_max):
                            warnings.append(
                                f"Regime segments end_ts fallback used from run_meta.data_path column `{ts_col}`."
                            )
                            return pd.Timestamp(d_max), "run_meta_data_max_ts"
        except Exception as exc:
            warnings.append(f"Regime segments end_ts run_meta fallback failed: {exc}.")

    warnings.append("Regime segments end_ts unresolved: no valid signals/events/run_meta timestamp found.")
    return None, "unresolved"


def _build_regime_segments(
    regime_enters: pd.DataFrame,
    segment_end_ts_utc: pd.Timestamp | None,
    warnings: list[str],
) -> pd.DataFrame:
    cols = [
        "segment_id",
        "regime",
        "start_ts_utc",
        "end_ts_utc",
        "duration_seconds",
        "duration_minutes",
        "bars_est_m5",
        "start_hour_utc",
    ]
    if regime_enters.empty:
        warnings.append("L_regime_segments: no regime enter events available.")
        return pd.DataFrame(columns=cols)

    reg = regime_enters.sort_values("ts_utc").reset_index(drop=True).copy()

    rows: list[dict[str, Any]] = []
    for i in range(len(reg)):
        start_ts = reg.at[i, "ts_utc"]
        if i < len(reg) - 1:
            end_ts = reg.at[i + 1, "ts_utc"]
        else:
            end_ts = segment_end_ts_utc
        if pd.isna(start_ts) or pd.isna(end_ts):
            continue
        duration_seconds = float((end_ts - start_ts).total_seconds())
        if duration_seconds < 0:
            continue
        duration_minutes = duration_seconds / 60.0
        bars_est_m5 = int(duration_seconds // 300.0) if duration_seconds >= 0 else 0
        rows.append(
            {
                "segment_id": i + 1,
                "regime": reg.at[i, "regime"],
                "start_ts_utc": start_ts,
                "end_ts_utc": end_ts,
                "duration_seconds": duration_seconds,
                "duration_minutes": duration_minutes,
                "bars_est_m5": bars_est_m5,
                "start_hour_utc": int(pd.Timestamp(start_ts).hour),
            }
        )

    if not rows:
        warnings.append("L_regime_segments: unable to build valid segments after timestamp filtering.")
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame(rows, columns=cols)
    out["segment_id"] = pd.to_numeric(out["segment_id"], errors="coerce").fillna(0).astype(int)
    out["bars_est_m5"] = pd.to_numeric(out["bars_est_m5"], errors="coerce").fillna(0).astype(int)
    out["start_hour_utc"] = pd.to_numeric(out["start_hour_utc"], errors="coerce").astype("Int64")
    return out


def _build_regime_time_share(
    l_segments: pd.DataFrame,
    warnings: list[str],
) -> pd.DataFrame:
    cols = [
        "regime",
        "segments",
        "total_seconds",
        "share",
        "total_minutes",
        "pct_time",
        "avg_minutes",
        "p50_minutes",
        "p90_minutes",
    ]
    if l_segments.empty:
        warnings.append("M_regime_time_share: no L segments available.")
        return pd.DataFrame(columns=cols)

    base = l_segments.copy()
    if "duration_seconds" in base.columns:
        base["duration_seconds"] = _to_num(base["duration_seconds"])
        base["duration_minutes"] = base["duration_seconds"] / 60.0
    else:
        base["duration_minutes"] = _to_num(base["duration_minutes"])
        base["duration_seconds"] = base["duration_minutes"] * 60.0
    base = base.dropna(subset=["duration_minutes"])
    if base.empty:
        warnings.append("M_regime_time_share: no valid duration_minutes in L segments.")
        return pd.DataFrame(columns=cols)

    total_all_seconds = float(base["duration_seconds"].sum())
    grouped = (
        base.groupby("regime", dropna=False)
        .agg(
            segments=("duration_minutes", "count"),
            total_minutes=("duration_minutes", "sum"),
            total_seconds=("duration_seconds", "sum"),
            avg_minutes=("duration_minutes", "mean"),
            p50_minutes=("duration_minutes", "median"),
        )
        .reset_index()
    )
    p90 = (
        base.groupby("regime", dropna=False)["duration_minutes"]
        .quantile(0.90)
        .rename("p90_minutes")
        .reset_index()
    )
    out = grouped.merge(p90, on="regime", how="left")
    out["share"] = out["total_seconds"] / total_all_seconds if total_all_seconds > 0 else pd.NA
    out["pct_time"] = out["share"]
    out["segments"] = pd.to_numeric(out["segments"], errors="coerce").fillna(0).astype(int)
    out = out[cols].sort_values("total_minutes", ascending=False).reset_index(drop=True)
    return out


def _build_signals_by_regime(
    signals_hourly: pd.DataFrame,
    signals_event_col: str | None,
    regime_enters: pd.DataFrame,
    warnings: list[str],
) -> pd.DataFrame:
    cols = ["scope", "regime", "hour_utc", "opportunities"]
    if signals_event_col is None:
        warnings.append("N_signals_by_regime: missing event_type-like column in signals.")
        return pd.DataFrame(columns=cols)

    event_text = _as_text_series(signals_hourly, signals_event_col).str.upper()
    signals_detected = signals_hourly[event_text == "SIGNAL_DETECTED"].copy()
    if signals_detected.empty:
        warnings.append("N_signals_by_regime: no SIGNAL_DETECTED rows in signals.")
        return pd.DataFrame(columns=cols)

    before_drop = len(signals_detected)
    signals_detected = signals_detected.dropna(subset=["_ts_utc"]).copy()
    dropped = before_drop - len(signals_detected)
    if dropped > 0:
        warnings.append(f"N_signals_by_regime: omitted {dropped} SIGNAL_DETECTED rows with invalid timestamp (NaT).")
    if signals_detected.empty:
        return pd.DataFrame(columns=cols)

    signals_detected = signals_detected.sort_values("_ts_utc").reset_index(drop=True)
    signals_detected["_hour_utc"] = pd.to_numeric(signals_detected["_hour_utc"], errors="coerce")
    missing_hour = signals_detected["_hour_utc"].isna()
    if int(missing_hour.sum()) > 0:
        signals_detected.loc[missing_hour, "_hour_utc"] = signals_detected.loc[missing_hour, "_ts_utc"].dt.hour
    signals_detected["_hour_utc"] = signals_detected["_hour_utc"].astype("Int64")

    if regime_enters.empty:
        signals_detected["regime"] = "UNKNOWN"
    else:
        enters = regime_enters.dropna(subset=["ts_utc"]).sort_values("ts_utc").copy()
        if enters.empty:
            signals_detected["regime"] = "UNKNOWN"
        else:
            enters = enters.rename(columns={"ts_utc": "_regime_enter_ts"})
            merged = pd.merge_asof(
                signals_detected,
                enters[["_regime_enter_ts", "regime"]],
                left_on="_ts_utc",
                right_on="_regime_enter_ts",
                direction="backward",
            )
            merged["regime"] = merged["regime"].fillna("UNKNOWN")
            signals_detected = merged

    global_counts = (
        signals_detected["regime"]
        .value_counts(dropna=False)
        .rename_axis("regime")
        .reset_index(name="opportunities")
        .sort_values("opportunities", ascending=False)
        .reset_index(drop=True)
    )
    global_df = global_counts.copy()
    global_df["scope"] = "global"
    global_df["hour_utc"] = pd.NA
    global_df = global_df[["scope", "regime", "hour_utc", "opportunities"]]

    hourly_counts = (
        signals_detected.dropna(subset=["_hour_utc"])
        .groupby(["regime", "_hour_utc"], dropna=False)
        .size()
        .reset_index(name="opportunities")
        .rename(columns={"_hour_utc": "hour_utc"})
        .sort_values(["hour_utc", "opportunities", "regime"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    hourly_df = hourly_counts.copy()
    hourly_df["scope"] = "hourly"
    hourly_df = hourly_df[["scope", "regime", "hour_utc", "opportunities"]]

    out_records = global_df.to_dict("records") + hourly_df.to_dict("records")
    out = pd.DataFrame(out_records, columns=cols) if out_records else pd.DataFrame(columns=cols)
    out["hour_utc"] = pd.to_numeric(out["hour_utc"], errors="coerce").astype("Int64")
    out["opportunities"] = pd.to_numeric(out["opportunities"], errors="coerce").fillna(0).astype(int)
    return out[cols]


def diagnose_run(run_dir: Path) -> int:
    trades_path = run_dir / "trades.csv"
    fills_path = run_dir / "fills.csv"
    events_path = run_dir / "events.csv"
    signals_path = run_dir / "signals.csv"

    required = [trades_path, fills_path, events_path, signals_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("ERROR: Missing required CSV files:")
        for p in missing:
            print(f"- {p}")
        return 2

    trades = pd.read_csv(trades_path)
    fills = pd.read_csv(fills_path)
    events = pd.read_csv(events_path)
    signals = pd.read_csv(signals_path)

    warnings: list[str] = []

    trades_prepared, found = _prepare_trade_base(trades, warnings)
    trades_cost = _build_cost_r(trades_prepared, fills, found, warnings)
    signals_hourly, signals_ts_col = _prepare_hourly_base(signals, SIGNALS_TS_CANDIDATES, "signals", warnings)
    events_hourly, events_ts_col = _prepare_hourly_base(events, EVENTS_TS_CANDIDATES, "events", warnings)

    if (
        (signals_ts_col is None or int(signals_hourly["_ts_utc"].notna().sum()) == 0)
        and events_ts_col is not None
        and len(signals_hourly) == len(events_hourly)
    ):
        signals_hourly["_ts_utc"] = events_hourly["_ts_utc"].values
        signals_hourly["_hour_utc"] = events_hourly["_hour_utc"].values
        warnings.append(
            "signals: using row-wise fallback timestamp from events because signals timestamp is missing/unparseable."
        )
        signals_ts_col = f"fallback_from_events.{events_ts_col}"
    elif (
        signals_ts_col is None
        and events_ts_col is not None
        and len(signals_hourly) != len(events_hourly)
    ):
        warnings.append(
            "signals timestamp missing and events length differs; cannot apply row-wise fallback timestamps."
        )

    r_col = "_R"
    mode_col = "_mode"
    session_col = "_session_bucket"
    hour_col = "_hour_utc"

    a_df = _build_perf_table(trades_prepared, [mode_col], r_col).rename(
        columns={
            mode_col: "mode",
        }
    )

    b_df = _build_perf_table(trades_prepared, [session_col], r_col).rename(
        columns={
            session_col: "session_bucket",
        }
    )

    c_base = trades_prepared.copy()
    c_base[hour_col] = pd.to_numeric(c_base[hour_col], errors="coerce")
    c_base = c_base.dropna(subset=[hour_col])
    c_base[hour_col] = c_base[hour_col].astype(int)
    c_df = _build_perf_table(c_base, [hour_col], r_col).rename(columns={hour_col: "hour_utc"})
    if not c_df.empty:
        c_df = c_df.sort_values("hour_utc").reset_index(drop=True)
        c_df["hour_utc"] = pd.to_numeric(c_df["hour_utc"], errors="coerce").astype("Int64")
        c_df["trades"] = pd.to_numeric(c_df["trades"], errors="coerce").fillna(0).astype(int)

    d_df = _build_cost_percentiles_table(trades_cost, include_hour=True)

    signals_event_col = _find_first_col(signals, EVENT_TYPE_CANDIDATES)
    signals_state_col = _find_first_col(signals, SIGNALS_STATE_CANDIDATES)
    event_col = _find_first_col(events, EVENT_TYPE_CANDIDATES)
    block_counts = _extract_block_counts(events, event_col)
    rule_counts = _extract_rule_counts(events, event_col)

    opportunities, denom_src = _detect_opportunities(signals, events)
    e_rows: list[dict[str, Any]] = []
    for key in BLOCK_TARGETS:
        count = int(block_counts.get(key, 0))
        pct = (count / opportunities) if opportunities > 0 else pd.NA
        e_rows.append(
            {
                "block_type": key,
                "count": count,
                "pct_of_opportunities": pct,
                "opportunities_denom": opportunities,
                "denominator_source": denom_src,
            }
        )
    e_df = pd.DataFrame(e_rows).sort_values("count", ascending=False).reset_index(drop=True)
    o_rows: list[dict[str, Any]] = []
    for key in RULE_TARGETS:
        count = int(rule_counts.get(key, 0))
        pct = (count / opportunities) if opportunities > 0 else pd.NA
        o_rows.append(
            {
                "rule_id": key,
                "count": count,
                "pct_of_opportunities": pct,
                "opportunities_denom": opportunities,
                "denominator_source": denom_src,
            }
        )
    o_df = pd.DataFrame(o_rows).sort_values("count", ascending=False).reset_index(drop=True)

    g_df, g_source = _build_signals_by_hour(
        signals_hourly=signals_hourly,
        events_hourly=events_hourly,
        signals_event_col=signals_event_col,
        events_event_col=event_col,
        warnings=warnings,
    )
    if not g_df.empty:
        g_df["hour_utc"] = pd.to_numeric(g_df["hour_utc"], errors="coerce").astype("Int64")
        g_df["opportunities"] = pd.to_numeric(g_df["opportunities"], errors="coerce").fillna(0).astype(int)

    f_df = _build_blocks_by_hour(
        events_hourly=events_hourly,
        event_col=event_col,
        opportunities_by_hour=g_df,
        warnings=warnings,
    )
    if not f_df.empty:
        f_df["hour_utc"] = pd.to_numeric(f_df["hour_utc"], errors="coerce").astype("Int64")
        f_df["opportunities"] = pd.to_numeric(f_df["opportunities"], errors="coerce").fillna(0).astype(int)
    p_df = _build_rules_by_hour(
        events_hourly=events_hourly,
        event_col=event_col,
        warnings=warnings,
    )
    if not p_df.empty:
        p_df["hour_utc"] = pd.to_numeric(p_df["hour_utc"], errors="coerce").astype("Int64")
        p_df["total_blocks"] = pd.to_numeric(p_df["total_blocks"], errors="coerce").fillna(0).astype(int)
        for col in ("HOUR_BLACKLIST_count", "HOUR_NOT_IN_WHITELIST_count", "COST_GATE_OVERRIDE_HOUR_count"):
            p_df[col] = pd.to_numeric(p_df[col], errors="coerce").fillna(0).astype(int)

    h_df = _build_hour_robust_perf(trades_prepared)
    if h_df.empty:
        warnings.append("H_perf_by_hour_robust is empty (no trade hours with valid R and timestamp).")
    else:
        h_df["hour_utc"] = pd.to_numeric(h_df["hour_utc"], errors="coerce").astype("Int64")
        for col in ("trades", "wins", "losses"):
            h_df[col] = pd.to_numeric(h_df[col], errors="coerce").fillna(0).astype(int)

    if "regime_at_entry" in trades_prepared.columns:
        i_base = trades_prepared.copy()
        i_base["regime_at_entry"] = _as_text_series(i_base, "regime_at_entry").replace("", "UNKNOWN")
        i_df = _build_perf_table(i_base, ["regime_at_entry"], r_col)
    else:
        warnings.append("Missing `regime_at_entry` in trades; I_perf_by_regime_at_entry generated as empty.")
        i_df = pd.DataFrame(columns=["regime_at_entry", "pf", "expectancy_R", "winrate", "avg_R", "trades"])

    j_df = _build_signals_state_counts(
        signals_hourly=signals_hourly,
        state_col=signals_state_col,
        warnings=warnings,
    )
    k_df = _build_regime_event_counts(
        events_hourly=events_hourly,
        event_col=event_col,
        warnings=warnings,
    )
    regime_enters_df = _extract_regime_enter_events(
        events_hourly=events_hourly,
        event_col=event_col,
        warnings=warnings,
    )
    regime_segment_end_ts, regime_segment_end_source = _resolve_regime_segment_end_ts(
        run_dir=run_dir,
        signals_hourly=signals_hourly,
        events_hourly=events_hourly,
        warnings=warnings,
    )
    l_df = _build_regime_segments(
        regime_enters=regime_enters_df,
        segment_end_ts_utc=regime_segment_end_ts,
        warnings=warnings,
    )
    m_df = _build_regime_time_share(
        l_segments=l_df,
        warnings=warnings,
    )
    n_df = _build_signals_by_regime(
        signals_hourly=signals_hourly,
        signals_event_col=signals_event_col,
        regime_enters=regime_enters_df,
        warnings=warnings,
    )

    diagnostics_dir = run_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    out_a = diagnostics_dir / "A_perf_by_mode.csv"
    out_b = diagnostics_dir / "B_perf_by_session_bucket.csv"
    out_c = diagnostics_dir / "C_perf_by_hour_utc.csv"
    out_d = diagnostics_dir / "D_costR_percentiles.csv"
    out_e = diagnostics_dir / "E_blocks.csv"
    out_f = diagnostics_dir / "F_blocks_by_hour_utc.csv"
    out_g = diagnostics_dir / "G_signals_by_hour_utc.csv"
    out_h = diagnostics_dir / "H_perf_by_hour_robust.csv"
    out_i = diagnostics_dir / "I_perf_by_regime_at_entry.csv"
    out_j = diagnostics_dir / "J_signals_state_counts.csv"
    out_k = diagnostics_dir / "K_regime_event_counts.csv"
    out_l = diagnostics_dir / "L_regime_segments.csv"
    out_m = diagnostics_dir / "M_regime_time_share.csv"
    out_n = diagnostics_dir / "N_signals_by_regime.csv"
    out_o = diagnostics_dir / "O_trades_blocked_by_rule.csv"
    out_p = diagnostics_dir / "P_trades_blocked_by_hour.csv"
    out_md = diagnostics_dir / "diagnostics.md"

    a_df.to_csv(out_a, index=False)
    b_df.to_csv(out_b, index=False)
    c_df.to_csv(out_c, index=False)
    d_df.to_csv(out_d, index=False)
    e_df.to_csv(out_e, index=False)
    f_df.to_csv(out_f, index=False)
    g_df.to_csv(out_g, index=False)
    h_df.to_csv(out_h, index=False)
    i_df.to_csv(out_i, index=False)
    j_df.to_csv(out_j, index=False)
    k_df.to_csv(out_k, index=False)
    l_df.to_csv(out_l, index=False)
    m_df.to_csv(out_m, index=False)
    n_df.to_csv(out_n, index=False)
    o_df.to_csv(out_o, index=False)
    p_df.to_csv(out_p, index=False)

    resolved_meta_lines = [
        f"- run_dir: `{run_dir.as_posix()}`",
        f"- R column used: `{found['r_col']}`",
        f"- mode column used: `{found['mode_col']}`",
        f"- entry timestamp column used: `{found['entry_ts_col']}` (parsed as UTC; naive assumed UTC)",
        f"- signals timestamp column used: `{signals_ts_col}` (parsed as UTC; naive assumed UTC)",
        f"- signals state column used (J): `{signals_state_col}`",
        f"- events timestamp column used: `{events_ts_col}` (parsed as UTC; naive assumed UTC)",
        f"- session bucket source: `{'trades column ' + found['session_col'] if found['session_col'] else 'derived by hour (ASIA 00-07, MODE_SESSION 07-17, OFF_SESSION 17-24 UTC)'}`",
        f"- risk denominator source: `{found['risk_col'] if found['risk_col'] else 'abs(entry-sl)'}`",
        f"- event type source for blocks: `{event_col}`",
        f"- opportunities denominator: `{opportunities}` from `{denom_src}`",
        f"- opportunities by hour source (G/F): `{g_source}`",
        f"- regime enter events found (L/M/N): `{len(regime_enters_df)}`",
        f"- regime segment end_ts source (L/M): `{regime_segment_end_source}`",
    ]

    warning_lines = ["- none"] if not warnings else [f"- {w}" for w in warnings]

    md_parts = [
        "# Run Diagnostics",
        "",
        "## Resolved Columns & Rules",
        *resolved_meta_lines,
        "",
        "## Warnings",
        *warning_lines,
        "",
        "## A) Performance by Mode",
        _markdown_table(
            a_df,
            float_cols={"pf", "expectancy_R", "winrate", "avg_R"},
        ),
        "",
        "## B) Performance by Session Bucket",
        _markdown_table(
            b_df,
            float_cols={"pf", "expectancy_R", "winrate", "avg_R"},
        ),
        "",
        "## C) Performance by Hour UTC (60m)",
        _markdown_table(
            c_df,
            float_cols={"pf", "expectancy_R", "winrate", "avg_R"},
        ),
        "",
        "## D) Cost_R Percentiles",
        _markdown_table(
            d_df,
            float_cols={"cost_R_mean", "cost_R_p50", "cost_R_p75", "cost_R_p90"},
        ),
        "",
        "## E) Blocks",
        _markdown_table(
            e_df,
            float_cols={"pct_of_opportunities"},
        ),
        "",
        "## F) Blocks by Hour UTC",
        _markdown_table(
            f_df,
            float_cols={
                "SESSION_BLOCK_pct",
                "COST_FILTER_BLOCK_pct",
                "SHOCK_BLOCK_pct",
                "MAX_TRADES_pct",
            },
        ),
        "",
        "## G) Signals by Hour UTC",
        _markdown_table(
            g_df,
            float_cols=set(),
        ),
        "",
        "## H) Hour Robust Perf",
        _markdown_table(
            h_df,
            float_cols={"sum_R_pos", "sum_R_neg_abs", "pf", "expectancy_R", "winrate"},
        ),
        "",
        "## I) Perf by regime_at_entry",
        _markdown_table(
            i_df,
            float_cols={"pf", "expectancy_R", "winrate", "avg_R"},
        ),
        "",
        "## J) Signals state counts",
        _markdown_table(
            j_df,
            float_cols=set(),
        ),
        "",
        "## K) Regime event counts",
        _markdown_table(
            k_df,
            float_cols=set(),
        ),
        "",
        "## L) Regime segments",
        _markdown_table(
            l_df,
            float_cols={"duration_seconds", "duration_minutes"},
        ),
        "",
        "## M) Regime time share",
        _markdown_table(
            m_df,
            float_cols={"total_seconds", "share", "total_minutes", "pct_time", "avg_minutes", "p50_minutes", "p90_minutes"},
        ),
        "",
        "## N) Signals by regime",
        _markdown_table(
            n_df,
            float_cols=set(),
        ),
        "",
        "## O) Trades blocked by rule",
        _markdown_table(
            o_df,
            float_cols={"pct_of_opportunities"},
        ),
        "",
        "## P) Trades blocked by hour UTC",
        _markdown_table(
            p_df,
            float_cols=set(),
        ),
        "",
        "## Outputs",
        f"- `{out_a.as_posix()}`",
        f"- `{out_b.as_posix()}`",
        f"- `{out_c.as_posix()}`",
        f"- `{out_d.as_posix()}`",
        f"- `{out_e.as_posix()}`",
        f"- `{out_f.as_posix()}`",
        f"- `{out_g.as_posix()}`",
        f"- `{out_h.as_posix()}`",
        f"- `{out_i.as_posix()}`",
        f"- `{out_j.as_posix()}`",
        f"- `{out_k.as_posix()}`",
        f"- `{out_l.as_posix()}`",
        f"- `{out_m.as_posix()}`",
        f"- `{out_n.as_posix()}`",
        f"- `{out_o.as_posix()}`",
        f"- `{out_p.as_posix()}`",
        f"- `{out_md.as_posix()}`",
    ]
    out_md.write_text("\n".join(md_parts) + "\n", encoding="utf-8")

    print(f"Diagnostics generated in: {diagnostics_dir.as_posix()}")
    print(f"- {out_a.name}")
    print(f"- {out_b.name}")
    print(f"- {out_c.name}")
    print(f"- {out_d.name}")
    print(f"- {out_e.name}")
    print(f"- {out_f.name}")
    print(f"- {out_g.name}")
    print(f"- {out_h.name}")
    print(f"- {out_i.name}")
    print(f"- {out_j.name}")
    print(f"- {out_k.name}")
    print(f"- {out_l.name}")
    print(f"- {out_m.name}")
    print(f"- {out_n.name}")
    print(f"- {out_o.name}")
    print(f"- {out_p.name}")
    print(f"- {out_md.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate diagnostics tables A-N for a backtest run directory.")
    parser.add_argument(
        "run_dir",
        nargs="?",
        default=str(DEFAULT_RUN_DIR),
        help=f"Run directory path (default: {DEFAULT_RUN_DIR.as_posix()})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir.as_posix()}")
        return 2
    return diagnose_run(run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
