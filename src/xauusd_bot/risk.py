from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from xauusd_bot.models import Trade


@dataclass(slots=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskManager:
    def __init__(self, config: dict):
        self.starting_balance = float(config.get("starting_balance", 10_000.0))
        self.equity = self.starting_balance
        self.peak_equity = self.starting_balance
        self.risk_per_trade_pct = float(config.get("risk_per_trade_pct", 0.01))
        self.day_pnl: dict[str, float] = {}
        self.week_pnl: dict[str, float] = {}
        self.day_r: dict[str, float] = {}
        self.week_r: dict[str, float] = {}
        self.day_start_equity: dict[str, float] = {}
        self.week_start_equity: dict[str, float] = {}

    @staticmethod
    def _week_key(timestamp: datetime) -> str:
        year, week, _ = timestamp.isocalendar()
        return f"{year:04d}-W{week:02d}"

    def can_open_trade(self, timestamp: datetime) -> RiskDecision:
        return RiskDecision(allowed=True, reason="OK")

    def position_size(self, entry: float, stop_loss: float) -> tuple[float, float]:
        stop_distance = max(abs(entry - stop_loss), 1e-9)
        risk_amount = max(self.equity * self.risk_per_trade_pct, 0.0)
        size = risk_amount / stop_distance
        return size, risk_amount

    def register_fill_pnl(self, timestamp: datetime, pnl_delta: float) -> float:
        self.equity += pnl_delta
        self.peak_equity = max(self.peak_equity, self.equity)

        day_key = timestamp.date().isoformat()
        week_key = self._week_key(timestamp)
        if day_key not in self.day_start_equity:
            self.day_start_equity[day_key] = self.equity - pnl_delta
        if week_key not in self.week_start_equity:
            self.week_start_equity[week_key] = self.equity - pnl_delta

        self.day_pnl[day_key] = float(self.day_pnl.get(day_key, 0.0)) + pnl_delta
        self.week_pnl[week_key] = float(self.week_pnl.get(week_key, 0.0)) + pnl_delta
        return self.equity

    def register_trade_result(self, trade: Trade) -> float:
        pnl = float(getattr(trade, "pnl", trade.risk_amount * trade.r_multiple))
        ts = trade.exit_time or trade.entry_time
        self.register_fill_pnl(ts, pnl)

        day_key = ts.date().isoformat()
        week_key = self._week_key(ts)
        if trade.risk_amount > 0:
            r = pnl / trade.risk_amount
            self.day_r[day_key] = float(self.day_r.get(day_key, 0.0)) + r
            self.week_r[week_key] = float(self.week_r.get(week_key, 0.0)) + r
        return pnl
