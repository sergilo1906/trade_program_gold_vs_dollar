from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


PLOT_EVENT_TYPES = {"SIGNAL_DETECTED", "TRADE_OPEN", "TRADE_CLOSE"}


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _load_m5(data_path: Path, bars: int) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    if "timestamp" not in df.columns or "close" not in df.columns:
        raise ValueError("Input data must include 'timestamp' and 'close' columns.")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["timestamp", "close"]).sort_values("timestamp")
    if df.empty:
        raise ValueError("No valid rows in market data.")
    return df.tail(max(1, int(bars))).reset_index(drop=True)


def _load_signals(signals_path: Path) -> pd.DataFrame:
    if not signals_path.exists():
        return pd.DataFrame(columns=["ts", "event_type", "signal", "entry_price_candidate", "outcome", "payload_json"])
    df = pd.read_csv(signals_path)
    if df.empty:
        return df
    timestamp_col = "ts" if "ts" in df.columns else "timestamp" if "timestamp" in df.columns else None
    if timestamp_col is None or "event_type" not in df.columns:
        return pd.DataFrame(columns=["ts", "event_type", "signal", "entry_price_candidate", "outcome", "payload_json"])
    df = df.copy()
    if timestamp_col != "ts":
        df["ts"] = df[timestamp_col]
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    df = df.dropna(subset=["ts"])
    df = df[df["event_type"].isin(PLOT_EVENT_TYPES)]
    return df.sort_values("ts").reset_index(drop=True)


def _payload_dict(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, str):
        return {}
    text = raw.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if isinstance(value, dict):
        return value
    return {}


def _label_for_event(event: str, signal: str, outcome: str) -> str:
    signal_text = signal if signal else "-"
    if event == "SIGNAL_DETECTED":
        return f"SIG {signal_text}"
    if event == "TRADE_OPEN":
        return f"OPEN {signal_text}"
    if event == "TRADE_CLOSE":
        out = outcome or ""
        if out.startswith("TP"):
            return f"TP {signal_text}"
        if out.startswith("SL"):
            return f"SL {signal_text}"
        if "TIME" in out:
            return f"TIME {signal_text}"
        if out:
            return f"{out[:8]} {signal_text}"
        return f"CLOSE {signal_text}"
    return event


def _draw_marker(draw: ImageDraw.ImageDraw, event: str, signal: str, x: int, y: int) -> tuple[int, int, int]:
    if event == "SIGNAL_DETECTED":
        color = (28, 90, 180)
        if signal == "BUY":
            draw.polygon([(x, y - 7), (x - 6, y + 6), (x + 6, y + 6)], fill=color)
        else:
            draw.polygon([(x, y + 7), (x - 6, y - 6), (x + 6, y - 6)], fill=color)
        return color
    if event == "TRADE_OPEN":
        color = (18, 140, 70)
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
        return color
    color = (180, 36, 36)
    draw.line((x - 6, y - 6, x + 6, y + 6), fill=color, width=2)
    draw.line((x - 6, y + 6, x + 6, y - 6), fill=color, width=2)
    return color


def generate_plot(
    data_path: str | Path = "data/sample_m5.csv",
    signals_path: str | Path = "output/signals.csv",
    output_path: str | Path = "output/last_chart.png",
    bars: int = 300,
) -> Path:
    market = _load_m5(Path(data_path), bars=bars)
    signals = _load_signals(Path(signals_path))

    width, height = 1500, 850
    margin_x, margin_y = 70, 50
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    ts_min = market["timestamp"].iloc[0]
    ts_max = market["timestamp"].iloc[-1]
    ts_span = max((ts_max - ts_min).total_seconds(), 1.0)

    price_min = float(market["close"].min())
    price_max = float(market["close"].max())
    pad = (price_max - price_min) * 0.05
    if pad == 0:
        pad = 1.0
    y_min = price_min - pad
    y_max = price_max + pad
    y_span = max(y_max - y_min, 1e-9)

    def x_of(ts: pd.Timestamp) -> int:
        ratio = (ts - ts_min).total_seconds() / ts_span
        return int(margin_x + ratio * (width - (2 * margin_x)))

    def y_of(price: float) -> int:
        ratio = (price - y_min) / y_span
        return int(height - margin_y - ratio * (height - (2 * margin_y)))

    draw.rectangle((margin_x, margin_y, width - margin_x, height - margin_y), outline=(200, 200, 200), width=1)

    close_points = [(x_of(ts), y_of(float(price))) for ts, price in zip(market["timestamp"], market["close"])]
    if len(close_points) >= 2:
        draw.line(close_points, fill=(30, 30, 30), width=2)

    def nearest_close(ts: pd.Timestamp) -> float:
        deltas = (market["timestamp"] - ts).abs()
        nearest_idx = int(deltas.idxmin())
        return float(market.loc[nearest_idx, "close"])

    in_window = signals[(signals["ts"] >= ts_min) & (signals["ts"] <= ts_max)].copy()
    for _, event_row in in_window.iterrows():
        event_ts = pd.Timestamp(event_row["ts"])
        event_type = str(event_row.get("event_type", ""))
        signal = str(event_row.get("signal", "") or "")
        outcome = str(event_row.get("outcome", "") or "")
        payload = _payload_dict(event_row.get("payload_json", ""))

        price = None
        if event_type == "TRADE_CLOSE":
            price = _parse_float(payload.get("exit_price"))
        if price is None:
            price = _parse_float(event_row.get("entry_price_candidate", ""))
        if price is None:
            price = nearest_close(event_ts)

        px = x_of(event_ts)
        py = y_of(float(price))
        color = _draw_marker(draw, event_type, signal, px, py)
        label = _label_for_event(event_type, signal, outcome)
        draw.text((px + 8, py - 10), label, fill=color, font=font)

    draw.text((margin_x, 15), "XAUUSD - close + signal markers", fill=(20, 20, 20), font=font)
    draw.text((margin_x, height - 28), f"{ts_min} -> {ts_max}", fill=(70, 70, 70), font=font)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot close line with signal markers from signals.csv")
    parser.add_argument("--data", default="data/sample_m5.csv", help="Path to market CSV (timestamp, close required)")
    parser.add_argument("--signals", default="output/signals.csv", help="Path to signals CSV")
    parser.add_argument("--output", default="output/last_chart.png", help="Output PNG path")
    parser.add_argument("--bars", type=int, default=300, help="Number of latest bars to draw")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = generate_plot(data_path=args.data, signals_path=args.signals, output_path=args.output, bars=args.bars)
    print(f"Wrote chart to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
