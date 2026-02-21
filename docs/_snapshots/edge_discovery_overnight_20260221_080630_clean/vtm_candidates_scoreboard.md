# VTM Candidates DEV Scoreboard

- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/tmp_vtm/vtm_input_20260221_062745.csv`
- baseline_config: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/configs/config_v3_PIVOT_B4.yaml`
- baseline_run_id: `20260221_073415`
- baseline_trades: `6`
- pass_count(gate_all): `0`

## Candidate results
| candidate | run_id | status | pf | expectancy_R | trades | crosses_zero | gate_exp_gt_0 | gate_ci_not_cross_zero | gate_trades_ge_100 | gate_all | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| config_edge_vtm_reversal_fast_v1 | 20260221_075421 | ok | 1.321147 | 0.18281 | 2 | True | True | False | False | False |  |
| config_edge_v4_orb_wide_v1 | 20260221_063806 | ok | 0.633867 | -0.09459 | 140 | False | False | True | True | False |  |
| config_edge_vtm_mr_balanced_v1 | 20260221_064929 | ok | 0.647797 | -0.126333 | 4 | True | False | False | False | False |  |
| config_edge_v3_trend_lite_v1 | 20260221_074352 | ok | 0.785859 | -0.160052 | 127 | True | False | False | True | False |  |
| config_edge_vtm_mr_strict_v1 | 20260221_070041 | ok |  |  | 0 | False | False | True | False | False |  |

## Artifacts
- csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard.csv`
- json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard_summary.json`

## Notes
- scoreboard rebuilt from run_meta/trades/boot artifacts
