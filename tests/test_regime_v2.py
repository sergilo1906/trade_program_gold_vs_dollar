from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger
from xauusd_bot.models import Bias, BiasContext, Confirmation, EntrySignal


def _base_config(output_dir: Path) -> dict[str, object]:
    return {
        "output_dir": str(output_dir),
        "starting_balance": 10000.0,
        "risk_per_trade_pct": 0.005,
        "ema_h1_fast": 2,
        "ema_h1_slow": 3,
        "ema_m15": 2,
        "ema_m5": 2,
        "rsi_period_m15": 2,
        "atr_period": 2,
        "h1_bias_slope_lookback": 1,
        "h1_bias_atr_mult": 0.0,
        "h1_min_sep_atr_mult": 0.0,
        "h1_slope_min_atr_mult": 0.0,
        "h1_range_max_sep_atr_mult": 999.0,
        "h1_range_max_slope_atr_mult": 999.0,
        "atr_rel_lookback": 2,
        "atr_rel_trend_min": 0.0,
        "atr_rel_range_max": 999.0,
        "atr_rel_dead_max": 0.0,
        "regime_trend_enter_score": 3,
        "regime_trend_exit_score": 2,
        "regime_range_enter_score": 3,
        "regime_range_exit_score": 2,
        "trend_min_bars_m15": 0,
        "range_min_bars_m15": 0,
        "confirm_valid_m15_bars": 6,
        "bos_lookback": 2,
        "body_ratio": 0.0,
        "wick_ratio_max": 1.0,
        "rsi_pullback_long_max": 100.0,
        "rsi_recover_long_min": 0.0,
        "rsi_pullback_short_min": 0.0,
        "rsi_recover_short_max": 100.0,
        "max_trades_per_day": 99,
        "swing_lookback": 3,
        "shock_threshold": 999.0,
        "shock_cooldown_bars": 0,
        "cooldown_after_trade_bars": 0,
        "atr_floor_mult": 0.8,
        "sl_buffer_mult": 0.1,
        "tp1_r": 1.0,
        "partial_pct": 0.5,
        "trailing_mult": 2.0,
        "trailing_mult_phase1": 2.0,
        "trailing_mult_phase2": 1.0,
        "be_after_r": 2.0,
        "time_stop_bars": 8,
        "time_stop_min_r": 0.5,
        "k_atr_range": 1.0,
        "range_reject_wick_min": 0.0,
        "range_body_min": 0.0,
        "range_rsi_long_max": 40.0,
        "range_rsi_short_min": 60.0,
        "range_sl_atr_buffer": 0.5,
        "range_touch_ttl_m5_bars": 12,
        "spread_usd": 0.2,
        "slippage_usd": 0.0,
        "cost_max_atr_mult": 999.0,
        "cost_max_sl_frac": 999.0,
        "cost_max_tp_frac_range": 999.0,
        "cost_mult_trend_session": 1.0,
        "cost_mult_off_session": 1.0,
        "cost_mult_asia": 1.0,
        "ablation_force_regime": "AUTO",
        "ablation_disable_cost_filter": False,
        "ablation_disable_session_gating": False,
        "daily_stop_r": -99.0,
        "daily_stop_pct": -0.99,
        "weekly_stop_r": -99.0,
        "weekly_stop_pct": -0.99,
        "loss_streak_limit": 99,
        "loss_streak_block_hours": 24,
        "force_session_close": False,
        "session": {
            "mon_thu_start": "00:00",
            "mon_thu_end": "23:59",
            "fri_start": "00:00",
            "fri_end": "23:59",
        },
        "trend_sessions": ["00:00-23:59"],
        "range_sessions": ["00:00-23:59"],
        "blocked_windows": [],
        "progress_every_days": 0,
    }


