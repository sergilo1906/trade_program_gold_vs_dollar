from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "outputs" / "runs"
WFA_DIR = ROOT / "outputs" / "wfa"
TRAIN_CSV = WFA_DIR / "wfa_train_runs.csv"
VAL_CSV = WFA_DIR / "wfa_val_runs.csv"
SPLITS_CSV = WFA_DIR / "wfa_splits.csv"
SUMMARY_JSON = WFA_DIR / "wfa_summary.json"
DOC_PATH = ROOT / "docs" / "WALK_FORWARD_RESULTS.md"
LOG_PATH = ROOT / "docs" / "UNATTENDED_LOG.md"

R_COL_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)

FOLD2_RUNS = {
    "EXP_A": "20260219_101829",
    "EXP_B": "20260219_102723",
    "EXP_C": "20260219_103558",
}
FOLD2_WINNER = {
    "label": "EXP_C",
    "config_path": "configs/config_v3_AUTO_EXP_C.yaml",
    "val_run_id": "20260219_104443",
}


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    raise ValueError(f"No R column found in trades.csv columns={list(df.columns)}")


def _trade_kpis(run_id: str) -> dict[str, Any]:
    trades_path = RUNS_ROOT / run_id / "trades.csv"
    trades = pd.read_csv(trades_path)
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    if r.empty:
        return {
            "expectancy_R": float("nan"),
            "pf": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
            "r_col": r_col,
        }
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    pf = gross_win / gross_loss if gross_loss > 0 else (float("inf") if gross_win > 0 else float("nan"))
    return {
        "expectancy_R": float(r.mean()),
        "pf": float(pf),
        "winrate": float((r > 0).mean()),
        "trades": int(r.size),
        "r_col": r_col,
    }


def _boot_row(run_id: str) -> dict[str, Any]:
    path = RUNS_ROOT / run_id / "diagnostics" / "BOOT_expectancy_ci.csv"
    if not path.exists():
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples_file": pd.NA,
        }
    df = pd.read_csv(path)
    if df.empty:
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples_file": pd.NA,
        }
    row = df.iloc[0]
    return {
        "boot_n": row.get("n", pd.NA),
        "boot_mean": row.get("mean", pd.NA),
        "boot_ci_low": row.get("ci_low", pd.NA),
        "boot_ci_high": row.get("ci_high", pd.NA),
        "boot_crosses_zero": row.get("crosses_zero", pd.NA),
        "boot_resamples_file": row.get("resamples", pd.NA),
    }


def _md_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data_"
    float_cols = float_cols or set()
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for c in cols:
            v = row[c]
            if isinstance(v, pd.Series):
                v = v.iloc[0] if not v.empty else pd.NA
            if pd.isna(v):
                vals.append("")
            elif c in float_cols:
                vals.append(f"{float(v):.6f}".rstrip("0").rstrip("."))
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _append_log(lines: list[str]) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n".join(lines).rstrip() + "\n")


