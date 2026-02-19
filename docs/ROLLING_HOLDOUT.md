# Rolling HOLDOUT (OOS) - Winner Config

- data: `data/xauusd_m5_backtest_ready.csv`
- config: `configs/config_v3_ROUTE_A.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_152419 | ok | 1.157903 | 0.093985 | 28 | 0.428571 | -0.403426 | 0.612154 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_152817 | ok | 1.854436 | 0.412608 | 23 | 0.521739 | -0.172399 | 1.010691 | True |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_153128 | ok | 1.614413 | 0.316177 | 39 | 0.487179 | -0.136772 | 0.765554 | True |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_153455 | ok | 0.602889 | -0.300696 | 38 | 0.263158 | -0.672834 | 0.128378 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `3`
- windows with PF > 1: `3`
- windows with bootstrap CI crossing 0: `4`

## Artifacts
- runs_csv: `outputs/rolling_holdout_routeA/rolling_holdout_runs.csv`
- summary_json: `outputs/rolling_holdout_routeA/rolling_holdout_summary.json`
- run_ids_ok: `20260219_152419`, `20260219_152817`, `20260219_153128`, `20260219_153455`
