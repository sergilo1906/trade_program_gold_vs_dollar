# EDGE DISCOVERY ROUND 2

- date_utc: `2026-02-21`
- repo: `trade_program_gold_vs_dollar`
- template_status: `./_templates/plantillas_mejoradas.zip` missing, using `_zip_template_ref_audit_20260216.zip` reference + repo style.
- data: `data_local/xauusd_m5_DEV_2021_2023.csv` (materialized input: `data/tmp_vtm/vtm_input_20260221_141618.csv`, max-bars=60000)
- baseline_config: `configs/config_v3_PIVOT_B4.yaml`

## Executive Summary

- Round 2 was executed end-to-end with 8 candidates (`configs/edge_discovery_candidates2`), baseline B4, bootstrap=2000, seed=42.
- Scoreboard completed without rebuild fallback.
- `gate_all` result: **0/8**.
- Expectancy math audit: **PIPELINE_BUG_SUSPECTED=NO**.
- Best raw candidate by expectancy/PF was `config_edge_mr_vtm_thr22_v2`, but with only **2 trades** and CI crossing zero.
- Higher-frequency candidates (29-30 trades) were all negative in expectancy and PF<1, and worsened under +20/+50% post-hoc cost stress.
- Pass 2 was **not executed**: no finalist met minimum eligibility criteria.

## Configs Tested

### Family A - Trend-following simple (V3_CLASSIC)
- `config_edge_tf_simple_core_v1.yaml`
- `config_edge_tf_simple_freq_v2.yaml`
- `config_edge_tf_simple_entry_loose_v3.yaml`
- `config_edge_tf_simple_rr_compact_v4.yaml`

### Family B - Mean-reversion minimal (VTM_VOL_MR)
- `config_edge_mr_vtm_core_v1.yaml`
- `config_edge_mr_vtm_thr22_v2.yaml`
- `config_edge_mr_vtm_stop12_v3.yaml`
- `config_edge_mr_vtm_hold4_v4.yaml`

## Scoreboard vs Baseline B4

Source: `outputs/edge_discovery_overnight2/vtm_candidates_scoreboard.csv`

| candidate | run_id | PF | expectancy_R | trades | CI crosses 0 |
| --- | --- | ---: | ---: | ---: | --- |
| baseline B4 (reference run) | `20260221_141619` | 2.7700 | 0.3830 | 6 | yes |
| config_edge_mr_vtm_thr22_v2 | `20260221_145350` | 5.8254 | 0.3849 | 2 | yes |
| config_edge_mr_vtm_core_v1 | `20260221_142524` | 0.6478 | -0.1263 | 4 | yes |
| config_edge_mr_vtm_hold4_v4 | `20260221_143447` | 0.5726 | -0.1533 | 4 | yes |
| config_edge_mr_vtm_stop12_v3 | `20260221_144418` | 0.4402 | -0.2445 | 13 | yes |
| config_edge_tf_simple_core_v1 | `20260221_150309` | 0.5877 | -0.3199 | 29 | yes |
| config_edge_tf_simple_entry_loose_v3 | `20260221_151316` | 0.5877 | -0.3199 | 29 | yes |
| config_edge_tf_simple_freq_v2 | `20260221_152326` | 0.5594 | -0.3469 | 30 | yes |
| config_edge_tf_simple_rr_compact_v4 | `20260221_153339` | 0.4810 | -0.4026 | 29 | yes |

## Top Candidates (and why they fail)

1. `config_edge_mr_vtm_thr22_v2`
- Pros: best raw PF/expectancy.
- Fail reason: `trades=2` and CI crosses zero -> non-operable / low-power.
- Cost stress (+20/+50): still positive but still low-power (2 trades).

2. `config_edge_tf_simple_freq_v2`
- Pros: highest trade count in Round 2 (`30`).
- Fail reason: negative expectancy, PF<1, CI crosses zero.
- Cost stress (+20/+50): remains negative and deteriorates.
- Temporal/hour fragility: negative high-volume hour (`UTC 10`, 12 trades, expectancy -0.3645).

3. `config_edge_tf_simple_core_v1`
- Pros: similar frequency (`29` trades).
- Fail reason: negative expectancy, PF<1, CI crosses zero.
- Cost stress (+20/+50): remains negative and deteriorates.
- Temporal/hour fragility: negative high-volume hour (`UTC 10`, 11 trades, expectancy -0.2956).

## Validation Checks

1. Expectancy audit  
- File: `docs/_snapshots/edge_discovery_round2_expectancy_audit_20260221_1545/expectancy_audit.md`  
- Result: `PIPELINE_BUG_SUSPECTED=NO`.

2. Post-hoc cost stress (+20/+50)  
- File: `outputs/posthoc_cost_stress/edge_discovery_round2_posthoc.csv`  
- For higher-frequency candidates tested, both PF and expectancy remain weak/negative.

3. Temporal review  
- Files:
  - `outputs/edge_discovery_overnight2/edge_discovery_temporal_segments.csv`
  - `outputs/edge_discovery_overnight2/edge_discovery_yearly.csv`
  - `outputs/edge_discovery_overnight2/edge_discovery_hourly.csv`
- Trend family runs show mostly negative segments and clear negative hour concentration.

## Pass 2 Decision

- Pass 2 criteria required:
  - expectancy_R > 0
  - PF > 1.0
  - `crosses_zero == false`
  - trades >= 100
  - survives +20% post-hoc
  - no strong temporal fragility
- Outcome: **No candidate qualifies**.
- Action: Pass 2 skipped intentionally (no forced optimization).

## Final Verdict

**NO VIABLE (de momento)**  

### Confidence
- `87%`

### Main auto-deception risk
- Treating ultra-low-sample outliers (2 trades) as real edge signal.

## Artifacts

- Main run outputs:
  - `outputs/edge_discovery_overnight2/vtm_candidates_scoreboard.csv`
  - `outputs/edge_discovery_overnight2/vtm_candidates_scoreboard.md`
  - `outputs/edge_discovery_overnight2/vtm_candidates_scoreboard_summary.json`
- Snapshot:
  - `docs/_snapshots/edge_discovery_round2_20260221_154519/`
