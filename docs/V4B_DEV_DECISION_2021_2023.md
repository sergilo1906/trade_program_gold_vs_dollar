# V4B DEV Decision (2021-2023)

- baseline_run_id: `20260220_145346`
- baseline_trades: `26`
- candidatos_totales: `8`
- candidatos_gate_all_pass: `0`
- reconstructed_scoreboard: `True`

## Top 5

| candidate | run_id | expectancy_R | pf | trades | winrate | retention_vs_b4_pct | crosses_zero | gate_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v4b_orb_01 | 20260220_151326 | 0.025761 | 1.18397 | 118 | 0.516949 | 453.846154 | True | False |
| v4b_orb_02 | 20260220_153447 | 0.022468 | 1.160454 | 118 | 0.516949 | 453.846154 | True | False |
| v4b_orb_03 | 20260220_153001 | -0.003767 | 0.991435 | 78 | 0.525641 | 300 | True | False |
| v4b_orb_04 |  |  |  | 0 |  | 0 |  | False |
| v4b_orb_05 |  |  |  | 0 |  | 0 |  | False |

## Expectancy Audit

- PIPELINE_BUG_SUSPECTED: **NO**
- audit_csv: `docs/_snapshots/v4b_expectancy_audit_2021_2023/expectancy_audit.csv`
- audit_md: `docs/_snapshots/v4b_expectancy_audit_2021_2023/expectancy_audit.md`

## Decision

- decision: **NO-GO**
- rationale: no candidate satisfies expectancy_R > 0 + CI not crossing zero + reasonable trades; and several candidates failed execution due parser errors in `xauusd_bot run` post-processing.

## Next Command

```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v4_candidates2 --out-dir outputs/v4_dev_runs2_retry --resamples 5000 --seed 42
```