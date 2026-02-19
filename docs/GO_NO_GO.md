# GO / NO-GO

- decision:
  - legacy base (`config_v3_AUTO_EXP_B`): **NO-GO**
  - pivot base (`config_v3_PIVOT_B4`): **GO**

## Metrics
- HOLDOUT run_id: `20260219_104745`
- HOLDOUT expectancy_R: `0.013004`
- HOLDOUT PF: `1.019508`
- HOLDOUT trades: `44`
- HOLDOUT winrate: `0.363636`
- HOLDOUT bootstrap CI: [`-0.402205`, `0.438432`]

- Post-hoc +20% expectancy_R: `-0.004203`
- Post-hoc +20% PF: `0.993797`
- Post-hoc +20% bootstrap CI: [`-0.419012`, `0.421265`]

- Post-hoc +50% expectancy_R: `-0.030013`
- Post-hoc +50% PF: `0.956739`
- Post-hoc +50% bootstrap CI: [`-0.444637`, `0.394854`]

## Post-hoc cost stress (trade-set fixed)
- Source: `outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
- Metodo: mismo set de trades del HOLDOUT base, solo se escala coste post-hoc (sin re-simular ni alterar gating).
- Resultado: con +20% costes el sistema cae por debajo de PF=1 y expectancy_R <= 0.

## Legacy cost stress (trade set may differ)
- +20% costs run_id: `20260219_105305`
- +20% expectancy_R: `0.066337`
- +20% PF: `1.101903`
- +20% bootstrap CI: [`-0.347144`, `0.49096`]
- +50% costs run_id: `20260219_105707`
- +50% expectancy_R: `0.035853`
- +50% PF: `1.053998`
- +50% bootstrap CI: [`-0.393653`, `0.475998`]

## Hour Concentration
- top hour share on HOLDOUT: `50%` (hour `13`)
- negative hour >=10 trades: hour `13`, trades `22`, expectancy_R `-0.143829`

## Fase Decision - Rolling Post-hoc Robustness
- source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`

| factor | windows with PF>1 | windows with expectancy_R>0 | windows with both |
| --- | --- | --- | --- |
| 1.2 (+20%) | 3/4 | 3/4 | 3/4 |
| 1.5 (+50%) | 3/4 | 3/4 | 3/4 |

- Window break point at both factors: `W4` (`run_id 20260219_142432`)
  - +20%: PF `0.993797`, expectancy_R `-0.004203`
  - +50%: PF `0.956739`, expectancy_R `-0.030013`

## Cost Sensitivity Attribution
- source: `docs/COST_SENSITIVITY_ATTRIBUTION.md`

Top clusters by delta_R_20 (most negative):
- `TREND/TREND/V3_EXIT_TP`: trades `15`, delta_R_20 `-0.017890`
- `TREND/TREND/V3_EXIT_SL`: trades `27`, delta_R_20 `-0.016983`
- `TREND/TREND/V3_EXIT_SESSION_END`: trades `2`, delta_R_20 `-0.015101`

Top hours by delta_R_20 (most negative):
- hour `8`: trades `5`, delta_R_20 `-0.020902`
- hour `13`: trades `22`, delta_R_20 `-0.019675`
- hour `14`: trades `9`, delta_R_20 `-0.015402`
- hour `15`: trades `8`, delta_R_20 `-0.010141`

Top 10 trades by delta_R_20:
- trade_id `8`, `21`, `15`, `17`, `22`, `34`, `32`, `28`, `13`, `27`

## Proposed Routes (no new entry/exit rules)
### Route A - Surgical cuts (minimal filters/gating)
- Restrict/trim highest fragility slots first: hour `13` and optionally hour `8`, preserving existing entry/exit logic.
- Tighten cost gating only in the fragile hours/clusters (`V3_EXIT_SL` and `V3_EXIT_TP` concentration), not globally.
- Keep trade-set diagnostics and re-run W4-centric holdout check to verify that +20% stays above `PF>1` and `expectancy_R>0`.

### Route B - Pivot a v3 (if A is insufficient)
- If Route A cannot make W4 pass (+20%) without large trade loss, stop patching and move to v3 baseline path.
- Reuse current evaluation framework (fixed trade-set post-hoc + rolling OOS) as acceptance gate for the pivot.