def _market_data(rows: int = 800, seed: int = 17) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2026-01-05 00:05:00", periods=rows, freq="5min")
    close = []
    px = 2500.0
    for i in range(rows):
        px += 0.03 + (0.2 * np.sin(i / 5.0)) + rng.normal(0.0, 0.02)
        close.append(float(px))
    open_ = [close[0]] + close[:-1]
    high = [max(o, c) + 0.35 for o, c in zip(open_, close)]
    low = [min(o, c) - 0.25 for o, c in zip(open_, close)]
    return pd.DataFrame({"timestamp": ts, "open": open_, "high": high, "low": low, "close": close, "volume": [100.0] * rows})


def _strong_trend_data(rows: int = 600, slope: float = 0.45) -> pd.DataFrame:
    ts = pd.date_range("2026-01-05 00:05:00", periods=rows, freq="5min")
    close = [2500.0 + (slope * i) for i in range(rows)]
    open_ = [close[0]] + close[:-1]
    high = [max(o, c) + 0.25 for o, c in zip(open_, close)]
    low = [min(o, c) - 0.15 for o, c in zip(open_, close)]
    return pd.DataFrame({"timestamp": ts, "open": open_, "high": high, "low": low, "close": close, "volume": [100.0] * rows})


def test_regime_hysteresis_stability(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path / "out")
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = SimulationEngine(config=cfg, logger=logger)

    t0 = pd.Timestamp("2026-01-01 00:00:00")
    engine._update_regime_from_scores(t0, m15_index=10, trend_score=3, range_score=0, dominant_reason="SCORE_TREND_OK", atr_rel=1.2, slope=1.0, ema_sep=1.0)
    assert engine.regime_state == "TREND"

    # Hysteresis: at exit threshold should still stay TREND.
    engine._update_regime_from_scores(t0 + pd.Timedelta(minutes=15), m15_index=11, trend_score=2, range_score=1, dominant_reason="SCORE_NO_EDGE", atr_rel=1.0, slope=0.0, ema_sep=0.5)
    assert engine.regime_state == "TREND"

    engine._update_regime_from_scores(t0 + pd.Timedelta(minutes=30), m15_index=12, trend_score=1, range_score=1, dominant_reason="SCORE_NO_EDGE", atr_rel=1.0, slope=0.0, ema_sep=0.5)
    assert engine.regime_state == "NO_TRADE"


def test_min_bars_regime(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path / "out")
    cfg["trend_min_bars_m15"] = 4
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = SimulationEngine(config=cfg, logger=logger)

    t0 = pd.Timestamp("2026-01-01 00:00:00")
    engine._update_regime_from_scores(t0, m15_index=10, trend_score=4, range_score=0, dominant_reason="SCORE_TREND_OK", atr_rel=1.2, slope=1.0, ema_sep=1.0)
    assert engine.regime_state == "TREND"

    # Attempt to flip before min bars is ignored.
    engine._update_regime_from_scores(t0 + pd.Timedelta(minutes=30), m15_index=12, trend_score=0, range_score=4, dominant_reason="SCORE_RANGE_OK", atr_rel=0.8, slope=0.0, ema_sep=0.0)
    assert engine.regime_state == "TREND"

    # After min bars elapsed, flip is allowed.
    engine._update_regime_from_scores(t0 + pd.Timedelta(minutes=60), m15_index=14, trend_score=0, range_score=4, dominant_reason="SCORE_RANGE_OK", atr_rel=0.8, slope=0.0, ema_sep=0.0)
    assert engine.regime_state == "RANGE"


