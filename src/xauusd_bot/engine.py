from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from xauusd_bot.indicators import atr_wilder, ema, rsi_wilder, true_range
from xauusd_bot.logger import CsvLogger
from xauusd_bot.models import Bias, BiasContext, Confirmation, Direction, EngineState, EntrySignal, M15Context, Trade
from xauusd_bot.risk import RiskManager
from xauusd_bot.timeframes import resample_from_m5


@dataclass(slots=True)
class PendingEntry:
    signal: EntrySignal
    signal_index: int
    execute_index: int
    signal_ts: pd.Timestamp
    swing_low6: float
    swing_high6: float
    atr_signal: float
    trigger_price: float
    mode: str = "TREND"
    fixed_sl_mid: float | None = None
    fixed_tp_mid: float | None = None
    regime_state: str = "NO_TRADE"
    cost_multiplier: float = 1.0
    setup_reason: str = ""
    signal_high: float | None = None
    signal_low: float | None = None


@dataclass(slots=True)
class Position:
    trade: Trade
    remaining_qty: float
    risk_distance: float
    current_sl_mid: float
    initial_sl_mid: float
    tp1_mid: float
    highest_high: float
    lowest_low: float
    mode: str = "TREND"
    pending_exit_reason: str | None = None
    pending_exit_index: int | None = None


