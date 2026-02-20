# V4A DEV 2021-2023 Debug Bundle

- purpose: compact, versionable evidence to inspect V4A DEV NO-GO from GitHub.
- selected runs: baseline + top 3 candidates by (`gate_all`, `expectancy_R`, `pf`, `trades`).
- selected_run_ids: `20260219_235935`, `20260220_015938`, `20260220_005035`, `20260220_004047`

## Included

- Scoreboard artifacts:
  - `v4_candidates_scoreboard.csv` (from `outputs/v4_dev_runs`, current size is 0 bytes)
  - `v4_candidates_scoreboard.md`
  - `v4_candidates_scoreboard_summary.json`
  - snapshot fallback copies:
    - `v4_candidates_scoreboard_snapshot.csv`
    - `v4_candidates_scoreboard_snapshot.md`
    - `v4_candidates_scoreboard_snapshot_summary.json`
- Decision doc:
  - `V4A_DEV_DECISION_2021_2023.md`
- Configs:
  - `config_v3_PIVOT_B4.yaml`
  - `configs_v4_candidates/*.yaml`
- Per-run evidence:
  - `runs/<run_id>/run_meta.json`
  - `runs/<run_id>/config_used.yaml`
  - `runs/<run_id>/diagnostics/BOOT_expectancy_ci.csv`
  - `runs/<run_id>/trades_head.csv` (first 200 lines)
  - `runs/20260219_235935/trades.csv` (small enough to include full file)
- Environment:
  - `env_python.txt`
  - `env_pip_freeze.txt`
  - `env_platform.txt`

## Missing Paths

- none

## Notes

- Large files (`events.csv`, `signals.csv`, full large `trades.csv`) were intentionally excluded.
- This bundle is for diagnostics/debug traceability only.