def test_cost_filter_blocks(tmp_path: Path) -> None:
    class ForcedTrendEngine(SimulationEngine):
        def _evaluate_h1_bias_fast(self, h1: pd.DataFrame, h1_end: int) -> BiasContext:  # type: ignore[override]
            return BiasContext(bias=Bias.LONG, reason="TEST_FORCE")

        def _update_m15_confirmation_fast(  # type: ignore[override]
            self,
            bias: Bias,
            m15_row: pd.Series,
            m15_index: int,
            pullback_active: bool,
            confirm_idx: int | None,
            confirm_time: pd.Timestamp | None,
        ) -> tuple[bool, int | None, pd.Timestamp | None]:
            return False, m15_index, pd.Timestamp(m15_row["timestamp"])

        def _evaluate_m5_entry_fast(self, row: pd.Series, bias: Bias, m15_confirm: Confirmation) -> EntrySignal:  # type: ignore[override]
            if bias == Bias.LONG and m15_confirm == Confirmation.OK:
                return EntrySignal.BUY
            return EntrySignal.NONE

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            return 10, 0, "SCORE_TREND_OK", 1.2, 1.0, 1.0

    cfg = _base_config(tmp_path / "out")
    cfg["spread_usd"] = 4.0
    cfg["slippage_usd"] = 1.0
    cfg["cost_max_atr_mult"] = 0.01
    cfg["cost_max_sl_frac"] = 0.01
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedTrendEngine(config=cfg, logger=logger)
    engine.run(_market_data())

    events = pd.read_csv(Path(cfg["output_dir"]) / "events.csv")
    assert "COST_FILTER_BLOCK" in set(events["event_type"].tolist())


def test_session_block(tmp_path: Path) -> None:
    class ForcedTrendEngine(SimulationEngine):
        def _evaluate_h1_bias_fast(self, h1: pd.DataFrame, h1_end: int) -> BiasContext:  # type: ignore[override]
            return BiasContext(bias=Bias.LONG, reason="TEST_FORCE")

        def _update_m15_confirmation_fast(  # type: ignore[override]
            self,
            bias: Bias,
            m15_row: pd.Series,
            m15_index: int,
            pullback_active: bool,
            confirm_idx: int | None,
            confirm_time: pd.Timestamp | None,
        ) -> tuple[bool, int | None, pd.Timestamp | None]:
            return False, m15_index, pd.Timestamp(m15_row["timestamp"])

        def _evaluate_m5_entry_fast(self, row: pd.Series, bias: Bias, m15_confirm: Confirmation) -> EntrySignal:  # type: ignore[override]
            if bias == Bias.LONG and m15_confirm == Confirmation.OK:
                return EntrySignal.BUY
            return EntrySignal.NONE

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            return 10, 0, "SCORE_TREND_OK", 1.2, 1.0, 1.0

    cfg = _base_config(tmp_path / "out")
    cfg["trend_sessions"] = ["23:55-23:59"]
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedTrendEngine(config=cfg, logger=logger)
    engine.run(_market_data())

    events = pd.read_csv(Path(cfg["output_dir"]) / "events.csv")
    assert "SESSION_BLOCK" in set(events["event_type"].tolist())


def test_range_entry_and_exit(tmp_path: Path) -> None:
    class ForcedRangeEngine(SimulationEngine):
        def __init__(self, config: dict[str, object], logger: CsvLogger):
            super().__init__(config=config, logger=logger)
            self._fired = False

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            return 0, 10, "SCORE_RANGE_OK", 0.8, 0.0, 0.0

        def _evaluate_range_entry_fast(  # type: ignore[override]
            self, row: pd.Series, m15_last_row: pd.Series | None, current_index: int
        ) -> tuple[EntrySignal, dict[str, float] | None]:
            if self._fired:
                return EntrySignal.NONE, None
            self._fired = True
            close = float(row["close"])
            return EntrySignal.BUY, {"sl_mid": close - 1.0, "tp_mid": close + 0.2, "atr_m15": 1.0}

    cfg = _base_config(tmp_path / "out")
    cfg["range_sessions"] = ["00:00-23:59"]
    cfg["trend_sessions"] = ["00:00-23:59"]
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedRangeEngine(config=cfg, logger=logger)
    engine.run(_market_data(rows=600, seed=21))

    trades = pd.read_csv(Path(cfg["output_dir"]) / "trades.csv")
    assert not trades.empty
    assert "RANGE" in set(trades["mode"].astype(str).tolist())
    assert "RANGE_TP_MID" in set(trades["exit_reason"].astype(str).tolist())


