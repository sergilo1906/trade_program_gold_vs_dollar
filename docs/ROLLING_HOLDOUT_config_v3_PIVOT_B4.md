# Rolling HOLDOUT (OOS) - Winner Config

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/xauusd_m5_backtest_ready.csv`
- config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B4.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_164110 | ok | 1.117274 | 0.075254 | 37 | 0.405405 | -0.386944 | 0.540192 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_164425 | ok | 1.640242 | 0.354581 | 34 | 0.5 | -0.143471 | 0.867959 | True |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_164706 | ok | 1.237996 | 0.14608 | 47 | 0.425532 | -0.274631 | 0.564744 | True |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_165006 | ok | 1.103654 | 0.066868 | 42 | 0.380952 | -0.361346 | 0.510624 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `4`
- windows with PF > 1: `4`
- windows with bootstrap CI crossing 0: `4`

## Artifacts
- runs_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B4/rolling_holdout_runs.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B4/rolling_holdout_summary.json`
- run_ids_ok: `20260219_164110`, `20260219_164425`, `20260219_164706`, `20260219_165006`
