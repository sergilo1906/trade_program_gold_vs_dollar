# XAUUSD backtesting

A Python research tool for testing trading strategies on five-minute gold/USD historical candles. It simulates next-open execution using OHLC data and produces trade logs and diagnostics for offline analysis.

The focus is reproducibility: YAML experiment settings, fixed random seeds, walk-forward evaluation, holdout data and transaction-cost stress tests. It is a backtesting project, not a live trading system or evidence of profitable future performance.

## Run a small experiment

Python 3.11 or newer. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/run_smoke.py --data data/sample_m5.csv --config configs/config_smoke_baseline.yaml --max-bars 1200 --resamples 500 --seed 42
```

The smoke run generates trade and diagnostic files under `outputs/`. Run `python -m pytest` to execute the test suite.

The research engine is in `src/xauusd_bot/`, settings in `configs/`, and experiment runners and analysis utilities in `scripts/`. For full experiments and the holdout procedure, see [reproduction notes](docs/REPRO_RUNS.md).

Historical candle data has limitations: it cannot establish the exact sequence of intrabar prices or reproduce every live execution condition. Larger datasets are included in the repository; check their source and redistribution rights before reuse. Generated outputs and local external datasets are excluded from version control.
