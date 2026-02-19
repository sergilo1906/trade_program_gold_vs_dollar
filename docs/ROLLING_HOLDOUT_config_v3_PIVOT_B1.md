# Rolling HOLDOUT (OOS) - Winner Config

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/xauusd_m5_backtest_ready.csv`
- config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B1.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_160711 | ok | 0.855237 | -0.096152 | 34 | 0.382353 | -0.525019 | 0.352805 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_161020 | ok | 1.35402 | 0.216629 | 29 | 0.448276 | -0.306376 | 0.736476 | True |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_161309 | ok | 1.007322 | 0.005026 | 33 | 0.363636 | -0.468835 | 0.517948 | True |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_161610 | ok | 0.991349 | -0.005556 | 39 | 0.384615 | -0.419336 | 0.43935 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `2`
- windows with PF > 1: `2`
- windows with bootstrap CI crossing 0: `4`

## Artifacts
- runs_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B1/rolling_holdout_runs.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B1/rolling_holdout_summary.json`
- run_ids_ok: `20260219_160711`, `20260219_161020`, `20260219_161309`, `20260219_161610`
