# V4 Next Plan

## Context

- V4A DEV queue (`2021-2023`) result is NO-GO (`0/12` pass `gate_all`).
- Expectancy audit confirms math consistency (`PIPELINE_BUG_SUSPECTED=NO`), so this is not a scoreboard/trades mismatch issue.
- Next step should test a tighter, explainable ORB family before discarding V4 architecture.

## Hypothesis

- Current V4A set is too permissive in breakout quality and stop placement.
- We can improve robustness by:
  - increasing breakout selectivity (`buffer_atr_mult`, `stop_buffer_atr_mult`),
  - constraining execution window (`trade_end` earlier or `trade_start` later),
  - testing both stop structures (`box` vs `break_wick`) with explicit RR tradeoffs.

## New Candidate Set

- Directory: `configs/v4_candidates2/`
- Files:
  - `v4b_orb_01.yaml`
  - `v4b_orb_02.yaml`
  - `v4b_orb_03.yaml`
  - `v4b_orb_04.yaml`
  - `v4b_orb_05.yaml`
  - `v4b_orb_06.yaml`
  - `v4b_orb_07.yaml`
  - `v4b_orb_08.yaml`

Design summary:
- Buffers tested: `0.10`, `0.15`, `0.20`
- Stop buffer tested: `0.00`, `0.02`, `0.05`
- RR tested: `1.0`, `1.5`, `2.0`
- Stop mode tested: `box`, `break_wick`
- Session window variants:
  - `07:00-09:00`
  - `07:30-10:00`
  - `07:00-08:30`
  - Alt Asia box (`23:00-05:00`) for one candidate

## Repro Commands

DEV full queue (`2021-2023`):

```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v4_candidates2 --out-dir outputs/v4_dev_runs2 --resamples 5000 --seed 42
```

Quick smoke before full queue:

```powershell
python scripts/run_v4_candidates_smoke.py --data data/xauusd_m5_test.csv --candidates-dir configs/v4_candidates2 --candidates v4b_orb_01 v4b_orb_04 --max-bars 4000 --resamples 200 --seed 42
```

Expectancy consistency audit for queue output:

```powershell
python scripts/verify_expectancy_math.py --scoreboard outputs/v4_dev_runs2/v4_candidates_scoreboard.csv --scoreboard-fallback docs/_snapshots/v4_dev_runs_2021_2023/v4_candidates_scoreboard.csv --runs-root outputs/runs --out-dir docs/_snapshots/v4b_expectancy_audit_2021_2023
```

## GO / NO-GO Criteria

GO candidate (for promotion to FULL rolling/posthoc) if all hold:
- `pf > 1.0`
- `expectancy_R > 0`
- bootstrap `crosses_zero == False`
- trades not collapsed (`trades >= 50` in DEV sample, plus retention sanity vs baseline)

NO-GO for this generation if:
- all candidates keep `expectancy_R <= 0`, or
- improvements come only from severe trade collapse / unstable CI.