def test_range_rsi_filter_applies(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path / "out")
    cfg["range_reject_wick_min"] = 0.0
    cfg["range_body_min"] = 0.0
    cfg["range_rsi_long_max"] = 40.0
    cfg["range_rsi_short_min"] = 60.0
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = SimulationEngine(config=cfg, logger=logger)

    row_short = pd.Series(
        {
            "atr_m5": 1.0,
            "close": 99.0,
            "body_ratio": 0.60,
            "upper_wick_ratio": 0.60,
            "lower_wick_ratio": 0.10,
        }
    )
    m15_short = pd.Series(
        {
            "range_mid": 95.0,
            "range_upper": 100.0,
            "range_lower": 90.0,
            "atr_m15": 2.0,
            "rsi14_m15": 50.0,
        }
    )
    engine.last_touch_upper_m5_index = 10
    sig, _ = engine._evaluate_range_entry_fast(row=row_short, m15_last_row=m15_short, current_index=12)
    assert sig == EntrySignal.NONE

    m15_short["rsi14_m15"] = 70.0
    sig, setup = engine._evaluate_range_entry_fast(row=row_short, m15_last_row=m15_short, current_index=12)
    assert sig == EntrySignal.SELL
    assert setup is not None

    row_long = pd.Series(
        {
            "atr_m5": 1.0,
            "close": 91.0,
            "body_ratio": 0.60,
            "upper_wick_ratio": 0.10,
            "lower_wick_ratio": 0.60,
        }
    )
    m15_long = pd.Series(
        {
            "range_mid": 95.0,
            "range_upper": 100.0,
            "range_lower": 90.0,
            "atr_m15": 2.0,
            "rsi14_m15": 50.0,
        }
    )
    engine.last_touch_lower_m5_index = 20
    sig, _ = engine._evaluate_range_entry_fast(row=row_long, m15_last_row=m15_long, current_index=23)
    assert sig == EntrySignal.NONE

    m15_long["rsi14_m15"] = 30.0
    sig, setup = engine._evaluate_range_entry_fast(row=row_long, m15_last_row=m15_long, current_index=23)
    assert sig == EntrySignal.BUY
    assert setup is not None


def test_be_move_event(tmp_path: Path) -> None:
    class ForcedTrendOneShot(SimulationEngine):
        def __init__(self, config: dict[str, object], logger: CsvLogger):
            super().__init__(config=config, logger=logger)
            self._fired = False

        def _evaluate_h1_bias_fast(self, h1: pd.DataFrame, h1_end: int) -> BiasContext:  # type: ignore[override]
            return BiasContext(bias=Bias.LONG, reason="TEST_FORCE")

        def _update_m15_confirmation_fast(  # type: ignore[override]
            self,
            bias: Bias,
            m15_row: pd.Series,
            m15_index: int,
            pullback_active: bool,
            confirm_idx: int | None,
            confirm_time: pd.Timestamp | None,
        ) -> tuple[bool, int | None, pd.Timestamp | None]:
            return False, m15_index, pd.Timestamp(m15_row["timestamp"])

        def _evaluate_m5_entry_fast(self, row: pd.Series, bias: Bias, m15_confirm: Confirmation) -> EntrySignal:  # type: ignore[override]
            if self._fired:
                return EntrySignal.NONE
            if bias == Bias.LONG and m15_confirm == Confirmation.OK:
                self._fired = True
                return EntrySignal.BUY
            return EntrySignal.NONE

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            return 10, 0, "SCORE_TREND_OK", 1.2, 1.0, 1.0

    cfg = _base_config(tmp_path / "out")
    cfg["ablation_disable_session_gating"] = True
    cfg["ablation_disable_cost_filter"] = True
    cfg["tp1_r"] = 20.0
    cfg["be_after_r"] = 0.2
    cfg["trailing_mult_phase1"] = 50.0
    cfg["time_stop_bars"] = 200
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedTrendOneShot(config=cfg, logger=logger)
    engine.run(_strong_trend_data(rows=700, slope=0.60))

    events = pd.read_csv(Path(cfg["output_dir"]) / "events.csv")
    assert "BE_MOVE" in set(events["event_type"].astype(str).tolist())


