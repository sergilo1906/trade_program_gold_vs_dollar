from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


R_COL_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)

TS_COL_CANDIDATES = (
    "entry_time",
    "open_time",
    "entry_ts",
    "timestamp",
    "time",
    "ts",
)


def _norm_path(value: str | Path) -> str:
    return str(value).replace("\\", "/").strip().lower()


def _find_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        col = lowered.get(str(cand).lower())
        if col is not None:
            return col
    return None


def _as_bool(value: Any) -> bool | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _safe_float(value: Any) -> float:
    try:
        out = float(value)
    except Exception:
        return math.nan
    if not math.isfinite(out):
        return math.nan
    return out


def _profit_factor(r: pd.Series) -> float:
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss <= 0.0:
        return float("inf") if gross_win > 0 else math.nan
    return gross_win / gross_loss


def _max_drawdown_r(r: pd.Series) -> float:
    if r.empty:
        return math.nan
    cum = r.cumsum()
    peak = cum.cummax()
    dd = peak - cum
    return float(dd.max()) if not dd.empty else math.nan


def _retention_vs_baseline(trades: int, baseline_trades: int) -> float:
    if baseline_trades <= 0:
        return math.nan
    return float(100.0 * float(trades) / float(baseline_trades))


def load_trade_kpis(run_dir: Path) -> dict[str, Any]:
    trades_path = run_dir / "trades.csv"
    out: dict[str, Any] = {
        "trade_status": "ok",
        "trades": 0,
        "winrate": math.nan,
        "expectancy_R": math.nan,
        "median_R": math.nan,
        "sum_R": math.nan,
        "pf": math.nan,
        "max_drawdown_r": math.nan,
        "active_months": math.nan,
        "active_years": math.nan,
        "r_col": "",
        "ts_col": "",
    }
    if not trades_path.exists():
        out["trade_status"] = "missing_trades"
        return out

    trades = pd.read_csv(trades_path)
    if trades.empty:
        out["trade_status"] = "empty_trades"
        return out

    r_col = _find_col(trades, R_COL_CANDIDATES)
    if r_col is None:
        out["trade_status"] = "missing_r_col"
        return out

    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    if r.empty:
        out["trade_status"] = "invalid_r_col"
        return out

    ts_col = _find_col(trades, TS_COL_CANDIDATES)
    active_months = math.nan
    active_years = math.nan
    if ts_col is not None:
        ts = pd.to_datetime(trades[ts_col], errors="coerce", utc=True).dropna()
        if not ts.empty:
            active_months = float(ts.dt.to_period("M").nunique())
            active_years = float(ts.dt.year.nunique())

    out.update(
        {
            "trades": int(r.size),
            "winrate": float((r > 0).mean()),
            "expectancy_R": float(r.mean()),
            "median_R": float(r.median()),
            "sum_R": float(r.sum()),
            "pf": float(_profit_factor(r)),
            "max_drawdown_r": float(_max_drawdown_r(r)),
            "active_months": active_months,
            "active_years": active_years,
            "r_col": str(r_col),
            "ts_col": str(ts_col) if ts_col is not None else "",
        }
    )
    return out


