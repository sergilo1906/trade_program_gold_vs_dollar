# Post-hoc Cost Stress (Trade-set fixed)

Este stress es **post-hoc** con **mismo set de trades** del run base (sin re-simular).

- run_dir: `outputs/runs/20260219_104745`
- trades (fixed): `44`
- cost_model_formula: `gross_from_mid_minus_net`
- risk_source: `risk_amount`
- summary_csv: `outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
- per_trade_csv: `outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv`

## Stress Table
| scenario | factor | pf | expectancy_R | trades | winrate | ci_low | ci_high | crosses_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | 1 | 1.019508 | 0.013004 | 44 | 0.363636 | -0.402206 | 0.438432 | True |
| +20% COST | 1.2 | 0.993797 | -0.004203 | 44 | 0.363636 | -0.419012 | 0.421265 | True |
| +50% COST | 1.5 | 0.956739 | -0.030013 | 44 | 0.363636 | -0.444637 | 0.394854 | True |
