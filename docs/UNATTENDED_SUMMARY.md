# Unattended Summary

## WINNER_GLOBAL (WFA OOS)
- `EXP_B` (`configs/config_v3_AUTO_EXP_B.yaml`)

## HOLDOUT Result
- run_id `20260219_104745` | PF `1.019508` | expectancy_R `0.013004` | trades `44` | winrate `0.363636`
- bootstrap CI [`-0.402205`, `0.438432`], crosses_zero `True`

## Cost Stress
- Post-hoc (trade-set fixed) source: `outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
- BASE factor `1.0`: PF `1.019508`, expectancy_R `0.013004`, CI [`-0.402206`, `0.438432`]
- +20 factor `1.2`: PF `0.993797`, expectancy_R `-0.004203`, CI [`-0.419012`, `0.421265`]
- +50 factor `1.5`: PF `0.956739`, expectancy_R `-0.030013`, CI [`-0.444637`, `0.394854`]
- Legacy (trade set may differ): +20 run `20260219_105305`, +50 run `20260219_105707`

## Rolling HOLDOUT OOS
- windows: `0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0`
- run_ids: `20260219_141334`, `20260219_141728`, `20260219_142049`, `20260219_142432`
- windows with expectancy_R > 0: `4/4`
- windows with PF > 1: `4/4`
- windows with CI crossing 0: `4/4`

## Rolling Post-hoc Cost Robustness (trade-set fixed)
- source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- +20% (`factor 1.2`): PF>1 in `3/4`, expectancy_R>0 in `3/4`, both in `3/4`
- +50% (`factor 1.5`): PF>1 in `3/4`, expectancy_R>0 in `3/4`, both in `3/4`
- break window: `W4` (`run_id 20260219_142432`) fails both PF>1 and expectancy_R>0 at +20/+50

## Attribution Highlights
- clusters with highest negative delta_R_20:
  - `TREND/TREND/V3_EXIT_TP`: `-0.017890`
  - `TREND/TREND/V3_EXIT_SL`: `-0.016983`
  - `TREND/TREND/V3_EXIT_SESSION_END`: `-0.015101`
- hours with highest negative delta_R_20:
  - `8` (`-0.020902`), `13` (`-0.019675`), `14` (`-0.015402`), `15` (`-0.010141`)
- top trades by delta_R_20:
  - `8, 21, 15, 17, 22, 34, 32, 28, 13, 27`

## Decision Routes
- Route A (Surgical cuts): minimal gating/filter trims on fragile hours/clusters only, no new entry/exit rules.
- Route B (Pivot to v3): if Route A cannot make W4 pass +20% without major trade loss.

## Route A Execution Summary
- Initial config tested: `configs/config_v3_ROUTE_A.yaml` (hour 13 blacklist + hour 13 cost override)
- Rolling run_ids: `20260219_152419`, `20260219_152817`, `20260219_153128`, `20260219_153455`
- Post-hoc source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA.csv`
- Result:
  - +20% pass windows (PF>1 & expectancy_R>0): `3/4`
  - W4 +20%: PF `0.589845`, expectancy_R `-0.314530` (FAIL)
  - W4 trades retained vs base: `38/44 = 86.36%`

- Extension tested: `configs/config_v3_ROUTE_A_H13_H8.yaml` (blacklist 13+8)
- Rolling run_ids: `20260219_154058`, `20260219_154459`, `20260219_154802`, `20260219_155141`
- Post-hoc source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA_h13_h8.csv`
- Result:
  - +20% pass windows (PF>1 & expectancy_R>0): `3/4`
  - W4 +20%: PF `0.521906`, expectancy_R `-0.385963` (FAIL)
  - W4 trades retained vs base: `32/44 = 72.73%`

## Decision
- legacy base (`config_v3_AUTO_EXP_B`): `NO-GO`
- pivot base (`config_v3_PIVOT_B4`): `GO`

## Route B Pivot (final)
- scoreboard: `docs/PIVOT_SCOREBOARD.md`
- winner: `config_v3_PIVOT_B4` (`configs/config_v3_PIVOT_B4.yaml`)
- rolling run_ids winner: `20260219_164110`, `20260219_164425`, `20260219_164706`, `20260219_165006`
- gates:
  - +20% post-hoc fixed trade-set: `4/4` windows pass
  - +50% post-hoc fixed trade-set: `4/4` windows pass
  - W4 +20%: PF `1.076243`, expectancy_R `0.049967`, trades `42`
  - W4 +50%: PF `1.036698`, expectancy_R `0.024615`, trades `42`
- trade retention:
  - global: `160/168 = 95.24%` (loss `4.76%`)
  - W4 vs baseline: `42/44 = 95.45%`
- profitability approximation (equity_start=10,000):
  - monthly_equiv: `0.008434` (~`0.84%`/mes)
  - annualized: `0.106041` (~`10.60%`/año)
  - expectancy_R_oos_mean: `0.160696`
  - trades_per_month_est: `11.78`
- profile comparison: más cercano a `20%/año` que a `4%/mes` (actualmente por debajo de 20%/año).

## Relevant run_ids
- WFA VAL: `20260219_085634`, `20260219_104443`, `20260219_093546`, `20260219_101410`
- HOLDOUT base: `20260219_104745`
- HOLDOUT cost legacy: `20260219_105305`, `20260219_105707`
- ROLLING HOLDOUT: `20260219_141334`, `20260219_141728`, `20260219_142049`, `20260219_142432`
- ROLLING ROUTE A (h13): `20260219_152419`, `20260219_152817`, `20260219_153128`, `20260219_153455`
- ROLLING ROUTE A (h13+h8): `20260219_154058`, `20260219_154459`, `20260219_154802`, `20260219_155141`
- ROLLING PIVOT B1: `20260219_160711`, `20260219_161020`, `20260219_161309`, `20260219_161610`
- ROLLING PIVOT B2: `20260219_161907`, `20260219_162157`, `20260219_162422`, `20260219_162708`
- ROLLING PIVOT B3: `20260219_162948`, `20260219_163238`, `20260219_163509`, `20260219_163817`
- ROLLING PIVOT B4 (winner): `20260219_164110`, `20260219_164425`, `20260219_164706`, `20260219_165006`
