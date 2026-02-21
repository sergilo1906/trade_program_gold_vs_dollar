# EDGE FACTORY MVP Decision

- date_utc: `2026-02-21`
- status: **EDGE FACTORY MVP OPERATIVO**

## Evidence

- smoke batch command executed with new runner:
  - `python scripts/run_edge_factory_batch.py --data data/xauusd_m5_test.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_smoke --runs-root outputs/runs --resamples 500 --seed 42 --max-bars 4000 --gates-config configs/research_gates/default_edge_factory.yaml --stage smoke --snapshot-root docs/_snapshots --snapshot-prefix edge_factory_smoke`
- generated artifacts:
  - `outputs/edge_factory_smoke/edge_factory_scoreboard.csv`
  - `outputs/edge_factory_smoke/edge_factory_scoreboard.md`
  - `outputs/edge_factory_smoke/edge_factory_scoreboard_summary.json`
  - `outputs/edge_factory_smoke/edge_factory_manifest.json`
  - `outputs/edge_factory_smoke/edge_factory_progress.jsonl`
  - snapshot: `docs/_snapshots/edge_factory_smoke_20260221_181917/`
- scoreboard summary:
  - `baseline_run_id=20260221_181919`
  - `candidate_rows=8`
  - `pass_count(stage=smoke)=8`

## Consistency check

- expectancy audit command:
  - `python scripts/verify_expectancy_math.py --scoreboard outputs/edge_factory_smoke/edge_factory_scoreboard.csv --scoreboard-fallback outputs/edge_factory_smoke/edge_factory_scoreboard.csv --runs-root outputs/runs --out-dir docs/_snapshots/edge_factory_expectancy_audit_20260221_1819`
- result:
  - `PIPELINE_BUG_SUSPECTED=NO`

## Decision

- The subsystem is **operational**:
  - one-command batch execution
  - configurable stage gates
  - rebuild path (`--rebuild-only`)
  - snapshot + manifest + progress traceability
  - tests for gates/rebuild/meta passing
- This decision is about plumbing, not edge quality.

## Current limitations

1. `holdout` stage is documented but not yet automated in the generic runner.
2. `max_drawdown_r`, `min_years_active`, `min_months_with_trades` remain optional/pending when artifacts do not provide robust data.
3. `bootstrap_expectancy.py` still writes legacy `docs/RANGE_EDGE_VALIDATION.md` side-effect.

## Next required step to reach v1 usable

1. Run `dev_fast` with real DEV dataset and keep top candidates only.
2. Run `dev_robust` with posthoc + temporal gates.
3. Integrate holdout stage (promotion only for robust finalists).

