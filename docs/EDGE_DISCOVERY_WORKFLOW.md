# Edge Discovery Workflow (practical)

## 1) Define hypothesis (single sentence)

Template:
- change proposed
- expected behavior
- kill criterion

Example:
- "Increase signal frequency by relaxing entry body ratio; expected more trades with non-negative expectancy; kill if trades < 30 or PF < 1."

## 2) Build a small candidate set (3-10 YAML)

Rules:
- max 1-2 parameter deltas per config
- no massive grids
- keep baseline fixed for honest comparison

## 3) Run funnel

## Smoke

```powershell
python scripts/run_edge_factory_batch.py --data data/xauusd_m5_test.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_smoke --runs-root outputs/runs --resamples 500 --seed 42 --max-bars 4000 --gates-config configs/research_gates/default_edge_factory.yaml --stage smoke --snapshot-prefix edge_factory_smoke
```

## Dev fast

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_dev_fast
```

## Dev robust

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_robust --runs-root outputs/runs --resamples 5000 --seed 42 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_robust --with-posthoc --with-temporal --snapshot-prefix edge_factory_dev_robust
```

## 4) Rebuild if interrupted

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --rebuild-only
```

## 5) Audit math consistency

```powershell
python scripts/verify_expectancy_math.py --scoreboard outputs/edge_factory_smoke/edge_factory_scoreboard.csv --scoreboard-fallback outputs/edge_factory_smoke/edge_factory_scoreboard.csv --runs-root outputs/runs --out-dir docs/_snapshots/edge_factory_expectancy_audit_YYYYMMDD_HHMM
```

## 6) Promote or kill

- Kill candidate if:
  - very low trades
  - negative expectancy with weak PF
  - CI crosses zero under robust gates
  - cost or temporal fails (dev_robust)
- Promote only when multiple dimensions improve (not a single metric).

## Anti p-hacking guardrails

- predeclare gates before run
- keep candidate count small
- do not alter thresholds mid-batch
- keep baseline fixed in every batch
- snapshot each run batch with `meta.json`

