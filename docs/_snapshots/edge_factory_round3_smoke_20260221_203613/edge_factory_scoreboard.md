# Edge Factory Scoreboard

- stage: `smoke`
- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/tmp_edge_factory/edge_factory_input_20260221_203613.csv`
- baseline_run_id: `20260221_203614`
- baseline_trades: `2`
- pass_count(gate_all): `3`

## Baseline

| candidate | run_id | status | trades | pf | expectancy_R | note |
| --- | --- | --- | --- | --- | --- | --- |
| __baseline__ | 20260221_203614 | ok | 2 | 0 | -1.07969 |  |

## Candidates

| candidate | run_id | status | trades | pf | expectancy_R | ci_low | ci_high | crosses_zero | retention_vs_b4_pct | gate_all | fail_reasons | pending_metrics | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mr_session_shock_london_t25_tp08 | 20260221_203636 | ok | 5 | 0.463559 | -0.331958 | -1.034657 | 0.379512 | True | 250 | True |  |  |  |
| mr_session_shock_nyopen_t25_tp08 | 20260221_203751 | ok | 5 | 0.463559 | -0.331958 | -1.034657 | 0.379512 | True | 250 | True |  |  |  |
| mr_session_shock_uspm_t25_tp08 | 20260221_203907 | ok | 5 | 0.463559 | -0.331958 | -1.034657 | 0.379512 | True | 250 | True |  |  |  |
| mr_session_shock_london_t30_tp12 | 20260221_203714 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 1.000000; status=failed |  | trade_status=empty_trades |
| mr_session_shock_nyopen_t30_tp12 | 20260221_203829 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 1.000000; status=failed |  | trade_status=empty_trades |
| mr_session_shock_uspm_t30_tp12 | 20260221_203945 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 1.000000; status=failed |  | trade_status=empty_trades |

## Artifacts

- scoreboard_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_round3_smoke/edge_factory_scoreboard.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_round3_smoke/edge_factory_scoreboard_summary.json`