## Decision Update
- Legacy state (pre-pivot) remains **NO-GO** for production robustness.
- Reason (legacy): post-hoc cost stress fails in `W4` at +20% and +50%, and holdout base remains statistically weak (CI crosses zero).
- Conditional path: attempt Route A only if minimal gating can fix W4 without collapsing trade count; otherwise Route B.

## Route A Result (Surgical cuts)
- Config tested (initial): `configs/config_v3_ROUTE_A.yaml`
  - `trade_filter.hour_blacklist_utc: [13]`
  - `cost_gate_overrides_by_hour: {13: {max_cost_multiplier: 1.0}}`
- Extension tested (because initial did not reach objective): `configs/config_v3_ROUTE_A_H13_H8.yaml`
  - `trade_filter.hour_blacklist_utc: [8, 13]`
  - `cost_gate_overrides_by_hour: {8: {max_cost_multiplier: 1.0}, 13: {max_cost_multiplier: 1.0}}`

### Rolling Route A (initial h13) + post-hoc fixed trade-set
- rolling runs: `20260219_152419`, `20260219_152817`, `20260219_153128`, `20260219_153455`
- source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA.csv`
- windows passing PF>1 and expectancy_R>0:
  - +20%: `3/4`
  - +50%: `3/4`
- W4 (`20260219_153455`) at +20%: PF `0.589845`, expectancy_R `-0.314530` -> **FAIL**
- W4 trades retained vs base W4 (44 trades): `38/44 = 86.36%`

### Rolling Route A extension (h13+h8) + post-hoc fixed trade-set
- rolling runs: `20260219_154058`, `20260219_154459`, `20260219_154802`, `20260219_155141`
- source: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA_h13_h8.csv`
- windows passing PF>1 and expectancy_R>0:
  - +20%: `3/4`
  - +50%: `3/4`
- W4 (`20260219_155141`) at +20%: PF `0.521906`, expectancy_R `-0.385963` -> **FAIL**
- W4 trades retained vs base W4 (44 trades): `32/44 = 72.73%`

### Route A conclusion
- Route A does **not** solve the W4 robustness break under +20% cost stress.
- Trade count does not collapse (retention >= 60%), but edge remains negative in W4.
- Automatic decision: **Pivot to Route B (cambiar estrategia base)**.

## Route B Result (Pivot)
- candidate set evaluated: `configs/config_v3_PIVOT_B1.yaml`, `configs/config_v3_PIVOT_B2.yaml`, `configs/config_v3_PIVOT_B3.yaml`, `configs/config_v3_PIVOT_B4.yaml`
- scoreboard source: `outputs/rolling_holdout_pivot/pivot_scoreboard.csv`
- decision source: `docs/PIVOT_SCOREBOARD.md`
- winner: `configs/config_v3_PIVOT_B4.yaml`
- rolling run_ids winner: `20260219_164110`, `20260219_164425`, `20260219_164706`, `20260219_165006`

### Robustness gates
- +20% post-hoc (trade-set fixed): `4/4` windows pass (`PF > 1` and `expectancy_R > 0`)
- +50% post-hoc (trade-set fixed): `4/4` windows pass
- W4 (`run_id 20260219_165006`) +20%: PF `1.076243`, expectancy_R `0.049967`, trades `42`
- W4 (`run_id 20260219_165006`) +50%: PF `1.036698`, expectancy_R `0.024615`, trades `42`

### Trade-loss control
- baseline total rolling trades (factor 1.0): `168`
- pivot B4 total rolling trades (factor 1.0): `160`
- global trade retention: `95.24%` (loss `4.76%`) -> no overfilter
- W4 retention vs baseline W4=44: `42/44 = 95.45%`
- note: `config_v3_PIVOT_B3` also passed robustness but was rejected for overfilter (`41.07%` retention, loss `58.93%`)

### Profitability approximation (OOS rolling aggregate, equity_start=10,000)
- monthly_equiv: `0.008434` (~`0.84%`/mes)
- annualized: `0.106041` (~`10.60%` anual)
- expectancy_R_oos_mean: `0.160696`
- trades_per_month_est: `11.78`
- interpretation: rendimiento más cercano a un perfil tipo `20%/año` que a `4%/mes` (y actualmente por debajo de 20%/año).

### Final Route B decision
- **GO** para continuar sobre `config_v3_PIVOT_B4.yaml` como nueva base.
