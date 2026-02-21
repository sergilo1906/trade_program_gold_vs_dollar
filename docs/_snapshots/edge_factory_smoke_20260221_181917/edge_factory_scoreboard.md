# Edge Factory Scoreboard

- stage: `smoke`
- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/tmp_edge_factory/edge_factory_input_20260221_181917.csv`
- baseline_run_id: `20260221_181919`
- baseline_trades: `2`
- pass_count(gate_all): `8`

## Baseline

| candidate | run_id | status | trades | pf | expectancy_R | note |
| --- | --- | --- | --- | --- | --- | --- |
| __baseline__ | 20260221_181919 | ok | 2 | 0 | -1.07969 |  |

## Candidates

| candidate | run_id | status | trades | pf | expectancy_R | ci_low | ci_high | crosses_zero | retention_vs_b4_pct | gate_all | fail_reasons | pending_metrics | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| config_edge_mr_vtm_thr22_v2 | 20260221_182138 | ok | 14 | 0.518515 | -0.222911 | -0.629363 | 0.232831 | True | 700 | True |  |  |  |
| config_edge_tf_simple_core_v1 | 20260221_182216 | ok | 22 | 0.621987 | -0.289413 | -0.793623 | 0.227393 | True | 1100 | True |  |  |  |
| config_edge_tf_simple_entry_loose_v3 | 20260221_182257 | ok | 22 | 0.621987 | -0.289413 | -0.793623 | 0.227393 | True | 1100 | True |  |  |  |
| config_edge_tf_simple_rr_compact_v4 | 20260221_182417 | ok | 23 | 0.603682 | -0.290065 | -0.7208 | 0.202312 | True | 1150 | True |  |  |  |
| config_edge_tf_simple_freq_v2 | 20260221_182337 | ok | 26 | 0.612094 | -0.297835 | -0.72937 | 0.240318 | True | 1300 | True |  |  |  |
| config_edge_mr_vtm_stop12_v3 | 20260221_182059 | ok | 20 | 0.383756 | -0.299593 | -0.60933 | 0.057037 | True | 1000 | True |  |  |  |
| config_edge_mr_vtm_core_v1 | 20260221_181941 | ok | 20 | 0.412005 | -0.31951 | -0.671629 | 0.103781 | True | 1000 | True |  |  |  |
| config_edge_mr_vtm_hold4_v4 | 20260221_182020 | ok | 20 | 0.412005 | -0.31951 | -0.671629 | 0.103781 | True | 1000 | True |  |  |  |

## Artifacts

- scoreboard_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_smoke/edge_factory_scoreboard.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_smoke/edge_factory_scoreboard_summary.json`