class SimulationEngine:
    def __init__(self, config: dict[str, Any], logger: CsvLogger):
        self.config = config
        self.logger = logger
        self.risk = RiskManager(config)

        self.trade_id = 0
        self.fill_id = 0

        self.ema_h1_fast = int(config.get("ema_h1_fast", 50))
        self.ema_h1_slow = int(config.get("ema_h1_slow", 200))
        self.ema_m15 = int(config.get("ema_m15", 20))
        self.ema_m5 = int(config.get("ema_m5", 20))
        self.rsi_period_m15 = int(config.get("rsi_period_m15", 14))
        self.atr_period = int(config.get("atr_period", 14))

        self.h1_bias_slope_lookback = int(config.get("h1_bias_slope_lookback", 3))
        self.h1_bias_atr_mult = float(config.get("h1_bias_atr_mult", 0.10))
        self.h1_min_sep_atr_mult = float(config.get("h1_min_sep_atr_mult", 0.25))
        self.h1_slope_min_atr_mult = float(config.get("h1_slope_min_atr_mult", 0.05))
        self.h1_range_max_sep_atr_mult = float(config.get("h1_range_max_sep_atr_mult", 0.20))
        self.h1_range_max_slope_atr_mult = float(config.get("h1_range_max_slope_atr_mult", 0.05))
        self.atr_rel_lookback = int(config.get("atr_rel_lookback", 20))
        self.atr_rel_trend_min = float(config.get("atr_rel_trend_min", 1.05))
        self.atr_rel_range_max = float(config.get("atr_rel_range_max", 0.95))
        self.atr_rel_dead_max = float(config.get("atr_rel_dead_max", 0.70))
        self.regime_trend_enter_score = int(config.get("regime_trend_enter_score", 3))
        self.regime_trend_exit_score = int(config.get("regime_trend_exit_score", 2))
        self.regime_range_enter_score = int(config.get("regime_range_enter_score", 3))
        self.regime_range_exit_score = int(config.get("regime_range_exit_score", 2))
        self.trend_min_bars_m15 = int(config.get("trend_min_bars_m15", 4))
        self.range_min_bars_m15 = int(config.get("range_min_bars_m15", 4))
        self.confirm_valid_m15_bars = int(config.get("confirm_valid_m15_bars", 3))
        self.bos_lookback = int(config.get("bos_lookback", 5))
        self.body_ratio = float(config.get("body_ratio", 0.70))
        self.wick_ratio_max = float(config.get("wick_ratio_max", 0.20))
        self.rsi_pullback_long_max = float(config.get("rsi_pullback_long_max", 35.0))
        self.rsi_recover_long_min = float(config.get("rsi_recover_long_min", 40.0))
        self.rsi_pullback_short_min = float(config.get("rsi_pullback_short_min", 65.0))
        self.rsi_recover_short_max = float(config.get("rsi_recover_short_max", 60.0))
        self.max_trades_per_day = int(config.get("max_trades_per_day", 2))
        self.swing_lookback = int(config.get("swing_lookback", 6))

        self.shock_threshold = float(config.get("shock_threshold", 3.0))
        self.shock_cooldown_bars = int(config.get("shock_cooldown_bars", 12))
        self.cooldown_after_trade_bars = int(config.get("cooldown_after_trade_bars", 6))

        self.atr_floor_mult = float(config.get("atr_floor_mult", 0.80))
        self.sl_buffer_mult = float(config.get("sl_buffer_mult", 0.10))
        self.tp1_r = float(config.get("tp1_r", 1.0))
        self.partial_pct = float(config.get("partial_pct", 0.50))
        self.trailing_mult = float(config.get("trailing_mult", 2.5))
        self.trailing_mult_phase1 = float(config.get("trailing_mult_phase1", 2.0))
        self.trailing_mult_phase2 = float(config.get("trailing_mult_phase2", 1.0))
        self.be_after_r = float(config.get("be_after_r", 2.0))
        self.time_stop_bars = int(config.get("time_stop_bars", 12))
        self.time_stop_min_r = float(config.get("time_stop_min_r", 0.50))
        self.strategy_family = str(config.get("strategy_family", "AUTO")).upper()
        self.enable_strategy_v3 = bool(config.get("enable_strategy_v3", False))
        self.enable_strategy_v4_orb = self.strategy_family == "V4_SESSION_ORB"
        if self.enable_strategy_v4_orb:
            self.enable_strategy_v3 = False
        v4_cfg = config.get("v4_session_orb", {}) or {}
        self.v4_asia_start = self._hhmm_to_minutes(str(v4_cfg.get("asia_start", "00:00")))
        self.v4_asia_end = self._hhmm_to_minutes(str(v4_cfg.get("asia_end", "06:00")))
        self.v4_trade_start = self._hhmm_to_minutes(str(v4_cfg.get("trade_start", "07:00")))
        self.v4_trade_end = self._hhmm_to_minutes(str(v4_cfg.get("trade_end", "10:00")))
        self.v4_buffer_atr_mult = float(v4_cfg.get("buffer_atr_mult", 0.05))
        self.v4_stop_buffer_atr_mult = float(v4_cfg.get("stop_buffer_atr_mult", 0.0))
        self.v4_atr_period = int(v4_cfg.get("atr_period", self.atr_period))
        self.v4_rr = float(v4_cfg.get("rr", 1.5))
        self.v4_time_stop = bool(v4_cfg.get("time_stop", True))
        self.v4_exit_at_trade_end = bool(v4_cfg.get("exit_at_trade_end", True))
        self.v4_stop_mode = str(v4_cfg.get("stop_mode", "box")).lower()
        self.v3_breakout_N1 = int(config.get("v3_breakout_N1", 20))
        self.v3_atr_period_M = int(config.get("v3_atr_period_M", self.atr_period))
        self.v3_k_trend = float(config.get("v3_k_trend", 1.05))
        self.v3_k_range = float(config.get("v3_k_range", 0.95))
        self.v3_atr_sl_trend = float(config.get("v3_atr_sl_trend", 1.2))
        self.v3_rr_trend = float(config.get("v3_rr_trend", 2.0))
        self.v3_rsi_period = int(config.get("v3_rsi_period", 14))
        self.v3_atr_sl_range = float(config.get("v3_atr_sl_range", 1.0))
        self.v3_rr_range = float(config.get("v3_rr_range", 1.5))
        self.max_trades_per_session = int(config.get("max_trades_per_session", 1))
        self.close_at_session_end = bool(config.get("close_at_session_end", True))
        self.k_atr_range = float(config.get("k_atr_range", 1.2))
        self.range_reject_wick_min = float(config.get("range_reject_wick_min", 0.45))
        self.range_body_min = float(config.get("range_body_min", 0.45))
        self.range_rsi_long_max = float(config.get("range_rsi_long_max", 40.0))
        self.range_rsi_short_min = float(config.get("range_rsi_short_min", 60.0))
        self.range_sl_atr_buffer = float(config.get("range_sl_atr_buffer", 0.5))
        self.range_touch_ttl_m5_bars = int(config.get("range_touch_ttl_m5_bars", 12))

        self.spread_usd = float(config.get("spread_usd", 0.41))
        self.slippage_usd = float(config.get("slippage_usd", 0.05))
        self.cost_max_atr_mult = float(config.get("cost_max_atr_mult", 0.25))
        self.cost_max_sl_frac = float(config.get("cost_max_sl_frac", 0.15))
        self.cost_max_tp_frac_range = float(config.get("cost_max_tp_frac_range", 0.20))
        self.cost_mult_trend_session = float(config.get("cost_mult_trend_session", 1.0))
        self.cost_mult_off_session = float(config.get("cost_mult_off_session", 1.2))
        self.cost_mult_asia = float(config.get("cost_mult_asia", 1.5))
        self.ablation_force_regime = str(config.get("ablation_force_regime", "AUTO")).upper()
        self.ablation_disable_cost_filter = bool(config.get("ablation_disable_cost_filter", False))
        self.ablation_disable_session_gating = bool(config.get("ablation_disable_session_gating", False))

        self.daily_stop_r = float(config.get("daily_stop_r", -2.0))
        self.daily_stop_pct = float(config.get("daily_stop_pct", -0.015))
        self.weekly_stop_r = float(config.get("weekly_stop_r", -5.0))
        self.weekly_stop_pct = float(config.get("weekly_stop_pct", -0.04))
        self.loss_streak_limit = int(config.get("loss_streak_limit", 3))
        self.loss_streak_block_hours = int(config.get("loss_streak_block_hours", 24))

        session_cfg = config.get("session", {})
        self.session_mon_thu_start = self._hhmm_to_minutes(str(session_cfg.get("mon_thu_start", "07:00")))
        self.session_mon_thu_end = self._hhmm_to_minutes(str(session_cfg.get("mon_thu_end", "17:00")))
        self.session_fri_start = self._hhmm_to_minutes(str(session_cfg.get("fri_start", "07:00")))
        self.session_fri_end = self._hhmm_to_minutes(str(session_cfg.get("fri_end", "15:00")))
        self.force_session_close = bool(config.get("force_session_close", False))
        self.trend_sessions = self._parse_windows(config.get("trend_sessions", ["08:00-12:00", "13:00-16:00"]))
        self.range_sessions = self._parse_windows(config.get("range_sessions", ["06:00-08:00", "16:00-19:00"]))
        self.blocked_windows = self._parse_windows(config.get("blocked_windows", []))
        trade_filter_cfg = config.get("trade_filter", {}) or {}
        self.hour_blacklist_utc = {int(h) for h in trade_filter_cfg.get("hour_blacklist_utc", [])}
        self.hour_whitelist_utc = {int(h) for h in trade_filter_cfg.get("hour_whitelist_utc", [])}
        raw_hour_overrides = config.get("cost_gate_overrides_by_hour", {}) or {}
        self.cost_gate_overrides_by_hour: dict[int, float] = {}
        for raw_hour, payload in raw_hour_overrides.items():
            if not isinstance(payload, dict):
                continue
            try:
                hour = int(raw_hour)
                max_mult = float(payload.get("max_cost_multiplier"))
            except (TypeError, ValueError):
                continue
            self.cost_gate_overrides_by_hour[hour] = max_mult

        self.progress_every_days = max(0, int(config.get("progress_every_days", 5)))
        self.stdout_trade_events = bool(config.get("stdout_trade_events", False))

        self.cooldown_until_index = -1
        self.shock_block_until_index = -1
        self.loss_streak = 0
        self.loss_streak_block_until: pd.Timestamp | None = None
        self.daily_block_until: pd.Timestamp | None = None
        self.weekly_block_until: pd.Timestamp | None = None

        self.daily_realized_pnl: dict[str, float] = {}
        self.weekly_realized_pnl: dict[str, float] = {}
        self.daily_realized_r: dict[str, float] = {}
        self.weekly_realized_r: dict[str, float] = {}
        self.daily_start_equity: dict[str, float] = {}
        self.weekly_start_equity: dict[str, float] = {}
        self.trades_opened_per_day: dict[str, int] = {}
        self.trades_opened_per_session: dict[str, int] = {}
        self.regime_state = "NO_TRADE"
        self.regime_since_m15_idx: int | None = None
        self.regime_stats: dict[str, int] = {"TREND": 0, "RANGE": 0, "NO_TRADE": 0}
        self.last_touch_upper_m5_index: int | None = None
        self.last_touch_lower_m5_index: int | None = None

        self.equity_curve: list[dict[str, Any]] = []
        self.bar_delta = pd.Timedelta(minutes=5)
        self._m15_pullback_rsi_ok = False
        self._m15_pullback_start_idx: int | None = None
        self._m15_last_reason = "INIT"

    def run(self, m5_df: pd.DataFrame) -> dict[str, Any]:
        if m5_df.empty:
            raise ValueError("Input M5 data is empty.")

        m5 = self._prepare_m5(m5_df)
        if len(m5) > 1:
            inferred = pd.Series(m5["timestamp"]).diff().dropna().median()
            if pd.notna(inferred) and inferred > pd.Timedelta(0):
                self.bar_delta = inferred

        m15 = self._prepare_m15(m5)
        h1 = self._prepare_h1(m5)

        sim_start_ts = pd.Timestamp(m5.iloc[0]["timestamp"]).to_pydatetime()
        sim_end_ts = pd.Timestamp(m5.iloc[-1]["timestamp"]).to_pydatetime()
        sim_days = (sim_end_ts - sim_start_ts).total_seconds() / 86400.0
        total_bars = len(m5)
        total_seconds = max((sim_end_ts - sim_start_ts).total_seconds(), 1.0)
        progress_step = pd.Timedelta(days=self.progress_every_days) if self.progress_every_days > 0 else None
        next_progress_ts = (pd.Timestamp(sim_start_ts) + progress_step) if progress_step is not None else None

        state = EngineState.WAIT_H1_BIAS
        bias_context = BiasContext(bias=Bias.NONE, reason="INIT")
        m15_context = M15Context(confirmation=Confirmation.NO, reason="INIT")
        pending_entry: PendingEntry | None = None
        open_position: Position | None = None
        closed_trades = 0
        states_visited = {state.value}
        self.equity_curve = [{"timestamp": pd.Timestamp(sim_start_ts), "equity": self.risk.equity}]

        m15_timestamps = m15["timestamp"].to_numpy()
        h1_timestamps = h1["timestamp"].to_numpy()
        m15_end = 0
        h1_end = 0
        prev_m15_end = 0
        prev_h1_end = 0

        m15_pullback_active = False
        m15_confirm_idx: int | None = None
        m15_confirm_time: pd.Timestamp | None = None
        m15_state_bias = Bias.NONE
        self._m15_pullback_rsi_ok = False
        self._m15_pullback_start_idx = None
        self._m15_last_reason = "M15_CONFIRM_NOT_READY"
        self.trades_opened_per_day = {}
        self.trades_opened_per_session = {}
        self.regime_state = "NO_TRADE"
        self.regime_since_m15_idx = None
        self.regime_stats = {"TREND": 0, "RANGE": 0, "NO_TRADE": 0}
        self.last_touch_upper_m5_index = None
        self.last_touch_lower_m5_index = None

        for i in range(total_bars):
            row = m5.iloc[i]
            ts = pd.Timestamp(row["timestamp"])
            open_ts = ts - self.bar_delta
            self._ensure_period_baselines(open_ts)

            while m15_end < len(m15_timestamps) and pd.Timestamp(m15_timestamps[m15_end]) <= ts:
                m15_end += 1
            while h1_end < len(h1_timestamps) and pd.Timestamp(h1_timestamps[h1_end]) <= ts:
                h1_end += 1

            m15_last_row = m15.iloc[m15_end - 1] if m15_end > 0 else None
            m15_new_close = m15_end > prev_m15_end
            h1_new_close = h1_end > prev_h1_end

            if h1_new_close:
                bias_context = self._evaluate_h1_bias_fast(h1=h1, h1_end=h1_end)
                prev_h1_end = h1_end
                if bias_context.bias != m15_state_bias:
                    m15_state_bias = bias_context.bias
                    m15_pullback_active = False
                    m15_confirm_idx = None
                    m15_confirm_time = None
                    self._m15_pullback_rsi_ok = False
                    self._m15_pullback_start_idx = None
                    self._m15_last_reason = "NO_H1_BIAS" if bias_context.bias == Bias.NONE else "M15_CONFIRM_NOT_READY"

            if m15_new_close:
                new_start = prev_m15_end
                new_end = m15_end
                for idx in range(new_start, new_end):
                    m15_row = m15.iloc[idx]
                    if bool(m15_row.get("touch_upper", False)):
                        self.last_touch_upper_m5_index = i
                    if bool(m15_row.get("touch_lower", False)):
                        self.last_touch_lower_m5_index = i
                    m15_pullback_active, m15_confirm_idx, m15_confirm_time = self._update_m15_confirmation_fast(
                        bias=bias_context.bias,
                        m15_row=m15_row,
                        m15_index=idx,
                        pullback_active=m15_pullback_active,
                        confirm_idx=m15_confirm_idx,
                        confirm_time=m15_confirm_time,
                    )
                prev_m15_end = m15_end

                if m15_end > 0:
                    if self.ablation_force_regime != "AUTO":
                        self._force_regime_state(
                            ts=ts,
                            m15_index=m15_end - 1,
                            forced_state=self.ablation_force_regime,
                        )
                    else:
                        trend_score, range_score, dominant_reason, atr_rel, slope_h1, ema_sep_h1 = self._evaluate_regime_scores(
                            h1=h1,
                            h1_end=h1_end,
                            current_index=i,
                        )
                        self._update_regime_from_scores(
                            ts=ts,
                            m15_index=m15_end - 1,
                            trend_score=trend_score,
                            range_score=range_score,
                            dominant_reason=dominant_reason,
                            atr_rel=atr_rel,
                            slope=slope_h1,
                            ema_sep=ema_sep_h1,
                        )

            if bias_context.bias == Bias.NONE:
                m15_context = M15Context(confirmation=Confirmation.NO, reason="NO_H1_BIAS")
            elif m15_end == 0:
                m15_context = M15Context(confirmation=Confirmation.NO, reason="NO_M15_BAR")
            else:
                latest_m15_idx = m15_end - 1
                pullback_start_time = (
                    pd.Timestamp(m15.iloc[self._m15_pullback_start_idx]["timestamp"]).to_pydatetime()
                    if self._m15_pullback_start_idx is not None and self._m15_pullback_start_idx < m15_end
                    else None
                )
                touched_zone = pullback_start_time is not None

                if m15_confirm_idx is not None and (latest_m15_idx - m15_confirm_idx) < self.confirm_valid_m15_bars:
                    m15_context = M15Context(
                        confirmation=Confirmation.OK,
                        touched_zone=touched_zone,
                        pullback_start_time=pullback_start_time,
                        confirmation_time=m15_confirm_time.to_pydatetime() if m15_confirm_time is not None else None,
                        reason="M15_CONFIRM_OK",
                    )
                else:
                    reason = "M15_CONFIRM_EXPIRED" if m15_confirm_idx is not None else self._m15_last_reason
                    m15_context = M15Context(
                        confirmation=Confirmation.NO,
                        touched_zone=touched_zone,
                        pullback_start_time=pullback_start_time,
                        confirmation_time=m15_confirm_time.to_pydatetime() if m15_confirm_time is not None else None,
                        reason=reason,
                    )

            self._register_shock(i, ts, row)

            if open_position is None and pending_entry is not None and pending_entry.execute_index == i:
                opened = self._try_execute_pending_entry(
                    pending=pending_entry,
                    row=row,
                    ts=ts,
                    current_index=i,
                    bias_context=bias_context,
                    m15_context=m15_context,
                    state=state,
                )
                pending_entry = None
                if opened is not None:
                    open_position = opened

            if open_position is not None:
                open_mode = open_position.mode
                if (not self.enable_strategy_v4_orb) and open_position.mode == "TREND" and self.regime_state != "TREND":
                    self._schedule_position_exit_next_open(open_position, i, "REGIME_EXIT")
                if (not self.enable_strategy_v4_orb) and open_position.mode == "RANGE" and self.regime_state == "TREND":
                    self._schedule_position_exit_next_open(open_position, i, "KILL_SWITCH_REGIME_FLIP")

                if self.enable_strategy_v3 and self._should_v3_session_close(open_mode, open_ts):
                    if self._close_position_full(
                        position=open_position,
                        timestamp=ts,
                        current_index=i,
                        exit_mid=float(row["open"]),
                        reason="V3_EXIT_SESSION_END",
                        event_state=EngineState.WAIT_M5_ENTRY if self.enable_strategy_v4_orb else EngineState.WAIT_H1_BIAS,
                    ):
                        closed_trades += 1
                        self.cooldown_until_index = i + self.cooldown_after_trade_bars
                        open_position = None

                elif self.force_session_close and self._should_force_session_close(open_ts):
                    if self._close_position_full(
                        position=open_position,
                        timestamp=ts,
                        current_index=i,
                        exit_mid=float(row["open"]),
                        reason="SESSION_FORCED_CLOSE",
                        event_state=EngineState.WAIT_M5_ENTRY if self.enable_strategy_v4_orb else EngineState.WAIT_H1_BIAS,
                    ):
                        closed_trades += 1
                        self.cooldown_until_index = i + self.cooldown_after_trade_bars
                        open_position = None

                elif open_position.pending_exit_index is not None and open_position.pending_exit_index == i:
                    reason = open_position.pending_exit_reason or "RULE_EXIT"
                    if self._close_position_full(
                        position=open_position,
                        timestamp=ts,
                        current_index=i,
                        exit_mid=float(row["open"]),
                        reason=reason,
                        event_state=EngineState.WAIT_M5_ENTRY if self.enable_strategy_v4_orb else EngineState.WAIT_H1_BIAS,
                    ):
                        closed_trades += 1
                        self.cooldown_until_index = i + self.cooldown_after_trade_bars
                        open_position = None

            if open_position is not None:
                was_open = True
                still_open = self._manage_open_position(
                    position=open_position,
                    row=row,
                    ts=ts,
                    current_index=i,
                    m15_last_row=m15_last_row,
                    m15_new_close=m15_new_close,
                )
                if was_open and (not still_open):
                    closed_trades += 1
                    self.cooldown_until_index = i + self.cooldown_after_trade_bars
                    open_position = None

            if open_position is None:
                if self.enable_strategy_v4_orb:
                    state = EngineState.WAIT_M5_ENTRY
                elif self.enable_strategy_v3:
                    if self.regime_state in {"TREND", "RANGE"}:
                        state = EngineState.WAIT_M5_ENTRY
                    else:
                        state = EngineState.WAIT_H1_BIAS
                else:
                    if self.regime_state == "NO_TRADE":
                        state = EngineState.WAIT_H1_BIAS
                    elif self.regime_state == "RANGE":
                        state = EngineState.WAIT_M5_ENTRY
                    else:
                        if bias_context.bias == Bias.NONE:
                            state = EngineState.WAIT_H1_BIAS
                        elif m15_context.confirmation != Confirmation.OK:
                            state = EngineState.WAIT_M15_CONFIRM
                        else:
                            state = EngineState.WAIT_M5_ENTRY
            else:
                state = EngineState.IN_TRADE

            if pending_entry is not None and i < pending_entry.execute_index:
                clear_reason: str | None = None
                if self.enable_strategy_v4_orb:
                    clear_reason = None
                elif self.enable_strategy_v3:
                    if pending_entry.mode != self.regime_state:
                        clear_reason = "REGIME_CHANGED_BEFORE_ENTRY"
                elif pending_entry.mode == "TREND":
                    if self.regime_state != "TREND":
                        clear_reason = "REGIME_NOT_TREND"
                    elif bias_context.bias == Bias.NONE or m15_context.confirmation != Confirmation.OK:
                        clear_reason = "BIAS_OR_CONFIRMATION_LOST"
                elif pending_entry.mode == "RANGE":
                    if self.regime_state != "RANGE":
                        clear_reason = "REGIME_NOT_RANGE"
                if clear_reason is not None:
                    self._log_signal(
                        timestamp=ts.to_pydatetime(),
                        state=state,
                        event_type="PENDING_CLEARED",
                        signal=pending_entry.signal,
                        bias_context=bias_context,
                        m15_context=m15_context,
                        payload_json={"reason": clear_reason, "mode": pending_entry.mode},
                    )
                    pending_entry = None

            if open_position is None and pending_entry is None and state == EngineState.WAIT_M5_ENTRY:
                signal = EntrySignal.NONE
                event_type = "SIGNAL_DETECTED"
                pending_mode = "TREND"
                fixed_sl_mid: float | None = None
                fixed_tp_mid: float | None = None
                setup_reason = ""
                v3_payload: dict[str, Any] | None = None
                v4_payload: dict[str, Any] | None = None

                if self.enable_strategy_v4_orb:
                    signal, event_type, v4_payload = self._evaluate_v4_entry_signal(row=row, signal_ts=ts)
                    pending_mode = "V4_ORB"
                    if signal != EntrySignal.NONE and v4_payload is not None:
                        fixed_sl_mid = float(v4_payload["sl_mid"])
                        setup_reason = str(v4_payload.get("setup_reason", "V4_SESSION_ORB"))
                elif self.enable_strategy_v3:
                    pending_mode = self.regime_state
                    signal, event_type, v3_payload = self._evaluate_v3_entry_signal(row=row, mode=self.regime_state)
                    if signal != EntrySignal.NONE and v3_payload is not None:
                        atr_for_sl = float(v3_payload["atr_t"])
                        if signal == EntrySignal.BUY:
                            fixed_sl_mid = float(row["close"]) - float(v3_payload["sl_dist"])
                            fixed_tp_mid = float(row["close"]) + float(v3_payload["tp_dist"])
                        else:
                            fixed_sl_mid = float(row["close"]) + float(v3_payload["sl_dist"])
                            fixed_tp_mid = float(row["close"]) - float(v3_payload["tp_dist"])
                        setup_reason = "V3_TREND_BREAKOUT" if self.regime_state == "TREND" else "V3_RANGE_RSI"
                        v3_payload["atr_for_sl"] = atr_for_sl
                else:
                    if self.regime_state == "TREND":
                        signal = self._evaluate_m5_entry_fast(row=row, bias=bias_context.bias, m15_confirm=m15_context.confirmation)
                        setup_reason = "TREND_MTF_TRIGGER"
                    elif self.regime_state == "RANGE":
                        pending_mode = "RANGE"
                        event_type = "RANGE_SIGNAL_DETECTED"
                        signal, range_setup = self._evaluate_range_entry_fast(
                            row=row,
                            m15_last_row=m15_last_row,
                            current_index=i,
                        )
                        if range_setup is not None:
                            fixed_sl_mid = float(range_setup["sl_mid"])
                            fixed_tp_mid = float(range_setup["tp_mid"])
                            setup_reason = "RANGE_BAND_REJECTION"

                if signal != EntrySignal.NONE:
                    if i + 1 < total_bars:
                        next_open = float(m5.iloc[i + 1]["open"])
                        if self.enable_strategy_v4_orb and v4_payload is not None and fixed_sl_mid is not None:
                            rr = float(v4_payload["rr"])
                            if signal == EntrySignal.BUY:
                                fixed_tp_mid = next_open + (rr * abs(next_open - fixed_sl_mid))
                            else:
                                fixed_tp_mid = next_open - (rr * abs(next_open - fixed_sl_mid))
                        elif self.enable_strategy_v3 and v3_payload is not None:
                            if signal == EntrySignal.BUY:
                                fixed_sl_mid = next_open - float(v3_payload["sl_dist"])
                                fixed_tp_mid = next_open + float(v3_payload["tp_dist"])
                            else:
                                fixed_sl_mid = next_open + float(v3_payload["sl_dist"])
                                fixed_tp_mid = next_open - float(v3_payload["tp_dist"])
                        pending_entry = PendingEntry(
                            signal=signal,
                            signal_index=i,
                            execute_index=i + 1,
                            signal_ts=ts,
                            swing_low6=float(row["swing_low"]) if pd.notna(row["swing_low"]) else float("nan"),
                            swing_high6=float(row["swing_high"]) if pd.notna(row["swing_high"]) else float("nan"),
                            atr_signal=(
                                float(row["atr_v3"])
                                if (self.enable_strategy_v3 and pd.notna(row["atr_v3"]))
                                else (float(row["atr_m5"]) if pd.notna(row["atr_m5"]) else 0.0)
                            ),
                            trigger_price=float(row["close"]),
                            mode=pending_mode,
                            fixed_sl_mid=fixed_sl_mid,
                            fixed_tp_mid=fixed_tp_mid,
                            regime_state=self.regime_state,
                            cost_multiplier=1.0,
                            setup_reason=setup_reason,
                            signal_high=float(row["high"]) if pd.notna(row["high"]) else None,
                            signal_low=float(row["low"]) if pd.notna(row["low"]) else None,
                        )
                        if self.enable_strategy_v4_orb and v4_payload is not None:
                            direction = "LONG" if signal == EntrySignal.BUY else "SHORT"
                            signal_details = {
                                "strategy": "V4_SESSION_ORB",
                                "direction": direction,
                                "close_t": float(row["close"]),
                                "entry_open_t1": next_open,
                                "entry_ts_t1": pd.Timestamp(m5.iloc[i + 1]["timestamp"]).isoformat(),
                                "asia_high": float(v4_payload["asia_high"]),
                                "asia_low": float(v4_payload["asia_low"]),
                                "buffer": float(v4_payload["buffer"]),
                                "break_level": float(v4_payload["break_level"]),
                                "sl_mid": float(fixed_sl_mid) if fixed_sl_mid is not None else None,
                                "tp_mid": float(fixed_tp_mid) if fixed_tp_mid is not None else None,
                                "rr": float(v4_payload["rr"]),
                                "stop_mode": self.v4_stop_mode,
                                "params": self._v4_active_params(),
                            }
                            self.logger.log_event(ts.to_pydatetime(), event_type, signal_details)
                        elif self.enable_strategy_v3:
                            direction = "LONG" if signal == EntrySignal.BUY else "SHORT"
                            signal_details = {
                                "regime": self.regime_state,
                                "direction": direction,
                                "close_t": float(row["close"]),
                                "entry_open_t1": next_open,
                                "entry_ts_t1": pd.Timestamp(m5.iloc[i + 1]["timestamp"]).isoformat(),
                                "atr_t": float(row["atr_v3"]) if pd.notna(row["atr_v3"]) else None,
                                "atr_ma_t": float(row["atr_ma_v3"]) if pd.notna(row["atr_ma_v3"]) else None,
                                "rsi_t": float(row["rsi_v3"]) if pd.notna(row["rsi_v3"]) else None,
                                "n1_high": float(row["v3_hh_prev"]) if pd.notna(row["v3_hh_prev"]) else None,
                                "n1_low": float(row["v3_ll_prev"]) if pd.notna(row["v3_ll_prev"]) else None,
                                "sl_dist": abs(next_open - float(fixed_sl_mid)) if fixed_sl_mid is not None else None,
                                "tp_dist": abs(float(fixed_tp_mid) - next_open) if fixed_tp_mid is not None else None,
                                "params": self._v3_active_params(),
                            }
                            self.logger.log_event(ts.to_pydatetime(), event_type, signal_details)
                        self._log_signal(
                            timestamp=ts.to_pydatetime(),
                            state=state,
                            event_type=event_type,
                            signal=signal,
                            bias_context=bias_context,
                            m15_context=m15_context,
                            entry_price_candidate=float(row["close"]),
                            entry_price_side="MID",
                            payload_json={
                                "signal_index": i,
                                "execute_index": i + 1,
                                "mode": pending_mode,
                                "regime": self.regime_state,
                                "setup_reason": setup_reason,
                                "trigger_price": float(row["close"]),
                                "swing_low6": float(row["swing_low"]) if pd.notna(row["swing_low"]) else None,
                                "swing_high6": float(row["swing_high"]) if pd.notna(row["swing_high"]) else None,
                                "atr_signal": (
                                    float(row["atr_v3"])
                                    if (self.enable_strategy_v3 and pd.notna(row["atr_v3"]))
                                    else (float(row["atr_m5"]) if pd.notna(row["atr_m5"]) else None)
                                ),
                                "fixed_sl_mid": fixed_sl_mid,
                                "fixed_tp_mid": fixed_tp_mid,
                                "v3": self.enable_strategy_v3,
                                "v3_payload": v3_payload or {},
                                "v4": self.enable_strategy_v4_orb,
                            },
                        )
                        self._log_signal(
                            timestamp=ts.to_pydatetime(),
                            state=state,
                            event_type="PENDING_SET",
                            signal=signal,
                            bias_context=bias_context,
                            m15_context=m15_context,
                            payload_json={"execute_index": i + 1, "mode": pending_mode, "regime": self.regime_state},
                        )
                    elif self.enable_strategy_v3:
                        self.logger.log_event(
                            ts.to_pydatetime(),
                            "V3_BLOCK_NO_NEXT_BAR",
                            {
                                "regime": self.regime_state,
                                "direction": "LONG" if signal == EntrySignal.BUY else "SHORT",
                                "close_t": float(row["close"]),
                                "params": self._v3_active_params(),
                            },
                        )
                    elif self.enable_strategy_v4_orb:
                        self.logger.log_event(
                            ts.to_pydatetime(),
                            "V4_BLOCK_NO_NEXT_BAR",
                            {"strategy": "V4_SESSION_ORB", "close_t": float(row["close"]), "params": self._v4_active_params()},
                        )
                    else:
                        self._log_signal(
                            timestamp=ts.to_pydatetime(),
                            state=state,
                            event_type="PENDING_IGNORED",
                            signal=signal,
                            bias_context=bias_context,
                            m15_context=m15_context,
                            payload_json={"reason": "NO_NEXT_BAR", "mode": pending_mode},
                        )
                elif self.enable_strategy_v3 and event_type.startswith("V3_BLOCK_"):
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        event_type,
                        {
                            "regime": self.regime_state,
                            "close_t": float(row["close"]),
                            "atr_t": float(row["atr_v3"]) if pd.notna(row["atr_v3"]) else None,
                            "atr_ma_t": float(row["atr_ma_v3"]) if pd.notna(row["atr_ma_v3"]) else None,
                            "rsi_t": float(row["rsi_v3"]) if pd.notna(row["rsi_v3"]) else None,
                            "n1_high": float(row["v3_hh_prev"]) if pd.notna(row["v3_hh_prev"]) else None,
                            "n1_low": float(row["v3_ll_prev"]) if pd.notna(row["v3_ll_prev"]) else None,
                                "params": self._v3_active_params(),
                            },
                        )
                elif self.enable_strategy_v4_orb and event_type.startswith("V4_BLOCK_"):
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        event_type,
                        {
                            "strategy": "V4_SESSION_ORB",
                            "close_t": float(row["close"]),
                            "atr_t": float(row["atr_v4"]) if pd.notna(row["atr_v4"]) else None,
                            "params": self._v4_active_params(),
                        },
                    )

            self.regime_stats[self.regime_state] = int(self.regime_stats.get(self.regime_state, 0)) + 1

            if next_progress_ts is not None and ts >= next_progress_ts:
                elapsed_seconds = max((ts.to_pydatetime() - sim_start_ts).total_seconds(), 0.0)
                progress_pct = max(0.0, min(100.0, (elapsed_seconds / total_seconds) * 100.0))
                elapsed_days = elapsed_seconds / 86400.0
                self._print_progress(
                    ts=ts,
                    bars_done=i + 1,
                    bars_total=total_bars,
                    elapsed_days=elapsed_days,
                    total_days=sim_days,
                    progress_pct=progress_pct,
                    closed_trades=closed_trades,
                )
                while next_progress_ts is not None and ts >= next_progress_ts:
                    next_progress_ts = next_progress_ts + progress_step  # type: ignore[operator]

            states_visited.add(state.value)

        if open_position is not None:
            last_row = m5.iloc[-1]
            last_ts = pd.Timestamp(last_row["timestamp"])
            self._close_position_full(
                position=open_position,
                timestamp=last_ts,
                current_index=total_bars - 1,
                exit_mid=float(last_row["close"]),
                reason="END_OF_DATA",
                event_state=EngineState.WAIT_M5_ENTRY if self.enable_strategy_v4_orb else EngineState.WAIT_H1_BIAS,
            )
            closed_trades += 1

        return {
            "events_path": str(self.logger.events_path),
            "trades_path": str(self.logger.trades_path),
            "signals_path": str(self.logger.signals_path),
            "fills_path": str(self.logger.fills_path),
            "sim_start_ts": sim_start_ts.isoformat(),
            "sim_end_ts": sim_end_ts.isoformat(),
            "sim_days": round(sim_days, 4),
            "states_visited": sorted(states_visited),
            "closed_trades": closed_trades,
            "final_equity": round(self.risk.equity, 2),
            "equity_curve": pd.DataFrame(self.equity_curve),
            "regime_stats": dict(self.regime_stats),
        }

    def _prepare_m5(self, m5_df: pd.DataFrame) -> pd.DataFrame:
        m5 = m5_df.sort_values("timestamp").reset_index(drop=True).copy()
        m5["tr_m5"] = true_range(m5)
        m5["atr_m5"] = atr_wilder(m5, self.atr_period)
        m5["atr_v4"] = atr_wilder(m5, self.v4_atr_period)
        m5["atr_v3"] = atr_wilder(m5, self.v3_atr_period_M)
        m5["atr_ma_v3"] = m5["atr_v3"].rolling(self.v3_atr_period_M, min_periods=self.v3_atr_period_M).mean()
        m5["rsi_v3"] = rsi_wilder(m5["close"], self.v3_rsi_period)
        m5["v3_hh_prev"] = (
            m5["high"]
            .rolling(self.v3_breakout_N1, min_periods=self.v3_breakout_N1)
            .max()
            .shift(1)
        )
        m5["v3_ll_prev"] = (
            m5["low"]
            .rolling(self.v3_breakout_N1, min_periods=self.v3_breakout_N1)
            .min()
            .shift(1)
        )
        m5["ema20_m5"] = ema(m5["close"], self.ema_m5)
        m5["hh_prev"] = m5["high"].rolling(self.bos_lookback, min_periods=self.bos_lookback).max().shift(1)
        m5["ll_prev"] = m5["low"].rolling(self.bos_lookback, min_periods=self.bos_lookback).min().shift(1)
        m5["swing_low"] = m5["low"].rolling(self.swing_lookback, min_periods=self.swing_lookback).min()
        m5["swing_high"] = m5["high"].rolling(self.swing_lookback, min_periods=self.swing_lookback).max()
        rng = (m5["high"] - m5["low"]).clip(lower=0.0)
        body = (m5["close"] - m5["open"]).abs()
        upper_wick = m5["high"] - m5[["open", "close"]].max(axis=1)
        lower_wick = m5[["open", "close"]].min(axis=1) - m5["low"]
        m5["body_ratio"] = (body / rng.replace(0.0, float("nan"))).astype("float64").fillna(0.0)
        m5["upper_wick_ratio"] = (upper_wick / rng.replace(0.0, float("nan"))).astype("float64").fillna(1.0)
        m5["lower_wick_ratio"] = (lower_wick / rng.replace(0.0, float("nan"))).astype("float64").fillna(1.0)
        m5["wick_ok_long"] = m5["upper_wick_ratio"] <= self.wick_ratio_max
        m5["wick_ok_short"] = m5["lower_wick_ratio"] <= self.wick_ratio_max
        m5["strong_bull"] = (m5["close"] > m5["open"]) & (m5["body_ratio"] >= self.body_ratio)
        m5["strong_bear"] = (m5["close"] < m5["open"]) & (m5["body_ratio"] >= self.body_ratio)

        minute_utc = (m5["timestamp"].dt.hour * 60) + m5["timestamp"].dt.minute
        day_key = m5["timestamp"].dt.date
        asia_mask = minute_utc.apply(lambda m: self._in_any_window(int(m), [(self.v4_asia_start, self.v4_asia_end)]))
        asia_slice = m5.loc[asia_mask].copy()
        if asia_slice.empty:
            m5["v4_asia_high"] = pd.NA
            m5["v4_asia_low"] = pd.NA
        else:
            asia_day = asia_slice["timestamp"].dt.date
            asia_high_by_day = asia_slice.groupby(asia_day)["high"].max()
            asia_low_by_day = asia_slice.groupby(asia_day)["low"].min()
            m5["v4_asia_high"] = day_key.map(asia_high_by_day)
            m5["v4_asia_low"] = day_key.map(asia_low_by_day)
        return m5

    def _prepare_m15(self, m5: pd.DataFrame) -> pd.DataFrame:
        m15 = resample_from_m5(m5, "15min")
        m15["ema20_m15"] = ema(m15["close"], self.ema_m15)
        m15["ema50_m15"] = ema(m15["close"], 50)
        m15["rsi14_m15"] = rsi_wilder(m15["close"], self.rsi_period_m15)
        m15["atr_m15"] = atr_wilder(m15, self.atr_period)
        m15["range_mid"] = m15["ema20_m15"]
        m15["range_band"] = self.k_atr_range * m15["atr_m15"]
        m15["range_upper"] = m15["range_mid"] + m15["range_band"]
        m15["range_lower"] = m15["range_mid"] - m15["range_band"]
        m15["touch_upper"] = m15["high"] >= m15["range_upper"]
        m15["touch_lower"] = m15["low"] <= m15["range_lower"]
        return m15

    def _prepare_h1(self, m5: pd.DataFrame) -> pd.DataFrame:
        h1 = resample_from_m5(m5, "1h")
        h1["ema50_h1"] = ema(h1["close"], self.ema_h1_fast)
        h1["ema200_h1"] = ema(h1["close"], self.ema_h1_slow)
        h1["atr_h1"] = atr_wilder(h1, self.atr_period)
        h1["atr_h1_sma"] = h1["atr_h1"].rolling(self.atr_rel_lookback, min_periods=self.atr_rel_lookback).mean()
        h1["atr_h1_rel"] = (h1["atr_h1"] / h1["atr_h1_sma"]).replace([float("inf"), float("-inf")], pd.NA)
        return h1

    def _evaluate_h1_bias_fast(self, h1: pd.DataFrame, h1_end: int) -> BiasContext:
        if h1_end <= 0:
            return BiasContext(bias=Bias.NONE, reason="NO_H1_BAR")
        last_idx = h1_end - 1
        if last_idx - self.h1_bias_slope_lookback < 0:
            return BiasContext(bias=Bias.NONE, reason="NOT_ENOUGH_H1_FOR_SLOPE")

        row = h1.iloc[last_idx]
        prev = h1.iloc[last_idx - self.h1_bias_slope_lookback]
        ema_fast = float(row["ema50_h1"]) if pd.notna(row["ema50_h1"]) else float("nan")
        ema_slow = float(row["ema200_h1"]) if pd.notna(row["ema200_h1"]) else float("nan")
        close = float(row["close"])
        atr = float(row["atr_h1"]) if pd.notna(row["atr_h1"]) else 0.0
        ema_fast_prev = float(prev["ema50_h1"]) if pd.notna(prev["ema50_h1"]) else float("nan")
        if pd.isna(ema_fast) or pd.isna(ema_slow) or pd.isna(ema_fast_prev):
            return BiasContext(bias=Bias.NONE, reason="H1_EMA_NA")
        slope = ema_fast - ema_fast_prev
        ema_sep = abs(ema_fast - ema_slow)
        if ema_sep < (self.h1_min_sep_atr_mult * atr):
            return BiasContext(bias=Bias.NONE, reason="H1_BIAS_NONE_FLAT")

        if (ema_fast > ema_slow) and (close > ema_slow + self.h1_bias_atr_mult * atr) and (slope > 0):
            return BiasContext(bias=Bias.LONG, reason="H1_BIAS_LONG")
        if (ema_fast < ema_slow) and (close < ema_slow - self.h1_bias_atr_mult * atr) and (slope < 0):
            return BiasContext(bias=Bias.SHORT, reason="H1_BIAS_SHORT")
        return BiasContext(bias=Bias.NONE, reason="H1_BIAS_NONE")

    @staticmethod
    def _parse_windows(raw: Any) -> list[tuple[int, int]]:
        windows: list[tuple[int, int]] = []
        if not isinstance(raw, list):
            return windows
        for item in raw:
            if not isinstance(item, str) or "-" not in item:
                continue
            start_raw, end_raw = item.split("-", 1)
            start = SimulationEngine._hhmm_to_minutes(start_raw.strip())
            end = SimulationEngine._hhmm_to_minutes(end_raw.strip())
            if start == end:
                continue
            windows.append((start, end))
        return windows

    @staticmethod
    def _in_any_window(minute: int, windows: list[tuple[int, int]]) -> bool:
        for start, end in windows:
            if start < end:
                if start <= minute < end:
                    return True
            else:
                if minute >= start or minute < end:
                    return True
        return False

    def _session_mode_allowed(self, mode: str, open_ts: pd.Timestamp) -> tuple[bool, str]:
        minute = int(open_ts.hour) * 60 + int(open_ts.minute)
        if self._in_any_window(minute, self.blocked_windows):
            return False, "BLOCKED_WINDOW"
        mode_windows = self.trend_sessions if mode == "TREND" else self.range_sessions
        if self._in_any_window(minute, mode_windows):
            return True, "MODE_WINDOW_OK"
        return False, "OUTSIDE_MODE_WINDOW"

    def _hour_trade_filter_rule(self, open_ts: pd.Timestamp) -> str | None:
        hour = int(open_ts.hour)
        if self.hour_whitelist_utc and (hour not in self.hour_whitelist_utc):
            return "HOUR_NOT_IN_WHITELIST"
        if self.hour_blacklist_utc and (hour in self.hour_blacklist_utc):
            return "HOUR_BLACKLIST"
        return None

    def _effective_cost_multiplier(self, open_ts: pd.Timestamp, mode: str, in_mode_session: bool) -> tuple[float, str]:
        minute = int(open_ts.hour) * 60 + int(open_ts.minute)
        asia = minute < (6 * 60)
        if in_mode_session:
            return self.cost_mult_trend_session, "MODE_SESSION"
        if asia:
            return self.cost_mult_asia, "ASIA"
        return self.cost_mult_off_session, "OFF_SESSION"

    def _active_mode_window_label(self, mode: str, open_ts: pd.Timestamp) -> str | None:
        minute = int(open_ts.hour) * 60 + int(open_ts.minute)
        windows = self.trend_sessions if mode == "TREND" else self.range_sessions
        for idx, (start, end) in enumerate(windows):
            in_window = (start <= minute < end) if start < end else (minute >= start or minute < end)
            if in_window:
                return f"{idx}:{start:04d}-{end:04d}"
        return None

    def _v3_session_key(self, mode: str, open_ts: pd.Timestamp) -> str:
        label = self._active_mode_window_label(mode, open_ts)
        day = open_ts.date().isoformat()
        return f"{day}|{label or 'NO_WINDOW'}"

    def _should_v3_session_close(self, mode: str, open_ts: pd.Timestamp) -> bool:
        if not self.close_at_session_end:
            return False
        return self._active_mode_window_label(mode, open_ts) is None

    def _v3_active_params(self) -> dict[str, Any]:
        return {
            "enable_strategy_v3": self.enable_strategy_v3,
            "v3_breakout_N1": self.v3_breakout_N1,
            "v3_atr_period_M": self.v3_atr_period_M,
            "v3_k_trend": self.v3_k_trend,
            "v3_k_range": self.v3_k_range,
            "v3_atr_sl_trend": self.v3_atr_sl_trend,
            "v3_rr_trend": self.v3_rr_trend,
            "v3_rsi_period": self.v3_rsi_period,
            "v3_atr_sl_range": self.v3_atr_sl_range,
            "v3_rr_range": self.v3_rr_range,
            "max_trades_per_session": self.max_trades_per_session,
            "close_at_session_end": self.close_at_session_end,
        }

    def _v4_active_params(self) -> dict[str, Any]:
        return {
            "strategy_family": self.strategy_family,
            "asia_start": f"{self.v4_asia_start // 60:02d}:{self.v4_asia_start % 60:02d}",
            "asia_end": f"{self.v4_asia_end // 60:02d}:{self.v4_asia_end % 60:02d}",
            "trade_start": f"{self.v4_trade_start // 60:02d}:{self.v4_trade_start % 60:02d}",
            "trade_end": f"{self.v4_trade_end // 60:02d}:{self.v4_trade_end % 60:02d}",
            "buffer_atr_mult": self.v4_buffer_atr_mult,
            "stop_buffer_atr_mult": self.v4_stop_buffer_atr_mult,
            "atr_period": self.v4_atr_period,
            "rr": self.v4_rr,
            "time_stop": self.v4_time_stop,
            "exit_at_trade_end": self.v4_exit_at_trade_end,
            "stop_mode": self.v4_stop_mode,
        }

    def _evaluate_v4_entry_signal(
        self,
        row: pd.Series,
        signal_ts: pd.Timestamp,
    ) -> tuple[EntrySignal, str, dict[str, Any] | None]:
        minute = int(signal_ts.hour) * 60 + int(signal_ts.minute)
        trade_window = self._in_any_window(minute, [(self.v4_trade_start, self.v4_trade_end)])
        if not trade_window:
            return EntrySignal.NONE, "V4_BLOCK_OUTSIDE_TRADE_WINDOW", None

        ts = pd.Timestamp(row["timestamp"])
        asia_high = float(row["v4_asia_high"]) if pd.notna(row["v4_asia_high"]) else float("nan")
        asia_low = float(row["v4_asia_low"]) if pd.notna(row["v4_asia_low"]) else float("nan")
        if pd.isna(asia_high) or pd.isna(asia_low):
            return EntrySignal.NONE, "V4_BLOCK_NO_ASIA_BOX", None

        # For non-wrapping windows, only allow signals after Asia close.
        if self._in_any_window(minute, [(self.v4_asia_start, self.v4_asia_end)]):
            return EntrySignal.NONE, "V4_BLOCK_ASIA_STILL_OPEN", None
        if minute < self.v4_asia_end and self.v4_asia_start < self.v4_asia_end:
            return EntrySignal.NONE, "V4_BLOCK_ASIA_NOT_FINALIZED", None

        close_t = float(row["close"])
        atr_t = float(row["atr_v4"]) if pd.notna(row["atr_v4"]) else float("nan")
        if pd.isna(atr_t) or atr_t <= 0.0:
            return EntrySignal.NONE, "V4_BLOCK_ATR_NA", None
        buffer = self.v4_buffer_atr_mult * atr_t
        stop_buffer = self.v4_stop_buffer_atr_mult * atr_t

        long_break = close_t > (asia_high + buffer)
        short_break = close_t < (asia_low - buffer)
        if (not long_break) and (not short_break):
            return EntrySignal.NONE, "V4_BLOCK_NO_BREAKOUT", None

        if long_break:
            if self.v4_stop_mode == "break_wick":
                sl_mid = float(row["low"]) - stop_buffer
                setup_reason = "V4_ORB_BREAK_WICK_LONG"
            else:
                sl_mid = asia_low - stop_buffer
                setup_reason = "V4_ORB_BOX_LONG"
            payload = {
                "direction": "LONG",
                "asia_high": asia_high,
                "asia_low": asia_low,
                "buffer": buffer,
                "break_level": asia_high + buffer,
                "rr": self.v4_rr,
                "sl_mid": sl_mid,
                "atr_t": atr_t,
                "signal_ts": ts.isoformat(),
                "setup_reason": setup_reason,
                "params": self._v4_active_params(),
            }
            return EntrySignal.BUY, "V4_SIGNAL_ORB_BREAKOUT", payload

        if self.v4_stop_mode == "break_wick":
            sl_mid = float(row["high"]) + stop_buffer
            setup_reason = "V4_ORB_BREAK_WICK_SHORT"
        else:
            sl_mid = asia_high + stop_buffer
            setup_reason = "V4_ORB_BOX_SHORT"
        payload = {
            "direction": "SHORT",
            "asia_high": asia_high,
            "asia_low": asia_low,
            "buffer": buffer,
            "break_level": asia_low - buffer,
            "rr": self.v4_rr,
            "sl_mid": sl_mid,
            "atr_t": atr_t,
            "signal_ts": ts.isoformat(),
            "setup_reason": setup_reason,
            "params": self._v4_active_params(),
        }
        return EntrySignal.SELL, "V4_SIGNAL_ORB_BREAKOUT", payload

    def _evaluate_v3_entry_signal(
        self,
        row: pd.Series,
        mode: str,
    ) -> tuple[EntrySignal, str, dict[str, Any] | None]:
        close_t = float(row["close"])
        atr_t = float(row["atr_v3"]) if pd.notna(row["atr_v3"]) else float("nan")
        atr_ma_t = float(row["atr_ma_v3"]) if pd.notna(row["atr_ma_v3"]) else float("nan")
        rsi_t = float(row["rsi_v3"]) if pd.notna(row["rsi_v3"]) else float("nan")
        n1_high = float(row["v3_hh_prev"]) if pd.notna(row["v3_hh_prev"]) else float("nan")
        n1_low = float(row["v3_ll_prev"]) if pd.notna(row["v3_ll_prev"]) else float("nan")

        if pd.isna(atr_t) or pd.isna(atr_ma_t) or atr_t <= 0.0 or atr_ma_t <= 0.0:
            return EntrySignal.NONE, "V3_BLOCK_INDICATOR_NA", None

        if mode == "TREND":
            if atr_t < (self.v3_k_trend * atr_ma_t):
                return EntrySignal.NONE, "V3_BLOCK_TREND_ATR_FILTER", None
            if pd.notna(n1_high) and close_t > n1_high:
                sl_dist = self.v3_atr_sl_trend * atr_t
                tp_dist = self.v3_rr_trend * sl_dist
                payload = {
                    "regime": mode,
                    "direction": "LONG",
                    "close_t": close_t,
                    "atr_t": atr_t,
                    "atr_ma_t": atr_ma_t,
                    "rsi_t": rsi_t,
                    "n1_high": n1_high,
                    "n1_low": n1_low,
                    "sl_dist": sl_dist,
                    "tp_dist": tp_dist,
                    "params": self._v3_active_params(),
                }
                return EntrySignal.BUY, "V3_SIGNAL_TREND_BREAKOUT", payload
            if pd.notna(n1_low) and close_t < n1_low:
                sl_dist = self.v3_atr_sl_trend * atr_t
                tp_dist = self.v3_rr_trend * sl_dist
                payload = {
                    "regime": mode,
                    "direction": "SHORT",
                    "close_t": close_t,
                    "atr_t": atr_t,
                    "atr_ma_t": atr_ma_t,
                    "rsi_t": rsi_t,
                    "n1_high": n1_high,
                    "n1_low": n1_low,
                    "sl_dist": sl_dist,
                    "tp_dist": tp_dist,
                    "params": self._v3_active_params(),
                }
                return EntrySignal.SELL, "V3_SIGNAL_TREND_BREAKOUT", payload
            return EntrySignal.NONE, "V3_BLOCK_TREND_NO_BREAKOUT", None

        if mode == "RANGE":
            if atr_t > (self.v3_k_range * atr_ma_t):
                return EntrySignal.NONE, "V3_BLOCK_RANGE_ATR_FILTER", None
            if pd.notna(rsi_t) and rsi_t <= 30.0:
                sl_dist = self.v3_atr_sl_range * atr_t
                tp_dist = self.v3_rr_range * sl_dist
                payload = {
                    "regime": mode,
                    "direction": "LONG",
                    "close_t": close_t,
                    "atr_t": atr_t,
                    "atr_ma_t": atr_ma_t,
                    "rsi_t": rsi_t,
                    "n1_high": n1_high,
                    "n1_low": n1_low,
                    "sl_dist": sl_dist,
                    "tp_dist": tp_dist,
                    "params": self._v3_active_params(),
                }
                return EntrySignal.BUY, "V3_SIGNAL_RANGE_RSI", payload
            if pd.notna(rsi_t) and rsi_t >= 70.0:
                sl_dist = self.v3_atr_sl_range * atr_t
                tp_dist = self.v3_rr_range * sl_dist
                payload = {
                    "regime": mode,
                    "direction": "SHORT",
                    "close_t": close_t,
                    "atr_t": atr_t,
                    "atr_ma_t": atr_ma_t,
                    "rsi_t": rsi_t,
                    "n1_high": n1_high,
                    "n1_low": n1_low,
                    "sl_dist": sl_dist,
                    "tp_dist": tp_dist,
                    "params": self._v3_active_params(),
                }
                return EntrySignal.SELL, "V3_SIGNAL_RANGE_RSI", payload
            return EntrySignal.NONE, "V3_BLOCK_RANGE_RSI_FILTER", None

        return EntrySignal.NONE, "V3_BLOCK_REGIME_NOT_ALLOWED", None

    def _evaluate_regime_scores(
        self,
        h1: pd.DataFrame,
        h1_end: int,
        current_index: int,
    ) -> tuple[int, int, str, float, float, float]:
        if h1_end <= 0:
            return 0, 0, "REGIME_NO_H1", 0.0, 0.0, 0.0
        last_idx = h1_end - 1
        if last_idx - self.h1_bias_slope_lookback < 0:
            return 0, 0, "REGIME_NOT_ENOUGH_H1", 0.0, 0.0, 0.0

        row = h1.iloc[last_idx]
        prev = h1.iloc[last_idx - self.h1_bias_slope_lookback]
        ema_fast = float(row["ema50_h1"]) if pd.notna(row["ema50_h1"]) else float("nan")
        ema_slow = float(row["ema200_h1"]) if pd.notna(row["ema200_h1"]) else float("nan")
        atr_h1 = float(row["atr_h1"]) if pd.notna(row["atr_h1"]) else 0.0
        atr_rel = float(row["atr_h1_rel"]) if pd.notna(row["atr_h1_rel"]) else 0.0
        ema_fast_prev = float(prev["ema50_h1"]) if pd.notna(prev["ema50_h1"]) else float("nan")
        if pd.isna(ema_fast) or pd.isna(ema_slow) or pd.isna(ema_fast_prev) or atr_h1 <= 0.0:
            return 0, 0, "REGIME_INVALID_H1_DATA", atr_rel, 0.0, 0.0

        slope = ema_fast - ema_fast_prev
        ema_sep = abs(ema_fast - ema_slow)
        shock_active = current_index <= self.shock_block_until_index

        trend_score = 0
        range_score = 0

        # Regla coherente direccional: separacion y pendiente en la misma direccion.
        if (ema_fast > ema_slow and slope > 0.0) or (ema_fast < ema_slow and slope < 0.0):
            trend_score += 1
        if ema_sep >= self.h1_min_sep_atr_mult * atr_h1:
            trend_score += 1
        if abs(slope) >= self.h1_slope_min_atr_mult * atr_h1:
            trend_score += 1
        if atr_rel >= self.atr_rel_trend_min:
            trend_score += 1
        if shock_active:
            trend_score -= 1
        if atr_rel <= self.atr_rel_dead_max:
            trend_score -= 1

        if ema_sep <= self.h1_range_max_sep_atr_mult * atr_h1:
            range_score += 1
        if abs(slope) <= self.h1_range_max_slope_atr_mult * atr_h1:
            range_score += 1
        if atr_rel <= self.atr_rel_range_max:
            range_score += 1
        if shock_active:
            range_score -= 1

        dominant_reason = "SCORE_NO_EDGE"
        if shock_active:
            dominant_reason = "SHOCK_BLOCK"
        elif atr_rel <= self.atr_rel_dead_max:
            dominant_reason = "DEAD_ATR"
        elif trend_score >= self.regime_trend_enter_score:
            dominant_reason = "SCORE_TREND_OK"
        elif range_score >= self.regime_range_enter_score:
            dominant_reason = "SCORE_RANGE_OK"
        return trend_score, range_score, dominant_reason, atr_rel, slope, ema_sep

    def _update_regime_from_scores(
        self,
        ts: pd.Timestamp,
        m15_index: int,
        trend_score: int,
        range_score: int,
        dominant_reason: str,
        atr_rel: float,
        slope: float,
        ema_sep: float,
    ) -> None:
        current = self.regime_state
        if current == "TREND":
            min_bars = self.trend_min_bars_m15
        elif current == "RANGE":
            min_bars = self.range_min_bars_m15
        else:
            min_bars = 0

        if self.regime_since_m15_idx is not None and current in {"TREND", "RANGE"}:
            bars_in_regime = m15_index - self.regime_since_m15_idx
            if bars_in_regime < min_bars:
                return

        target = current
        if current == "TREND":
            if trend_score < self.regime_trend_exit_score:
                if range_score >= self.regime_range_enter_score:
                    target = "RANGE"
                else:
                    target = "NO_TRADE"
        elif current == "RANGE":
            if range_score < self.regime_range_exit_score:
                if trend_score >= self.regime_trend_enter_score:
                    target = "TREND"
                else:
                    target = "NO_TRADE"
        else:
            if trend_score >= self.regime_trend_enter_score:
                target = "TREND"
            elif range_score >= self.regime_range_enter_score:
                target = "RANGE"
            else:
                target = "NO_TRADE"

        if target == current:
            return

        self._apply_regime_transition(
            ts=ts,
            m15_index=m15_index,
            target=target,
            trend_score=trend_score,
            range_score=range_score,
            dominant_reason=dominant_reason,
            atr_rel=atr_rel,
            slope=slope,
            ema_sep=ema_sep,
        )

    def _force_regime_state(self, ts: pd.Timestamp, m15_index: int, forced_state: str) -> None:
        target = forced_state if forced_state in {"TREND", "RANGE", "NO_TRADE"} else "NO_TRADE"
        self._apply_regime_transition(
            ts=ts,
            m15_index=m15_index,
            target=target,
            trend_score=0,
            range_score=0,
            dominant_reason="ABLATION_FORCE_REGIME",
            atr_rel=0.0,
            slope=0.0,
            ema_sep=0.0,
        )

    def _apply_regime_transition(
        self,
        ts: pd.Timestamp,
        m15_index: int,
        target: str,
        trend_score: int,
        range_score: int,
        dominant_reason: str,
        atr_rel: float,
        slope: float,
        ema_sep: float,
    ) -> None:
        current = self.regime_state
        if target == current:
            return

        details = {
            "from": current,
            "to": target,
            "trend_score": trend_score,
            "range_score": range_score,
            "reason": dominant_reason,
            "atr_rel": atr_rel,
            "slope_h1": slope,
            "ema_sep_h1": ema_sep,
        }

        if current == "TREND":
            self.logger.log_event(ts.to_pydatetime(), "REGIME_TREND_EXIT", details)
        elif current == "RANGE":
            self.logger.log_event(ts.to_pydatetime(), "REGIME_RANGE_EXIT", details)

        if target == "TREND":
            self.logger.log_event(ts.to_pydatetime(), "REGIME_TREND_ENTER", details)
        elif target == "RANGE":
            self.logger.log_event(ts.to_pydatetime(), "REGIME_RANGE_ENTER", details)
        else:
            self.logger.log_event(ts.to_pydatetime(), "REGIME_NO_TRADE_ENTER", details)

        if current == "TREND":
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=EngineState.WAIT_H1_BIAS,
                event_type="REGIME_TREND_EXIT",
                payload_json=details,
            )
        elif current == "RANGE":
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=EngineState.WAIT_H1_BIAS,
                event_type="REGIME_RANGE_EXIT",
                payload_json=details,
            )
        if target == "TREND":
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=EngineState.WAIT_H1_BIAS,
                event_type="REGIME_TREND_ENTER",
                payload_json=details,
            )
        elif target == "RANGE":
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=EngineState.WAIT_H1_BIAS,
                event_type="REGIME_RANGE_ENTER",
                payload_json=details,
            )
        else:
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=EngineState.WAIT_H1_BIAS,
                event_type="REGIME_NO_TRADE_ENTER",
                payload_json=details,
            )

        self.regime_state = target
        self.regime_since_m15_idx = m15_index

    def _evaluate_range_entry_fast(
        self,
        row: pd.Series,
        m15_last_row: pd.Series | None,
        current_index: int,
    ) -> tuple[EntrySignal, dict[str, float] | None]:
        if m15_last_row is None:
            return EntrySignal.NONE, None
        atr_m5 = float(row["atr_m5"]) if pd.notna(row["atr_m5"]) else 0.0
        if atr_m5 <= 0.0:
            return EntrySignal.NONE, None

        m15_mid = float(m15_last_row["range_mid"]) if pd.notna(m15_last_row["range_mid"]) else float("nan")
        m15_upper = float(m15_last_row["range_upper"]) if pd.notna(m15_last_row["range_upper"]) else float("nan")
        m15_lower = float(m15_last_row["range_lower"]) if pd.notna(m15_last_row["range_lower"]) else float("nan")
        m15_atr = float(m15_last_row["atr_m15"]) if pd.notna(m15_last_row["atr_m15"]) else 0.0
        m15_rsi = float(m15_last_row["rsi14_m15"]) if pd.notna(m15_last_row["rsi14_m15"]) else float("nan")
        if pd.isna(m15_mid) or pd.isna(m15_upper) or pd.isna(m15_lower) or m15_atr <= 0.0:
            return EntrySignal.NONE, None

        close = float(row["close"])
        body_ratio = float(row["body_ratio"]) if pd.notna(row["body_ratio"]) else 0.0
        upper_wick = float(row["upper_wick_ratio"]) if pd.notna(row["upper_wick_ratio"]) else 0.0
        lower_wick = float(row["lower_wick_ratio"]) if pd.notna(row["lower_wick_ratio"]) else 0.0
        touch_upper_age = (
            (current_index - self.last_touch_upper_m5_index)
            if self.last_touch_upper_m5_index is not None
            else None
        )
        touch_lower_age = (
            (current_index - self.last_touch_lower_m5_index)
            if self.last_touch_lower_m5_index is not None
            else None
        )
        touch_valid_upper = touch_upper_age is not None and touch_upper_age <= self.range_touch_ttl_m5_bars
        touch_valid_lower = touch_lower_age is not None and touch_lower_age <= self.range_touch_ttl_m5_bars

        if (
            touch_valid_upper
            and close < m15_upper
            and upper_wick >= self.range_reject_wick_min
            and body_ratio >= self.range_body_min
            and pd.notna(m15_rsi)
            and m15_rsi >= self.range_rsi_short_min
        ):
            sl_mid = m15_upper + (self.range_sl_atr_buffer * m15_atr)
            return EntrySignal.SELL, {
                "sl_mid": sl_mid,
                "tp_mid": m15_mid,
                "atr_m15": m15_atr,
                "rsi_m15": m15_rsi,
                "touch_age": float(touch_upper_age if touch_upper_age is not None else -1),
            }

        if (
            touch_valid_lower
            and close > m15_lower
            and lower_wick >= self.range_reject_wick_min
            and body_ratio >= self.range_body_min
            and pd.notna(m15_rsi)
            and m15_rsi <= self.range_rsi_long_max
        ):
            sl_mid = m15_lower - (self.range_sl_atr_buffer * m15_atr)
            return EntrySignal.BUY, {
                "sl_mid": sl_mid,
                "tp_mid": m15_mid,
                "atr_m15": m15_atr,
                "rsi_m15": m15_rsi,
                "touch_age": float(touch_lower_age if touch_lower_age is not None else -1),
            }

        return EntrySignal.NONE, None

    def _update_m15_confirmation_fast(
        self,
        bias: Bias,
        m15_row: pd.Series,
        m15_index: int,
        pullback_active: bool,
        confirm_idx: int | None,
        confirm_time: pd.Timestamp | None,
    ) -> tuple[bool, int | None, pd.Timestamp | None]:
        if bias == Bias.NONE:
            self._m15_pullback_rsi_ok = False
            self._m15_pullback_start_idx = None
            self._m15_last_reason = "NO_H1_BIAS"
            return False, None, None

        close = float(m15_row["close"])
        ema_val = float(m15_row["ema20_m15"]) if pd.notna(m15_row["ema20_m15"]) else float("nan")
        rsi_val = float(m15_row["rsi14_m15"]) if pd.notna(m15_row["rsi14_m15"]) else float("nan")
        ts = pd.Timestamp(m15_row["timestamp"])
        if pd.isna(ema_val):
            self._m15_last_reason = "M15_EMA_NA"
            return pullback_active, confirm_idx, confirm_time

        if bias == Bias.LONG:
            if close <= ema_val:
                if not pullback_active:
                    self._m15_pullback_start_idx = m15_index
                    self._m15_pullback_rsi_ok = False
                pullback_active = True
                confirm_idx = None
                confirm_time = None
                self._m15_last_reason = "M15_PULLBACK_STARTED"

            if pullback_active and pd.notna(rsi_val) and rsi_val <= self.rsi_pullback_long_max:
                self._m15_pullback_rsi_ok = True
                self._m15_last_reason = "M15_PULLBACK_RSI_OK"

            if (
                pullback_active
                and self._m15_pullback_rsi_ok
                and close > ema_val
                and pd.notna(rsi_val)
                and rsi_val >= self.rsi_recover_long_min
            ):
                self._m15_pullback_rsi_ok = False
                self._m15_last_reason = "M15_CONFIRM_OK"
                return False, m15_index, ts

            if not pullback_active and confirm_idx is None:
                self._m15_last_reason = "M15_CONFIRM_NOT_READY"
            return pullback_active, confirm_idx, confirm_time

        if close >= ema_val:
            if not pullback_active:
                self._m15_pullback_start_idx = m15_index
                self._m15_pullback_rsi_ok = False
            pullback_active = True
            confirm_idx = None
            confirm_time = None
            self._m15_last_reason = "M15_PULLBACK_STARTED"

        if pullback_active and pd.notna(rsi_val) and rsi_val >= self.rsi_pullback_short_min:
            self._m15_pullback_rsi_ok = True
            self._m15_last_reason = "M15_PULLBACK_RSI_OK"

        if (
            pullback_active
            and self._m15_pullback_rsi_ok
            and close < ema_val
            and pd.notna(rsi_val)
            and rsi_val <= self.rsi_recover_short_max
        ):
            self._m15_pullback_rsi_ok = False
            self._m15_last_reason = "M15_CONFIRM_OK"
            return False, m15_index, ts

        if not pullback_active and confirm_idx is None:
            self._m15_last_reason = "M15_CONFIRM_NOT_READY"
        return pullback_active, confirm_idx, confirm_time

    def _evaluate_m5_entry_fast(self, row: pd.Series, bias: Bias, m15_confirm: Confirmation) -> EntrySignal:
        if bias == Bias.NONE or m15_confirm != Confirmation.OK:
            return EntrySignal.NONE
        close = float(row["close"])
        ema_val = float(row["ema20_m5"]) if pd.notna(row["ema20_m5"]) else float("nan")
        hh_prev = float(row["hh_prev"]) if pd.notna(row["hh_prev"]) else float("nan")
        ll_prev = float(row["ll_prev"]) if pd.notna(row["ll_prev"]) else float("nan")
        if pd.isna(ema_val):
            return EntrySignal.NONE

        if bias == Bias.LONG:
            if (
                close > ema_val
                and pd.notna(hh_prev)
                and close > hh_prev
                and bool(row["strong_bull"])
                and bool(row["wick_ok_long"])
                and pd.notna(row["swing_low"])
                and pd.notna(row["atr_m5"])
            ):
                return EntrySignal.BUY
            return EntrySignal.NONE

        if (
            close < ema_val
            and pd.notna(ll_prev)
            and close < ll_prev
            and bool(row["strong_bear"])
            and bool(row["wick_ok_short"])
            and pd.notna(row["swing_high"])
            and pd.notna(row["atr_m5"])
        ):
            return EntrySignal.SELL
        return EntrySignal.NONE

    def _h1_strategy_params(self) -> dict[str, Any]:
        return {
            "h1_bias_slope_lookback": self.h1_bias_slope_lookback,
            "h1_bias_atr_mult": self.h1_bias_atr_mult,
            "h1_min_sep_atr_mult": self.h1_min_sep_atr_mult,
        }

    def _m15_strategy_params(self) -> dict[str, Any]:
        return {
            "confirm_valid_m15_bars": self.confirm_valid_m15_bars,
            "rsi_pullback_long_max": self.rsi_pullback_long_max,
            "rsi_recover_long_min": self.rsi_recover_long_min,
            "rsi_pullback_short_min": self.rsi_pullback_short_min,
            "rsi_recover_short_max": self.rsi_recover_short_max,
        }

    def _m5_strategy_params(self) -> dict[str, Any]:
        return {
            "bos_lookback": self.bos_lookback,
            "body_ratio": self.body_ratio,
            "wick_ratio_max": self.wick_ratio_max,
            "swing_lookback": self.swing_lookback,
        }

    def _register_shock(self, current_index: int, ts: pd.Timestamp, row: pd.Series) -> None:
        atr_now = float(row["atr_m5"]) if pd.notna(row["atr_m5"]) else 0.0
        tr_now = float(row["tr_m5"]) if pd.notna(row["tr_m5"]) else 0.0
        if atr_now <= 0.0:
            return
        if tr_now >= self.shock_threshold * atr_now:
            self.shock_block_until_index = max(self.shock_block_until_index, current_index + self.shock_cooldown_bars)
            self.logger.log_event(
                ts.to_pydatetime(),
                "SHOCK_DETECTED",
                {
                    "tr_m5": tr_now,
                    "atr_m5": atr_now,
                    "threshold": self.shock_threshold,
                    "block_until_index": self.shock_block_until_index,
                },
            )

    def _try_execute_pending_entry(
        self,
        pending: PendingEntry,
        row: pd.Series,
        ts: pd.Timestamp,
        current_index: int,
        bias_context: BiasContext,
        m15_context: M15Context,
        state: EngineState,
    ) -> Position | None:
        open_ts = ts - self.bar_delta
        if (not self.enable_strategy_v4_orb) and pending.mode == "TREND" and self.regime_state != "TREND":
            self.logger.log_event(
                ts.to_pydatetime(),
                "REGIME_BLOCK",
                {"index": current_index, "mode": pending.mode, "regime": self.regime_state},
            )
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=state,
                event_type="REGIME_BLOCK",
                signal=pending.signal,
                payload_json={"mode": pending.mode, "regime": self.regime_state},
            )
            if self.enable_strategy_v3:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V3_BLOCK_REGIME",
                    {"mode": pending.mode, "regime": self.regime_state, "params": self._v3_active_params()},
                )
            return None
        if (not self.enable_strategy_v4_orb) and pending.mode == "RANGE" and self.regime_state != "RANGE":
            self.logger.log_event(
                ts.to_pydatetime(),
                "REGIME_BLOCK",
                {"index": current_index, "mode": pending.mode, "regime": self.regime_state},
            )
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=state,
                event_type="REGIME_BLOCK",
                signal=pending.signal,
                payload_json={"mode": pending.mode, "regime": self.regime_state},
            )
            if self.enable_strategy_v3:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V3_BLOCK_REGIME",
                    {"mode": pending.mode, "regime": self.regime_state, "params": self._v3_active_params()},
                )
            return None

        if self.enable_strategy_v4_orb:
            session_allowed = True
            session_reason = "V4_ORB_WINDOW_OK"
        elif self.ablation_disable_session_gating:
            session_allowed = True
            session_reason = "ABLATION_SESSION_GATING_DISABLED"
        else:
            hour_rule = self._hour_trade_filter_rule(open_ts)
            if hour_rule is not None:
                details = {
                    "index": current_index,
                    "mode": pending.mode,
                    "rule_id": hour_rule,
                    "hour_utc": int(open_ts.hour),
                }
                self.logger.log_event(
                    ts.to_pydatetime(),
                    f"SESSION_BLOCK_{hour_rule}",
                    details,
                )
                self._log_signal(
                    timestamp=ts.to_pydatetime(),
                    state=state,
                    event_type=f"SESSION_BLOCK_{hour_rule}",
                    signal=pending.signal,
                    bias_context=bias_context,
                    m15_context=m15_context,
                    payload_json=details,
                )
                if self.enable_strategy_v3:
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        f"V3_BLOCK_{hour_rule}",
                        {**details, "params": self._v3_active_params()},
                    )
                return None
            session_allowed, session_reason = self._session_mode_allowed(pending.mode, open_ts)
            if not session_allowed:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "SESSION_BLOCK",
                    {
                        "index": current_index,
                        "mode": pending.mode,
                        "reason": session_reason,
                    },
                )
                self._log_signal(
                    timestamp=ts.to_pydatetime(),
                    state=state,
                    event_type="SESSION_BLOCK",
                    signal=pending.signal,
                    bias_context=bias_context,
                    m15_context=m15_context,
                    payload_json={"mode": pending.mode, "reason": session_reason},
                )
                if self.enable_strategy_v3:
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        "V3_BLOCK_SESSION",
                        {"mode": pending.mode, "reason": session_reason, "params": self._v3_active_params()},
                    )
                return None

        block_reason = self._entry_block_reason(current_index, open_ts, pending.mode)
        if block_reason is not None:
            self.logger.log_event(ts.to_pydatetime(), block_reason, {"index": current_index, "mode": pending.mode})
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=state,
                event_type=block_reason,
                signal=pending.signal,
                bias_context=bias_context,
                m15_context=m15_context,
                payload_json={"reason": block_reason, "mode": pending.mode},
            )
            if self.enable_strategy_v3:
                norm_reason = block_reason[8:] if block_reason.startswith("BLOCKED_") else block_reason
                self.logger.log_event(
                    ts.to_pydatetime(),
                    f"V3_BLOCK_{norm_reason}",
                    {"mode": pending.mode, "reason": block_reason, "params": self._v3_active_params()},
                )
            return None

        entry_mid = float(row["open"])
        cost_mult, cost_bucket = self._effective_cost_multiplier(open_ts, pending.mode, in_mode_session=session_allowed)
        spread_eff = self.spread_usd * cost_mult
        slippage_eff = self.slippage_usd * cost_mult
        atr_now = float(pending.atr_signal)
        if not pd.notna(atr_now) or atr_now <= 0.0:
            self.logger.log_event(ts.to_pydatetime(), "BLOCKED_INVALID_ATR", {"atr_signal": pending.atr_signal})
            if self.enable_strategy_v3:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V3_BLOCK_INVALID_ATR",
                    {"atr_signal": pending.atr_signal, "params": self._v3_active_params()},
                )
            return None

        if pending.fixed_sl_mid is not None and pending.fixed_tp_mid is not None:
            sl_mid = float(pending.fixed_sl_mid)
            tp1_mid = float(pending.fixed_tp_mid)
            if pending.signal == EntrySignal.BUY:
                direction = Direction.LONG
                entry_side = "BUY"
            else:
                direction = Direction.SHORT
                entry_side = "SELL"
        else:
            if pending.signal == EntrySignal.BUY:
                sl_struct = float(pending.swing_low6) - (self.sl_buffer_mult * atr_now)
                sl_floor = entry_mid - (self.atr_floor_mult * atr_now)
                sl_mid = min(sl_struct, sl_floor)
                direction = Direction.LONG
                tp1_mid = entry_mid + (self.tp1_r * abs(entry_mid - sl_mid))
                entry_side = "BUY"
            else:
                sl_struct = float(pending.swing_high6) + (self.sl_buffer_mult * atr_now)
                sl_floor = entry_mid + (self.atr_floor_mult * atr_now)
                sl_mid = max(sl_struct, sl_floor)
                direction = Direction.SHORT
                tp1_mid = entry_mid - (self.tp1_r * abs(entry_mid - sl_mid))
                entry_side = "SELL"

        if self.enable_strategy_v4_orb:
            if direction == Direction.LONG and sl_mid >= entry_mid:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V4_BLOCK_INVALID_SL_SIDE",
                    {"entry_mid": entry_mid, "sl_mid": sl_mid, "mode": pending.mode},
                )
                return None
            if direction == Direction.SHORT and sl_mid <= entry_mid:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V4_BLOCK_INVALID_SL_SIDE",
                    {"entry_mid": entry_mid, "sl_mid": sl_mid, "mode": pending.mode},
                )
                return None

        risk_distance = abs(entry_mid - sl_mid)
        if risk_distance <= 1e-9:
            self.logger.log_event(ts.to_pydatetime(), "BLOCKED_INVALID_RISK_DISTANCE", {"risk_distance": risk_distance})
            return None

        cost_total = (self.spread_usd + self.slippage_usd) * cost_mult
        max_cost_mult_by_hour = self.cost_gate_overrides_by_hour.get(int(open_ts.hour))
        if max_cost_mult_by_hour is not None and cost_mult > max_cost_mult_by_hour:
            details = {
                "cost_total": cost_total,
                "cost_multiplier": cost_mult,
                "cost_bucket": cost_bucket,
                "mode": pending.mode,
                "hour_utc": int(open_ts.hour),
                "rule_id": "COST_GATE_OVERRIDE_HOUR",
                "max_cost_multiplier_hour": max_cost_mult_by_hour,
            }
            self.logger.log_event(ts.to_pydatetime(), "COST_FILTER_BLOCK_OVERRIDE_HOUR", details)
            self._log_signal(
                timestamp=ts.to_pydatetime(),
                state=state,
                event_type="COST_FILTER_BLOCK_OVERRIDE_HOUR",
                signal=pending.signal,
                bias_context=bias_context,
                m15_context=m15_context,
                payload_json=details,
            )
            if self.enable_strategy_v3:
                self.logger.log_event(ts.to_pydatetime(), "V3_BLOCK_COST_GATE_OVERRIDE_HOUR", details)
            return None

        if not self.ablation_disable_cost_filter:
            should_block = False
            details = {
                "cost_total": cost_total,
                "cost_multiplier": cost_mult,
                "cost_bucket": cost_bucket,
                "atr_m5": atr_now,
                "sl_distance": risk_distance,
                "max_atr_mult": self.cost_max_atr_mult,
                "mode": pending.mode,
            }
            if pending.mode == "RANGE":
                tp_distance = abs(tp1_mid - entry_mid)
                details["tp_distance"] = tp_distance
                details["max_tp_frac_range"] = self.cost_max_tp_frac_range
                should_block = (cost_total > self.cost_max_atr_mult * atr_now) or (
                    tp_distance <= 1e-9 or cost_total > self.cost_max_tp_frac_range * tp_distance
                )
            else:
                details["max_sl_frac"] = self.cost_max_sl_frac
                should_block = (cost_total > self.cost_max_atr_mult * atr_now) or (
                    cost_total > self.cost_max_sl_frac * risk_distance
                )

            if should_block:
                self.logger.log_event(ts.to_pydatetime(), "COST_FILTER_BLOCK", details)
                self._log_signal(
                    timestamp=ts.to_pydatetime(),
                    state=state,
                    event_type="COST_FILTER_BLOCK",
                    signal=pending.signal,
                    bias_context=bias_context,
                    m15_context=m15_context,
                    payload_json=details,
                )
                if self.enable_strategy_v3:
                    self.logger.log_event(ts.to_pydatetime(), "V3_BLOCK_COST_FILTER", details)
                return None

        size, risk_amount = self.risk.position_size(entry_mid, sl_mid)
        if size <= 0.0:
            self.logger.log_event(ts.to_pydatetime(), "BLOCKED_INVALID_SIZE", {"size": size})
            if self.enable_strategy_v3:
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "V3_BLOCK_INVALID_SIZE",
                    {"size": size, "params": self._v3_active_params()},
                )
            return None

        self.trade_id += 1
        entry_fill = self._fill_price(entry_mid, entry_side, spread_eff, slippage_eff)

        trade = Trade(
            trade_id=self.trade_id,
            direction=direction,
            entry_time=ts.to_pydatetime(),
            entry_price=entry_fill,
            sl=sl_mid,
            tp=tp1_mid,
            spread=spread_eff,
            mode=pending.mode,
            regime_at_entry=self.regime_state,
            cost_multiplier=cost_mult,
            entry_mid=entry_mid,
            size=size,
            closed_size=0.0,
            risk_amount=risk_amount,
            entry_index=current_index,
            signal_index=pending.signal_index,
            tp1_price_mid=tp1_mid,
            tp1_hit=False,
            partial_pct=self.partial_pct if pending.mode == "TREND" else 1.0,
            entry_fill_price=entry_fill,
            mfe_r=0.0,
            mae_r=0.0,
            pnl=0.0,
        )
        position = Position(
            trade=trade,
            remaining_qty=size,
            risk_distance=risk_distance,
            current_sl_mid=sl_mid,
            initial_sl_mid=sl_mid,
            tp1_mid=tp1_mid,
            highest_high=entry_mid,
            lowest_low=entry_mid,
            mode=pending.mode,
        )
        day_key = open_ts.date().isoformat()
        self.trades_opened_per_day[day_key] = int(self.trades_opened_per_day.get(day_key, 0)) + 1
        if self.enable_strategy_v3:
            session_key = self._v3_session_key(pending.mode, open_ts)
            self.trades_opened_per_session[session_key] = int(self.trades_opened_per_session.get(session_key, 0)) + 1

        self.fill_id += 1
        self.logger.log_fill(
            {
                "fill_id": self.fill_id,
                "trade_id": trade.trade_id,
                "timestamp": ts.isoformat(),
                "fill_type": "ENTRY",
                "side": entry_side,
                "qty": f"{size:.8f}",
                "mid_price": f"{entry_mid:.5f}",
                "fill_price": f"{entry_fill:.5f}",
                "spread_usd": f"{spread_eff:.5f}",
                "slippage_usd": f"{slippage_eff:.5f}",
                "cost_multiplier": f"{cost_mult:.4f}",
                "reason": "NEXT_OPEN_ENTRY",
                "pnl_delta": f"{0.0:.5f}",
                "equity_after": f"{self.risk.equity:.2f}",
            }
        )

        self.logger.log_event(
            ts.to_pydatetime(),
            "TRADE_OPEN",
            {
                "trade_id": trade.trade_id,
                "mode": pending.mode,
                "regime": self.regime_state,
                "direction": trade.direction.value,
                "entry_mid": trade.entry_mid,
                "entry_fill": trade.entry_price,
                "sl_mid": trade.sl,
                "tp1_mid": trade.tp,
                "size": trade.size,
                "opened_today": self.trades_opened_per_day[day_key],
                "cost_multiplier": cost_mult,
                "cost_bucket": cost_bucket,
                "setup_reason": pending.setup_reason,
            },
        )
        if self.enable_strategy_v3:
            self.logger.log_event(
                ts.to_pydatetime(),
                "V3_ENTRY",
                {
                    "trade_id": trade.trade_id,
                    "regime": self.regime_state,
                    "mode": pending.mode,
                    "direction": trade.direction.value,
                    "entry_open_t1": trade.entry_mid,
                    "entry_fill": trade.entry_price,
                    "close_t": pending.trigger_price,
                    "atr_t": atr_now,
                    "atr_ma_t": float(row["atr_ma_v3"]) if pd.notna(row.get("atr_ma_v3", pd.NA)) else None,
                    "rsi_t": float(row["rsi_v3"]) if pd.notna(row.get("rsi_v3", pd.NA)) else None,
                    "n1_high": float(row["v3_hh_prev"]) if pd.notna(row.get("v3_hh_prev", pd.NA)) else None,
                    "n1_low": float(row["v3_ll_prev"]) if pd.notna(row.get("v3_ll_prev", pd.NA)) else None,
                    "sl_dist": risk_distance,
                    "tp_dist": abs(tp1_mid - entry_mid),
                    "params": self._v3_active_params(),
                },
            )
        entry_event_type = "V4_ENTRY" if self.enable_strategy_v4_orb else ("V3_ENTRY" if self.enable_strategy_v3 else "TRADE_OPEN")
        self._log_signal(
            timestamp=ts.to_pydatetime(),
            state=EngineState.IN_TRADE,
            event_type=entry_event_type,
            signal=pending.signal,
            entry_price_candidate=trade.entry_price,
            entry_price_side=entry_side,
            sl=trade.sl,
            tp=trade.tp,
            payload_json={
                "trade_id": trade.trade_id,
                "mode": pending.mode,
                "regime": self.regime_state,
                "entry_mid": trade.entry_mid,
                "entry_fill": trade.entry_price,
                "risk_distance": risk_distance,
                "size": trade.size,
                "cost_multiplier": cost_mult,
                "cost_bucket": cost_bucket,
                "setup_reason": pending.setup_reason,
            },
        )
        if self.stdout_trade_events:
            self._print_trade_open(ts, trade, pending.trigger_price)
        return position

    def _manage_open_position(
        self,
        position: Position,
        row: pd.Series,
        ts: pd.Timestamp,
        current_index: int,
        m15_last_row: pd.Series | None,
        m15_new_close: bool,
    ) -> bool:
        trade = position.trade
        high = float(row["high"])
        low = float(row["low"])
        atr_now = float(row["atr_m5"]) if pd.notna(row["atr_m5"]) else 0.0

        if self.enable_strategy_v4_orb:
            open_ts = ts - self.bar_delta
            minute = int(open_ts.hour) * 60 + int(open_ts.minute)
            in_trade_window = self._in_any_window(minute, [(self.v4_trade_start, self.v4_trade_end)])
            if (self.v4_time_stop or self.v4_exit_at_trade_end) and (not in_trade_window):
                self._schedule_position_exit_next_open(position, current_index, "V4_EXIT_TRADE_WINDOW_END")

            if trade.direction == Direction.LONG:
                sl_hit = low <= position.current_sl_mid
                tp_hit = high >= position.tp1_mid
            else:
                sl_hit = high >= position.current_sl_mid
                tp_hit = low <= position.tp1_mid

            if sl_hit and tp_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.current_sl_mid,
                    reason="V4_EXIT_SL",
                    event_state=EngineState.WAIT_M5_ENTRY,
                )
            if sl_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.current_sl_mid,
                    reason="V4_EXIT_SL",
                    event_state=EngineState.WAIT_M5_ENTRY,
                )
            if tp_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.tp1_mid,
                    reason="V4_EXIT_TP",
                    event_state=EngineState.WAIT_M5_ENTRY,
                )
            return True

        if self.enable_strategy_v3:
            if trade.direction == Direction.LONG:
                sl_hit = low <= position.current_sl_mid
                tp_hit = high >= position.tp1_mid
            else:
                sl_hit = high >= position.current_sl_mid
                tp_hit = low <= position.tp1_mid

            if sl_hit and tp_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.current_sl_mid,
                    reason="V3_EXIT_SL",
                    event_state=EngineState.WAIT_H1_BIAS,
                )
            if sl_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.current_sl_mid,
                    reason="V3_EXIT_SL",
                    event_state=EngineState.WAIT_H1_BIAS,
                )
            if tp_hit:
                return not self._close_position_full(
                    position=position,
                    timestamp=ts,
                    current_index=current_index,
                    exit_mid=position.tp1_mid,
                    reason="V3_EXIT_TP",
                    event_state=EngineState.WAIT_H1_BIAS,
                )
            return True

        position.highest_high = max(position.highest_high, high)
        position.lowest_low = min(position.lowest_low, low)

        if trade.direction == Direction.LONG:
            favorable = max(0.0, high - trade.entry_mid)
            adverse = max(0.0, trade.entry_mid - low)
        else:
            favorable = max(0.0, trade.entry_mid - low)
            adverse = max(0.0, high - trade.entry_mid)
        trade.mfe_r = max(trade.mfe_r, favorable / position.risk_distance)
        trade.mae_r = max(trade.mae_r, adverse / position.risk_distance)

        tp1_hit_this_bar = False

        if not trade.tp1_hit:
            if trade.direction == Direction.LONG:
                sl_hit = low <= position.current_sl_mid
                tp1_hit = high >= position.tp1_mid
                if sl_hit and tp1_hit:
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason="SL_AND_TP1_SAME_CANDLE_SL_PRIORITY",
                        event_state=EngineState.WAIT_H1_BIAS,
                    )
                if sl_hit:
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason="SL_HIT",
                        event_state=EngineState.WAIT_H1_BIAS,
                    )
                if tp1_hit:
                    if position.mode == "RANGE":
                        return not self._close_position_full(
                            position=position,
                            timestamp=ts,
                            current_index=current_index,
                            exit_mid=position.tp1_mid,
                            reason="RANGE_TP_MID",
                            event_state=EngineState.WAIT_H1_BIAS,
                        )
                    self._close_position_partial(position, ts, position.tp1_mid, "TP1_PARTIAL")
                    tp1_hit_this_bar = True
            else:
                sl_hit = high >= position.current_sl_mid
                tp1_hit = low <= position.tp1_mid
                if sl_hit and tp1_hit:
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason="SL_AND_TP1_SAME_CANDLE_SL_PRIORITY",
                        event_state=EngineState.WAIT_H1_BIAS,
                    )
                if sl_hit:
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason="SL_HIT",
                        event_state=EngineState.WAIT_H1_BIAS,
                    )
                if tp1_hit:
                    if position.mode == "RANGE":
                        return not self._close_position_full(
                            position=position,
                            timestamp=ts,
                            current_index=current_index,
                            exit_mid=position.tp1_mid,
                            reason="RANGE_TP_MID",
                            event_state=EngineState.WAIT_H1_BIAS,
                        )
                    self._close_position_partial(position, ts, position.tp1_mid, "TP1_PARTIAL")
                    tp1_hit_this_bar = True

        if position.remaining_qty <= 1e-12:
            return False

        if trade.tp1_hit and (not tp1_hit_this_bar):
            if trade.direction == Direction.LONG:
                stop_hit = low <= position.current_sl_mid
                if stop_hit:
                    reason = "BREAKEVEN_STOP_HIT" if abs(position.current_sl_mid - trade.entry_mid) <= 1e-9 else "TRAILING_STOP_HIT"
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason=reason,
                        event_state=EngineState.WAIT_H1_BIAS,
                    )
            else:
                stop_hit = high >= position.current_sl_mid
                if stop_hit:
                    reason = "BREAKEVEN_STOP_HIT" if abs(position.current_sl_mid - trade.entry_mid) <= 1e-9 else "TRAILING_STOP_HIT"
                    return not self._close_position_full(
                        position=position,
                        timestamp=ts,
                        current_index=current_index,
                        exit_mid=position.current_sl_mid,
                        reason=reason,
                        event_state=EngineState.WAIT_H1_BIAS,
                    )

        if position.mode == "TREND":
            bars_since_entry = current_index - trade.entry_index + 1
            if bars_since_entry >= self.time_stop_bars and trade.mfe_r < self.time_stop_min_r:
                self._schedule_position_exit_next_open(position, current_index, "TIME_STOP_MFE")

            if m15_new_close and m15_last_row is not None:
                m15_last = m15_last_row
                m15_close = float(m15_last["close"])
                m15_ema = float(m15_last["ema20_m15"]) if pd.notna(m15_last["ema20_m15"]) else float("nan")
                if pd.notna(m15_ema):
                    if trade.direction == Direction.LONG and m15_close < m15_ema:
                        self._schedule_position_exit_next_open(position, current_index, "M15_FAILURE_EXIT")
                    if trade.direction == Direction.SHORT and m15_close > m15_ema:
                        self._schedule_position_exit_next_open(position, current_index, "M15_FAILURE_EXIT")

            if (not trade.be_moved) and trade.mfe_r >= self.be_after_r:
                prev_sl = position.current_sl_mid
                if trade.direction == Direction.LONG:
                    position.current_sl_mid = max(position.current_sl_mid, trade.entry_mid)
                else:
                    position.current_sl_mid = min(position.current_sl_mid, trade.entry_mid)
                if abs(position.current_sl_mid - prev_sl) > 1e-9:
                    trade.be_moved = True
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        "BE_MOVE",
                        {"trade_id": trade.trade_id, "from": prev_sl, "to": position.current_sl_mid, "mfe_r": trade.mfe_r},
                    )
                    self._log_signal(
                        timestamp=ts.to_pydatetime(),
                        state=EngineState.IN_TRADE,
                        event_type="BE_MOVE",
                        signal=EntrySignal.BUY if trade.direction == Direction.LONG else EntrySignal.SELL,
                        entry_price_candidate=trade.entry_price,
                        entry_price_side="BUY" if trade.direction == Direction.LONG else "SELL",
                        sl=position.current_sl_mid,
                        tp=position.tp1_mid,
                        payload_json={"trade_id": trade.trade_id, "from": prev_sl, "to": position.current_sl_mid},
                    )

            if atr_now > 0:
                trail_mult = self.trailing_mult_phase2 if trade.tp1_hit else self.trailing_mult_phase1
                prev_sl = position.current_sl_mid
                if trade.direction == Direction.LONG:
                    trail = position.highest_high - (trail_mult * atr_now)
                    position.current_sl_mid = max(position.current_sl_mid, trail)
                else:
                    trail = position.lowest_low + (trail_mult * atr_now)
                    position.current_sl_mid = min(position.current_sl_mid, trail)
                if abs(position.current_sl_mid - prev_sl) > 1e-9:
                    phase_event = "TRAIL_PHASE2" if trade.tp1_hit else "TRAIL_PHASE1"
                    self.logger.log_event(
                        ts.to_pydatetime(),
                        phase_event,
                        {
                            "trade_id": trade.trade_id,
                            "trail_mult": trail_mult,
                            "from": prev_sl,
                            "to": position.current_sl_mid,
                        },
                    )
                    self._log_signal(
                        timestamp=ts.to_pydatetime(),
                        state=EngineState.IN_TRADE,
                        event_type=phase_event,
                        signal=EntrySignal.BUY if trade.direction == Direction.LONG else EntrySignal.SELL,
                        entry_price_candidate=trade.entry_price,
                        entry_price_side="BUY" if trade.direction == Direction.LONG else "SELL",
                        sl=position.current_sl_mid,
                        tp=position.tp1_mid,
                        payload_json={"trade_id": trade.trade_id, "from": prev_sl, "to": position.current_sl_mid},
                    )

        return True

    def _schedule_position_exit_next_open(self, position: Position, current_index: int, reason: str) -> None:
        next_index = current_index + 1
        if position.pending_exit_index is None or next_index < position.pending_exit_index:
            position.pending_exit_index = next_index
            position.pending_exit_reason = reason
        elif next_index == position.pending_exit_index:
            position.pending_exit_reason = reason

    def _close_position_partial(self, position: Position, timestamp: pd.Timestamp, exit_mid: float, reason: str) -> None:
        trade = position.trade
        qty = min(position.remaining_qty, trade.size * trade.partial_pct)
        if qty <= 1e-12:
            return
        pnl_delta, fill_price, side = self._apply_exit_fill(trade, qty, exit_mid, timestamp)
        position.remaining_qty -= qty

        trade.tp1_hit = True

        self.logger.log_event(
            timestamp.to_pydatetime(),
            "TRADE_PARTIAL",
            {
                "trade_id": trade.trade_id,
                "reason": reason,
                "qty": qty,
                "exit_mid": exit_mid,
                "exit_fill": fill_price,
                "pnl_delta": pnl_delta,
            },
        )
        self._log_signal(
            timestamp=timestamp.to_pydatetime(),
            state=EngineState.IN_TRADE,
            event_type="TRADE_PARTIAL",
            signal=EntrySignal.BUY if trade.direction == Direction.LONG else EntrySignal.SELL,
            entry_price_candidate=trade.entry_price,
            entry_price_side="BUY" if trade.direction == Direction.LONG else "SELL",
            sl=position.current_sl_mid,
            tp=position.tp1_mid,
            outcome=reason,
            pnl=pnl_delta,
            r_multiple=(trade.pnl / trade.risk_amount) if trade.risk_amount > 0 else 0.0,
            payload_json={"trade_id": trade.trade_id, "qty": qty, "side": side, "mode": trade.mode},
        )

    def _close_position_full(
        self,
        position: Position,
        timestamp: pd.Timestamp,
        current_index: int,
        exit_mid: float,
        reason: str,
        event_state: EngineState,
    ) -> bool:
        trade = position.trade
        qty = position.remaining_qty
        if qty <= 1e-12:
            return False

        pnl_delta, fill_price, _ = self._apply_exit_fill(trade, qty, exit_mid, timestamp)
        position.remaining_qty = 0.0

        trade.exit_time = timestamp.to_pydatetime()
        trade.exit_mid = exit_mid
        trade.exit_fill_price = fill_price
        trade.exit_price = fill_price
        trade.exit_reason = reason
        trade.r_multiple = (trade.pnl / trade.risk_amount) if trade.risk_amount > 0 else 0.0
        trade.bars_in_trade = max(1, current_index - trade.entry_index + 1)
        trade.minutes_in_trade = max(
            0.0, (timestamp.to_pydatetime() - trade.entry_time).total_seconds() / 60.0
        )

        if self.enable_strategy_v3 and reason.startswith("V3_EXIT_"):
            self.logger.log_event(
                timestamp.to_pydatetime(),
                reason,
                {
                    "trade_id": trade.trade_id,
                    "regime": trade.regime_at_entry,
                    "mode": trade.mode,
                    "direction": trade.direction.value,
                    "entry_open_t1": trade.entry_mid,
                    "exit_mid": exit_mid,
                    "exit_fill": fill_price,
                    "sl": trade.sl,
                    "tp": trade.tp,
                    "r_multiple": trade.r_multiple,
                    "pnl": trade.pnl,
                    "bars_in_trade": trade.bars_in_trade,
                    "minutes_in_trade": trade.minutes_in_trade,
                    "params": self._v3_active_params(),
                },
            )

        self._update_governance_after_trade_close(trade)
        self.logger.log_event(
            timestamp.to_pydatetime(),
            "TRADE_CLOSE",
            {
                "trade_id": trade.trade_id,
                "reason": reason,
                "exit_mid": exit_mid,
                "exit_fill": fill_price,
                "r_multiple": trade.r_multiple,
                "mae_r": trade.mae_r,
                "mfe_r": trade.mfe_r,
                "pnl": trade.pnl,
                "pnl_delta_last_fill": pnl_delta,
            },
        )
        self._log_signal(
            timestamp=timestamp.to_pydatetime(),
            state=event_state,
            event_type=reason if (self.enable_strategy_v3 and reason.startswith("V3_EXIT_")) else "TRADE_CLOSE",
            signal=EntrySignal.BUY if trade.direction == Direction.LONG else EntrySignal.SELL,
            entry_price_candidate=trade.entry_price,
            entry_price_side="BUY" if trade.direction == Direction.LONG else "SELL",
            sl=trade.sl,
            tp=trade.tp,
            outcome=reason,
            pnl=trade.pnl,
            r_multiple=trade.r_multiple,
            bars_in_trade=trade.bars_in_trade,
            minutes_in_trade=trade.minutes_in_trade,
            payload_json={
                "trade_id": trade.trade_id,
                "mode": trade.mode,
                "regime_at_entry": trade.regime_at_entry,
                "exit_mid": exit_mid,
                "exit_fill": fill_price,
            },
        )
        self.logger.log_trade(trade)
        if self.stdout_trade_events:
            self._print_trade_close(timestamp, trade)
        return True

    def _apply_exit_fill(self, trade: Trade, qty: float, exit_mid: float, timestamp: pd.Timestamp) -> tuple[float, float, str]:
        spread_eff = self.spread_usd * trade.cost_multiplier
        slippage_eff = self.slippage_usd * trade.cost_multiplier
        if trade.direction == Direction.LONG:
            side = "SELL"
            fill_price = self._fill_price(exit_mid, side, spread_eff, slippage_eff)
            pnl_delta = (fill_price - trade.entry_fill_price) * qty
        else:
            side = "BUY"
            fill_price = self._fill_price(exit_mid, side, spread_eff, slippage_eff)
            pnl_delta = (trade.entry_fill_price - fill_price) * qty

        trade.pnl += pnl_delta
        trade.closed_size += qty
        equity_after = self.risk.register_fill_pnl(timestamp.to_pydatetime(), pnl_delta)
        self.equity_curve.append({"timestamp": timestamp, "equity": equity_after})

        self.fill_id += 1
        self.logger.log_fill(
            {
                "fill_id": self.fill_id,
                "trade_id": trade.trade_id,
                "timestamp": timestamp.isoformat(),
                "fill_type": "EXIT" if abs(trade.closed_size - trade.size) <= 1e-9 else "PARTIAL",
                "side": side,
                "qty": f"{qty:.8f}",
                "mid_price": f"{exit_mid:.5f}",
                "fill_price": f"{fill_price:.5f}",
                "spread_usd": f"{spread_eff:.5f}",
                "slippage_usd": f"{slippage_eff:.5f}",
                "cost_multiplier": f"{trade.cost_multiplier:.4f}",
                "reason": trade.exit_reason or "",
                "pnl_delta": f"{pnl_delta:.5f}",
                "equity_after": f"{equity_after:.2f}",
            }
        )
        return pnl_delta, fill_price, side

    def _entry_block_reason(self, current_index: int, open_ts: pd.Timestamp, mode: str) -> str | None:
        if current_index <= self.cooldown_until_index:
            return "BLOCKED_TRADE_COOLDOWN"
        if current_index <= self.shock_block_until_index:
            return "SHOCK_BLOCK"
        if self.daily_block_until is not None and open_ts < self.daily_block_until:
            return "BLOCKED_DAILY_STOP"
        if self.weekly_block_until is not None and open_ts < self.weekly_block_until:
            return "BLOCKED_WEEKLY_STOP"
        if self.loss_streak_block_until is not None and open_ts < self.loss_streak_block_until:
            return "BLOCKED_LOSS_STREAK"
        if self.enable_strategy_v3:
            session_key = self._v3_session_key(mode, open_ts)
            if int(self.trades_opened_per_session.get(session_key, 0)) >= self.max_trades_per_session:
                return "BLOCKED_MAX_TRADES_SESSION"
        else:
            day_key = open_ts.date().isoformat()
            if int(self.trades_opened_per_day.get(day_key, 0)) >= self.max_trades_per_day:
                return "BLOCKED_MAX_TRADES_DAY"
        return None

    def _is_entry_session_allowed(self, open_ts: pd.Timestamp) -> bool:
        wday = int(open_ts.dayofweek)
        minute = int(open_ts.hour) * 60 + int(open_ts.minute)
        if 0 <= wday <= 3:
            return self.session_mon_thu_start <= minute < self.session_mon_thu_end
        if wday == 4:
            return self.session_fri_start <= minute < self.session_fri_end
        return False

    def _should_force_session_close(self, open_ts: pd.Timestamp) -> bool:
        wday = int(open_ts.dayofweek)
        minute = int(open_ts.hour) * 60 + int(open_ts.minute)
        if 0 <= wday <= 3:
            return minute >= self.session_mon_thu_end
        if wday == 4:
            return minute >= self.session_fri_end
        return True

    def _update_governance_after_trade_close(self, trade: Trade) -> None:
        ts = pd.Timestamp(trade.exit_time or trade.entry_time)
        day_key = ts.date().isoformat()
        week_key = self._week_key(ts)

        self.daily_realized_pnl[day_key] = float(self.daily_realized_pnl.get(day_key, 0.0)) + float(trade.pnl)
        self.weekly_realized_pnl[week_key] = float(self.weekly_realized_pnl.get(week_key, 0.0)) + float(trade.pnl)
        self.daily_realized_r[day_key] = float(self.daily_realized_r.get(day_key, 0.0)) + float(trade.r_multiple)
        self.weekly_realized_r[week_key] = float(self.weekly_realized_r.get(week_key, 0.0)) + float(trade.r_multiple)

        day_start = float(self.daily_start_equity.get(day_key, self.risk.starting_balance))
        week_start = float(self.weekly_start_equity.get(week_key, self.risk.starting_balance))
        day_pnl = float(self.daily_realized_pnl.get(day_key, 0.0))
        week_pnl = float(self.weekly_realized_pnl.get(week_key, 0.0))
        day_r = float(self.daily_realized_r.get(day_key, 0.0))
        week_r = float(self.weekly_realized_r.get(week_key, 0.0))

        if day_r <= self.daily_stop_r or day_pnl <= (day_start * self.daily_stop_pct):
            next_day = ts.normalize() + pd.Timedelta(days=1)
            if self.daily_block_until is None or next_day > self.daily_block_until:
                self.daily_block_until = next_day
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "BLOCKED_DAILY_STOP_SET",
                    {"until": self.daily_block_until.isoformat(), "day_r": day_r, "day_pnl": day_pnl},
                )

        if week_r <= self.weekly_stop_r or week_pnl <= (week_start * self.weekly_stop_pct):
            weekday = int(ts.dayofweek)
            days_to_next_monday = 7 - weekday
            next_monday = ts.normalize() + pd.Timedelta(days=days_to_next_monday)
            if self.weekly_block_until is None or next_monday > self.weekly_block_until:
                self.weekly_block_until = next_monday
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "BLOCKED_WEEKLY_STOP_SET",
                    {"until": self.weekly_block_until.isoformat(), "week_r": week_r, "week_pnl": week_pnl},
                )

        if trade.pnl < 0:
            self.loss_streak += 1
        else:
            self.loss_streak = 0

        if self.loss_streak >= self.loss_streak_limit:
            block_until = ts + pd.Timedelta(hours=self.loss_streak_block_hours)
            if self.loss_streak_block_until is None or block_until > self.loss_streak_block_until:
                self.loss_streak_block_until = block_until
                self.logger.log_event(
                    ts.to_pydatetime(),
                    "BLOCKED_LOSS_STREAK_SET",
                    {"until": self.loss_streak_block_until.isoformat(), "loss_streak": self.loss_streak},
                )

    def _ensure_period_baselines(self, ts: pd.Timestamp) -> None:
        day_key = ts.date().isoformat()
        week_key = self._week_key(ts)
        if day_key not in self.daily_start_equity:
            self.daily_start_equity[day_key] = float(self.risk.equity)
        if week_key not in self.weekly_start_equity:
            self.weekly_start_equity[week_key] = float(self.risk.equity)

    @staticmethod
    def _week_key(ts: pd.Timestamp) -> str:
        year, week, _ = ts.isocalendar()
        return f"{year:04d}-W{week:02d}"

    @staticmethod
    def _hhmm_to_minutes(value: str) -> int:
        hh, mm = value.split(":")
        return (int(hh) * 60) + int(mm)

    @staticmethod
    def _fill_price(mid_price: float, side: str, spread: float, slippage: float) -> float:
        side_upper = side.upper()
        if side_upper == "BUY":
            return mid_price + (spread / 2.0) + slippage
        return mid_price - (spread / 2.0) - slippage

    def _log_signal(
        self,
        timestamp: datetime,
        state: EngineState,
        event_type: str,
        signal: EntrySignal = EntrySignal.NONE,
        bias_context: BiasContext | None = None,
        m15_context: M15Context | None = None,
        entry_price_candidate: float | None = None,
        entry_price_side: str = "",
        sl: float | None = None,
        tp: float | None = None,
        outcome: str = "",
        pnl: float | None = None,
        r_multiple: float | None = None,
        bars_in_trade: int | None = None,
        minutes_in_trade: float | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> None:
        self.logger.log_signal(
            timestamp=timestamp,
            payload={
                "state": state.value,
                "event_type": event_type,
                "signal": signal.value if isinstance(signal, EntrySignal) else str(signal),
                "bias": bias_context.bias.value if bias_context is not None else "",
                "bias_reason": bias_context.reason if bias_context is not None else "",
                "m15_confirmation": m15_context.confirmation.value if m15_context is not None else "",
                "m15_reason": m15_context.reason if m15_context is not None else "",
                "entry_price_candidate": f"{entry_price_candidate:.5f}" if entry_price_candidate is not None else "",
                "entry_price_side": entry_price_side,
                "sl": f"{sl:.5f}" if sl is not None else "",
                "tp": f"{tp:.5f}" if tp is not None else "",
                "outcome": outcome,
                "pnl": f"{pnl:.5f}" if pnl is not None else "",
                "r_multiple": f"{r_multiple:.5f}" if r_multiple is not None else "",
                "bars_in_trade": bars_in_trade if bars_in_trade is not None else "",
                "minutes_in_trade": f"{minutes_in_trade:.2f}" if minutes_in_trade is not None else "",
                "payload_json": payload_json or {},
            },
        )

    def _print_progress(
        self,
        ts: pd.Timestamp,
        bars_done: int,
        bars_total: int,
        elapsed_days: float,
        total_days: float,
        progress_pct: float,
        closed_trades: int,
    ) -> None:
        print(
            "PROGRESS | "
            f"sim_ts={ts.isoformat()} | bars={bars_done}/{bars_total} | "
            f"sim_days={elapsed_days:.2f}/{total_days:.2f} | progress={progress_pct:.2f}% | "
            f"closed_trades={closed_trades} | trade_id={self.trade_id} | equity={self.risk.equity:.2f}",
            flush=True,
        )

    def _print_trade_open(self, ts: pd.Timestamp, trade: Trade, trigger_price: float) -> None:
        print(
            "TRADE_OPEN | "
            f"ts={ts.isoformat()} | trade_id={trade.trade_id} | mode={trade.mode} | direction={trade.direction.value} | "
            f"entry_mid={trade.entry_mid:.5f} | entry_fill={trade.entry_price:.5f} | "
            f"sl_mid={trade.sl:.5f} | tp1_mid={trade.tp:.5f} | trigger={trigger_price:.5f}",
            flush=True,
        )

    def _print_trade_close(self, ts: pd.Timestamp, trade: Trade) -> None:
        print(
            "TRADE_CLOSE | "
            f"ts={ts.isoformat()} | trade_id={trade.trade_id} | mode={trade.mode} | direction={trade.direction.value} | "
            f"reason={trade.exit_reason or 'UNKNOWN'} | exit_fill={float(trade.exit_price):.5f} | "
            f"r={float(trade.r_multiple):.3f} | pnl={float(trade.pnl):.2f}",
            flush=True,
        )
