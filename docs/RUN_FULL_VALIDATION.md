# Run Full Validation (B4)

Objective: run the existing pipeline on FULL history with winner `config_v3_PIVOT_B4.yaml`, without changing strategy logic.

## Inputs
- FULL dataset path: `data_local/xauusd_m5_2010_2023.csv`
- Winner config: `configs/config_v3_PIVOT_B4.yaml`

## 1) Rolling OOS on FULL (4 windows)

```powershell
python scripts/rolling_holdout_eval.py --data data_local/xauusd_m5_2010_2023.csv --config configs/config_v3_PIVOT_B4.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_full_b4 --resamples 5000 --seed 42 --report docs/ROLLING_HOLDOUT_FULL_B4.md
```

Output artifacts:
- `outputs/rolling_holdout_full_b4/rolling_holdout_runs.csv`
- `outputs/rolling_holdout_full_b4/rolling_holdout_summary.json`
- `docs/ROLLING_HOLDOUT_FULL_B4.md`

## 2) Post-hoc cost stress on rolling run_ids (+20/+50)

```powershell
$runs = Import-Csv outputs/rolling_holdout_full_b4/rolling_holdout_runs.csv | Where-Object { $_.status -eq 'ok' } | Select-Object -ExpandProperty run_id
python scripts/posthoc_cost_stress_batch.py --runs $runs --window-map-csv outputs/rolling_holdout_full_b4/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_full_b4.csv
```

Expected output:
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_full_b4.csv`

## Optional: Smoke Test Only (fast)

```powershell
python scripts/smoke_test_b4_dev.py --data data_local/xauusd_m5_DEV_2021_2023.csv --config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/smoke_dev_b4
```

## Red Flags Checklist
- Timezone mismatch or timestamp parsing anomalies (unexpected min/max date).
- `SUMMARY: FAIL` in `scripts/data/validate_m5_integrity.py`.
- `trades = 0` in one or more rolling windows.
- Dominant delta not equal to 5 minutes.
- Excessive large gaps (>60m) outside known market closures.
- Bootstrap fallback to 2000 repeatedly due resource pressure.
