# RANGE vs TREND Delta

## Scope
- RUN_RANGE: `outputs/runs/20260218_200211`
- RUN_TREND: `outputs/runs/20260218_200726`
- Fuentes comparadas: `A_perf_by_mode.csv`, `E_blocks.csv`, `H_perf_by_hour_robust.csv`, `G_signals_by_hour_utc.csv`, `D_costR_percentiles.csv`.
- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.

## Top Metrics (A + opportunities)
| run_label | run_id | mode | pf | expectancy_R | winrate | trades | opportunities_G_sum | opportunities_E_denom |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUN_RANGE | 20260218_200211 | RANGE | 2.307687 | 0.493273 | 0.666667 | 18 | 0 | 112 |
| RUN_TREND | 20260218_200726 | TREND | 0.52 | -0.135098 | 0.375 | 16 | 64 | 64 |

## A) Perf by Mode
### RUN_RANGE
| mode | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| RANGE | 2.307687 | 0.493273 | 0.666667 | 0.493273 | 18 |

### RUN_TREND
| mode | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| TREND | 0.52 | -0.135098 | 0.375 | -0.135098 | 16 |

## E) Blocks
| block_type | RANGE_count | RANGE_pct | TREND_count | TREND_pct |
| --- | --- | --- | --- | --- |
| SESSION_BLOCK | 89 | 0.794643 | 41 | 0.640625 |
| COST_FILTER_BLOCK | 5 | 0.044643 | 5 | 0.078125 |
| SHOCK_BLOCK | 0 | 0 | 2 | 0.03125 |
| MAX_TRADES | 0 | 0 | 0 | 0 |

## D) Cost_R Percentiles (mode_session_bucket)
| run_label | scope | mode | session_bucket | trades | cost_R_mean | cost_R_p50 | cost_R_p75 | cost_R_p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUN_RANGE | mode_session_bucket | RANGE | ALL_ROWS | 18 | 0.018199 | 0.018214 | 0.018319 | 0.018564 |
| RUN_TREND | mode_session_bucket | TREND | MODE_SESSION | 16 | 0.018436 | 0.018409 | 0.018452 | 0.018543 |

## G) Opportunities by Hour UTC
| hour_utc | RANGE_opportunities | TREND_opportunities |
| --- | --- | --- |
| 0 |  | 2 |
| 1 |  | 0 |
| 2 |  | 4 |
| 3 |  | 4 |
| 4 |  | 2 |
| 5 |  | 1 |
| 6 |  | 3 |
| 7 |  | 3 |
| 8 |  | 6 |
| 9 |  | 1 |
| 10 |  | 6 |
| 11 |  | 3 |
| 12 |  | 6 |
| 13 |  | 1 |
| 14 |  | 2 |
| 15 |  | 4 |
| 16 |  | 4 |
| 17 |  | 1 |
| 18 |  | 4 |
| 19 |  | 3 |
| 20 |  | 2 |
| 21 |  | 1 |
| 22 |  | 0 |
| 23 |  | 1 |

## H) Hour Robust Perf
### RUN_RANGE
| hour_utc | trades | wins | losses | sum_R_pos | sum_R_neg_abs | pf | expectancy_R | winrate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 3 | 3 | 0 | 4.10962 | 0 |  | 1.369873 | 1 |
| 7 | 6 | 4 | 2 | 4.4225 | 2.22187 | 1.99044 | 0.366772 | 0.666667 |
| 16 | 4 | 3 | 1 | 4.88331 | 1.17653 | 4.150604 | 0.926695 | 0.75 |
| 17 | 5 | 2 | 3 | 2.25326 | 3.39138 | 0.664408 | -0.227624 | 0.4 |

### RUN_TREND
| hour_utc | trades | wins | losses | sum_R_pos | sum_R_neg_abs | pf | expectancy_R | winrate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 4 | 1 | 3 | 0.11671 | 1.58546 | 0.073613 | -0.367188 | 0.25 |
| 9 | 1 | 1 | 0 | 0.05697 | 0 |  | 0.05697 | 1 |
| 10 | 4 | 2 | 2 | 0.81883 | 0.6522 | 1.255489 | 0.041657 | 0.5 |
| 11 | 2 | 0 | 2 | 0 | 1.28907 | 0 | -0.644535 | 0 |
| 14 | 1 | 0 | 1 | 0 | 0.3547 | 0 | -0.3547 | 0 |
| 15 | 4 | 2 | 2 | 1.34918 | 0.62182 | 2.169728 | 0.18184 | 0.5 |

## Notes
- RUN_RANGE tiene `G_signals_by_hour_utc.csv` sin filas. En `diagnostics.md` se reporta que no hay SIGNAL_DETECTED con timestamp valido en signals para hourly G/F.
- RUN_RANGE usa denominador global de oportunidades en E: 112.
- RUN_TREND usa denominador global de oportunidades en E: 64.
- L/M corregidos en `scripts/diagnose_run.py` para ENTER-only: ahora `L_regime_segments.csv` y `M_regime_time_share.csv` ya no quedan vacios en runs forzados (se cierra el ultimo segmento con timestamp final disponible).
