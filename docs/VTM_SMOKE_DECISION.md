# VTM Smoke Decision

- date_utc: `2026-02-21`
- command:
  - `python scripts/run_vtm_candidates.py --data data/xauusd_m5_test.csv --candidates-dir configs/vtm_candidates --out-dir outputs/vtm_smoke --runs-root outputs/runs --resamples 500 --seed 42 --max-bars 4000 --snapshot-prefix vtm_smoke`
- snapshot:
  - `docs/_snapshots/vtm_smoke_20260221_020332/`
  - `docs/_snapshots/vtm_smoke_20260221_020332/meta.json`

## Outcome

- status: **PIPELINE_SMOKE_OK**
- candidates_total: `12`
- pass_count (gate_all): `0`
- baseline_run_id: `20260221_020333`
- baseline_trades: `2`

## Top Candidate (Smoke)

- candidate: `vtm_edge1_thr26`
- run_id: `20260221_020847`
- pf: `1.062439`
- expectancy_R: `0.032093`
- trades: `4`
- ci_crosses_zero: `True`
- gate_all: `False`

## Decision

- strategy decision on smoke sample: **NO-GO (statistical)**
- plumbing decision: **GO** (runner + diagnostics + bootstrap + snapshot generated end-to-end).

## Notes

- Smoke sample is intentionally small (`max-bars=4000`) and not suitable for final edge validation.
- Final edge decision remains the DEV report:
  - `docs/VTM_DEV_DECISION_2021_2023.md` (`NO-GO`).
