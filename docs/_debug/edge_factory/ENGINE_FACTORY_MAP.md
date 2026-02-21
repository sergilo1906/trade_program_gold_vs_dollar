# ENGINE / FACTORY MAP (real repo)

## Core run path

- [VERIFICADO] `scripts/run_and_tag.py`
  - launches `python -m xauusd_bot run --data ... --config ...`
  - always writes `outputs/runs/<run_id>/run_meta.json` and `config_used.yaml` (even on postprocess failure).
- [VERIFICADO] `src/xauusd_bot/main.py`
  - `run` command drives loader -> engine -> report artifacts.
- [VERIFICADO] `src/xauusd_bot/engine.py`
  - strategy routing via config:
    - `strategy_family` in `{"AUTO","LEGACY","V3_CLASSIC","V4_SESSION_ORB","VTM_VOL_MR"}`
    - flags `enable_strategy_v3`, `enable_strategy_v4_orb`, `enable_strategy_vtm`

## Metrics / diagnostics

- [VERIFICADO] `scripts/diagnose_run.py`
  - reads run artifacts (`trades.csv`, `fills.csv`, `events.csv`) and writes diagnostics.
- [VERIFICADO] `scripts/bootstrap_expectancy.py`
  - computes bootstrap CI over R column from `trades.csv`
  - writes `outputs/runs/<run_id>/diagnostics/BOOT_expectancy_ci.csv`
  - writes `docs/RANGE_EDGE_VALIDATION.md` (legacy side-effect)
- [VERIFICADO] canonical R columns used in scripts:
  - `r_multiple` first, fallback candidates (`R_net`, `r_net`, `net_R`, `net_r`, `pnl_R`, `pnl_r`)

## Existing orchestration scripts

- [VERIFICADO] `scripts/run_vtm_candidates.py`
  - baseline + candidates queue
  - supports `--rebuild-only`
  - builds `csv/md/json` scoreboard
  - can snapshot to `docs/_snapshots/...`
- [VERIFICADO] `scripts/run_edge_discovery_overnight.py`
  - orchestrates queue + posthoc + temporal
- [VERIFICADO] `scripts/posthoc_cost_stress_batch.py`
  - post-hoc cost stress (+20/+50) from fixed trade sets
- [VERIFICADO] `scripts/edge_temporal_review.py`
  - temporal segmentation (segments/year/hour)
- [VERIFICADO] `scripts/verify_expectancy_math.py`
  - compares scoreboard metrics vs recomputed metrics from `trades.csv`

## Rebuild / fallback patterns

- [VERIFICADO] `scripts/build_v4_scoreboard_from_runs.py`
  - rebuilds scoreboard from `run_meta + trades + boot` when wrappers timeout
- [INFERIDO] same pattern is safest base for generic Edge Factory rebuild.

## Versionable small artifacts

- [VERIFICADO] versionable:
  - `docs/_snapshots/...`
  - `docs/_debug/...`
  - `docs/*.md`, `docs/*.csv` (small)
- [VERIFICADO] non-versionable heavy:
  - `outputs/runs/...`
  - large datasets in `data_local/...`

## Fastest integration path (without refactor)

1. Reuse `run_and_tag -> diagnose_run -> bootstrap_expectancy` as execution primitive.
2. Add reusable gates evaluator module (`scripts/lib/edge_factory_eval.py`).
3. Add generic batch runner (`scripts/run_edge_factory_batch.py`) with:
   - manifest + progress jsonl
   - optional posthoc/temporal
   - snapshot + meta
4. Add rebuild script (`scripts/build_edge_factory_scoreboard_from_runs.py`) consuming progress first, `run_meta` fallback.
5. Keep strategy logic untouched.

## Pending / limits

- [PENDIENTE] dedicated max drawdown in R from official diagnostics (currently approximated from trade R path).
- [PENDIENTE] explicit holdout stage integration in generic runner (MVP documents level 3, not fully automated here).

