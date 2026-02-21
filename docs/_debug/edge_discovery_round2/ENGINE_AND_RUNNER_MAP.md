# Engine and Runner Map (Round 2)

- audited_at_utc: `2026-02-21T09:00:00Z`
- template_status: `./_templates/plantillas_mejoradas.zip` not found; using repo style + `_zip_template_ref_audit_20260216.zip` reference.

## Reused runner chain

1. `scripts/run_edge_discovery_overnight.py`
   - orchestrates queue + posthoc + temporal review.
2. `scripts/run_vtm_candidates.py`
   - executes baseline + candidates,
   - computes KPI from `trades.csv`,
   - runs diagnose/bootstrap per run,
   - builds scoreboard csv/md/json.

## Timeout fallback (same materialized dataset)

- Primary source:
  - `outputs/edge_discovery_overnight2/vtm_candidates_scoreboard_summary.json` field `data`
- Fallback source:
  - latest `data/tmp_vtm/vtm_input_*.csv` around run time
- Rebuild command:
  - `python scripts/run_vtm_candidates.py --data <materialized_csv> --candidates-dir configs/edge_discovery_candidates2 --out-dir outputs/edge_discovery_overnight2_clean --runs-root outputs/runs --baseline-config configs/config_v3_PIVOT_B4.yaml --resamples 2000 --seed 42 --rebuild-only`

## Metric sources (ground truth)

- Per-trade R:
  - `outputs/runs/<run_id>/trades.csv`, column resolved from `r_multiple` family.
- CI:
  - `outputs/runs/<run_id>/diagnostics/BOOT_expectancy_ci.csv`.
- Math consistency audit:
  - `scripts/verify_expectancy_math.py` compares scoreboard vs recomputed metrics from `trades.csv`.

## Snapshot target (versionable, small)

- `docs/_snapshots/edge_discovery_round2_<timestamp>/`
- includes:
  - scoreboard csv/md/json
  - expectancy audit csv/md
  - posthoc csv/json
  - temporal csv/json
  - `meta.json` with exact commands and run_ids
