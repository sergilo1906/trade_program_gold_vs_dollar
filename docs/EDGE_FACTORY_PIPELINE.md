# EDGE FACTORY Pipeline (MVP)

## Goal

Provide a reproducible funnel to promote/discard edge candidates using the existing run pipeline.

## Levels

## Level 0: `smoke`

- objective: plumbing works end-to-end
- requirements:
  - runs complete
  - scoreboard artifacts exist
  - snapshot + meta exist
- note: no requirement for positive edge

## Level 1: `dev_fast`

- objective: discard weak candidates quickly
- defaults:
  - moderate sample (`--max-bars` allowed)
  - bootstrap resamples low/moderate
- gates: minimum trades / PF / expectancy / retention

## Level 2: `dev_robust`

- objective: robust preliminary validation
- adds:
  - bootstrap stricter CI gate
  - optional post-hoc cost stress (+20/+50)
  - optional temporal stability checks
- gates: stricter thresholds, cost and temporal survival

## Level 3: `holdout` (design-ready)

- documented placeholder in MVP.
- recommended implementation next:
  - split immutable holdout
  - run only promoted finalists
  - apply same gate evaluator with holdout-specific thresholds.

## Main command (generic batch)

```powershell
python scripts/run_edge_factory_batch.py --data <DATA_CSV> --candidates-dir <CANDIDATES_DIR> --baseline-config <BASELINE_YAML> --out-dir <OUT_DIR> --runs-root outputs/runs --resamples <N> --seed 42 --max-bars <BARS_OR_0> --gates-config configs/research_gates/default_edge_factory.yaml --stage <smoke|dev_fast|dev_robust> --snapshot-prefix <PREFIX>
```

## Rebuild-only command

```powershell
python scripts/run_edge_factory_batch.py --data <DATA_CSV> --candidates-dir <CANDIDATES_DIR> --baseline-config <BASELINE_YAML> --out-dir <OUT_DIR> --runs-root outputs/runs --resamples <N> --seed 42 --max-bars <BARS_OR_0> --gates-config configs/research_gates/default_edge_factory.yaml --stage <smoke|dev_fast|dev_robust> --rebuild-only
```

## Optional robustness toggles

- `--with-posthoc` / `--no-posthoc`
- `--with-temporal` / `--no-temporal`

Defaults:
- `smoke`, `dev_fast`: posthoc/temporal off
- `dev_robust`: posthoc/temporal on

## Core artifacts

- `outputs/<out_dir>/edge_factory_scoreboard.csv`
- `outputs/<out_dir>/edge_factory_scoreboard.md`
- `outputs/<out_dir>/edge_factory_scoreboard_summary.json`
- `outputs/<out_dir>/edge_factory_manifest.json`
- `outputs/<out_dir>/edge_factory_progress.jsonl`
- snapshot: `docs/_snapshots/<prefix>_<timestamp>/` with `meta.json`