def test_trail_phase2_event(tmp_path: Path) -> None:
    class ForcedTrendOneShot(SimulationEngine):
        def __init__(self, config: dict[str, object], logger: CsvLogger):
            super().__init__(config=config, logger=logger)
            self._fired = False

        def _evaluate_h1_bias_fast(self, h1: pd.DataFrame, h1_end: int) -> BiasContext:  # type: ignore[override]
            return BiasContext(bias=Bias.LONG, reason="TEST_FORCE")

        def _update_m15_confirmation_fast(  # type: ignore[override]
            self,
            bias: Bias,
            m15_row: pd.Series,
            m15_index: int,
            pullback_active: bool,
            confirm_idx: int | None,
            confirm_time: pd.Timestamp | None,
        ) -> tuple[bool, int | None, pd.Timestamp | None]:
            return False, m15_index, pd.Timestamp(m15_row["timestamp"])

        def _evaluate_m5_entry_fast(self, row: pd.Series, bias: Bias, m15_confirm: Confirmation) -> EntrySignal:  # type: ignore[override]
            if self._fired:
                return EntrySignal.NONE
            if bias == Bias.LONG and m15_confirm == Confirmation.OK:
                self._fired = True
                return EntrySignal.BUY
            return EntrySignal.NONE

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            return 10, 0, "SCORE_TREND_OK", 1.2, 1.0, 1.0

    cfg = _base_config(tmp_path / "out")
    cfg["ablation_disable_session_gating"] = True
    cfg["ablation_disable_cost_filter"] = True
    cfg["tp1_r"] = 0.2
    cfg["trailing_mult_phase1"] = 2.0
    cfg["trailing_mult_phase2"] = 0.3
    cfg["be_after_r"] = 99.0
    cfg["time_stop_bars"] = 200
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedTrendOneShot(config=cfg, logger=logger)
    engine.run(_strong_trend_data(rows=700, slope=0.55))

    events = pd.read_csv(Path(cfg["output_dir"]) / "events.csv")
    assert "TRAIL_PHASE2" in set(events["event_type"].astype(str).tolist())


def test_kill_switch_regime_flip_event(tmp_path: Path) -> None:
    class ForcedRangeThenTrend(SimulationEngine):
        def __init__(self, config: dict[str, object], logger: CsvLogger):
            super().__init__(config=config, logger=logger)
            self._fired = False

        def _evaluate_regime_scores(  # type: ignore[override]
            self, h1: pd.DataFrame, h1_end: int, current_index: int
        ) -> tuple[int, int, str, float, float, float]:
            if self.trade_id >= 1:
                return 10, 0, "SCORE_TREND_OK", 1.2, 1.0, 1.0
            return 0, 10, "SCORE_RANGE_OK", 0.8, 0.0, 0.0

        def _evaluate_range_entry_fast(  # type: ignore[override]
            self, row: pd.Series, m15_last_row: pd.Series | None, current_index: int
        ) -> tuple[EntrySignal, dict[str, float] | None]:
            if self._fired:
                return EntrySignal.NONE, None
            self._fired = True
            close = float(row["close"])
            return EntrySignal.BUY, {"sl_mid": close - 20.0, "tp_mid": close + 20.0, "atr_m15": 1.0}

    cfg = _base_config(tmp_path / "out")
    cfg["ablation_disable_session_gating"] = True
    cfg["ablation_disable_cost_filter"] = True
    cfg["trend_min_bars_m15"] = 0
    cfg["range_min_bars_m15"] = 0
    cfg["time_stop_bars"] = 300
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedRangeThenTrend(config=cfg, logger=logger)
    engine.run(_market_data(rows=700, seed=11))

    trades = pd.read_csv(Path(cfg["output_dir"]) / "trades.csv")
    assert not trades.empty
    assert "KILL_SWITCH_REGIME_FLIP" in set(trades["exit_reason"].astype(str).tolist())
