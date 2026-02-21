# NEXT STEPS TOMORROW

## Objective

Move from MVP plumbing to a reliable research cadence using `run_edge_factory_batch.py` as the default entrypoint.

## Ordered tasks (3-5)

1. Run `dev_fast` on real DEV 2021-2023 and keep only candidates with acceptable trade count + non-degenerate metrics.
2. Run `dev_robust` only for finalists with `--with-posthoc --with-temporal` and strict gates.
3. Add holdout promotion stage (Level 3) using immutable split and same gate evaluator.
4. Normalize/contain `bootstrap_expectancy.py` side-effect to avoid accidental edits in `docs/RANGE_EDGE_VALIDATION.md` during batch loops.
5. Freeze one reproducible "promotion pack" snapshot for executive GO/NO-GO.

## Exact commands

### Dev fast

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_dev_fast
```

### Dev robust (finalists only)

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_robust --runs-root outputs/runs --resamples 5000 --seed 42 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_robust --with-posthoc --with-temporal --snapshot-prefix edge_factory_dev_robust
```

### Rebuild (if interrupted)

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --rebuild-only
```

## Do not touch yet

- do not alter strategy logic while validating Edge Factory plumbing
- do not tune thresholds mid-batch
- do not mix unrelated docs (keep `docs/RANGE_EDGE_VALIDATION.md` out of commits)
