# Rolling HOLDOUT (OOS) - Winner Config

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/xauusd_m5_backtest_ready.csv`
- config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B2.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_161907 | ok | 1.49796 | 0.280341 | 26 | 0.5 | -0.263406 | 0.846742 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_162157 | ok | 3.417356 | 0.891478 | 18 | 0.666667 | 0.223852 | 1.54832 | False |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_162422 | ok | 3.831313 | 0.946917 | 23 | 0.695652 | 0.381074 | 1.480308 | False |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_162708 | ok | 0.787881 | -0.157689 | 26 | 0.307692 | -0.624364 | 0.410946 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `3`
- windows with PF > 1: `3`
- windows with bootstrap CI crossing 0: `2`

## Artifacts
- runs_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B2/rolling_holdout_runs.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B2/rolling_holdout_summary.json`
- run_ids_ok: `20260219_161907`, `20260219_162157`, `20260219_162422`, `20260219_162708`
