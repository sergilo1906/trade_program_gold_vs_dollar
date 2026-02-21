# V4A Expectancy Audit (DEV 2021-2023)

- scoreboard_used: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv`
- rows_audited: `7`
- PIPELINE_BUG_SUSPECTED: **YES**
- tolerances: `expectancy=1e-06`, `pf=1e-06`, `winrate=1e-06`, `trades=exact`

## Summary

| candidate | run_id | status | expectancy_scoreboard | expectancy_calc | delta_expectancy | pf_scoreboard | pf_calc | delta_pf | trades_scoreboard | trades_calc | delta_trades | pipeline_bug_suspected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| __baseline__ | 20260221_204030 | ok | 0.99606667 | 0.99606667 | -0 | 18.87628619 | 18.87628619 | 0 | 3 | 3 | 0 | False |
| mr_session_shock_london_t25_tp08 | 20260221_204455 | ok | 0.63822 | 0.63822 | 0 | inf | inf |  | 1 | 1 | 0 | True |
| mr_session_shock_nyopen_t25_tp08 | 20260221_205408 | ok | 0.63822 | 0.63822 | 0 | inf | inf |  | 1 | 1 | 0 | True |
| mr_session_shock_uspm_t25_tp08 | 20260221_210316 | ok | 0.63822 | 0.63822 | 0 | inf | inf |  | 1 | 1 | 0 | True |
| mr_session_shock_london_t30_tp12 | 20260221_204932 | empty_trades |  |  |  |  |  |  | 0 |  |  | False |
| mr_session_shock_nyopen_t30_tp12 | 20260221_205843 | empty_trades |  |  |  |  |  |  | 0 |  |  | False |
| mr_session_shock_uspm_t30_tp12 | 20260221_210750 | empty_trades |  |  |  |  |  |  | 0 |  |  | False |

## Suspected Rows

| candidate | run_id | status | expectancy_match | pf_match | trades_match | winrate_match | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mr_session_shock_london_t25_tp08 | 20260221_204455 | ok | True | False | True | True |  |
| mr_session_shock_nyopen_t25_tp08 | 20260221_205408 | ok | True | False | True | True |  |
| mr_session_shock_uspm_t25_tp08 | 20260221_210316 | ok | True | False | True | True |  |

- output_csv: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/docs/_snapshots/edge_factory_round3_expectancy_audit_20260221_2040/expectancy_audit.csv`