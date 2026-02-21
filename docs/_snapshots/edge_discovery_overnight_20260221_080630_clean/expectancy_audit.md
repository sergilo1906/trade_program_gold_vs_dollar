# V4A Expectancy Audit (DEV 2021-2023)

- scoreboard_used: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard.csv`
- rows_audited: `5`
- PIPELINE_BUG_SUSPECTED: **NO**
- tolerances: `expectancy=1e-06`, `pf=1e-06`, `winrate=1e-06`, `trades=exact`

## Summary

| candidate | run_id | status | expectancy_scoreboard | expectancy_calc | delta_expectancy | pf_scoreboard | pf_calc | delta_pf | trades_scoreboard | trades_calc | delta_trades | pipeline_bug_suspected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| config_edge_vtm_reversal_fast_v1 | 20260221_075421 | ok | 0.18281 | 0.18281 | 0 | 1.32114749 | 1.32114749 | 0 | 2 | 2 | 0 | False |
| config_edge_v4_orb_wide_v1 | 20260221_063806 | ok | -0.09459029 | -0.09459029 | -0 | 0.63386717 | 0.63386717 | 0 | 140 | 140 | 0 | False |
| config_edge_vtm_mr_balanced_v1 | 20260221_064929 | ok | -0.1263325 | -0.1263325 | -0 | 0.64779721 | 0.64779721 | 0 | 4 | 4 | 0 | False |
| config_edge_v3_trend_lite_v1 | 20260221_074352 | ok | -0.16005157 | -0.16005157 | 0 | 0.7858588 | 0.7858588 | 0 | 127 | 127 | 0 | False |
| config_edge_vtm_mr_strict_v1 | 20260221_070041 | empty_trades |  |  |  |  |  |  | 0 |  |  | False |

- output_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/docs/_snapshots/edge_discovery_expectancy_audit_20260221/expectancy_audit.csv`