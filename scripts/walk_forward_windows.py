from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEV_CSV = ROOT / "data" / "xauusd_m5_DEV80.csv"
TMP_WFA_DIR = ROOT / "data" / "tmp_wfa"
DOC_PATH = ROOT / "docs" / "WALK_FORWARD_RESULTS.md"
OUT_DIR = ROOT / "outputs" / "wfa"
RUNS_ROOT = ROOT / "outputs" / "runs"
UNATTENDED_LOG_PATH = ROOT / "docs" / "UNATTENDED_LOG.md"

CONFIGS: dict[str, Path] = {
    "EXP_A": ROOT / "configs" / "config_v3_AUTO_EXP_A.yaml",
    "EXP_B": ROOT / "configs" / "config_v3_AUTO_EXP_B.yaml",
    "EXP_C": ROOT / "configs" / "config_v3_AUTO_EXP_C.yaml",
}

FOLDS = [
    ("Fold1", 0.00, 0.40, 0.40, 0.50),
    ("Fold2", 0.00, 0.50, 0.50, 0.60),
    ("Fold3", 0.00, 0.60, 0.60, 0.70),
    ("Fold4", 0.00, 0.70, 0.70, 0.80),
]

R_COL_CANDIDATES = (
    "r_multiple",
    "R_net",
    "r_net",
    "net_R",
    "net_r",
    "pnl_R",
    "pnl_r",
)


@dataclass
class CmdResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


def _append_unattended_log(lines: list[str]) -> None:
    UNATTENDED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with UNATTENDED_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n".join(lines).rstrip() + "\n")


