from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Bias(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class Confirmation(str, Enum):
    OK = "OK"
    NO = "NO"


class EntrySignal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class EngineState(str, Enum):
    WAIT_H1_BIAS = "WAIT_H1_BIAS"
    WAIT_M15_CONFIRM = "WAIT_M15_CONFIRM"
    WAIT_M5_ENTRY = "WAIT_M5_ENTRY"
    IN_TRADE = "IN_TRADE"


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BosDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NONE = "NONE"


@dataclass(slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(slots=True)
class Trade:
    trade_id: int
    direction: Direction
    entry_time: datetime
    entry_price: float
    sl: float
    tp: float
    spread: float
    mode: str = "TREND"
    regime_at_entry: str = ""
    cost_multiplier: float = 1.0
    entry_mid: float = 0.0
    size: float = 0.0
    closed_size: float = 0.0
    risk_amount: float = 0.0
    entry_index: int = 0
    signal_index: int = 0
    tp1_price_mid: float = 0.0
    tp1_hit: bool = False
    be_moved: bool = False
    partial_pct: float = 0.5
    entry_fill_price: float = 0.0
    exit_mid: float | None = None
    exit_fill_price: float | None = None
    pnl: float = 0.0
    mae_r: float = 0.0
    mfe_r: float = 0.0
    bars_in_trade: int = 0
    minutes_in_trade: float = 0.0
    exit_time: datetime | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    r_multiple: float = 0.0


@dataclass(slots=True)
class BiasContext:
    bias: Bias
    bos_direction: BosDirection = BosDirection.NONE
    bos_level: float | None = None
    bos_timestamp: datetime | None = None
    bos_index_h1: int | None = None
    broken_swing_index: int | None = None
    impulse_origin_level: float | None = None
    impulse_origin_timestamp: datetime | None = None
    impulse_origin_index: int | None = None
    bos_buffer: float = 0.0
    reason: str = ""


@dataclass(slots=True)
class M15Context:
    confirmation: Confirmation
    zone_low: float | None = None
    zone_high: float | None = None
    touched_zone: bool = False
    invalidated: bool = False
    pullback_start_time: datetime | None = None
    confirmation_time: datetime | None = None
    reason: str = ""


@dataclass(slots=True)
class EntrySetup:
    signal: EntrySignal
    trigger_price: float
    micro_swing_high: float | None
    micro_swing_low: float | None
    buffer_micro: float
    setup_time: datetime
    setup_index: int
