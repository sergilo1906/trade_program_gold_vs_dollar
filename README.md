# trade_program_gold_vs_dollar

XAUUSD M5 (OHLC-only) quantitative research and backtesting app with next-open execution, diagnostics, walk-forward evaluation, holdout validation, and cost-stress tooling.

The repo contains strategy configs, execution engine, reporting/QA scripts, and reproducible experiment commands.

- GitHub repository: `https://github.com/sergilo1906/trade_program_gold_vs_dollar`

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run one tagged backtest:

```powershell
python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_B.yaml --runs-root outputs/runs
python scripts/diagnose_run.py outputs/runs/<run_id>
python scripts/bootstrap_expectancy.py outputs/runs/<run_id> --resamples 5000 --seed 42
```

Run quick end-to-end smoke (single command, reproducible artifacts):

```powershell
python scripts/run_smoke.py --data data/sample_m5.csv --config configs/config_smoke_baseline.yaml --max-bars 1200 --resamples 500 --seed 42
```

Smoke artifacts:

- `outputs/runs/<run_id>/` with `trades.csv` + diagnostics.
- `outputs/smoke_runs/smoke_scoreboard.csv|.md|_summary.json`
- `docs/_snapshots/smoke_<timestamp>/...`
- `docs/SMOKE_DECISION.md`

Reproducibility cookbook:

- `docs/REPRO_RUNS.md`

## Repository Structure

- `src/xauusd_bot/`: strategy engine, configuration, reporting.
- `scripts/`: orchestration, QA, diagnostics, post-hoc stress, holdout/rolling tooling.
- `configs/`: strategy and experiment YAML configs.
- `docs/`: reports, logs, reproducibility notes, decisions.
- `data/`: input datasets and generated splits.
- `tests/`: test suite.

## Tracking and Publish Policy

- Heavy generated outputs are not versioned via git:
  - `outputs/`, `output/`, `output_bench/`, `output_opt_tmp/`, `output_test_tmp/`
- Temporary generated window files are not versioned:
  - `data/tmp_rolling/`, `data/tmp_wfa/`
- Local external datasets are not versioned:
  - `data_local/` (FULL/DEV local files for large-history validation)
- Main datasets under `data/` are versioned (except temp folders above).
- Long-history dataset integrated for robustness:
  - `data/xauusd_m5_2010_2023_backtest_ready.csv` (2010-01 to 2023-12, normalized OHLCV schema).
  - Current size is ~52 MB and is tracked directly (acceptable for now). If dataset grows, migrate this file to Git LFS.

## Templates ZIP Status

- Expected: `./_templates/plantillas_mejoradas.zip`
- Current status: **MISSING**
- Decision: not tracked because file is absent. If later added and size is large, use Git LFS or keep it ignored; document the final choice in this README and `docs/UNATTENDED_LOG.md`.

## Git Flow (Autopush)

For each new change:

1. `git pull origin main`
2. Run quick checks, for example:
   - `python -m py_compile src/xauusd_bot/configuration.py scripts/run_and_tag.py`
3. Run:
   - `powershell -ExecutionPolicy Bypass -File scripts/git_autopush.ps1`

The script commits and pushes changes, then updates `docs/LATEST_COMMIT.md` for quick repo/commit traceability.

## Push in 10 Seconds

```powershell
powershell -ExecutionPolicy Bypass -File scripts/git_autopush.ps1 -Message "feat: short description"
```

If `gh` is not authenticated yet:

```powershell
gh auth login
gh repo create trade_program_gold_vs_dollar --public --source=. --remote=origin --push
```
