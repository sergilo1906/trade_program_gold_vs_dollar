# Edge Factory Scoreboard

- stage: `dev_fast`
- data: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/tmp_edge_factory/edge_factory_input_20260221_204029.csv`
- baseline_run_id: `20260221_204030`
- baseline_trades: `3`
- pass_count(gate_all): `0`

## Baseline

| candidate | run_id | status | trades | pf | expectancy_R | note |
| --- | --- | --- | --- | --- | --- | --- |
| __baseline__ | 20260221_204030 | ok | 3 | 18.876286 | 0.996067 |  |

## Candidates

| candidate | run_id | status | trades | pf | expectancy_R | ci_low | ci_high | crosses_zero | retention_vs_b4_pct | gate_all | fail_reasons | pending_metrics | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mr_session_shock_london_t25_tp08 | 20260221_204455 | ok | 1 | inf | 0.63822 | 0.63822 | 0.63822 | False | 33.333333 | False | gate_min_trades: trades=1.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=33.333333 < 50.000000 | pf |  |
| mr_session_shock_nyopen_t25_tp08 | 20260221_205408 | ok | 1 | inf | 0.63822 | 0.63822 | 0.63822 | False | 33.333333 | False | gate_min_trades: trades=1.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=33.333333 < 50.000000 | pf |  |
| mr_session_shock_uspm_t25_tp08 | 20260221_210316 | ok | 1 | inf | 0.63822 | 0.63822 | 0.63822 | False | 33.333333 | False | gate_min_trades: trades=1.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=33.333333 < 50.000000 | pf |  |
| mr_session_shock_london_t30_tp12 | 20260221_204932 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=0.000000 < 50.000000; status=failed | expectancy_R; pf | trade_status=empty_trades |
| mr_session_shock_nyopen_t30_tp12 | 20260221_205843 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=0.000000 < 50.000000; status=failed | expectancy_R; pf | trade_status=empty_trades |
| mr_session_shock_uspm_t30_tp12 | 20260221_210750 | failed | 0 |  |  |  |  | False | 0 | False | gate_min_trades: trades=0.000000 < 20.000000; gate_min_retention: retention_vs_b4_pct=0.000000 < 50.000000; status=failed | expectancy_R; pf | trade_status=empty_trades |

## Artifacts

- scoreboard_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv`
- summary_json: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard_summary.json`
