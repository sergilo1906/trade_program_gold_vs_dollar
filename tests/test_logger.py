from __future__ import annotations

from pathlib import Path

from xauusd_bot.logger import EVENT_HEADERS, FILL_HEADERS, SIGNAL_HEADERS, TRADE_HEADERS, CsvLogger


def test_logger_creates_csvs_with_headers(tmp_path: Path) -> None:
    logger = CsvLogger(output_dir=tmp_path)

    events_header = logger.events_path.read_text(encoding="utf-8").splitlines()[0]
    trades_header = logger.trades_path.read_text(encoding="utf-8").splitlines()[0]
    signals_header = logger.signals_path.read_text(encoding="utf-8").splitlines()[0]
    fills_header = logger.fills_path.read_text(encoding="utf-8").splitlines()[0]

    assert events_header == ",".join(EVENT_HEADERS)
    assert trades_header == ",".join(TRADE_HEADERS)
    assert signals_header == ",".join(SIGNAL_HEADERS)
    assert fills_header == ",".join(FILL_HEADERS)
