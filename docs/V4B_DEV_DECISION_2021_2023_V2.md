# V4B DEV Decision 2021-2023 (V2)

- dataset: `data_local/xauusd_m5_DEV_2021_2023.csv`
- scoreboard: `outputs/v4_dev_runs2/v4_candidates_scoreboard.csv`
- snapshot: `docs/_snapshots/v4_dev_runs2b_2021_2023/`
- audit: `docs/_snapshots/v4b_expectancy_audit_2021_2023/expectancy_audit.md`
- note: `v4b_orb_04..08` were re-run and included in this revision.

## Baseline

- baseline_run_id: `20260220_145346`
- baseline_trades: `26`
- candidates_total: `8`
- gate_all_passed: `0`

## Top 5 Candidates

| candidate | run_id | expectancy_R | pf | trades | winrate | retention_vs_b4_pct | crosses_zero | gate_all |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| v4b_orb_01 | 20260220_151326 | 0.025761 | 1.183970 | 118 | 0.516949 | 453.846154 | True | False |
| v4b_orb_07 | 20260220_184022 | 0.024344 | 1.052280 | 42 | 0.476190 | 161.538462 | True | False |
| v4b_orb_02 | 20260220_153447 | 0.022468 | 1.160454 | 118 | 0.516949 | 453.846154 | True | False |
| v4b_orb_03 | 20260220_153001 | -0.003767 | 0.991435 | 78 | 0.525641 | 300.000000 | True | False |
| v4b_orb_06 | 20260220_175518 | -0.028266 | 0.851618 | 320 | 0.456250 | 1230.769231 | True | False |

## Expectancy Audit

- PIPELINE_BUG_SUSPECTED: `NO`
- Source: `docs/_snapshots/v4b_expectancy_audit_2021_2023/expectancy_audit.md`
- Result: scoreboard metrics match recomputation from `trades.csv` within tolerance.

## Decision

- decision: **NO-GO**
- rationale:
  - `0/8` candidates pass `gate_all`.
  - candidates with positive expectancy (`v4b_orb_01`, `v4b_orb_07`, `v4b_orb_02`) still have `crosses_zero=True`.
  - strongest negative outlier (`v4b_orb_08`) has `expectancy_R=-0.134098` and `pf=0.382742`.
  - no evidence of metric bug in expectancy/PF computation.

## Execution Notes

- During resume, failure for `v4b_orb_07` was reproduced as:
  - `OSError: [Errno 28] No space left on device` while writing `events.csv` and then `run_meta.json`.
  - Path evidence: `docs/_snapshots/v4_dev_runs2b_2021_2023/run_resume_04_08.log`.
- After retry with free space, `v4b_orb_07` completed with run_id `20260220_184022`.

## Next Command

Because V4B remains NO-GO, move to pivot-planning step:

```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v4_candidates3 --out-dir outputs/v4_dev_runs3 --resamples 5000 --seed 42
```

(`configs/v4_candidates3` should be created from the plan in `docs/PIVOT_PLAN_TREND_OR_MR.md` first.)
