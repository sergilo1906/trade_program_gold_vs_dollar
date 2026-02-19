from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(slots=True)
class MetricsBundle:
    global_metrics: dict[str, Any]
    monthly: pd.DataFrame
    yearly: pd.DataFrame


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        if math.isfinite(out):
            return out
        return default
    except (TypeError, ValueError):
        return default


def _profit_factor(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    gross_win = float(pnl[pnl > 0].sum())
    gross_loss = float((-pnl[pnl < 0]).sum())
    if gross_loss <= 0:
        return float("inf") if gross_win > 0 else 0.0
    return gross_win / gross_loss


def _max_drawdown_from_equity(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = (peak - equity) / peak.replace(0.0, pd.NA)
    dd = dd.fillna(0.0)
    return float(dd.max())


def _ensure_trade_types(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    df = trades.copy()
    if "entry_time" in df.columns:
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
    if "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    for col in ("pnl", "r_multiple", "mae_r", "mfe_r", "risk_amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "trade_id" in df.columns:
        df["trade_id"] = pd.to_numeric(df["trade_id"], errors="coerce").fillna(0).astype(int)
    return df


def equity_curve_from_trades(trades: pd.DataFrame, starting_equity: float) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame({"timestamp": [pd.NaT], "equity": [starting_equity]})
    df = _ensure_trade_types(trades).sort_values("exit_time").copy()
    eq = starting_equity
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        eq += _safe_float(row.get("pnl"))
        rows.append({"timestamp": row.get("exit_time"), "equity": eq})
    return pd.DataFrame(rows)


def compute_global_metrics(
    trades: pd.DataFrame,
    starting_equity: float,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> dict[str, Any]:
    df = _ensure_trade_types(trades)
    if df.empty:
        months = max(1.0, (period_end - period_start).days / 30.4375) if pd.notna(period_start) and pd.notna(period_end) else 1.0
        return {
            "final_equity": starting_equity,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
            "payoff_ratio": 0.0,
            "expectancy_R": 0.0,
            "avg_win_R": 0.0,
            "avg_loss_R": 0.0,
            "trades": 0,
            "trades_per_month": 0.0,
            "mae_r_mean": 0.0,
            "mae_r_median": 0.0,
            "mae_r_p90": 0.0,
            "mfe_r_mean": 0.0,
            "mfe_r_median": 0.0,
            "mfe_r_p90": 0.0,
            "months": months,
        }

    df = df.sort_values("exit_time")
    pnl = df["pnl"]
    final_equity = starting_equity + float(pnl.sum())
    total_return = (final_equity / starting_equity) - 1.0 if starting_equity > 0 else 0.0
    curve = equity_curve_from_trades(df, starting_equity)
    mdd = _max_drawdown_from_equity(curve["equity"])
    pf = _profit_factor(pnl)

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] < 0]
    winrate = float(len(wins) / len(df)) if len(df) > 0 else 0.0
    avg_win = float(wins["pnl"].mean()) if not wins.empty else 0.0
    avg_loss = float(losses["pnl"].mean()) if not losses.empty else 0.0
    payoff_ratio = (avg_win / abs(avg_loss)) if avg_loss < 0 else 0.0

    expectancy_r = float(df["r_multiple"].mean()) if "r_multiple" in df.columns and not df.empty else 0.0
    avg_win_r = float(df.loc[df["r_multiple"] > 0, "r_multiple"].mean()) if "r_multiple" in df.columns else 0.0
    avg_loss_r = float(df.loc[df["r_multiple"] < 0, "r_multiple"].mean()) if "r_multiple" in df.columns else 0.0

    mae_series = df["mae_r"] if "mae_r" in df.columns else pd.Series(dtype="float64")
    mfe_series = df["mfe_r"] if "mfe_r" in df.columns else pd.Series(dtype="float64")

    period_days = max(1.0, float((period_end - period_start).days)) if pd.notna(period_start) and pd.notna(period_end) else 30.0
    months = max(1.0, period_days / 30.4375)

    return {
        "final_equity": final_equity,
        "total_return": total_return,
        "max_drawdown": mdd,
        "profit_factor": pf,
        "winrate": winrate,
        "payoff_ratio": payoff_ratio,
        "expectancy_R": expectancy_r,
        "avg_win_R": avg_win_r if pd.notna(avg_win_r) else 0.0,
        "avg_loss_R": avg_loss_r if pd.notna(avg_loss_r) else 0.0,
        "trades": int(len(df)),
        "trades_per_month": float(len(df) / months),
        "mae_r_mean": float(mae_series.mean()) if not mae_series.empty else 0.0,
        "mae_r_median": float(mae_series.median()) if not mae_series.empty else 0.0,
        "mae_r_p90": float(mae_series.quantile(0.90)) if not mae_series.empty else 0.0,
        "mfe_r_mean": float(mfe_series.mean()) if not mfe_series.empty else 0.0,
        "mfe_r_median": float(mfe_series.median()) if not mfe_series.empty else 0.0,
        "mfe_r_p90": float(mfe_series.quantile(0.90)) if not mfe_series.empty else 0.0,
        "months": months,
    }


def build_monthly_metrics(
    trades: pd.DataFrame,
    starting_equity: float,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> pd.DataFrame:
    if pd.isna(period_start) or pd.isna(period_end):
        return pd.DataFrame()
    df = _ensure_trade_types(trades)
    months = pd.period_range(period_start.to_period("M"), period_end.to_period("M"), freq="M")
    rows: list[dict[str, Any]] = []
    running_eq = starting_equity
    for month in months:
        m_start = month.start_time
        m_end = month.end_time
        if df.empty:
            m_trades = df
        else:
            m_trades = df[(df["exit_time"] >= m_start) & (df["exit_time"] <= m_end)]

        month_pnl = float(m_trades["pnl"].sum()) if not m_trades.empty else 0.0
        month_pf = _profit_factor(m_trades["pnl"]) if not m_trades.empty else 0.0
        month_curve = equity_curve_from_trades(m_trades, running_eq) if not m_trades.empty else pd.DataFrame({"equity": [running_eq]})
        month_dd = _max_drawdown_from_equity(month_curve["equity"]) if not month_curve.empty else 0.0
        eq_start = running_eq
        eq_end = running_eq + month_pnl
        compounded_return = (eq_end / eq_start - 1.0) if eq_start > 0 else 0.0
        simple_return = (month_pnl / starting_equity) if starting_equity > 0 else 0.0

        rows.append(
            {
                "month": str(month),
                "return_compounded": compounded_return,
                "return_simple": simple_return,
                "profit_factor": month_pf,
                "max_drawdown": month_dd,
                "trades": int(len(m_trades)),
                "pnl": month_pnl,
                "equity_start": eq_start,
                "equity_end": eq_end,
            }
        )
        running_eq = eq_end

    return pd.DataFrame(rows)


def build_yearly_metrics(
    trades: pd.DataFrame,
    starting_equity: float,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> pd.DataFrame:
    if pd.isna(period_start) or pd.isna(period_end):
        return pd.DataFrame()
    df = _ensure_trade_types(trades)
    years = list(range(period_start.year, period_end.year + 1))
    rows: list[dict[str, Any]] = []
    running_eq = starting_equity
    for y in years:
        start = pd.Timestamp(year=y, month=1, day=1)
        end = pd.Timestamp(year=y, month=12, day=31, hour=23, minute=59, second=59)
        if df.empty:
            y_trades = df
        else:
            y_trades = df[(df["exit_time"] >= start) & (df["exit_time"] <= end)]
        y_pnl = float(y_trades["pnl"].sum()) if not y_trades.empty else 0.0
        y_pf = _profit_factor(y_trades["pnl"]) if not y_trades.empty else 0.0
        y_curve = equity_curve_from_trades(y_trades, running_eq) if not y_trades.empty else pd.DataFrame({"equity": [running_eq]})
        y_dd = _max_drawdown_from_equity(y_curve["equity"]) if not y_curve.empty else 0.0
        eq_start = running_eq
        eq_end = running_eq + y_pnl
        y_ret = (eq_end / eq_start - 1.0) if eq_start > 0 else 0.0
        rows.append(
            {
                "year": y,
                "return": y_ret,
                "profit_factor": y_pf,
                "max_drawdown": y_dd,
                "trades": int(len(y_trades)),
                "pnl": y_pnl,
                "equity_start": eq_start,
                "equity_end": eq_end,
            }
        )
        running_eq = eq_end
    return pd.DataFrame(rows)


def compute_metrics_bundle(
    trades: pd.DataFrame,
    starting_equity: float,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> MetricsBundle:
    global_metrics = compute_global_metrics(trades, starting_equity, period_start, period_end)
    monthly = build_monthly_metrics(trades, starting_equity, period_start, period_end)
    yearly = build_yearly_metrics(trades, starting_equity, period_start, period_end)
    return MetricsBundle(global_metrics=global_metrics, monthly=monthly, yearly=yearly)


def monthly_health(monthly: pd.DataFrame) -> dict[str, Any]:
    if monthly.empty:
        return {
            "positive_months_pct": 0.0,
            "max_negative_streak": 0,
            "best_month": None,
            "worst_month": None,
            "avg_monthly_return": 0.0,
            "median_monthly_return": 0.0,
            "pct_months_ge_4": 0.0,
            "pct_months_ge_8": 0.0,
        }

    pos = int((monthly["return_compounded"] > 0).sum())
    total = int(len(monthly))
    positive_pct = pos / total if total > 0 else 0.0

    max_streak = 0
    cur = 0
    for value in monthly["return_compounded"].tolist():
        if value < 0:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 0

    best_idx = monthly["return_compounded"].idxmax()
    worst_idx = monthly["return_compounded"].idxmin()
    best_month = monthly.loc[best_idx, "month"] if pd.notna(best_idx) else None
    worst_month = monthly.loc[worst_idx, "month"] if pd.notna(worst_idx) else None
    avg_monthly_return = float(monthly["return_compounded"].mean())
    median_monthly_return = float(monthly["return_compounded"].median())
    pct_months_ge_4 = float((monthly["return_compounded"] >= 0.04).mean())
    pct_months_ge_8 = float((monthly["return_compounded"] >= 0.08).mean())
    return {
        "positive_months_pct": positive_pct,
        "max_negative_streak": max_streak,
        "best_month": best_month,
        "worst_month": worst_month,
        "avg_monthly_return": avg_monthly_return,
        "median_monthly_return": median_monthly_return,
        "pct_months_ge_4": pct_months_ge_4,
        "pct_months_ge_8": pct_months_ge_8,
    }


def mode_performance(trades: pd.DataFrame, starting_equity: float) -> pd.DataFrame:
    df = _ensure_trade_types(trades)
    if df.empty or ("mode" not in df.columns):
        return pd.DataFrame(columns=["mode", "trades", "return", "profit_factor", "winrate", "expectancy_R"])

    rows: list[dict[str, Any]] = []
    for mode in sorted(df["mode"].fillna("UNKNOWN").astype(str).unique().tolist()):
        sub = df[df["mode"].fillna("UNKNOWN").astype(str) == mode].copy()
        if sub.empty:
            continue
        pnl = sub["pnl"]
        wins = sub[sub["pnl"] > 0]
        rows.append(
            {
                "mode": mode,
                "trades": int(len(sub)),
                "return": float(pnl.sum() / starting_equity) if starting_equity > 0 else 0.0,
                "profit_factor": _profit_factor(pnl),
                "winrate": float(len(wins) / len(sub)) if len(sub) > 0 else 0.0,
                "expectancy_R": float(sub["r_multiple"].mean()) if "r_multiple" in sub.columns else 0.0,
            }
        )
    return pd.DataFrame(rows)


def block_summary(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty or ("event_type" not in events.columns):
        return pd.DataFrame(
            [
                {"block_type": "COST_FILTER_BLOCK", "count": 0},
                {"block_type": "SESSION_BLOCK", "count": 0},
                {"block_type": "SHOCK_BLOCK", "count": 0},
                {"block_type": "BLOCKED_MAX_TRADES_DAY", "count": 0},
                {"block_type": "MAX_TRADES_BLOCK", "count": 0},
                {"block_type": "HOUR_BLACKLIST", "count": 0},
                {"block_type": "HOUR_NOT_IN_WHITELIST", "count": 0},
                {"block_type": "COST_GATE_OVERRIDE_HOUR", "count": 0},
            ]
        )
    text = events["event_type"].fillna("").astype(str).str.upper()
    counts = text.value_counts().to_dict()
    max_trades_count = int(counts.get("BLOCKED_MAX_TRADES_DAY", 0))
    hour_blacklist_count = int(text.str.contains("HOUR_BLACKLIST", regex=False).sum())
    hour_whitelist_count = int(text.str.contains("HOUR_NOT_IN_WHITELIST", regex=False).sum())
    cost_override_count = int(
        (
            text.str.contains("COST_GATE_OVERRIDE_HOUR", regex=False)
            | text.str.contains("COST_FILTER_BLOCK_OVERRIDE_HOUR", regex=False)
        ).sum()
    )
    rows = [
        {"block_type": "COST_FILTER_BLOCK", "count": int(text.str.contains("COST_FILTER_BLOCK", regex=False).sum())},
        {"block_type": "SESSION_BLOCK", "count": int(text.str.contains("SESSION_BLOCK", regex=False).sum())},
        {"block_type": "SHOCK_BLOCK", "count": int(text.str.contains("SHOCK_BLOCK", regex=False).sum())},
        {"block_type": "BLOCKED_MAX_TRADES_DAY", "count": max_trades_count},
        {"block_type": "MAX_TRADES_BLOCK", "count": max_trades_count},
        {"block_type": "HOUR_BLACKLIST", "count": hour_blacklist_count},
        {"block_type": "HOUR_NOT_IN_WHITELIST", "count": hour_whitelist_count},
        {"block_type": "COST_GATE_OVERRIDE_HOUR", "count": cost_override_count},
    ]
    return pd.DataFrame(rows)


def average_entry_cost_multiplier(fills: pd.DataFrame) -> float:
    if fills.empty or ("fill_type" not in fills.columns):
        return 1.0
    df = fills.copy()
    df["fill_type"] = df["fill_type"].astype(str)
    if "cost_multiplier" not in df.columns:
        return 1.0
    entry = df[df["fill_type"] == "ENTRY"].copy()
    if entry.empty:
        return 1.0
    entry["cost_multiplier"] = pd.to_numeric(entry["cost_multiplier"], errors="coerce").fillna(1.0)
    return float(entry["cost_multiplier"].mean())


def monte_carlo_execution(
    trades: pd.DataFrame,
    fills: pd.DataFrame,
    starting_equity: float,
    sims: int,
    seed: int,
    spread_low: float = 0.30,
    spread_high: float = 0.70,
    slip_low: float = 0.00,
    slip_high: float = 0.15,
) -> dict[str, Any]:
    trades_df = _ensure_trade_types(trades)
    if trades_df.empty or fills.empty:
        return {
            "sims": sims,
            "return_p5": 0.0,
            "return_p50": 0.0,
            "return_p95": 0.0,
            "dd_p5": 0.0,
            "dd_p50": 0.0,
            "dd_p95": 0.0,
            "positive_pct": 0.0,
        }

    fills_df = fills.copy()
    fills_df["trade_id"] = pd.to_numeric(fills_df["trade_id"], errors="coerce").fillna(0).astype(int)
    fills_df["mid_price"] = pd.to_numeric(fills_df["mid_price"], errors="coerce").fillna(0.0)
    fills_df["qty"] = pd.to_numeric(fills_df["qty"], errors="coerce").fillna(0.0)
    fills_df["timestamp"] = pd.to_datetime(fills_df["timestamp"], errors="coerce")
    fills_df = fills_df.sort_values(["timestamp", "fill_id"])

    trade_order = trades_df.sort_values("entry_time")["trade_id"].tolist()
    trades_compact: list[dict[str, Any]] = []
    for trade_id in trade_order:
        tf = fills_df[fills_df["trade_id"] == trade_id]
        if tf.empty:
            continue
        entry = tf[tf["fill_type"] == "ENTRY"]
        exits = tf[tf["fill_type"].isin(["PARTIAL", "EXIT"])]
        if entry.empty or exits.empty:
            continue
        erow = entry.iloc[0]
        entry_side = str(erow["side"]).upper()
        entry_mid = float(erow["mid_price"])
        exit_parts = [(float(r["mid_price"]), float(r["qty"])) for _, r in exits.iterrows()]
        trades_compact.append(
            {
                "entry_side": entry_side,
                "entry_mid": entry_mid,
                "exits": exit_parts,
            }
        )

    if not trades_compact:
        return {
            "sims": sims,
            "return_p5": 0.0,
            "return_p50": 0.0,
            "return_p95": 0.0,
            "dd_p5": 0.0,
            "dd_p50": 0.0,
            "dd_p95": 0.0,
            "positive_pct": 0.0,
        }

    rng = random.Random(seed)
    returns: list[float] = []
    dds: list[float] = []

    def fill_price(mid: float, side: str, spread: float, slip: float) -> float:
        if side == "BUY":
            return mid + (spread / 2.0) + slip
        return mid - (spread / 2.0) - slip

    for _ in range(max(1, sims)):
        eq = starting_equity
        peak = eq
        max_dd = 0.0
        for t in trades_compact:
            spread = rng.uniform(spread_low, spread_high)
            slip = rng.uniform(slip_low, slip_high)
            entry_side = str(t["entry_side"])
            entry_mid = float(t["entry_mid"])
            entry_fill = fill_price(entry_mid, entry_side, spread, slip)

            trade_pnl = 0.0
            for exit_mid, qty in t["exits"]:
                if entry_side == "BUY":
                    exit_fill = fill_price(exit_mid, "SELL", spread, slip)
                    trade_pnl += (exit_fill - entry_fill) * qty
                else:
                    exit_fill = fill_price(exit_mid, "BUY", spread, slip)
                    trade_pnl += (entry_fill - exit_fill) * qty

            eq += trade_pnl
            peak = max(peak, eq)
            dd = (peak - eq) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        returns.append((eq / starting_equity) - 1.0 if starting_equity > 0 else 0.0)
        dds.append(max_dd)

    return {
        "sims": max(1, sims),
        "return_p5": float(pd.Series(returns).quantile(0.05)),
        "return_p50": float(pd.Series(returns).quantile(0.50)),
        "return_p95": float(pd.Series(returns).quantile(0.95)),
        "dd_p5": float(pd.Series(dds).quantile(0.05)),
        "dd_p50": float(pd.Series(dds).quantile(0.50)),
        "dd_p95": float(pd.Series(dds).quantile(0.95)),
        "positive_pct": float((pd.Series(returns) > 0).mean()),
    }


def markdown_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data_"
    float_cols = float_cols or set()
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        values: list[str] = []
        for h in headers:
            value = row[h]
            if h in float_cols:
                values.append(f"{_safe_float(value):.4f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)