def _ensure_fold2_rows(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fold = "Fold2"
    cfg_map = {
        "EXP_A": "configs/config_v3_AUTO_EXP_A.yaml",
        "EXP_B": "configs/config_v3_AUTO_EXP_B.yaml",
        "EXP_C": "configs/config_v3_AUTO_EXP_C.yaml",
    }

    train_df = train_df.copy()
    val_df = val_df.copy()

    train_df = train_df[train_df["fold"] != fold]
    val_df = val_df[val_df["fold"] != fold]

    rows: list[dict[str, Any]] = []
    for label, run_id in FOLD2_RUNS.items():
        k = _trade_kpis(run_id)
        rows.append(
            {
                "fold": fold,
                "data_scope": "TRAIN",
                "config_label": label,
                "config_path": cfg_map[label],
                "run_id": run_id,
                "expectancy_R": k["expectancy_R"],
                "pf": k["pf"],
                "winrate": k["winrate"],
                "trades": k["trades"],
                "r_col": k["r_col"],
                "data_csv": "data/tmp_wfa/Fold2_train.csv",
                "winner_config_label": "",
                "winner_config_path": "",
                "train_run_id": "",
            }
        )

    winner_train_run_id = FOLD2_RUNS[FOLD2_WINNER["label"]]
    winner_k = _trade_kpis(winner_train_run_id)
    rows.append(
        {
            "fold": fold,
            "data_scope": "TRAIN_WINNER",
            "config_label": FOLD2_WINNER["label"],
            "config_path": FOLD2_WINNER["config_path"],
            "run_id": winner_train_run_id,
            "expectancy_R": winner_k["expectancy_R"],
            "pf": winner_k["pf"],
            "winrate": winner_k["winrate"],
            "trades": winner_k["trades"],
            "r_col": winner_k["r_col"],
            "data_csv": "data/tmp_wfa/Fold2_train.csv",
            "winner_config_label": FOLD2_WINNER["label"],
            "winner_config_path": FOLD2_WINNER["config_path"],
            "train_run_id": winner_train_run_id,
        }
    )

    train_df = pd.concat([train_df, pd.DataFrame(rows)], ignore_index=True)

    val_k = _trade_kpis(FOLD2_WINNER["val_run_id"])
    boot = _boot_row(FOLD2_WINNER["val_run_id"])
    val_row = {
        "fold": fold,
        "winner_config_label": FOLD2_WINNER["label"],
        "winner_config_path": FOLD2_WINNER["config_path"],
        "val_run_id": FOLD2_WINNER["val_run_id"],
        "expectancy_R": val_k["expectancy_R"],
        "pf": val_k["pf"],
        "winrate": val_k["winrate"],
        "trades": val_k["trades"],
        "boot_n": boot["boot_n"],
        "boot_mean": boot["boot_mean"],
        "boot_ci_low": boot["boot_ci_low"],
        "boot_ci_high": boot["boot_ci_high"],
        "boot_crosses_zero": boot["boot_crosses_zero"],
        "boot_resamples_file": boot["boot_resamples_file"],
        "boot_resamples_used": 5000,
        "data_csv": "data/tmp_wfa/Fold2_val.csv",
        "winner_train_run_id": winner_train_run_id,
    }
    val_df = pd.concat([val_df, pd.DataFrame([val_row])], ignore_index=True)
    return train_df, val_df


def _build_doc(train_df: pd.DataFrame, val_df: pd.DataFrame, agg_df: pd.DataFrame, global_winner: pd.Series | None) -> None:
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    winner_rows = (
        train_df[train_df["data_scope"] == "TRAIN_WINNER"][
            ["fold", "config_label", "config_path", "run_id", "expectancy_R", "pf", "trades"]
        ]
        .rename(
            columns={
                "config_label": "winner_config_label",
                "config_path": "winner_config_path",
                "run_id": "train_run_id",
            }
        )
        .sort_values("fold")
        .reset_index(drop=True)
    )

    val_show = val_df[
        [
            "fold",
            "winner_config_label",
            "winner_config_path",
            "val_run_id",
            "expectancy_R",
            "pf",
            "winrate",
            "trades",
            "boot_ci_low",
            "boot_ci_high",
            "boot_crosses_zero",
            "boot_resamples_used",
        ]
    ].sort_values("fold")

    lines: list[str] = []
    lines.append("# Walk-Forward Results (DEV80 only)")
    lines.append("")
    lines.append(f"- generated_utc: {ts}")
    lines.append("- data_source: `data/xauusd_m5_DEV80.csv`")
    lines.append("- folds: Fold1 0-40/40-50, Fold2 0-50/50-60, Fold3 0-60/60-70, Fold4 0-70/70-80.")
    lines.append("- winner_fold criteria (TRAIN): expectancy_R, tie PF, tie trades.")
    lines.append("- winner_global criteria (VAL OOS): median expectancy_R, tie mean expectancy_R, tie mean PF.")
    lines.append("")
    lines.append("## Fold winner selection on TRAIN")
    lines.append(_md_table(winner_rows, float_cols={"expectancy_R", "pf"}))
    lines.append("")
    lines.append("## Winner performance on VAL (OOS)")
    lines.append(
        _md_table(
            val_show,
            float_cols={"expectancy_R", "pf", "winrate", "boot_ci_low", "boot_ci_high"},
        )
    )
    lines.append("")
    lines.append("## Aggregated by config (VAL OOS only)")
    lines.append(
        _md_table(
            agg_df,
            float_cols={"expectancy_R_mean", "expectancy_R_median", "pf_mean"},
        )
    )
    lines.append("")
    lines.append("## WINNER_GLOBAL (VAL OOS only)")
    if global_winner is None:
        lines.append("- WINNER_GLOBAL: `NA`")
    else:
        lines.append(
            f"- WINNER_GLOBAL: `{global_winner['config_label']}` (`{global_winner['config_path']}`)"
        )
        lines.append(
            f"- median_expectancy_R={float(global_winner['expectancy_R_median']):.6f}, "
            f"mean_expectancy_R={float(global_winner['expectancy_R_mean']):.6f}, "
            f"mean_PF={float(global_winner['pf_mean']):.6f}"
        )
    lines.append("")
    lines.append("## Run map")
    lines.append("- train runs csv: `outputs/wfa/wfa_train_runs.csv`")
    lines.append("- val runs csv: `outputs/wfa/wfa_val_runs.csv`")
    lines.append("- summary json: `outputs/wfa/wfa_summary.json`")
    lines.append("- note: Fold2 was re-run after transient disk-space exhaustion.")
    lines.append("")
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    WFA_DIR.mkdir(parents=True, exist_ok=True)
    train_df = pd.read_csv(TRAIN_CSV) if TRAIN_CSV.exists() else pd.DataFrame()
    val_df = pd.read_csv(VAL_CSV) if VAL_CSV.exists() else pd.DataFrame()
    if train_df.empty or val_df.empty:
        raise RuntimeError("Missing WFA base CSVs. Run WFA first.")

    train_df, val_df = _ensure_fold2_rows(train_df, val_df)
    train_df = train_df.sort_values(["fold", "data_scope", "config_label"], kind="stable").reset_index(drop=True)
    val_df = val_df.sort_values(["fold"], kind="stable").reset_index(drop=True)
    train_df.to_csv(TRAIN_CSV, index=False)
    val_df.to_csv(VAL_CSV, index=False)

    agg_df = (
        val_df.groupby(["winner_config_label", "winner_config_path"], as_index=False)
        .agg(
            folds_won=("fold", "count"),
            expectancy_R_mean=("expectancy_R", "mean"),
            expectancy_R_median=("expectancy_R", "median"),
            pf_mean=("pf", "mean"),
            trades_total=("trades", "sum"),
            trades_mean=("trades", "mean"),
        )
        .rename(
            columns={
                "winner_config_label": "config_label",
                "winner_config_path": "config_path",
            }
        )
        .sort_values(["expectancy_R_median", "expectancy_R_mean", "pf_mean"], ascending=[False, False, False])
        .reset_index(drop=True)
    )
    global_winner = agg_df.iloc[0] if not agg_df.empty else None

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dev_csv": "data/xauusd_m5_DEV80.csv",
        "splits_csv": "outputs/wfa/wfa_splits.csv",
        "train_runs_csv": "outputs/wfa/wfa_train_runs.csv",
        "val_runs_csv": "outputs/wfa/wfa_val_runs.csv",
        "winner_global_label": None if global_winner is None else str(global_winner["config_label"]),
        "winner_global_config_path": None if global_winner is None else str(global_winner["config_path"]),
        "winner_global_stats": None
        if global_winner is None
        else {
            "expectancy_R_median": float(global_winner["expectancy_R_median"]),
            "expectancy_R_mean": float(global_winner["expectancy_R_mean"]),
            "pf_mean": float(global_winner["pf_mean"]),
            "folds_won": int(global_winner["folds_won"]),
        },
        "val_run_ids": val_df["val_run_id"].astype(str).tolist(),
        "notes": [
            "Fold2 initial attempt failed due no space left on device; fold re-run completed successfully.",
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _build_doc(train_df, val_df, agg_df, global_winner)

    _append_log(
        [
            "",
            "### Phase 2.1 - Fold2 recovery",
            f"- Fold2 train EXP_A run_id: `{FOLD2_RUNS['EXP_A']}`",
            f"- Fold2 train EXP_B run_id: `{FOLD2_RUNS['EXP_B']}`",
            f"- Fold2 train EXP_C run_id: `{FOLD2_RUNS['EXP_C']}`",
            f"- Fold2 winner: `{FOLD2_WINNER['label']}`",
            f"- Fold2 VAL run_id: `{FOLD2_WINNER['val_run_id']}`",
            "- Updated: `outputs/wfa/wfa_train_runs.csv`, `outputs/wfa/wfa_val_runs.csv`, `outputs/wfa/wfa_summary.json`, `docs/WALK_FORWARD_RESULTS.md`",
        ]
    )

    print(f"Wrote: {TRAIN_CSV.as_posix()}")
    print(f"Wrote: {VAL_CSV.as_posix()}")
    print(f"Wrote: {SUMMARY_JSON.as_posix()}")
    print(f"Wrote: {DOC_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