def _run_cmd(cmd: list[str], cwd: Path = ROOT) -> CmdResult:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return CmdResult(
        cmd=cmd,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def _run_checked(cmd: list[str], cwd: Path = ROOT) -> CmdResult:
    res = _run_cmd(cmd, cwd=cwd)
    if res.returncode != 0:
        detail = (
            f"Command failed ({res.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )
        raise RuntimeError(detail)
    return res


def _extract_run_id(output: str) -> str:
    m = re.search(r"run_id:\s*([0-9_]+)", output)
    if not m:
        raise ValueError(f"Unable to parse run_id from output:\n{output}")
    return m.group(1)


def _find_r_col(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for cand in R_COL_CANDIDATES:
        col = lowered.get(cand.lower())
        if col is not None:
            return col
    raise ValueError(f"No R column found in trades.csv. columns={list(df.columns)}")


def _compute_trade_kpis(run_dir: Path) -> dict[str, Any]:
    trades_path = run_dir / "trades.csv"
    if not trades_path.exists():
        return {
            "pf": float("nan"),
            "expectancy_R": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
            "r_col": "",
        }
    trades = pd.read_csv(trades_path)
    if trades.empty:
        return {
            "pf": float("nan"),
            "expectancy_R": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
            "r_col": "",
        }
    r_col = _find_r_col(trades)
    r = pd.to_numeric(trades[r_col], errors="coerce").dropna()
    n = int(r.size)
    if n == 0:
        return {
            "pf": float("nan"),
            "expectancy_R": float("nan"),
            "winrate": float("nan"),
            "trades": 0,
            "r_col": r_col,
        }
    gross_win = float(r[r > 0].sum())
    gross_loss = float((-r[r < 0]).sum())
    if gross_loss > 0:
        pf = gross_win / gross_loss
    else:
        pf = float("inf") if gross_win > 0 else float("nan")
    return {
        "pf": float(pf),
        "expectancy_R": float(r.mean()),
        "winrate": float((r > 0).mean()),
        "trades": n,
        "r_col": r_col,
    }


def _md_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data_"
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()
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


def _winner_key(row: pd.Series) -> tuple[float, float, float]:
    exp = pd.to_numeric(row.get("expectancy_R", float("-inf")), errors="coerce")
    pf = pd.to_numeric(row.get("pf", float("-inf")), errors="coerce")
    trades = pd.to_numeric(row.get("trades", float("-inf")), errors="coerce")
    if pd.isna(exp):
        exp = float("-inf")
    if pd.isna(pf):
        pf = float("-inf")
    if pd.isna(trades):
        trades = float("-inf")
    return float(exp), float(pf), float(trades)


def _short_exc(exc: Exception, limit: int = 600) -> str:
    text = re.sub(r"\s+", " ", str(exc)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _run_and_tag(data_path: Path, config_path: Path) -> tuple[str, CmdResult]:
    cmd = [
        sys.executable,
        "scripts/run_and_tag.py",
        "--data",
        str(data_path),
        "--config",
        str(config_path),
        "--runs-root",
        str(RUNS_ROOT),
    ]
    res = _run_checked(cmd)
    run_id = _extract_run_id(res.stdout)
    return run_id, res


def _run_diagnose(run_id: str) -> CmdResult:
    run_dir = RUNS_ROOT / run_id
    cmd = [sys.executable, "scripts/diagnose_run.py", str(run_dir)]
    return _run_checked(cmd)


def _run_bootstrap(run_id: str, notes: list[str]) -> tuple[int, CmdResult]:
    run_dir = RUNS_ROOT / run_id
    cmd_5000 = [
        sys.executable,
        "scripts/bootstrap_expectancy.py",
        str(run_dir),
        "--resamples",
        "5000",
        "--seed",
        "42",
    ]
    first = _run_cmd(cmd_5000)
    if first.returncode == 0:
        return 5000, first

    notes.append(
        "bootstrap_expectancy failed at 5000; "
        f"retrying with 2000. run_id={run_id}; stderr={first.stderr.strip()[:400]}"
    )
    cmd_2000 = [
        sys.executable,
        "scripts/bootstrap_expectancy.py",
        str(run_dir),
        "--resamples",
        "2000",
        "--seed",
        "42",
    ]
    second = _run_checked(cmd_2000)
    return 2000, second


def _read_boot_row(run_id: str) -> dict[str, Any]:
    p = RUNS_ROOT / run_id / "diagnostics" / "BOOT_expectancy_ci.csv"
    if not p.exists():
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples": pd.NA,
        }
    df = pd.read_csv(p)
    if df.empty:
        return {
            "boot_n": pd.NA,
            "boot_mean": pd.NA,
            "boot_ci_low": pd.NA,
            "boot_ci_high": pd.NA,
            "boot_crosses_zero": pd.NA,
            "boot_resamples": pd.NA,
        }
    row = df.iloc[0]
    return {
        "boot_n": row.get("n", pd.NA),
        "boot_mean": row.get("mean", pd.NA),
        "boot_ci_low": row.get("ci_low", pd.NA),
        "boot_ci_high": row.get("ci_high", pd.NA),
        "boot_crosses_zero": row.get("crosses_zero", pd.NA),
        "boot_resamples": row.get("resamples", pd.NA),
    }


def _to_int_idx(pct: float, n: int) -> int:
    return int(math.floor(pct * n))


def _write_doc(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    agg_df: pd.DataFrame,
    global_winner_row: pd.Series | None,
    notes: list[str],
) -> None:
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines: list[str] = []
    lines.append("# Walk-Forward Results (DEV80 only)")
    lines.append("")
    lines.append(f"- generated_utc: {ts}")
    lines.append("- data_source: `data/xauusd_m5_DEV80.csv`")
    lines.append("- folds:")
    lines.append("  - Fold1: train 0-40%, val 40-50%")
    lines.append("  - Fold2: train 0-50%, val 50-60%")
    lines.append("  - Fold3: train 0-60%, val 60-70%")
    lines.append("  - Fold4: train 0-70%, val 70-80%")
    lines.append("- winner_fold criteria (TRAIN): higher `expectancy_R`, tie `pf`, tie `trades`.")
    lines.append("- global winner criteria (VAL OOS only): higher median `expectancy_R`, tie mean `expectancy_R`, tie mean `pf`.")
    lines.append("")
    lines.append("## Fold winner selection on TRAIN")
    if train_df.empty:
        lines.append("_No train data_")
    else:
        train_df = train_df.loc[:, ~train_df.columns.duplicated()].copy()
        selected = (
            train_df.sort_values(["fold", "expectancy_R", "pf", "trades"], ascending=[True, False, False, False])
            .groupby("fold", as_index=False)
            .head(1)
            .sort_values("fold")
        )
        train_cols = [
            "fold",
            "winner_config_label",
            "winner_config_path",
            "train_run_id",
            "expectancy_R",
            "pf",
            "trades",
        ]
        missing_train_cols = [c for c in train_cols if c not in selected.columns]
        if missing_train_cols:
            lines.append(f"_Missing TRAIN winner columns: {', '.join(missing_train_cols)}_")
        else:
            lines.append(
                _md_table(
                    selected[train_cols],
                    float_cols={"expectancy_R", "pf"},
                )
            )
    lines.append("")
    lines.append("## Winner performance on VAL (OOS)")
    if val_df.empty:
        lines.append("_No data_")
    else:
        val_df = val_df.loc[:, ~val_df.columns.duplicated()].copy()
        val_cols = [
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
        missing_val_cols = [c for c in val_cols if c not in val_df.columns]
        if missing_val_cols:
            lines.append(f"_Missing VAL columns: {', '.join(missing_val_cols)}_")
        else:
            lines.append(
                _md_table(
                    val_df[val_cols],
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
    if global_winner_row is None:
        lines.append("- WINNER_GLOBAL: `NA`")
    else:
        lines.append(
            f"- WINNER_GLOBAL: `{global_winner_row['config_label']}` "
            f"(`{global_winner_row['config_path']}`)"
        )
        lines.append(
            f"- median_expectancy_R={float(global_winner_row['expectancy_R_median']):.6f}, "
            f"mean_expectancy_R={float(global_winner_row['expectancy_R_mean']):.6f}, "
            f"mean_PF={float(global_winner_row['pf_mean']):.6f}"
        )
    lines.append("")
    lines.append("## Run map")
    lines.append("- train runs csv: `outputs/wfa/wfa_train_runs.csv`")
    lines.append("- val runs csv: `outputs/wfa/wfa_val_runs.csv`")
    lines.append("- summary json: `outputs/wfa/wfa_summary.json`")
    if notes:
        lines.append("")
        lines.append("## Notes / Errors")
        for n in notes:
            lines.append(f"- {n}")
    lines.append("")
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    notes: list[str] = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_WFA_DIR.mkdir(parents=True, exist_ok=True)

    if not DEV_CSV.exists():
        msg = f"Missing DEV dataset: {DEV_CSV.as_posix()}"
        notes.append(msg)
        _append_unattended_log(
            [
                "",
                "## Phase 2 - Walk Forward",
                "",
                f"- ERROR: {msg}",
            ]
        )
        empty = pd.DataFrame()
        _write_doc(empty, empty, empty, None, notes)
        return 1

    dev = pd.read_csv(DEV_CSV)
    if "timestamp" not in dev.columns:
        msg = "Missing 'timestamp' column in DEV dataset."
        notes.append(msg)
        _append_unattended_log(
            [
                "",
                "## Phase 2 - Walk Forward",
                "",
                f"- ERROR: {msg}",
            ]
        )
        empty = pd.DataFrame()
        _write_doc(empty, empty, empty, None, notes)
        return 1

    dev["timestamp"] = pd.to_datetime(dev["timestamp"], errors="coerce")
    dev = dev.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    n = len(dev)

    train_rows: list[dict[str, Any]] = []
    val_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []

    _append_unattended_log(
        [
            "",
            "## Phase 2 - Walk Forward",
            "",
            f"- DEV rows: {n}",
            f"- Started UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        ]
    )

    for fold_name, train_start_pct, train_end_pct, val_start_pct, val_end_pct in FOLDS:
        tr0 = _to_int_idx(train_start_pct, n)
        tr1 = _to_int_idx(train_end_pct, n)
        va0 = _to_int_idx(val_start_pct, n)
        va1 = _to_int_idx(val_end_pct, n)

        train_df = dev.iloc[tr0:tr1].copy()
        val_df = dev.iloc[va0:va1].copy()
        train_csv = TMP_WFA_DIR / f"{fold_name}_train.csv"
        val_csv = TMP_WFA_DIR / f"{fold_name}_val.csv"
        train_df.to_csv(train_csv, index=False)
        val_df.to_csv(val_csv, index=False)

        split_rows.append(
            {
                "fold": fold_name,
                "train_rows": int(len(train_df)),
                "train_start_ts": str(train_df["timestamp"].iloc[0]) if not train_df.empty else "NA",
                "train_end_ts": str(train_df["timestamp"].iloc[-1]) if not train_df.empty else "NA",
                "val_rows": int(len(val_df)),
                "val_start_ts": str(val_df["timestamp"].iloc[0]) if not val_df.empty else "NA",
                "val_end_ts": str(val_df["timestamp"].iloc[-1]) if not val_df.empty else "NA",
            }
        )

        this_fold_train: list[dict[str, Any]] = []
        for cfg_label, cfg_path in CONFIGS.items():
            if not cfg_path.exists():
                notes.append(f"{fold_name} - missing config: {cfg_path.as_posix()}")
                continue
            try:
                run_id, _ = _run_and_tag(train_csv, cfg_path)
                run_dir = RUNS_ROOT / run_id
                k = _compute_trade_kpis(run_dir)
                row = {
                    "fold": fold_name,
                    "data_scope": "TRAIN",
                    "config_label": cfg_label,
                    "config_path": cfg_path.relative_to(ROOT).as_posix(),
                    "run_id": run_id,
                    "expectancy_R": k["expectancy_R"],
                    "pf": k["pf"],
                    "winrate": k["winrate"],
                    "trades": k["trades"],
                    "r_col": k["r_col"],
                    "data_csv": train_csv.relative_to(ROOT).as_posix(),
                }
                train_rows.append(row)
                this_fold_train.append(row)
            except Exception as exc:
                notes.append(f"{fold_name} - TRAIN failed for {cfg_label}: {_short_exc(exc)}")

        if not this_fold_train:
            notes.append(f"{fold_name} - no successful TRAIN runs; VAL skipped.")
            continue

        train_frame = pd.DataFrame(this_fold_train)
        best_idx = train_frame.apply(_winner_key, axis=1).idxmax()
        winner = train_frame.loc[best_idx].to_dict()
        winner_label = str(winner["config_label"])
        winner_cfg = ROOT / str(winner["config_path"])

        try:
            val_run_id, _ = _run_and_tag(val_csv, winner_cfg)
            _run_diagnose(val_run_id)
            used_resamples, _ = _run_bootstrap(val_run_id, notes)
            val_run_dir = RUNS_ROOT / val_run_id
            k_val = _compute_trade_kpis(val_run_dir)
            boot = _read_boot_row(val_run_id)
            val_rows.append(
                {
                    "fold": fold_name,
                    "winner_config_label": winner_label,
                    "winner_config_path": winner_cfg.relative_to(ROOT).as_posix(),
                    "val_run_id": val_run_id,
                    "expectancy_R": k_val["expectancy_R"],
                    "pf": k_val["pf"],
                    "winrate": k_val["winrate"],
                    "trades": k_val["trades"],
                    "boot_n": boot["boot_n"],
                    "boot_mean": boot["boot_mean"],
                    "boot_ci_low": boot["boot_ci_low"],
                    "boot_ci_high": boot["boot_ci_high"],
                    "boot_crosses_zero": boot["boot_crosses_zero"],
                    "boot_resamples_file": boot["boot_resamples"],
                    "boot_resamples_used": used_resamples,
                    "data_csv": val_csv.relative_to(ROOT).as_posix(),
                    "winner_train_run_id": winner["run_id"],
                }
            )
            train_rows.append(
                {
                    "fold": fold_name,
                    "data_scope": "TRAIN_WINNER",
                    "config_label": winner_label,
                    "config_path": winner_cfg.relative_to(ROOT).as_posix(),
                    "run_id": winner["run_id"],
                    "expectancy_R": winner["expectancy_R"],
                    "pf": winner["pf"],
                    "winrate": winner["winrate"],
                    "trades": winner["trades"],
                    "r_col": winner.get("r_col", ""),
                    "data_csv": train_csv.relative_to(ROOT).as_posix(),
                    "winner_config_label": winner_label,
                    "winner_config_path": winner_cfg.relative_to(ROOT).as_posix(),
                    "train_run_id": winner["run_id"],
                }
            )
        except Exception as exc:
            notes.append(f"{fold_name} - VAL failed for winner {winner_label}: {_short_exc(exc)}")

    train_frame = pd.DataFrame(train_rows)
    val_frame = pd.DataFrame(val_rows)
    split_frame = pd.DataFrame(split_rows)

    out_split = OUT_DIR / "wfa_splits.csv"
    out_train = OUT_DIR / "wfa_train_runs.csv"
    out_val = OUT_DIR / "wfa_val_runs.csv"
    split_frame.to_csv(out_split, index=False)
    train_frame.to_csv(out_train, index=False)
    val_frame.to_csv(out_val, index=False)

    global_winner_row: pd.Series | None = None
    agg = pd.DataFrame(
        columns=[
            "config_label",
            "config_path",
            "folds_won",
            "expectancy_R_mean",
            "expectancy_R_median",
            "pf_mean",
            "trades_total",
            "trades_mean",
        ]
    )

    if not val_frame.empty:
        agg = (
            val_frame.groupby(["winner_config_label", "winner_config_path"], as_index=False)
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
        )
        agg = agg.sort_values(
            ["expectancy_R_median", "expectancy_R_mean", "pf_mean"],
            ascending=[False, False, False],
        ).reset_index(drop=True)
        global_winner_row = agg.iloc[0]

    summary = {
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dev_csv": DEV_CSV.relative_to(ROOT).as_posix(),
        "splits_csv": out_split.relative_to(ROOT).as_posix(),
        "train_runs_csv": out_train.relative_to(ROOT).as_posix(),
        "val_runs_csv": out_val.relative_to(ROOT).as_posix(),
        "winner_global_label": None if global_winner_row is None else str(global_winner_row["config_label"]),
        "winner_global_config_path": None if global_winner_row is None else str(global_winner_row["config_path"]),
        "winner_global_stats": None
        if global_winner_row is None
        else {
            "expectancy_R_median": float(global_winner_row["expectancy_R_median"]),
            "expectancy_R_mean": float(global_winner_row["expectancy_R_mean"]),
            "pf_mean": float(global_winner_row["pf_mean"]),
            "folds_won": int(global_winner_row["folds_won"]),
        },
        "val_run_ids": val_frame["val_run_id"].astype(str).tolist() if not val_frame.empty else [],
        "notes": notes,
    }
    (OUT_DIR / "wfa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    winner_table = pd.DataFrame()
    if not train_frame.empty:
        winner_src_cols = ["fold", "config_label", "config_path", "run_id", "expectancy_R", "pf", "trades"]
        winners = (
            train_frame.loc[train_frame["data_scope"] == "TRAIN", winner_src_cols]
            .sort_values(["fold", "expectancy_R", "pf", "trades"], ascending=[True, False, False, False])
            .groupby("fold", as_index=False)
            .head(1)
            .sort_values("fold")
            .copy()
        )
        winners = winners.rename(
            columns={
                "config_label": "winner_config_label",
                "config_path": "winner_config_path",
                "run_id": "train_run_id",
            }
        )
        winner_table = winners[
            ["fold", "winner_config_label", "winner_config_path", "train_run_id", "expectancy_R", "pf", "trades"]
        ]

    _write_doc(winner_table, val_frame, agg, global_winner_row, notes)

    log_lines = [
        "",
        f"- WFA splits csv: `{out_split.relative_to(ROOT).as_posix()}`",
        f"- WFA train runs csv: `{out_train.relative_to(ROOT).as_posix()}`",
        f"- WFA val runs csv: `{out_val.relative_to(ROOT).as_posix()}`",
        f"- WFA results doc: `{DOC_PATH.relative_to(ROOT).as_posix()}`",
    ]
    if global_winner_row is None:
        log_lines.append("- WINNER_GLOBAL: NA")
    else:
        log_lines.append(
            f"- WINNER_GLOBAL: {global_winner_row['config_label']} ({global_winner_row['config_path']})"
        )
    if notes:
        log_lines.append("- Notes:")
        for n in notes:
            log_lines.append(f"  - {n}")
    _append_unattended_log(log_lines)

    print(f"Wrote: {out_split.as_posix()}")
    print(f"Wrote: {out_train.as_posix()}")
    print(f"Wrote: {out_val.as_posix()}")
    print(f"Wrote: {(OUT_DIR / 'wfa_summary.json').as_posix()}")
    print(f"Wrote: {DOC_PATH.as_posix()}")
    if global_winner_row is not None:
        print(
            "WINNER_GLOBAL:",
            global_winner_row["config_label"],
            global_winner_row["config_path"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
