# EDGE FACTORY Gates (MVP)

Config file: `configs/research_gates/default_edge_factory.yaml`

## Supported gates

- `min_trades`
- `min_pf`
- `min_expectancy_r`
- `require_ci_non_crossing_zero`
- `min_retention_vs_baseline_pct`
- `require_cost_stress_survival_p20`
- `require_cost_stress_survival_p50`
- `require_temporal_stability`
- `max_drawdown_r` (optional/pending if unavailable)
- `min_years_active` (optional/pending)
- `min_months_with_trades` (optional/pending)

## How gates are applied

- All candidate gates are evaluated per row.
- `gate_all = true` only if every active gate is true.
- Baseline row is reference only (`is_baseline=true`) and is not used as promoted candidate.

## Pending metrics behavior

- If a gate needs a missing metric:
  - `smoke` / `dev_fast`: gate is informative (does not force fail), metric appears in `pending_metrics`.
  - `dev_robust`: gate fails and appears in `fail_reasons`.

## Cost and temporal gates

- Cost gates use `posthoc_cost_stress_batch.py` output:
  - pass condition per factor: `PF > 1` and `expectancy_R > 0`.
- Temporal gate uses `edge_temporal_review.py` summary:
  - current pass rule: no negative segment/year/hour bucket with `trades>=10` flagged by summary.

## Scoreboard columns to inspect

- Core: `pf`, `expectancy_R`, `trades`, `winrate`, `ci_low`, `ci_high`, `crosses_zero`
- Stability: `retention_vs_b4_pct`, `cost_survives_1p2`, `cost_survives_1p5`, `temporal_pass`
- Decision: `gate_all`, `fail_reasons`, `pending_metrics`

