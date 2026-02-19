from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger
from xauusd_bot.models import Bias, BiasContext, Confirmation, EntrySignal
from xauusd_bot.timeframes import closed_bars_count_up_to, resample_from_m5


def _market_data(rows: int = 900) -> pd.DataFrame:
    t = np.arange(rows, dtype=float)
    ts = pd.date_range("2026-01-05 00:05:00", periods=rows, freq="5min")
    close = 2500.0 + (0.035 * t) + (4.0 * np.sin(t / 7.0)) + (1.1 * np.sin(t / 2.8))
    open_ = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_, close)
    low = np.minimum(open_, close)
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(rows, 100.0),
        }
    )


def test_entry_is_next_bar_open_not_same_bar(tmp_path: Path) -> None:
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

    cfg = {
        "output_dir": str(tmp_path / "out"),
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
        "max_trades_per_day": 99,
        "swing_lookback": 3,
        "shock_threshold": 99.0,
        "shock_cooldown_bars": 0,
        "cooldown_after_trade_bars": 0,
        "atr_floor_mult": 0.6,
        "sl_buffer_mult": 0.05,
        "tp1_r": 0.8,
        "partial_pct": 0.5,
        "trailing_mult": 2.0,
        "time_stop_bars": 10,
        "time_stop_min_r": 0.5,
        "spread_usd": 0.2,
        "slippage_usd": 0.0,
        "daily_stop_r": -99.0,
        "daily_stop_pct": -0.99,
        "weekly_stop_r": -99.0,
        "weekly_stop_pct": -0.99,
        "loss_streak_limit": 99,
        "loss_streak_block_hours": 1,
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
    logger = CsvLogger(output_dir=cfg["output_dir"])
    engine = ForcedSignalEngine(config=cfg, logger=logger)
    summary = engine.run(_market_data())

    signals = pd.read_csv(Path(cfg["output_dir"]) / "signals.csv")
    signal_rows = signals[signals["event_type"] == "SIGNAL_DETECTED"]
    open_rows = signals[signals["event_type"] == "TRADE_OPEN"]
    assert not signal_rows.empty
    assert not open_rows.empty

    first_signal_ts = pd.to_datetime(signal_rows.iloc[0]["ts"])
    first_open_ts = pd.to_datetime(open_rows.iloc[0]["ts"])
    assert first_open_ts > first_signal_ts


def test_htf_alignment_uses_only_closed_bars() -> None:
    m5 = _market_data(rows=180)
    m15 = resample_from_m5(m5, "15min")
    h1 = resample_from_m5(m5, "1h")
    for ts in m5["timestamp"]:
        m15_count = closed_bars_count_up_to(m15, pd.Timestamp(ts))
        h1_count = closed_bars_count_up_to(h1, pd.Timestamp(ts))
        if m15_count > 0:
            assert pd.Timestamp(m15.iloc[m15_count - 1]["timestamp"]) <= pd.Timestamp(ts)
        if h1_count > 0:
            assert pd.Timestamp(h1.iloc[h1_count - 1]["timestamp"]) <= pd.Timestamp(ts)
