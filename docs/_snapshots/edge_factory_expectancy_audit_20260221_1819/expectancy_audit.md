# V4A Expectancy Audit (DEV 2021-2023)

- scoreboard_used: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_smoke/edge_factory_scoreboard.csv`
- rows_audited: `9`
- PIPELINE_BUG_SUSPECTED: **NO**
- tolerances: `expectancy=1e-06`, `pf=1e-06`, `winrate=1e-06`, `trades=exact`

## Summary

| candidate | run_id | status | expectancy_scoreboard | expectancy_calc | delta_expectancy | pf_scoreboard | pf_calc | delta_pf | trades_scoreboard | trades_calc | delta_trades | pipeline_bug_suspected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| __baseline__ | 20260221_181919 | ok | -1.07969 | -1.07969 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | False |
| config_edge_mr_vtm_thr22_v2 | 20260221_182138 | ok | -0.22291143 | -0.22291143 | -0 | 0.51851492 | 0.51851492 | 0 | 14 | 14 | 0 | False |
| config_edge_tf_simple_core_v1 | 20260221_182216 | ok | -0.28941318 | -0.28941318 | -0 | 0.62198668 | 0.62198668 | 0 | 22 | 22 | 0 | False |
| config_edge_tf_simple_entry_loose_v3 | 20260221_182257 | ok | -0.28941318 | -0.28941318 | -0 | 0.62198668 | 0.62198668 | 0 | 22 | 22 | 0 | False |
| config_edge_tf_simple_rr_compact_v4 | 20260221_182417 | ok | -0.29006478 | -0.29006478 | 0 | 0.60368179 | 0.60368179 | 0 | 23 | 23 | 0 | False |
| config_edge_tf_simple_freq_v2 | 20260221_182337 | ok | -0.297835 | -0.297835 | -0 | 0.61209435 | 0.61209435 | 0 | 26 | 26 | 0 | False |
| config_edge_mr_vtm_stop12_v3 | 20260221_182059 | ok | -0.299593 | -0.299593 | 0 | 0.38375574 | 0.38375574 | 0 | 20 | 20 | 0 | False |
| config_edge_mr_vtm_core_v1 | 20260221_181941 | ok | -0.3195105 | -0.3195105 | 0 | 0.41200519 | 0.41200519 | 0 | 20 | 20 | 0 | False |
| config_edge_mr_vtm_hold4_v4 | 20260221_182020 | ok | -0.3195105 | -0.3195105 | 0 | 0.41200519 | 0.41200519 | 0 | 20 | 20 | 0 | False |

- output_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/docs/_snapshots/edge_factory_expectancy_audit_20260221_1819/expectancy_audit.csv`