def load_boot_ci(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "diagnostics" / "BOOT_expectancy_ci.csv"
    out: dict[str, Any] = {
        "boot_status": "ok",
        "ci_low": math.nan,
        "ci_high": math.nan,
        "crosses_zero": None,
        "boot_resamples_used": math.nan,
    }
    if not p.exists():
        out["boot_status"] = "missing_boot"
        return out

    df = pd.read_csv(p)
    if df.empty:
        out["boot_status"] = "empty_boot"
        return out

    row = df.iloc[0]
    out["ci_low"] = _safe_float(row.get("ci_low"))
    out["ci_high"] = _safe_float(row.get("ci_high"))
    out["crosses_zero"] = _as_bool(row.get("crosses_zero"))
    out["boot_resamples_used"] = _safe_float(row.get("resamples"))
    return out


def load_cost_stress(posthoc_csv: Path | None, run_id: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "cost_status": "not_requested",
        "cost_survives_1p2": None,
        "cost_survives_1p5": None,
    }
    if posthoc_csv is None:
        return out
    if not posthoc_csv.exists():
        out["cost_status"] = "missing_posthoc_csv"
        return out

    df = pd.read_csv(posthoc_csv)
    if df.empty:
        out["cost_status"] = "empty_posthoc_csv"
        return out
    if "run_id" not in df.columns or "factor" not in df.columns:
        out["cost_status"] = "invalid_posthoc_schema"
        return out

    sub = df[df["run_id"].astype(str) == str(run_id)].copy()
    if sub.empty:
        out["cost_status"] = "run_not_found"
        return out

    out["cost_status"] = "ok"

    def _factor_pass(factor: float) -> bool | None:
        m = sub[pd.to_numeric(sub["factor"], errors="coerce").round(2).eq(round(factor, 2))]
        if m.empty:
            return None
        row = m.iloc[0]
        pf = _safe_float(row.get("pf"))
        expectancy = _safe_float(row.get("expectancy_R"))
        if pd.isna(pf) or pd.isna(expectancy):
            return None
        return bool((pf > 1.0) and (expectancy > 0.0))

    out["cost_survives_1p2"] = _factor_pass(1.2)
    out["cost_survives_1p5"] = _factor_pass(1.5)
    return out


def load_temporal_flags(temporal_summary_json: Path | None, run_id: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "temporal_status": "not_requested",
        "temporal_pass": None,
        "segments_negative": math.nan,
        "years_negative": math.nan,
        "hours_negative_ge10": math.nan,
        "fragility_notes": "",
    }
    if temporal_summary_json is None:
        return out
    if not temporal_summary_json.exists():
        out["temporal_status"] = "missing_temporal_summary"
        return out

    payload = json.loads(temporal_summary_json.read_text(encoding="utf-8"))
    summary_by_run = payload.get("summary_by_run", [])
    if not isinstance(summary_by_run, list):
        out["temporal_status"] = "invalid_temporal_summary"
        return out

    found = None
    for item in summary_by_run:
        if str(item.get("run_id", "")) == str(run_id):
            found = item
            break
    if found is None:
        out["temporal_status"] = "run_not_found"
        return out

    seg_neg = _safe_float(found.get("segments_negative"))
    years_neg = _safe_float(found.get("years_negative"))
    hours_neg = _safe_float(found.get("hours_negative_ge10"))
    notes: list[str] = []
    if pd.notna(seg_neg) and seg_neg > 0:
        notes.append(f"segments_negative={int(seg_neg)}")
    if pd.notna(years_neg) and years_neg > 0:
        notes.append(f"years_negative={int(years_neg)}")
    if pd.notna(hours_neg) and hours_neg > 0:
        notes.append(f"hours_negative_ge10={int(hours_neg)}")

    out.update(
        {
            "temporal_status": "ok",
            "temporal_pass": bool(
                (pd.notna(seg_neg) and seg_neg <= 0)
                and (pd.notna(years_neg) and years_neg <= 0)
                and (pd.notna(hours_neg) and hours_neg <= 0)
            ),
            "segments_negative": seg_neg,
            "years_negative": years_neg,
            "hours_negative_ge10": hours_neg,
            "fragility_notes": "; ".join(notes),
        }
    )
    return out


def load_gates_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing gates config: {path.as_posix()}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Gates config must be a YAML mapping.")
    if "stages" not in payload or not isinstance(payload.get("stages"), dict):
        raise ValueError("Gates config must define stages mapping.")
    return payload


def resolve_stage_config(gates_cfg: dict[str, Any], stage: str) -> dict[str, Any]:
    stages = gates_cfg.get("stages", {})
    if stage in stages and isinstance(stages[stage], dict):
        return dict(stages[stage])
    default_stage = str(gates_cfg.get("default_stage", "dev_fast"))
    if default_stage in stages and isinstance(stages[default_stage], dict):
        return dict(stages[default_stage])
    raise ValueError(f"Stage `{stage}` not found in gates config and no valid default_stage present.")


def apply_gates(
    metrics: dict[str, Any],
    stage_cfg: dict[str, Any],
    baseline_trades: int,
    *,
    stage_name: str,
) -> dict[str, Any]:
    robust = str(stage_name).strip().lower() == "dev_robust"
    gate_flags: dict[str, bool] = {}
    fail_reasons: list[str] = []
    pending_metrics: list[str] = []

    def _on_missing(metric_name: str, gate_name: str) -> bool:
        pending_metrics.append(metric_name)
        if robust:
            fail_reasons.append(f"{gate_name}: missing metric `{metric_name}`")
            return False
        return True

    def _gate_min(gate_name: str, metric_name: str, threshold: Any, value: Any) -> None:
        if threshold is None:
            return
        fv = _safe_float(value)
        ft = _safe_float(threshold)
        if pd.isna(fv):
            gate_flags[gate_name] = _on_missing(metric_name, gate_name)
            return
        gate_flags[gate_name] = bool(fv >= ft)
        if not gate_flags[gate_name]:
            fail_reasons.append(f"{gate_name}: {metric_name}={fv:.6f} < {ft:.6f}")

    def _gate_max(gate_name: str, metric_name: str, threshold: Any, value: Any) -> None:
        if threshold is None:
            return
        fv = _safe_float(value)
        ft = _safe_float(threshold)
        if pd.isna(fv):
            gate_flags[gate_name] = _on_missing(metric_name, gate_name)
            return
        gate_flags[gate_name] = bool(fv <= ft)
        if not gate_flags[gate_name]:
            fail_reasons.append(f"{gate_name}: {metric_name}={fv:.6f} > {ft:.6f}")

    _gate_min("gate_min_trades", "trades", stage_cfg.get("min_trades"), metrics.get("trades"))
    _gate_min("gate_min_pf", "pf", stage_cfg.get("min_pf"), metrics.get("pf"))
    _gate_min(
        "gate_min_expectancy_r",
        "expectancy_R",
        stage_cfg.get("min_expectancy_r"),
        metrics.get("expectancy_R"),
    )

    if bool(stage_cfg.get("require_ci_non_crossing_zero", False)):
        cz = metrics.get("crosses_zero")
        if cz is None:
            gate_flags["gate_ci_non_crossing_zero"] = _on_missing("crosses_zero", "gate_ci_non_crossing_zero")
        else:
            gate_flags["gate_ci_non_crossing_zero"] = bool(cz is False)
            if not gate_flags["gate_ci_non_crossing_zero"]:
                fail_reasons.append("gate_ci_non_crossing_zero: CI crosses zero")

    min_ret = stage_cfg.get("min_retention_vs_baseline_pct")
    if min_ret is not None:
        if baseline_trades <= 0:
            gate_flags["gate_min_retention"] = _on_missing("baseline_trades", "gate_min_retention")
        else:
            _gate_min(
                "gate_min_retention",
                "retention_vs_b4_pct",
                min_ret,
                metrics.get("retention_vs_b4_pct"),
            )

    if bool(stage_cfg.get("require_cost_stress_survival_p20", False)):
        v = metrics.get("cost_survives_1p2")
        if v is None:
            gate_flags["gate_cost_p20"] = _on_missing("cost_survives_1p2", "gate_cost_p20")
        else:
            gate_flags["gate_cost_p20"] = bool(v)
            if not gate_flags["gate_cost_p20"]:
                fail_reasons.append("gate_cost_p20: fails +20% cost stress")

    if bool(stage_cfg.get("require_cost_stress_survival_p50", False)):
        v = metrics.get("cost_survives_1p5")
        if v is None:
            gate_flags["gate_cost_p50"] = _on_missing("cost_survives_1p5", "gate_cost_p50")
        else:
            gate_flags["gate_cost_p50"] = bool(v)
            if not gate_flags["gate_cost_p50"]:
                fail_reasons.append("gate_cost_p50: fails +50% cost stress")

    if bool(stage_cfg.get("require_temporal_stability", False)):
        v = metrics.get("temporal_pass")
        if v is None:
            gate_flags["gate_temporal"] = _on_missing("temporal_pass", "gate_temporal")
        else:
            gate_flags["gate_temporal"] = bool(v)
            if not gate_flags["gate_temporal"]:
                fail_reasons.append("gate_temporal: temporal fragility detected")

    _gate_max(
        "gate_max_drawdown_r",
        "max_drawdown_r",
        stage_cfg.get("max_drawdown_r"),
        metrics.get("max_drawdown_r"),
    )
    _gate_min(
        "gate_min_years_active",
        "active_years",
        stage_cfg.get("min_years_active"),
        metrics.get("active_years"),
    )
    _gate_min(
        "gate_min_months_with_trades",
        "active_months",
        stage_cfg.get("min_months_with_trades"),
        metrics.get("active_months"),
    )

    gate_all = bool(all(v is True for v in gate_flags.values())) if gate_flags else True
    return {
        "gate_all": gate_all,
        "gate_flags": gate_flags,
        "fail_reasons": fail_reasons,
        "pending_metrics": sorted(set(pending_metrics)),
    }


def build_score_row(
    *,
    candidate: str,
    config_path: Path,
    run_id: str,
    status: str,
    is_baseline: bool,
    metrics: dict[str, Any],
    gate_result: dict[str, Any] | None,
    note: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate": candidate,
        "config": config_path.as_posix(),
        "is_baseline": bool(is_baseline),
        "run_id": run_id,
        "status": status,
        "pf": metrics.get("pf", math.nan),
        "expectancy_R": metrics.get("expectancy_R", math.nan),
        "trades": metrics.get("trades", 0),
        "winrate": metrics.get("winrate", math.nan),
        "median_R": metrics.get("median_R", math.nan),
        "sum_R": metrics.get("sum_R", math.nan),
        "max_drawdown_r": metrics.get("max_drawdown_r", math.nan),
        "ci_low": metrics.get("ci_low", math.nan),
        "ci_high": metrics.get("ci_high", math.nan),
        "crosses_zero": metrics.get("crosses_zero", None),
        "boot_resamples_used": metrics.get("boot_resamples_used", math.nan),
        "retention_vs_b4_pct": metrics.get("retention_vs_b4_pct", math.nan),
        "active_months": metrics.get("active_months", math.nan),
        "active_years": metrics.get("active_years", math.nan),
        "cost_survives_1p2": metrics.get("cost_survives_1p2", None),
        "cost_survives_1p5": metrics.get("cost_survives_1p5", None),
        "temporal_pass": metrics.get("temporal_pass", None),
        "segments_negative": metrics.get("segments_negative", math.nan),
        "years_negative": metrics.get("years_negative", math.nan),
        "hours_negative_ge10": metrics.get("hours_negative_ge10", math.nan),
        "fragility_notes": metrics.get("fragility_notes", ""),
        "gate_min_trades": None,
        "gate_min_pf": None,
        "gate_min_expectancy_r": None,
        "gate_ci_non_crossing_zero": None,
        "gate_min_retention": None,
        "gate_cost_p20": None,
        "gate_cost_p50": None,
        "gate_temporal": None,
        "gate_max_drawdown_r": None,
        "gate_min_years_active": None,
        "gate_min_months_with_trades": None,
        "gate_all": None,
        "fail_reasons": "",
        "pending_metrics": "",
        "note": note,
    }
    if gate_result is None:
        return row

    gate_flags = gate_result.get("gate_flags", {})
    for key in (
        "gate_min_trades",
        "gate_min_pf",
        "gate_min_expectancy_r",
        "gate_ci_non_crossing_zero",
        "gate_min_retention",
        "gate_cost_p20",
        "gate_cost_p50",
        "gate_temporal",
        "gate_max_drawdown_r",
        "gate_min_years_active",
        "gate_min_months_with_trades",
    ):
        row[key] = gate_flags.get(key, None)

    row["gate_all"] = bool(gate_result.get("gate_all", False))
    row["fail_reasons"] = "; ".join(gate_result.get("fail_reasons", []))
    row["pending_metrics"] = "; ".join(gate_result.get("pending_metrics", []))
    return row


def merge_metric_payload(
    *,
    trade_kpis: dict[str, Any],
    boot_kpis: dict[str, Any],
    cost_kpis: dict[str, Any],
    temporal_kpis: dict[str, Any],
    baseline_trades: int,
) -> dict[str, Any]:
    merged = dict(trade_kpis)
    merged.update(boot_kpis)
    merged.update(cost_kpis)
    merged.update(temporal_kpis)
    merged["retention_vs_b4_pct"] = _retention_vs_baseline(
        trades=int(merged.get("trades", 0) or 0),
        baseline_trades=int(baseline_trades),
    )
    return merged


def config_key(path: str | Path) -> str:
    p = Path(path) if not isinstance(path, Path) else path
    return _norm_path(p.as_posix())


def data_key(path: str | Path) -> str:
    p = Path(path) if not isinstance(path, Path) else path
    return _norm_path(p.as_posix())
