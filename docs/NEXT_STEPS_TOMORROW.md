# NEXT STEPS TOMORROW

## Focus

Round 3 MR-Session Shock needs one more `dev_fast` iteration focused on **frequency recovery** before any `dev_robust` promotion.

## Current decision state

- `candidates3` `dev_fast` completed.
- `pass_count(gate_all)=0`.
- no finalist eligible for `dev_robust` yet.

## Ordered tasks

1. Build `candidates3_r2` (small set) to increase sample size:
   - widen `entry_windows_utc` from 1h to 2h where justified,
   - relax `shock_threshold` around `2.2-2.6`,
   - keep stops/targets simple (no extra filters).
2. Re-run `dev_fast` with larger slice (`max-bars 60000`) and same gates.
3. Promote to `dev_robust` only candidates with:
   - trades >= 20,
   - expectancy > 0,
   - PF > 1,
   - retention >= 50,
   - no empty-trades failure.
4. Keep Compression Breakout as scaffolding-only until MR has enough frequency evidence.
5. Optional plumbing fix: harden `verify_expectancy_math.py` for `PF=inf` rows (avoid false bug flags).

## Exact command (next run)

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates3 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_round3_dev_fast_r2 --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_round3_dev_fast_r2
```

## Do not touch yet

- do not promote any round3 candidate to `dev_robust` with single-trade evidence.
- do not alter core edge factory gates mid-batch.
- keep `docs/RANGE_EDGE_VALIDATION.md` out of commits.
