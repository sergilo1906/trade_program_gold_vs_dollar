from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def read_csv_tolerant(
    path: Path,
    *,
    label: str,
    warnings: list[str] | None = None,
    required: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        msg = f"{label}: missing CSV at {path.as_posix()}"
        if required:
            raise FileNotFoundError(msg)
        if warnings is not None:
            warnings.append(msg)
        return pd.DataFrame()

    try:
        return pd.read_csv(path, **kwargs)
    except Exception as exc_default:
        try:
            fallback_kwargs = dict(kwargs)
            fallback_kwargs.pop("low_memory", None)
            df = pd.read_csv(
                path,
                engine="python",
                on_bad_lines="skip",
                encoding_errors="replace",
                **fallback_kwargs,
            )
            if warnings is not None:
                warnings.append(
                    f"{label}: tolerant CSV fallback used for {path.name} after parse error: {exc_default}"
                )
            return df
        except Exception as exc_fallback:
            msg = (
                f"{label}: failed to read CSV {path.name}; default={exc_default}; "
                f"tolerant_fallback={exc_fallback}"
            )
            if required:
                raise RuntimeError(msg) from exc_fallback
            if warnings is not None:
                warnings.append(msg)
            return pd.DataFrame()
