# Walk-Forward Results (DEV80 only)

- generated_utc: 2026-02-19T11:08:01Z
- data_source: `data/xauusd_m5_DEV80.csv`
- folds: Fold1 0-40/40-50, Fold2 0-50/50-60, Fold3 0-60/60-70, Fold4 0-70/70-80.
- winner_fold criteria (TRAIN): expectancy_R, tie PF, tie trades.
- winner_global criteria (VAL OOS): median expectancy_R, tie mean expectancy_R, tie mean PF.

## Fold winner selection on TRAIN
| fold | winner_config_label | winner_config_path | train_run_id | expectancy_R | pf | trades |
| --- | --- | --- | --- | --- | --- | --- |
| Fold1 | EXP_A | configs/config_v3_AUTO_EXP_A.yaml | 20260219_083710 | 0.235114 | 1.394264 | 51 |
| Fold2 | EXP_C | configs/config_v3_AUTO_EXP_C.yaml | 20260219_103558 | 0.188953 | 1.314289 | 76 |
| Fold3 | EXP_B | configs/config_v3_AUTO_EXP_B.yaml | 20260219_091433 | 0.127412 | 1.201137 | 91 |
| Fold4 | EXP_B | configs/config_v3_AUTO_EXP_B.yaml | 20260219_094915 | 0.162816 | 1.261161 | 105 |

## Winner performance on VAL (OOS)
| fold | winner_config_label | winner_config_path | val_run_id | expectancy_R | pf | winrate | trades | boot_ci_low | boot_ci_high | boot_crosses_zero | boot_resamples_used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fold1 | EXP_A | configs/config_v3_AUTO_EXP_A.yaml | 20260219_085634 | -0.530351 | 0.376473 | 0.230769 | 13 | -1.100071 | 0.152195 | True | 5000 |
| Fold2 | EXP_C | configs/config_v3_AUTO_EXP_C.yaml | 20260219_104443 | 0.142805 | 1.258465 | 0.4 | 15 | -0.522802 | 0.84259 | True | 5000 |
| Fold3 | EXP_B | configs/config_v3_AUTO_EXP_B.yaml | 20260219_093546 | 0.092136 | 1.137581 | 0.4 | 10 | -0.814041 | 1.003303 | True | 5000 |
| Fold4 | EXP_B | configs/config_v3_AUTO_EXP_B.yaml | 20260219_101410 | 0.325404 | 1.664885 | 0.4375 | 16 | -0.330968 | 1.024599 | True | 5000 |

## Aggregated by config (VAL OOS only)
| config_label | config_path | folds_won | expectancy_R_mean | expectancy_R_median | pf_mean | trades_total | trades_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP_B | configs/config_v3_AUTO_EXP_B.yaml | 2 | 0.20877 | 0.20877 | 1.401233 | 26 | 13.0 |
| EXP_C | configs/config_v3_AUTO_EXP_C.yaml | 1 | 0.142805 | 0.142805 | 1.258465 | 15 | 15.0 |
| EXP_A | configs/config_v3_AUTO_EXP_A.yaml | 1 | -0.530351 | -0.530351 | 0.376473 | 13 | 13.0 |

## WINNER_GLOBAL (VAL OOS only)
- WINNER_GLOBAL: `EXP_B` (`configs/config_v3_AUTO_EXP_B.yaml`)
- median_expectancy_R=0.208770, mean_expectancy_R=0.208770, mean_PF=1.401233

## Run map
- train runs csv: `outputs/wfa/wfa_train_runs.csv`
- val runs csv: `outputs/wfa/wfa_val_runs.csv`
- summary json: `outputs/wfa/wfa_summary.json`
- note: Fold2 was re-run after transient disk-space exhaustion.
