# RANGE Edge Validation

## Input
- run_dir: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/runs/20260219_165006`
- trades: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/runs/20260219_165006/trades.csv`
- R column: `r_multiple`
- resamples: `5000`
- seed: `42`

## Bootstrap CI (Expectancy_R)
| run_id | r_col | n | seed | resamples | mean | ci_low | ci_high | crosses_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20260219_165006 | r_multiple | 42 | 42 | 5000 | 0.066868 | -0.361346 | 0.510624 | True |

## Decision
- CI cruza 0: `YES`

## Trades por mes
| month | trades |
| --- | --- |
| 2025-11 | 7 |
| 2025-12 | 17 |
| 2026-01 | 16 |
| 2026-02 | 2 |

- output_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/runs/20260219_165006/diagnostics/BOOT_expectancy_ci.csv`
