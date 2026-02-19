# trade_program_gold_vs_dollar

XAUUSD M5 (OHLC-only) quantitative research and backtesting app with next-open execution, diagnostics, walk-forward evaluation, holdout validation, and cost-stress tooling.

The repo contains strategy configs, execution engine, reporting/QA scripts, and reproducible experiment commands.

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
- Main datasets under `data/` are versioned (except temp folders above).

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
