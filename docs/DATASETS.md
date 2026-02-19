# Datasets

## Definitions
- `FULL`: historical long-range CSV used for robustness validation.
- `DEV`: reduced slice extracted from FULL for fast iteration/smoke checks.

## Recommended Paths
- FULL: `data_local/xauusd_m5_2010_2023.csv`
- DEV: `data_local/xauusd_m5_DEV_2021_2023.csv`

`data_local/` is intentionally out of git tracking (see `.gitignore`).

## Required CSV Shape
- Minimum columns: `timestamp, open, high, low, close`
- Optional columns are allowed (for example `volume`).
- Timeframe target is M5 (dominant delta 5 minutes).

## Data Scripts

1. Validate FULL integrity:
```powershell
python scripts/data/validate_m5_integrity.py --input data_local/xauusd_m5_2010_2023.csv --expected_tf_minutes 5 --max_report_rows 20
```

2. Build DEV from FULL (from 2021):
```powershell
python scripts/data/make_dev_from_full.py --input data_local/xauusd_m5_2010_2023.csv --output data_local/xauusd_m5_DEV_2021_2023.csv --start "2021-01-01"
```

3. Validate DEV integrity:
```powershell
python scripts/data/validate_m5_integrity.py --input data_local/xauusd_m5_DEV_2021_2023.csv --expected_tf_minutes 5 --max_report_rows 20
```

## Passing `--data` to Existing Runners

Run one tagged backtest:
```powershell
python scripts/run_and_tag.py --data data_local/xauusd_m5_DEV_2021_2023.csv --config configs/config_v3_PIVOT_B4.yaml --runs-root outputs/runs
```

Rolling OOS evaluation:
```powershell
python scripts/rolling_holdout_eval.py --data data_local/xauusd_m5_2010_2023.csv --config configs/config_v3_PIVOT_B4.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_full_b4 --resamples 5000 --seed 42 --report docs/ROLLING_HOLDOUT_FULL_B4.md
```
