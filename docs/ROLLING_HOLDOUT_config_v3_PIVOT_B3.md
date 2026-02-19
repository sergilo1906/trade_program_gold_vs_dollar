# Rolling HOLDOUT (OOS) - Winner Config

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/xauusd_m5_backtest_ready.csv`
- config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B3.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_162948 | ok | 1.266829 | 0.158832 | 19 | 0.473684 | -0.467432 | 0.788832 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_163238 | ok | 3.404276 | 0.88834 | 15 | 0.666667 | 0.096457 | 1.496109 | False |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_163509 | ok | 4.131112 | 0.992437 | 14 | 0.714286 | 0.267322 | 1.652699 | False |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_163817 | ok | 1.186585 | 0.114706 | 21 | 0.428571 | -0.472118 | 0.737577 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `4`
- windows with PF > 1: `4`
- windows with bootstrap CI crossing 0: `2`

## Artifacts
- runs_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B3/rolling_holdout_runs.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B3/rolling_holdout_summary.json`
- run_ids_ok: `20260219_162948`, `20260219_163238`, `20260219_163509`, `20260219_163817`
