# Pivot Scoreboard (Route B)

- generated_utc: `2026-02-19T16:54:43Z`
- baseline_ref: `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- baseline_W4_trades_ref: `44`

## Candidate Table
| candidate | windows_pass_1p2 | windows_pass_1p5 | w4_pf_1p2 | w4_exp_1p2 | w4_trades_1p0 | global_trade_retention_pct | overfilter_gt35pct | monthly_equiv | annualized | run_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| config_v3_PIVOT_B3 | 4 | 4 | 1.158063 | 0.098542 | 21 | 41.07 | True | 0.011369 | 0.145295 | 20260219_162948,20260219_163238,20260219_163509,20260219_163817 |
| config_v3_PIVOT_B4 | 4 | 4 | 1.076243 | 0.049967 | 42 | 95.24 | False | 0.008434 | 0.106041 | 20260219_164110,20260219_164425,20260219_164706,20260219_165006 |
| config_v3_PIVOT_B2 | 3 | 3 | 0.769322 | -0.173843 | 26 | 55.36 | True | 0.014282 | 0.185506 | 20260219_161907,20260219_162157,20260219_162422,20260219_162708 |
| config_v3_PIVOT_B1 | 1 | 1 | 0.963652 | -0.023738 | 39 | 80.36 | False | 0.000889 | 0.010720 | 20260219_160711,20260219_161020,20260219_161309,20260219_161610 |

## Acceptance Gates
- Gate +20% (must pass each window): PF>1 and expectancy_R>0 in W1..W4.
- Trade-loss control: if global trade loss >35% => probable overfilter.

## Winner Selection
- winner: `config_v3_PIVOT_B4`
- rationale: passes +20% in `4/4` windows, W4 passes, and trade retention `95.24%` (loss `4.76%`, overfilter flag `False`).
- windows_pass_1p5: `4/4`
- profitability approx: monthly_equiv `0.008434` (~0.84%), annualized `0.106041` (~10.60%).

### Winner W4 by cost factor
| factor | run_id | pf | expectancy_R | trades |
| --- | --- | --- | --- | --- |
| 1.0 | 20260219_165006 | 1.103654 | 0.066868 | 42 |
| 1.2 | 20260219_165006 | 1.076243 | 0.049967 | 42 |
| 1.5 | 20260219_165006 | 1.036698 | 0.024615 | 42 |

## Top 2 Candidates (performance-only rank)
- `config_v3_PIVOT_B3`: +20 `4/4`, +50 `4/4`, W4 +20 PF `1.158063`, W4 +20 exp_R `0.098542`, retention `41.07%`, overfilter `True`
- `config_v3_PIVOT_B4`: +20 `4/4`, +50 `4/4`, W4 +20 PF `1.076243`, W4 +20 exp_R `0.049967`, retention `95.24%`, overfilter `False`

## Artifacts
- scoreboard_csv: `outputs/rolling_holdout_pivot/pivot_scoreboard.csv`
- scoreboard_summary_json: `outputs/rolling_holdout_pivot/pivot_scoreboard_summary.json`
- config_v3_PIVOT_B3 rolling_runs: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B3/rolling_holdout_runs.csv`
- config_v3_PIVOT_B3 posthoc: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B3.csv`
- config_v3_PIVOT_B4 rolling_runs: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B4/rolling_holdout_runs.csv`
- config_v3_PIVOT_B4 posthoc: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B4.csv`
- config_v3_PIVOT_B2 rolling_runs: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B2/rolling_holdout_runs.csv`
- config_v3_PIVOT_B2 posthoc: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B2.csv`
- config_v3_PIVOT_B1 rolling_runs: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/rolling_holdout_pivot/config_v3_PIVOT_B1/rolling_holdout_runs.csv`
- config_v3_PIVOT_B1 posthoc: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B1.csv`