# Baselines Congelados

## Estado de plantillas
- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.

## Tabla de baselines
| label | run_id | mode | pf | expectancy_R | winrate | trades | opportunities_denom | SESSION_BLOCK | COST_FILTER_BLOCK | SHOCK_BLOCK | report.md | diagnostics.md |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE_RANGE | 20260218_200211 | RANGE | 2.307687 | 0.493273 | 0.666667 | 18 | 112 | 89 (0.794643) | 5 (0.044643) | 0 (0.000000) | `outputs/runs/20260218_200211/report.md` | `outputs/runs/20260218_200211/diagnostics/diagnostics.md` |
| BASELINE_TREND | 20260218_200726 | TREND | 0.520000 | -0.135098 | 0.375000 | 16 | 64 | 41 (0.640625) | 5 (0.078125) | 2 (0.031250) | `outputs/runs/20260218_200726/report.md` | `outputs/runs/20260218_200726/diagnostics/diagnostics.md` |
| BASELINE_AUTO | 20260218_202210 | TREND | 0.520000 | -0.135098 | 0.375000 | 16 | 62 | 40 (0.645161) | 5 (0.080645) | 1 (0.016129) | `outputs/runs/20260218_202210/report.md` | `outputs/runs/20260218_202210/diagnostics/diagnostics.md` |

## Metodologia
- KPIs (`pf`, `expectancy_R`, `winrate`, `trades`) tomados de `A_perf_by_mode.csv`.
- `opportunities_denom` y bloques tomados de `E_blocks.csv`.
- AUTO creado con `scripts/run_and_tag.py` usando `configs/config.yaml` y diagnosticado con `scripts/diagnose_run.py`.
