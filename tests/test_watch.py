from __future__ import annotations

import csv
import io

from xauusd_bot.watch import filter_event, format_line, parse_line


def test_parse_line_handles_payload_with_commas() -> None:
    headers = [
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
    row_values = [
        "2026-01-01T10:00:00",
        "WAIT_M5_ENTRY",
        "SIGNAL_DETECTED",
        "BUY",
        "LONG",
        "BULL_BOS",
        "OK",
        "OK",
        "2650.12",
        "ASK",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        '{"a":1,"b":2}',
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(row_values)
    line = buffer.getvalue()
    row = parse_line(line, headers)
    assert row is not None
    assert row["event_type"] == "SIGNAL_DETECTED"
    assert row["payload_json"] == '{"a":1,"b":2}'


def test_filter_event_allows_only_relevant_events() -> None:
    keep_row = {"event_type": "TRADE_CLOSE"}
    drop_row = {"event_type": "BIAS_SET"}
    assert filter_event(keep_row) is True
    assert filter_event(drop_row) is False


def test_format_line_contains_core_fields() -> None:
    row = {
        "ts": "2026-01-01T10:00:00",
        "event_type": "TRADE_CLOSE",
        "signal": "BUY",
        "bias": "LONG",
        "m15_confirmation": "OK",
        "entry_price_candidate": "2650.12",
        "outcome": "TP_HIT",
        "pnl": "150.00",
        "payload_json": '{"trade_id":1}',
    }
    text = format_line(row)
    assert "TRADE_CLOSE" in text
    assert "signal=BUY" in text
    assert "outcome=TP_HIT" in text
    assert "pnl=150.00" in text
