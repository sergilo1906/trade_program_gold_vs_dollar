from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "output_dir": "output",
    "runs_output_dir": "outputs/runs",
    "starting_balance": 10000.0,
    "risk_per_trade_pct": 0.005,
    "ema_h1_fast": 50,
    "ema_h1_slow": 200,
    "ema_m15": 20,
    "ema_m5": 20,
    "rsi_period_m15": 14,
    "atr_period": 14,
    "h1_bias_slope_lookback": 3,
    "h1_bias_atr_mult": 0.10,
    "h1_min_sep_atr_mult": 0.25,
    "h1_slope_min_atr_mult": 0.05,
    "h1_range_max_sep_atr_mult": 0.20,
    "h1_range_max_slope_atr_mult": 0.05,
    "atr_rel_lookback": 20,
    "atr_rel_trend_min": 1.05,
    "atr_rel_range_max": 0.95,
    "atr_rel_dead_max": 0.70,
    "regime_trend_enter_score": 3,
    "regime_trend_exit_score": 2,
    "regime_range_enter_score": 3,
    "regime_range_exit_score": 2,
    "trend_min_bars_m15": 4,
    "range_min_bars_m15": 4,
    "shock_threshold": 3.0,
    "shock_cooldown_bars": 12,
    "confirm_valid_m15_bars": 3,
    "bos_lookback": 5,
    "body_ratio": 0.70,
    "wick_ratio_max": 0.20,
    "rsi_pullback_long_max": 35.0,
    "rsi_recover_long_min": 40.0,
    "rsi_pullback_short_min": 65.0,
    "rsi_recover_short_max": 60.0,
    "max_trades_per_day": 2,
    "swing_lookback": 6,
    "atr_floor_mult": 0.80,
    "sl_buffer_mult": 0.10,
    "tp1_r": 1.5,
    "partial_pct": 0.50,
    "trailing_mult": 2.5,
    "trailing_mult_phase1": 2.0,
    "trailing_mult_phase2": 1.0,
    "be_after_r": 2.0,
    "time_stop_bars": 12,
    "time_stop_min_r": 0.50,
    "cooldown_after_trade_bars": 6,
    "strategy_family": "AUTO",
    "enable_strategy_v3": False,
    "v4_session_orb": {
        "asia_start": "00:00",
        "asia_end": "06:00",
        "trade_start": "07:00",
        "trade_end": "10:00",
        "buffer_atr_mult": 0.05,
        "stop_buffer_atr_mult": 0.0,
        "atr_period": 14,
        "rr": 1.5,
        "time_stop": True,
        "exit_at_trade_end": True,
        "stop_mode": "box",
    },
    "vtm_vol_mr": {
        "atr_period": 14,
        "ma_period": 30,
        "threshold_range": 2.0,
        "stop_atr": 1.0,
        "holding_bars": 6,
        "close_extreme_frac": 0.15,
        "vol_filter_min": 1.0,
        "slope_lookback": 10,
        "slope_threshold": 0.0,
        "spread_max_usd": 0.9,
        "exit_on_sma_cross": True,
        "be_trigger_atr": 0.5,
        "entry_windows": ["00:30-22:30"],
        "excluded_windows": ["07:30-08:30", "12:30-13:30", "16:30-17:30", "21:30-22:30"],
    },
    "v3_breakout_N1": 20,
    "v3_atr_period_M": 14,
    "v3_k_trend": 1.05,
    "v3_k_range": 0.95,
    "v3_atr_sl_trend": 1.2,
    "v3_rr_trend": 2.0,
    "v3_rsi_period": 14,
    "v3_atr_sl_range": 1.0,
    "v3_rr_range": 1.5,
    "max_trades_per_session": 1,
    "close_at_session_end": True,
    "k_atr_range": 1.2,
    "range_reject_wick_min": 0.45,
    "range_body_min": 0.45,
    "range_rsi_long_max": 40.0,
    "range_rsi_short_min": 60.0,
    "range_sl_atr_buffer": 0.5,
    "range_touch_ttl_m5_bars": 12,
    "spread_usd": 0.41,
    "slippage_usd": 0.05,
    "cost_max_atr_mult": 0.25,
    "cost_max_sl_frac": 0.15,
    "cost_max_tp_frac_range": 0.20,
    "cost_mult_trend_session": 1.0,
    "cost_mult_off_session": 1.2,
    "cost_mult_asia": 1.5,
    "ablation_force_regime": "AUTO",
    "ablation_disable_cost_filter": False,
    "ablation_disable_session_gating": False,
    "daily_stop_r": -2.0,
    "daily_stop_pct": -0.015,
    "weekly_stop_r": -5.0,
    "weekly_stop_pct": -0.04,
    "loss_streak_limit": 3,
    "loss_streak_block_hours": 24,
    "force_session_close": False,
    "session": {
        "mon_thu_start": "07:00",
        "mon_thu_end": "17:00",
        "fri_start": "07:00",
        "fri_end": "15:00",
    },
    "trend_sessions": ["08:00-12:00", "13:00-16:00"],
    "range_sessions": ["06:00-08:00", "16:00-19:00"],
    "blocked_windows": ["21:50-22:10"],
    "trade_filter": {
        "hour_blacklist_utc": [],
        "hour_whitelist_utc": [],
    },
    "cost_gate_overrides_by_hour": {},
    "progress_every_days": 5,
    "year_test_mode": "last_365_days",
    "monte_carlo_sims": 300,
    "monte_carlo_seed": 42,
    "sensitivity": {
        "trailing_mult": [2.0, 2.5, 3.0],
        "body_ratio": [0.65, 0.70, 0.75],
        "shock_threshold": [2.5, 3.0, 3.5],
        "wick_ratio_max": [0.15, 0.20, 0.25],
        "bos_lookback": [5, 7, 10],
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _to_int(cfg: dict[str, Any], key: str, *, minimum: int | None = None) -> int:
    value = cfg.get(key)
    if value is None:
        raise ValueError(f"Missing config key: {key}")
    try:
        ivalue = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Config key '{key}' must be int. Got: {value!r}") from exc
    if minimum is not None and ivalue < minimum:
        raise ValueError(f"Config key '{key}' must be >= {minimum}. Got: {ivalue}")
    return ivalue


def _to_float(cfg: dict[str, Any], key: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    value = cfg.get(key)
    if value is None:
        raise ValueError(f"Missing config key: {key}")
    try:
        fvalue = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Config key '{key}' must be float. Got: {value!r}") from exc
    if minimum is not None and fvalue < minimum:
        raise ValueError(f"Config key '{key}' must be >= {minimum}. Got: {fvalue}")
    if maximum is not None and fvalue > maximum:
        raise ValueError(f"Config key '{key}' must be <= {maximum}. Got: {fvalue}")
    return fvalue


def _validate_hhmm(value: str, key: str) -> str:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise ValueError(f"Config key '{key}' must be HH:MM. Got: {value!r}")
    hh = value[:2]
    mm = value[3:]
    if not hh.isdigit() or not mm.isdigit():
        raise ValueError(f"Config key '{key}' must be HH:MM. Got: {value!r}")
    h = int(hh)
    m = int(mm)
    if h < 0 or h > 23 or m < 0 or m > 59:
        raise ValueError(f"Config key '{key}' has invalid clock time. Got: {value!r}")
    return f"{h:02d}:{m:02d}"


def _validate_time_window(value: str, key: str) -> str:
    if not isinstance(value, str) or "-" not in value:
        raise ValueError(f"Config key '{key}' must be HH:MM-HH:MM. Got: {value!r}")
    start_raw, end_raw = value.split("-", 1)
    start = _validate_hhmm(start_raw.strip(), f"{key}.start")
    end = _validate_hhmm(end_raw.strip(), f"{key}.end")
    if start == end:
        raise ValueError(f"Config key '{key}' must have different start/end. Got: {value!r}")
    return f"{start}-{end}"


def _validate_windows_list(cfg: dict[str, Any], key: str, *, allow_empty: bool) -> list[str]:
    raw = cfg.get(key)
    if not isinstance(raw, list):
        raise ValueError(f"Config key '{key}' must be a list of HH:MM-HH:MM strings.")
    if (not allow_empty) and len(raw) == 0:
        raise ValueError(f"Config key '{key}' must not be empty.")
    out: list[str] = []
    for i, window in enumerate(raw):
        out.append(_validate_time_window(window, f"{key}[{i}]"))
    return out


def _validate_hour_list(raw: Any, key: str) -> list[int]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"Config key '{key}' must be a list of UTC hours (0..23).")
    out: list[int] = []
    for i, item in enumerate(raw):
        try:
            hour = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Config key '{key}[{i}]' must be an int in 0..23. Got: {item!r}") from exc
        if hour < 0 or hour > 23:
            raise ValueError(f"Config key '{key}[{i}]' must be in 0..23. Got: {hour}")
        out.append(hour)
    # Keep deterministic + deduplicated.
    return sorted(set(out))


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping/object.")

    cfg = _deep_merge(DEFAULT_CONFIG, data)

    _to_float(cfg, "starting_balance", minimum=1.0)
    _to_float(cfg, "risk_per_trade_pct", minimum=0.0001, maximum=0.2)

    _to_int(cfg, "ema_h1_fast", minimum=2)
    _to_int(cfg, "ema_h1_slow", minimum=3)
    if int(cfg["ema_h1_fast"]) >= int(cfg["ema_h1_slow"]):
        raise ValueError("Config keys 'ema_h1_fast' must be lower than 'ema_h1_slow'.")

    _to_int(cfg, "ema_m15", minimum=2)
    _to_int(cfg, "ema_m5", minimum=2)
    _to_int(cfg, "rsi_period_m15", minimum=2)
    _to_int(cfg, "atr_period", minimum=2)
    _to_int(cfg, "h1_bias_slope_lookback", minimum=1)
    _to_float(cfg, "h1_bias_atr_mult", minimum=0.0)
    _to_float(cfg, "h1_min_sep_atr_mult", minimum=0.0)
    _to_float(cfg, "h1_slope_min_atr_mult", minimum=0.0)
    _to_float(cfg, "h1_range_max_sep_atr_mult", minimum=0.0)
    _to_float(cfg, "h1_range_max_slope_atr_mult", minimum=0.0)

    _to_int(cfg, "atr_rel_lookback", minimum=2)
    _to_float(cfg, "atr_rel_trend_min", minimum=0.0)
    _to_float(cfg, "atr_rel_range_max", minimum=0.0)
    _to_float(cfg, "atr_rel_dead_max", minimum=0.0)
    if float(cfg["atr_rel_dead_max"]) > float(cfg["atr_rel_range_max"]):
        raise ValueError("Config keys 'atr_rel_dead_max' must be <= 'atr_rel_range_max'.")

    _to_int(cfg, "regime_trend_enter_score", minimum=-2)
    _to_int(cfg, "regime_trend_exit_score", minimum=-2)
    _to_int(cfg, "regime_range_enter_score", minimum=-2)
    _to_int(cfg, "regime_range_exit_score", minimum=-2)
    if int(cfg["regime_trend_enter_score"]) <= int(cfg["regime_trend_exit_score"]):
        raise ValueError("Config requires 'regime_trend_enter_score' > 'regime_trend_exit_score' for hysteresis.")
    if int(cfg["regime_range_enter_score"]) <= int(cfg["regime_range_exit_score"]):
        raise ValueError("Config requires 'regime_range_enter_score' > 'regime_range_exit_score' for hysteresis.")
    _to_int(cfg, "trend_min_bars_m15", minimum=0)
    _to_int(cfg, "range_min_bars_m15", minimum=0)

    _to_float(cfg, "shock_threshold", minimum=1.0)
    _to_int(cfg, "shock_cooldown_bars", minimum=0)
    _to_int(cfg, "confirm_valid_m15_bars", minimum=1)
    _to_int(cfg, "bos_lookback", minimum=2)
    _to_float(cfg, "body_ratio", minimum=0.0, maximum=1.0)
    _to_float(cfg, "wick_ratio_max", minimum=0.0, maximum=1.0)
    _to_float(cfg, "rsi_pullback_long_max", minimum=0.0, maximum=100.0)
    _to_float(cfg, "rsi_recover_long_min", minimum=0.0, maximum=100.0)
    _to_float(cfg, "rsi_pullback_short_min", minimum=0.0, maximum=100.0)
    _to_float(cfg, "rsi_recover_short_max", minimum=0.0, maximum=100.0)
    if float(cfg["rsi_pullback_long_max"]) > float(cfg["rsi_recover_long_min"]):
        raise ValueError("Config keys 'rsi_pullback_long_max' must be <= 'rsi_recover_long_min'.")
    if float(cfg["rsi_pullback_short_min"]) < float(cfg["rsi_recover_short_max"]):
        raise ValueError("Config keys 'rsi_pullback_short_min' must be >= 'rsi_recover_short_max'.")
    _to_int(cfg, "max_trades_per_day", minimum=1)
    _to_int(cfg, "swing_lookback", minimum=2)
    _to_float(cfg, "atr_floor_mult", minimum=0.0)
    _to_float(cfg, "sl_buffer_mult", minimum=0.0)
    _to_float(cfg, "tp1_r", minimum=0.1)
    _to_float(cfg, "partial_pct", minimum=0.05, maximum=0.95)
    _to_float(cfg, "trailing_mult", minimum=0.1)
    _to_float(cfg, "trailing_mult_phase1", minimum=0.1)
    _to_float(cfg, "trailing_mult_phase2", minimum=0.1)
    _to_float(cfg, "be_after_r", minimum=0.0)
    _to_int(cfg, "time_stop_bars", minimum=1)
    _to_float(cfg, "time_stop_min_r", minimum=0.0)
    _to_int(cfg, "cooldown_after_trade_bars", minimum=0)
    strategy_family = str(cfg.get("strategy_family", "AUTO")).upper()
    if strategy_family not in {"AUTO", "LEGACY", "V3_CLASSIC", "V4_SESSION_ORB", "VTM_VOL_MR"}:
        raise ValueError(
            "Config key 'strategy_family' must be one of: "
            "'AUTO', 'LEGACY', 'V3_CLASSIC', 'V4_SESSION_ORB', 'VTM_VOL_MR'."
        )
    cfg["strategy_family"] = strategy_family
    cfg["enable_strategy_v3"] = bool(cfg.get("enable_strategy_v3", False))
    v4_cfg = cfg.get("v4_session_orb", {})
    if not isinstance(v4_cfg, dict):
        raise ValueError("Config key 'v4_session_orb' must be a mapping/object.")
    v4_cfg["asia_start"] = _validate_hhmm(str(v4_cfg.get("asia_start", "00:00")), "v4_session_orb.asia_start")
    v4_cfg["asia_end"] = _validate_hhmm(str(v4_cfg.get("asia_end", "06:00")), "v4_session_orb.asia_end")
    v4_cfg["trade_start"] = _validate_hhmm(str(v4_cfg.get("trade_start", "07:00")), "v4_session_orb.trade_start")
    v4_cfg["trade_end"] = _validate_hhmm(str(v4_cfg.get("trade_end", "10:00")), "v4_session_orb.trade_end")
    try:
        v4_cfg["buffer_atr_mult"] = float(v4_cfg.get("buffer_atr_mult", 0.05))
        v4_cfg["stop_buffer_atr_mult"] = float(v4_cfg.get("stop_buffer_atr_mult", 0.0))
        v4_cfg["atr_period"] = int(v4_cfg.get("atr_period", cfg["atr_period"]))
        v4_cfg["rr"] = float(v4_cfg.get("rr", 1.5))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid numeric field in 'v4_session_orb'.") from exc
    if v4_cfg["buffer_atr_mult"] < 0.0:
        raise ValueError("Config key 'v4_session_orb.buffer_atr_mult' must be >= 0.")
    if v4_cfg["stop_buffer_atr_mult"] < 0.0:
        raise ValueError("Config key 'v4_session_orb.stop_buffer_atr_mult' must be >= 0.")
    if v4_cfg["atr_period"] < 2:
        raise ValueError("Config key 'v4_session_orb.atr_period' must be >= 2.")
    if v4_cfg["rr"] <= 0.0:
        raise ValueError("Config key 'v4_session_orb.rr' must be > 0.")
    v4_cfg["time_stop"] = bool(v4_cfg.get("time_stop", True))
    v4_cfg["exit_at_trade_end"] = bool(v4_cfg.get("exit_at_trade_end", True))
    stop_mode = str(v4_cfg.get("stop_mode", "box")).lower()
    if stop_mode not in {"box", "break_wick"}:
        raise ValueError("Config key 'v4_session_orb.stop_mode' must be 'box' or 'break_wick'.")
    v4_cfg["stop_mode"] = stop_mode
    cfg["v4_session_orb"] = v4_cfg
    vtm_cfg = cfg.get("vtm_vol_mr", {})
    if not isinstance(vtm_cfg, dict):
        raise ValueError("Config key 'vtm_vol_mr' must be a mapping/object.")
    try:
        vtm_cfg["atr_period"] = int(vtm_cfg.get("atr_period", 14))
        vtm_cfg["ma_period"] = int(vtm_cfg.get("ma_period", 30))
        vtm_cfg["threshold_range"] = float(vtm_cfg.get("threshold_range", 2.0))
        vtm_cfg["stop_atr"] = float(vtm_cfg.get("stop_atr", 1.0))
        vtm_cfg["holding_bars"] = int(vtm_cfg.get("holding_bars", 6))
        vtm_cfg["close_extreme_frac"] = float(vtm_cfg.get("close_extreme_frac", 0.15))
        vtm_cfg["vol_filter_min"] = float(vtm_cfg.get("vol_filter_min", 0.0))
        vtm_cfg["slope_lookback"] = int(vtm_cfg.get("slope_lookback", 10))
        vtm_cfg["slope_threshold"] = float(vtm_cfg.get("slope_threshold", 0.0))
        vtm_cfg["spread_max_usd"] = float(vtm_cfg.get("spread_max_usd", 0.0))
        vtm_cfg["be_trigger_atr"] = float(vtm_cfg.get("be_trigger_atr", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid numeric field in 'vtm_vol_mr'.") from exc
    if vtm_cfg["atr_period"] < 2:
        raise ValueError("Config key 'vtm_vol_mr.atr_period' must be >= 2.")
    if vtm_cfg["ma_period"] < 2:
        raise ValueError("Config key 'vtm_vol_mr.ma_period' must be >= 2.")
    if vtm_cfg["threshold_range"] <= 0.0:
        raise ValueError("Config key 'vtm_vol_mr.threshold_range' must be > 0.")
    if vtm_cfg["stop_atr"] <= 0.0:
        raise ValueError("Config key 'vtm_vol_mr.stop_atr' must be > 0.")
    if vtm_cfg["holding_bars"] < 1:
        raise ValueError("Config key 'vtm_vol_mr.holding_bars' must be >= 1.")
    if not (0.0 < vtm_cfg["close_extreme_frac"] <= 0.5):
        raise ValueError("Config key 'vtm_vol_mr.close_extreme_frac' must be in (0, 0.5].")
    if vtm_cfg["vol_filter_min"] < 0.0:
        raise ValueError("Config key 'vtm_vol_mr.vol_filter_min' must be >= 0.")
    if vtm_cfg["slope_lookback"] < 1:
        raise ValueError("Config key 'vtm_vol_mr.slope_lookback' must be >= 1.")
    if vtm_cfg["slope_threshold"] < 0.0:
        raise ValueError("Config key 'vtm_vol_mr.slope_threshold' must be >= 0.")
    if vtm_cfg["spread_max_usd"] < 0.0:
        raise ValueError("Config key 'vtm_vol_mr.spread_max_usd' must be >= 0.")
    if vtm_cfg["be_trigger_atr"] < 0.0:
        raise ValueError("Config key 'vtm_vol_mr.be_trigger_atr' must be >= 0.")
    vtm_cfg["exit_on_sma_cross"] = bool(vtm_cfg.get("exit_on_sma_cross", True))
    raw_entry_windows = vtm_cfg.get("entry_windows", [])
    if not isinstance(raw_entry_windows, list) or len(raw_entry_windows) == 0:
        raise ValueError("Config key 'vtm_vol_mr.entry_windows' must be a non-empty list.")
    vtm_cfg["entry_windows"] = [
        _validate_time_window(item, f"vtm_vol_mr.entry_windows[{i}]")
        for i, item in enumerate(raw_entry_windows)
    ]
    raw_excluded_windows = vtm_cfg.get("excluded_windows", [])
    if not isinstance(raw_excluded_windows, list):
        raise ValueError("Config key 'vtm_vol_mr.excluded_windows' must be a list.")
    vtm_cfg["excluded_windows"] = [
        _validate_time_window(item, f"vtm_vol_mr.excluded_windows[{i}]")
        for i, item in enumerate(raw_excluded_windows)
    ]
    cfg["vtm_vol_mr"] = vtm_cfg
    _to_int(cfg, "v3_breakout_N1", minimum=2)
    _to_int(cfg, "v3_atr_period_M", minimum=2)
    _to_float(cfg, "v3_k_trend", minimum=0.0)
    _to_float(cfg, "v3_k_range", minimum=0.0)
    _to_float(cfg, "v3_atr_sl_trend", minimum=0.05)
    _to_float(cfg, "v3_rr_trend", minimum=0.05)
    _to_int(cfg, "v3_rsi_period", minimum=2)
    _to_float(cfg, "v3_atr_sl_range", minimum=0.05)
    _to_float(cfg, "v3_rr_range", minimum=0.05)
    _to_int(cfg, "max_trades_per_session", minimum=1)
    cfg["close_at_session_end"] = bool(cfg.get("close_at_session_end", True))

    _to_float(cfg, "k_atr_range", minimum=0.1)
    _to_float(cfg, "range_reject_wick_min", minimum=0.0, maximum=1.0)
    _to_float(cfg, "range_body_min", minimum=0.0, maximum=1.0)
    _to_float(cfg, "range_rsi_long_max", minimum=0.0, maximum=100.0)
    _to_float(cfg, "range_rsi_short_min", minimum=0.0, maximum=100.0)
    if float(cfg["range_rsi_long_max"]) > float(cfg["range_rsi_short_min"]):
        raise ValueError("Config key 'range_rsi_long_max' must be <= 'range_rsi_short_min'.")
    _to_float(cfg, "range_sl_atr_buffer", minimum=0.0)
    _to_int(cfg, "range_touch_ttl_m5_bars", minimum=1)

    _to_float(cfg, "spread_usd", minimum=0.0)
    _to_float(cfg, "slippage_usd", minimum=0.0)
    _to_float(cfg, "cost_max_atr_mult", minimum=0.0)
    _to_float(cfg, "cost_max_sl_frac", minimum=0.0)
    _to_float(cfg, "cost_max_tp_frac_range", minimum=0.0, maximum=1.0)
    _to_float(cfg, "cost_mult_trend_session", minimum=0.1)
    _to_float(cfg, "cost_mult_off_session", minimum=0.1)
    _to_float(cfg, "cost_mult_asia", minimum=0.1)

    ablation_force = str(cfg.get("ablation_force_regime", "AUTO")).upper()
    if ablation_force not in {"AUTO", "TREND", "RANGE", "NO_TRADE"}:
        raise ValueError(
            "Config key 'ablation_force_regime' must be one of: "
            "'AUTO', 'TREND', 'RANGE', 'NO_TRADE'."
        )
    cfg["ablation_force_regime"] = ablation_force
    cfg["ablation_disable_cost_filter"] = bool(cfg.get("ablation_disable_cost_filter", False))
    cfg["ablation_disable_session_gating"] = bool(cfg.get("ablation_disable_session_gating", False))

    _to_float(cfg, "daily_stop_r")
    _to_float(cfg, "daily_stop_pct")
    _to_float(cfg, "weekly_stop_r")
    _to_float(cfg, "weekly_stop_pct")
    _to_int(cfg, "loss_streak_limit", minimum=1)
    _to_int(cfg, "loss_streak_block_hours", minimum=1)

    cfg["force_session_close"] = bool(cfg.get("force_session_close", False))

    session_cfg = cfg.get("session")
    if not isinstance(session_cfg, dict):
        raise ValueError("Config key 'session' must be a mapping/object.")
    for session_key in ("mon_thu_start", "mon_thu_end", "fri_start", "fri_end"):
        if session_key not in session_cfg:
            raise ValueError(f"Config key 'session.{session_key}' is required.")
        session_cfg[session_key] = _validate_hhmm(session_cfg[session_key], f"session.{session_key}")
    cfg["session"] = session_cfg

    cfg["trend_sessions"] = _validate_windows_list(cfg, "trend_sessions", allow_empty=False)
    cfg["range_sessions"] = _validate_windows_list(cfg, "range_sessions", allow_empty=False)
    cfg["blocked_windows"] = _validate_windows_list(cfg, "blocked_windows", allow_empty=True)

    trade_filter_cfg = cfg.get("trade_filter", {})
    if trade_filter_cfg is None:
        trade_filter_cfg = {}
    if not isinstance(trade_filter_cfg, dict):
        raise ValueError("Config key 'trade_filter' must be a mapping/object.")
    trade_filter_cfg["hour_blacklist_utc"] = _validate_hour_list(
        trade_filter_cfg.get("hour_blacklist_utc", []),
        "trade_filter.hour_blacklist_utc",
    )
    trade_filter_cfg["hour_whitelist_utc"] = _validate_hour_list(
        trade_filter_cfg.get("hour_whitelist_utc", []),
        "trade_filter.hour_whitelist_utc",
    )
    cfg["trade_filter"] = trade_filter_cfg

    cost_overrides = cfg.get("cost_gate_overrides_by_hour", {})
    if cost_overrides is None:
        cost_overrides = {}
    if not isinstance(cost_overrides, dict):
        raise ValueError("Config key 'cost_gate_overrides_by_hour' must be a mapping/object.")
    parsed_overrides: dict[int, dict[str, float]] = {}
    for raw_hour, payload in cost_overrides.items():
        try:
            hour = int(raw_hour)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour' has invalid hour key: {raw_hour!r}"
            ) from exc
        if hour < 0 or hour > 23:
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour' hour must be in 0..23. Got: {hour}"
            )
        if not isinstance(payload, dict):
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour.{hour}' must be a mapping/object."
            )
        if "max_cost_multiplier" not in payload:
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour.{hour}.max_cost_multiplier' is required."
            )
        try:
            max_mult = float(payload["max_cost_multiplier"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour.{hour}.max_cost_multiplier' must be float."
            ) from exc
        if max_mult < 0.0:
            raise ValueError(
                f"Config key 'cost_gate_overrides_by_hour.{hour}.max_cost_multiplier' must be >= 0."
            )
        parsed_overrides[hour] = {"max_cost_multiplier": max_mult}
    cfg["cost_gate_overrides_by_hour"] = parsed_overrides

    _to_int(cfg, "progress_every_days", minimum=0)

    year_test_mode = str(cfg.get("year_test_mode", "last_365_days"))
    if year_test_mode not in {"last_365_days", "last_12_full_calendar_months"}:
        raise ValueError(
            "Config key 'year_test_mode' must be one of: "
            "'last_365_days', 'last_12_full_calendar_months'."
        )
    cfg["year_test_mode"] = year_test_mode

    _to_int(cfg, "monte_carlo_sims", minimum=50)
    _to_int(cfg, "monte_carlo_seed", minimum=0)

    sensitivity = cfg.get("sensitivity")
    if not isinstance(sensitivity, dict):
        raise ValueError("Config key 'sensitivity' must be a mapping/object.")
    for k in ("trailing_mult", "body_ratio", "shock_threshold", "wick_ratio_max", "bos_lookback"):
        values = sensitivity.get(k)
        if not isinstance(values, list) or len(values) == 0:
            raise ValueError(f"Config key 'sensitivity.{k}' must be a non-empty list.")
        for item in values:
            if k == "bos_lookback":
                ivalue = int(item)
                if ivalue < 2:
                    raise ValueError(f"Config key 'sensitivity.{k}' values must be >= 2. Got: {item}")
            else:
                _ = float(item)

    if not isinstance(cfg.get("output_dir"), str) or not cfg["output_dir"].strip():
        raise ValueError("Config key 'output_dir' must be a non-empty string.")
    if not isinstance(cfg.get("runs_output_dir"), str) or not cfg["runs_output_dir"].strip():
        raise ValueError("Config key 'runs_output_dir' must be a non-empty string.")

    return cfg
