# HOLDOUT Split (80/20, Time-Ordered)

- Input: `data/xauusd_m5_backtest_ready.csv`
- Split rule: `cut = floor(0.8 * n_rows)` after sort by `timestamp` ascending
- n_rows: `100000`
- cut index: `80000`
- DEV output: `data/xauusd_m5_DEV80.csv`
- HOLDOUT output: `data/xauusd_m5_HOLDOUT20.csv`

## Date Ranges

| dataset | rows | start_ts | end_ts |
| --- | --- | --- | --- |
| FULL | 100000 | 2024-09-17 14:00:00 | 2026-02-16 19:25:00 |
| DEV80 | 80000 | 2024-09-17 14:00:00 | 2025-11-03 20:50:00 |
| HOLDOUT20 | 20000 | 2025-11-03 20:55:00 | 2026-02-16 19:25:00 |
