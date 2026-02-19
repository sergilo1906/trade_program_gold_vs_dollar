# Rolling HOLDOUT (OOS) - Winner Config

- data: `data/xauusd_m5_backtest_ready.csv`
- config: `configs/config_v3_ROUTE_A_H13_H8.yaml`
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`

## Results by window
| window | start_pct | end_pct | rows | start_ts | end_ts | run_id | status | pf | expectancy_R | trades | winrate | boot_ci_low | boot_ci_high | boot_crosses_zero | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0.2 | 0.4 | 20000 | 2024-12-30 11:45:00 | 2025-04-11 09:45:00 | 20260219_154058 | ok | 1.215113 | 0.123646 | 25 | 0.44 | -0.402973 | 0.677907 | True |  |
| W2 | 0.4 | 0.6 | 20000 | 2025-04-11 09:50:00 | 2025-07-24 06:35:00 | 20260219_154459 | ok | 1.875011 | 0.41613 | 21 | 0.52381 | -0.190724 | 1.015297 | True |  |
| W3 | 0.6 | 0.8 | 20000 | 2025-07-24 06:40:00 | 2025-11-03 20:50:00 | 20260219_154802 | ok | 1.106652 | 0.063107 | 32 | 0.40625 | -0.401209 | 0.53129 | True |  |
| W4 | 0.8 | 1 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 | 20260219_155141 | ok | 0.532465 | -0.372974 | 32 | 0.25 | -0.782401 | 0.060051 | True |  |

## Stability summary
- windows_ok: `4/4`
- windows with expectancy_R > 0: `3`
- windows with PF > 1: `3`
- windows with bootstrap CI crossing 0: `4`

## Artifacts
- runs_csv: `outputs/rolling_holdout_routeA_h13_h8/rolling_holdout_runs.csv`
- summary_json: `outputs/rolling_holdout_routeA_h13_h8/rolling_holdout_summary.json`
- run_ids_ok: `20260219_154058`, `20260219_154459`, `20260219_154802`, `20260219_155141`
