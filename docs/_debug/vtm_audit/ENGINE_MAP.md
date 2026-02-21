# VTM Engine Map (Audit)

- audited_at_utc: `2026-02-21T02:20:00Z`
- template_status: `./_templates/plant` not found; using existing repo style.

## 1) Data Loader Contract

- file: `src/xauusd_bot/data_loader.py`
- required CSV columns: `timestamp, open, high, low, close`
- optional columns recognized: `volume, bid, ask, spread`
- behavior:
  - normalizes headers to lowercase
  - parses `timestamp` with `pd.to_datetime(errors="coerce")`
  - drops invalid timestamps and OHLC NaNs
  - sorts ascending by `timestamp`

## 2) Strategy Routing in Engine

- file: `src/xauusd_bot/configuration.py`
  - `strategy_family` accepted values include `VTM_VOL_MR`
  - VTM params are under `vtm_vol_mr` block.
- file: `src/xauusd_bot/engine.py`
  - VTM selector flag: `self.enable_strategy_vtm = self.strategy_family == "VTM_VOL_MR"`
  - signal path: `_evaluate_vtm_entry_signal(...)`
  - execution timing: signal at bar `t` close, order scheduled and executed at `open[t+1]` (next-open).

## 3) VTM Signal/Exit Hooks (Current Integration)

- signal filters in `engine.py`:
  - entry/excluded windows (`vtm_entry_windows`, `vtm_excluded_windows`)
  - ATR/ATR-MA checks and optional `vol_filter_min`
  - optional SMA slope filter
  - `bar_range >= threshold_range * ATR`
  - close-at-extreme filter via `close_extreme_frac`
  - spread filter (uses `row["spread"]` if present, else config spread proxy)
- order payload:
  - `sl_dist = stop_atr * atr_t`
  - TP anchor = SMA (`tp_mid = sma_t`)
- exits in `engine.py`:
  - `VTM_EXIT_SL`
  - `VTM_EXIT_MEAN_REVERT` (touch/cross SMA)
  - `VTM_EXIT_TIME_STOP` (holding bars)
  - optional break-even move event `VTM_BE_MOVE`.

## 4) Run Artifacts and Metadata

- run wrapper: `scripts/run_and_tag.py`
  - always writes `outputs/runs/<run_id>/run_meta.json`
  - includes `postprocess_ok`, `postprocess_error`, `process_returncode`
  - copies `config_used.yaml`.
- tolerant CSV ingestion for diagnostics/report:
  - file: `src/xauusd_bot/csv_utils.py`
  - fallback read mode: `engine="python"`, `on_bad_lines="skip"`, `encoding_errors="replace"`.

## 5) KPI and Expectancy Path

- per-trade R column in runs: `r_multiple` (from engine/logger).
- KPI source:
  - `src/xauusd_bot/reporting.py`
  - `expectancy_R = mean(r_multiple)`
  - `profit_factor` from PnL gross win / gross loss.
- bootstrap CI source:
  - `scripts/bootstrap_expectancy.py`
  - writes `outputs/runs/<run_id>/diagnostics/BOOT_expectancy_ci.csv`.

## 6) Queue Runner

- file: `scripts/run_vtm_candidates.py`
- inputs:
  - `--data`, `--candidates-dir`, `--out-dir`, `--runs-root`, `--resamples`, `--seed`, `--max-bars`
- outputs:
  - `vtm_candidates_scoreboard.csv|.md|_summary.json`
  - `run.log`
  - snapshot copy under `docs/_snapshots/<prefix>_<timestamp>/`.
