from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close"}
TIMESTAMP_ALIASES = {"timestamp", "time", "datetime", "date", "ts"}
HEADERLESS_BASE_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def _print_data_summary(prefix: str, csv_path: Path, rows: int, min_ts: object, max_ts: object, unique_days: object) -> None:
    print(
        f"{prefix} | file_used={csv_path.resolve()} | rows={rows} | "
        f"min_ts={min_ts} | max_ts={max_ts} | unique_days={unique_days}"
    )


def _normalize_col(name: object) -> str:
    return str(name).strip().lower()


def _find_timestamp_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if _normalize_col(col) in TIMESTAMP_ALIASES:
            return str(col)
    return None


def _looks_like_headerless_ohlcv(df: pd.DataFrame) -> bool:
    if df.empty or df.shape[1] < 5:
        return False

    normalized = {_normalize_col(col) for col in df.columns}
    if "timestamp" in normalized:
        return False

    first_col_name = str(df.columns[0]).strip()
    header_name_ts = pd.to_datetime(first_col_name, errors="coerce")
    if pd.isna(header_name_ts):
        return False

    first_col_values = pd.to_datetime(df.iloc[:, 0], errors="coerce")
    parse_ratio = float(first_col_values.notna().mean()) if len(first_col_values) else 0.0
    return parse_ratio >= 0.90


def _read_raw_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if not _looks_like_headerless_ohlcv(df):
        return df

    df_no_header = pd.read_csv(csv_path, header=None)
    if df_no_header.shape[1] <= len(HEADERLESS_BASE_COLUMNS):
        df_no_header.columns = HEADERLESS_BASE_COLUMNS[: df_no_header.shape[1]]
    else:
        extra = [f"col_{i}" for i in range(len(HEADERLESS_BASE_COLUMNS), df_no_header.shape[1])]
        df_no_header.columns = HEADERLESS_BASE_COLUMNS + extra
    return df_no_header


def load_m5_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = _read_raw_csv(csv_path)
    raw_ts_col = _find_timestamp_col(df)
    if raw_ts_col is not None:
        raw_ts = pd.to_datetime(df[raw_ts_col], errors="coerce")
        _print_data_summary(
            prefix="DATA SUMMARY (RAW)",
            csv_path=csv_path,
            rows=len(df),
            min_ts=raw_ts.min(),
            max_ts=raw_ts.max(),
            unique_days=int(raw_ts.dt.date.nunique()) if len(raw_ts) > 0 else 0,
        )
    else:
        _print_data_summary(
            prefix="DATA SUMMARY (RAW)",
            csv_path=csv_path,
            rows=len(df),
            min_ts="N/A",
            max_ts="N/A",
            unique_days="N/A",
        )
    df.columns = [str(col).strip().lower() for col in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    numeric_columns = [col for col in ("open", "high", "low", "close", "volume", "bid", "ask", "spread") if col in df.columns]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    if "volume" not in df.columns:
        df["volume"] = 0.0

    _print_data_summary(
        prefix="DATA SUMMARY (CLEAN)",
        csv_path=csv_path,
        rows=len(df),
        min_ts=df["timestamp"].min(),
        max_ts=df["timestamp"].max(),
        unique_days=int(df["timestamp"].dt.date.nunique()) if len(df) > 0 else 0,
    )

    return df
