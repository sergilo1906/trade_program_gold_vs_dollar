# VTM Candidates DEV Scoreboard

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data_local/xauusd_m5_DEV_2021_2023.csv`
- baseline_config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B4.yaml`
- baseline_run_id: `20260220_215313`
- baseline_trades: `26`
- pass_count(gate_all): `0`

## Candidate results
| candidate | run_id | status | pf | expectancy_R | trades | crosses_zero | gate_exp_gt_0 | gate_ci_not_cross_zero | gate_trades_ge_100 | gate_all | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vtm_edge2_slow_atr | 20260221_004727 | ok | 0.625629 | -0.208539 | 358 | False | False | True | True | False |  |
| vtm_edge3_slope01_strict | 20260221_012253 | ok | 0.506162 | -0.297521 | 270 | False | False | True | True | False |  |
| vtm_edge1_stop12 | 20260220_204728 | ok | 0.407802 | -0.348327 | 1312 | False | False | True | True | False |  |
| vtm_edge1_thr22 | 20260221_014104 | ok | 0.446957 | -0.381316 | 878 | False | False | True | True | False |  |
| vtm_edge1_thr26 | 20260221_001050 | ok | 0.457272 | -0.399648 | 264 | False | False | True | True | False |  |
| vtm_edge1_hold8 | 20260220_201258 | ok | 0.400827 | -0.42266 | 1312 | False | False | True | True | False |  |
| vtm_edge1_baseline | 20260220_193807 | ok | 0.394626 | -0.42325 | 1312 | False | False | True | True | False |  |
| vtm_edge1_hold4 | 20260220_195535 | ok | 0.372054 | -0.432635 | 1313 | False | False | True | True | False |  |
| vtm_edge1_thr18 | 20260220_210512 | ok | 0.362699 | -0.445799 | 1804 | False | False | True | True | False |  |
| vtm_edge3_slope01 | 20260221_010511 | ok | 0.322651 | -0.507012 | 1009 | False | False | True | True | False |  |
| vtm_edge1_stop08 | 20260220_203005 | ok | 0.37687 | -0.537088 | 1317 | False | False | True | True | False |  |
| vtm_edge2_fast_atr | 20260221_002842 | ok | 0.339462 | -0.555956 | 1866 | False | False | True | True | False |  |

## Artifacts
- csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/vtm_dev_runs/vtm_candidates_scoreboard.csv`
- json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/vtm_dev_runs/vtm_candidates_scoreboard_summary.json`

## Notes
- scoreboard rebuilt from run_meta/trades/boot artifacts
