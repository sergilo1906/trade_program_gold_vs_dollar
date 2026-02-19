from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger
from xauusd_bot.models import Bias, BiasContext, Confirmation, EntrySignal


def _build_test_data(rows: int = 360, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2026-01-06 00:05:00", periods=rows, freq="5min")
    closes: list[float] = []
    px = 2600.0
    for i in range(rows):
        px += 0.04 + (0.25 * np.sin(i / 5.0)) + rng.normal(0.0, 0.03)
        closes.append(float(px))
    opens = [closes[0]] + closes[:-1]
    highs = [max(o, c) + abs(rng.normal(0.20, 0.03)) for o, c in zip(opens, closes)]
    lows = [min(o, c) - abs(rng.normal(0.20, 0.03)) for o, c in zip(opens, closes)]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [100.0] * rows,
        }
    )


def test_engine_runs_and_writes_core_outputs(tmp_path: Path) -> None:
    config = {
        "output_dir": str(tmp_path / "output"),
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
        "confirm_valid_m15_bars": 4,
        "bos_lookback": 2,
        "body_ratio": 0.0,
        "wick_ratio_max": 1.0,
        "rsi_pullback_long_max": 100.0,
        "rsi_recover_long_min": 0.0,
        "rsi_pullback_short_min": 0.0,
        "rsi_recover_short_max": 100.0,
        "max_trades_per_day": 99,
        "swing_lookback": 3,
        "shock_threshold": 99.0,
        "shock_cooldown_bars": 0,
        "cooldown_after_trade_bars": 0,
        "atr_floor_mult": 0.8,
        "sl_buffer_mult": 0.1,
        "tp1_r": 1.0,
        "partial_pct": 0.5,
        "trailing_mult": 2.5,
        "time_stop_bars": 8,
        "time_stop_min_r": 0.5,
        "spread_usd": 0.41,
        "slippage_usd": 0.05,
        "cost_max_atr_mult": 999.0,
        "cost_max_sl_frac": 999.0,
        "daily_stop_r": -99.0,
        "daily_stop_pct": -0.99,
        "weekly_stop_r": -99.0,
        "weekly_stop_pct": -0.99,
        "loss_streak_limit": 99,
        "loss_streak_block_hours": 24,
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

    logger = CsvLogger(output_dir=config["output_dir"])
    engine = SimulationEngine(config=config, logger=logger)
    summary = engine.run(_build_test_data())

    assert summary["sim_days"] > 0
    assert "WAIT_H1_BIAS" in summary["states_visited"]
    assert "WAIT_M15_CONFIRM" in summary["states_visited"]
    assert Path(summary["events_path"]).exists()
    assert Path(summary["trades_path"]).exists()
    assert Path(summary["signals_path"]).exists()
    assert Path(summary["fills_path"]).exists()


def test_max_trades_per_day_block_is_logged(tmp_path: Path) -> None:
    class ForcedSignalEngine(SimulationEngine):
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

    config = {
        "output_dir": str(tmp_path / "output"),
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
        "confirm_valid_m15_bars": 6,
        "bos_lookback": 2,
        "body_ratio": 0.0,
        "wick_ratio_max": 1.0,
        "rsi_pullback_long_max": 100.0,
        "rsi_recover_long_min": 0.0,
        "rsi_pullback_short_min": 0.0,
        "rsi_recover_short_max": 100.0,
        "max_trades_per_day": 1,
        "swing_lookback": 3,
        "shock_threshold": 99.0,
        "shock_cooldown_bars": 0,
        "cooldown_after_trade_bars": 0,
        "atr_floor_mult": 0.8,
        "sl_buffer_mult": 0.1,
        "tp1_r": 0.6,
        "partial_pct": 0.5,
        "trailing_mult": 2.0,
        "time_stop_bars": 1,
        "time_stop_min_r": 999.0,
        "spread_usd": 0.2,
        "slippage_usd": 0.0,
        "cost_max_atr_mult": 999.0,
        "cost_max_sl_frac": 999.0,
        "daily_stop_r": -99.0,
        "daily_stop_pct": -0.99,
        "weekly_stop_r": -99.0,
        "weekly_stop_pct": -0.99,
        "loss_streak_limit": 99,
        "loss_streak_block_hours": 24,
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

    logger = CsvLogger(output_dir=config["output_dir"])
    engine = ForcedSignalEngine(config=config, logger=logger)
    engine.run(_build_test_data(rows=600, seed=13))

    events = pd.read_csv(Path(config["output_dir"]) / "events.csv")
    signals = pd.read_csv(Path(config["output_dir"]) / "signals.csv")
    assert "BLOCKED_MAX_TRADES_DAY" in set(events["event_type"].tolist())
    assert "BLOCKED_MAX_TRADES_DAY" in set(signals["event_type"].tolist())
