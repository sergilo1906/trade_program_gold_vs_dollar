# B4 DEV Health (2021-2023)

- source_run_id: `20260219_235935`
- source_summary: `outputs/b4_dev_health/b4_dev_health_summary.json`
- source_monthly: `outputs/b4_dev_health/b4_dev_health_monthly.csv`
- source_bootstrap: `outputs/runs/20260219_235935/diagnostics/BOOT_expectancy_ci.csv`

## Snapshot Metrics
- trades: `26`
- winrate: `0.50`
- expectancy_R: `0.111834`
- PF: `1.251668`
- median_R: `-0.04472`
- max_drawdown_R (approx, cumulative R): `4.16978`
- bootstrap CI for expectancy_R: `[-0.321373, 0.563077]` (crosses 0 = `True`)

## Reading
- Point estimate is positive (`PF > 1`, `expectancy_R > 0`), but statistical confidence is weak (CI crosses 0).
- Sample size is low (`26` trades over 2021-2023), so estimate variance is high.
- Monthly profile is unstable (many months with 1-2 trades and alternating sign).
- Hourly concentration exists: hour `8` has most trades and negative expectancy in this sample.
- Cost drag is meaningful (`cost_R_mean ~ 0.1428`), so net edge is materially lower than gross-mid.

## Final
- decision: **NO-GO** (baseline)

- rationale:
- Bootstrap CI crosses zero, so edge is not statistically confirmed.
- Trade count is too small for a 3-year DEV conclusion.
- Median trade R is negative despite positive mean, indicating heavy dependence on few winners.
- Performance concentration by hour increases fragility risk.
- Net edge is sensitive to execution costs.

- next step binario:
- If GO: run one focused follow-up (`rolling 4-window + posthoc +20/+50`) with explicit gates `PF>1`, `expectancy_R>0`, `CI non-crossing`.
- If NO-GO: execute one minimum confirmation experiment before architecture changes:
  1) verify timezone alignment and hour mapping on `trades.csv` (`entry_time` vs expected UTC session),
  2) verify R sign/cost accounting on a 20-trade audit (`entry_mid/exit_mid/fills/pnl/r_multiple`),
  3) rerun bootstrap on a larger trade sample (extend DEV or aggregate equivalent OOS windows) to target `n >= 100` trades.
