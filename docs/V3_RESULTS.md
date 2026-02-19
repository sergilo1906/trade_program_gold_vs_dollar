# V3 Results

## Context
- OHLC-only, M5, next-open.
- `enable_strategy_v3=true` activo en runs V3.
- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.

## KPI Comparison (v2 baselines vs v3)
| label | version | run_id | mode | pf | expectancy_R | winrate | trades | opportunities_denom | session_block | cost_filter_block | shock_block | boot_n | boot_mean | boot_ci_low | boot_ci_high | boot_crosses_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE_RANGE | v2 | 20260218_200211 | RANGE | 2.307687 | 0.493273 | 0.666667 | 18 | 112 | 89 (0.7946) | 5 (0.0446) | 0 (0.0000) | 18 | 0.493273 | -0.066057 | 1.035451 | True |
| BASELINE_TREND | v2 | 20260218_200726 | TREND | 0.52 | -0.135098 | 0.375 | 16 | 64 | 41 (0.6406) | 5 (0.0781) | 2 (0.0312) |  |  |  |  |  |
| BASELINE_AUTO | v2 | 20260218_202210 | TREND | 0.52 | -0.135098 | 0.375 | 16 | 62 | 40 (0.6452) | 5 (0.0806) | 1 (0.0161) |  |  |  |  |  |
| V3_RANGE | v3 | 20260218_210540 | RANGE | 1.046231 | 0.027181 | 0.471429 | 70 | 1119 | 923 (0.8248) | 37 (0.0331) | 4 (0.0036) | 70 | 0.027181 | -0.260074 | 0.307498 | True |
| V3_TREND | v3 | 20260218_211849 | TREND | 1.07374 | 0.047884 | 0.398792 | 331 | 4752 | 3153 (0.6635) | 467 (0.0983) | 390 (0.0821) | 331 | 0.047884 | -0.099581 | 0.203075 | True |
| V3_AUTO | v3 | 20260218_213339 | TREND | 1.123865 | 0.078845 | 0.406844 | 263 | 3595 | 2416 (0.6720) | 345 (0.0960) | 272 (0.0757) | 263 | 0.078845 | -0.090337 | 0.254048 | True |

## QA v3
| run_id | diag_A_to_N | has_v3_signal_events | has_v3_entry_exit_events | next_open_match | next_open_ok | max_trades_per_session_seen | max_trades_per_session_allowed | session_limit_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20260218_210540 | OK | OK | OK | 70/70 | OK | 1 | 1 | OK |
| 20260218_211849 | OK | OK | OK | 331/331 | OK | 1 | 1 | OK |
| 20260218_213339 | OK | OK | OK | 263/263 | OK | 1 | 1 | OK |

## Paths
| label | run_id | report_path | diagnostics_path |
| --- | --- | --- | --- |
| BASELINE_RANGE | 20260218_200211 | outputs/runs/20260218_200211/report.md | outputs/runs/20260218_200211/diagnostics/diagnostics.md |
| BASELINE_TREND | 20260218_200726 | outputs/runs/20260218_200726/report.md | outputs/runs/20260218_200726/diagnostics/diagnostics.md |
| BASELINE_AUTO | 20260218_202210 | outputs/runs/20260218_202210/report.md | outputs/runs/20260218_202210/diagnostics/diagnostics.md |
| V3_RANGE | 20260218_210540 | outputs/runs/20260218_210540/report.md | outputs/runs/20260218_210540/diagnostics/diagnostics.md |
| V3_TREND | 20260218_211849 | outputs/runs/20260218_211849/report.md | outputs/runs/20260218_211849/diagnostics/diagnostics.md |
| V3_AUTO | 20260218_213339 | outputs/runs/20260218_213339/report.md | outputs/runs/20260218_213339/diagnostics/diagnostics.md |
