from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from xauusd_bot.models import Trade


EVENT_HEADERS = ["timestamp", "event_type", "details_json"]
TRADE_HEADERS = [
    "trade_id",
    "mode",
    "regime_at_entry",
    "direction",
    "entry_time",
    "entry_price",
    "sl",
    "tp",
    "exit_time",
    "exit_price",
    "exit_reason",
    "r_multiple",
    "spread",
    "entry_mid",
    "exit_mid",
    "size",
    "closed_size",
    "risk_amount",
    "pnl",
    "mae_r",
    "mfe_r",
    "tp1_hit",
    "bars_in_trade",
    "minutes_in_trade",
    "cost_multiplier",
]
SIGNAL_HEADERS = [
    "ts",
    "state",
    "event_type",
    "signal",
    "bias",
    "bias_reason",
    "m15_confirmation",
    "m15_reason",
    "entry_price_candidate",
    "entry_price_side",
    "sl",
    "tp",
    "outcome",
    "pnl",
    "r_multiple",
    "bars_in_trade",
    "minutes_in_trade",
    "payload_json",
]
FILL_HEADERS = [
    "fill_id",
    "trade_id",
    "timestamp",
    "fill_type",
    "side",
    "qty",
    "mid_price",
    "fill_price",
    "spread_usd",
    "slippage_usd",
    "cost_multiplier",
    "reason",
    "pnl_delta",
    "equity_after",
]


class CsvLogger:
    def __init__(self, output_dir: str | Path, reset: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.output_dir / "events.csv"
        self.trades_path = self.output_dir / "trades.csv"
        self.signals_path = self.output_dir / "signals.csv"
        self.fills_path = self.output_dir / "fills.csv"
        self._ensure_file(self.events_path, EVENT_HEADERS, reset=reset)
        self._ensure_file(self.trades_path, TRADE_HEADERS, reset=reset)
        self._ensure_file(self.signals_path, SIGNAL_HEADERS, reset=reset)
        self._ensure_file(self.fills_path, FILL_HEADERS, reset=reset)

    @staticmethod
    def _ensure_file(path: Path, headers: list[str], *, reset: bool) -> None:
        mode = "w" if reset or (not path.exists()) else "a"
        with path.open(mode, newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if mode == "w":
                writer.writerow(headers)

    def log_event(self, timestamp: datetime, event_type: str, details: dict[str, Any] | None = None) -> None:
        payload = details or {}
        with self.events_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp.isoformat(), event_type, json.dumps(payload, sort_keys=True, default=str)])

    def log_trade(self, trade: Trade) -> None:
        with self.trades_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    trade.trade_id,
                    trade.mode,
                    trade.regime_at_entry,
                    trade.direction.value,
                    trade.entry_time.isoformat(),
                    f"{trade.entry_price:.5f}",
                    f"{trade.sl:.5f}",
                    f"{trade.tp:.5f}",
                    trade.exit_time.isoformat() if trade.exit_time else "",
                    f"{trade.exit_price:.5f}" if trade.exit_price is not None else "",
                    trade.exit_reason or "",
                    f"{trade.r_multiple:.5f}",
                    f"{trade.spread:.5f}",
                    f"{trade.entry_mid:.5f}",
                    f"{trade.exit_mid:.5f}" if trade.exit_mid is not None else "",
                    f"{trade.size:.8f}",
                    f"{trade.closed_size:.8f}",
                    f"{trade.risk_amount:.5f}",
                    f"{trade.pnl:.5f}",
                    f"{trade.mae_r:.5f}",
                    f"{trade.mfe_r:.5f}",
                    int(trade.tp1_hit),
                    int(trade.bars_in_trade),
                    f"{trade.minutes_in_trade:.2f}",
                    f"{trade.cost_multiplier:.4f}",
                ]
            )

    def log_signal(self, timestamp: datetime, payload: dict[str, Any]) -> None:
        with self.signals_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp.isoformat(),
                    payload.get("state", ""),
                    payload.get("event_type", ""),
                    payload.get("signal", ""),
                    payload.get("bias", ""),
                    payload.get("bias_reason", ""),
                    payload.get("m15_confirmation", ""),
                    payload.get("m15_reason", ""),
                    payload.get("entry_price_candidate", ""),
                    payload.get("entry_price_side", ""),
                    payload.get("sl", ""),
                    payload.get("tp", ""),
                    payload.get("outcome", ""),
                    payload.get("pnl", ""),
                    payload.get("r_multiple", ""),
                    payload.get("bars_in_trade", ""),
                    payload.get("minutes_in_trade", ""),
                    json.dumps(payload.get("payload_json", {}), sort_keys=True, default=str),
                ]
            )

    def log_fill(self, payload: dict[str, Any]) -> None:
        with self.fills_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    payload.get("fill_id", ""),
                    payload.get("trade_id", ""),
                    payload.get("timestamp", ""),
                    payload.get("fill_type", ""),
                    payload.get("side", ""),
                    payload.get("qty", ""),
                    payload.get("mid_price", ""),
                    payload.get("fill_price", ""),
                    payload.get("spread_usd", ""),
                    payload.get("slippage_usd", ""),
                    payload.get("cost_multiplier", ""),
                    payload.get("reason", ""),
                    payload.get("pnl_delta", ""),
                    payload.get("equity_after", ""),
                ]
            )
