# Cost Sensitivity Attribution

- source_per_trade: `outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv`
- method: post-hoc trade-set fixed attribution (factors 1.0, 1.2, 1.5)

## Top 10 trades by R loss (1.0 -> 1.2)
| trade_id | entry_time | mode | regime_at_entry | direction | exit_reason | r_base | r_p20 | delta_R_20 | r_p50 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 2025-11-27T13:10:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.163697 | -1.196437 | -0.03274 | -1.245546 | -0.081849 |
| 21 | 2025-12-22T13:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.846052 | 1.815262 | -0.03079 | 1.769077 | -0.076975 |
| 15 | 2025-12-12T08:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.849317 | 1.81918 | -0.030137 | 1.773975 | -0.075341 |
| 17 | 2025-12-15T13:10:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.148632 | -1.178358 | -0.029726 | -1.222947 | -0.074315 |
| 22 | 2025-12-23T13:15:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.143237 | -1.171884 | -0.028648 | -1.214855 | -0.071619 |
| 34 | 2026-01-15T13:05:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.136556 | -1.163868 | -0.027311 | -1.204835 | -0.068279 |
| 32 | 2026-01-13T13:10:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.882015 | 1.858418 | -0.023597 | 1.823022 | -0.058993 |
| 28 | 2026-01-06T13:20:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.116451 | -1.139741 | -0.02329 | -1.174677 | -0.058225 |
| 13 | 2025-12-09T13:35:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.113437 | -1.136124 | -0.022687 | -1.170155 | -0.056719 |
| 27 | 2026-01-06T08:30:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.107841 | -1.129409 | -0.021568 | -1.161761 | -0.05392 |

## Top 10 trades by R loss (1.0 -> 1.5)
| trade_id | entry_time | mode | regime_at_entry | direction | exit_reason | r_base | r_p20 | delta_R_20 | r_p50 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 2025-11-27T13:10:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.163697 | -1.196437 | -0.03274 | -1.245546 | -0.081849 |
| 21 | 2025-12-22T13:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.846052 | 1.815262 | -0.03079 | 1.769077 | -0.076975 |
| 15 | 2025-12-12T08:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.849317 | 1.81918 | -0.030137 | 1.773975 | -0.075341 |
| 17 | 2025-12-15T13:10:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.148632 | -1.178358 | -0.029726 | -1.222947 | -0.074315 |
| 22 | 2025-12-23T13:15:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.143237 | -1.171884 | -0.028648 | -1.214855 | -0.071619 |
| 34 | 2026-01-15T13:05:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.136556 | -1.163868 | -0.027311 | -1.204835 | -0.068279 |
| 32 | 2026-01-13T13:10:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.882015 | 1.858418 | -0.023597 | 1.823022 | -0.058993 |
| 28 | 2026-01-06T13:20:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.116451 | -1.139741 | -0.02329 | -1.174677 | -0.058225 |
| 13 | 2025-12-09T13:35:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.113437 | -1.136124 | -0.022687 | -1.170155 | -0.056719 |
| 27 | 2026-01-06T08:30:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.107841 | -1.129409 | -0.021568 | -1.161761 | -0.05392 |

## Aggregation by mode / regime_at_entry / exit_reason
| mode | regime_at_entry | exit_reason | trades | exp_R_base | exp_R_p20 | exp_R_p50 | delta_R_20 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND | TREND | V3_EXIT_TP | 15 | 1.910549 | 1.892659 | 1.865824 | -0.01789 | -0.044725 |
| TREND | TREND | V3_EXIT_SL | 27 | -1.084916 | -1.101899 | -1.127374 | -0.016983 | -0.042458 |
| TREND | TREND | V3_EXIT_SESSION_END | 2 | 0.603337 | 0.588236 | 0.565585 | -0.015101 | -0.037752 |

## Aggregation by hour (derived from entry_time)
- note: entry_time parsed and hour_utc derived.
| hour_utc | trades | exp_R_base | exp_R_p20 | exp_R_p50 | delta_R_20 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- |
| 8.0 | 5.0 | 0.307275 | 0.286373 | 0.255021 | -0.020902 | -0.052255 |
| 13.0 | 22.0 | -0.143828 | -0.163503 | -0.193015 | -0.019675 | -0.049187 |
| 14.0 | 9.0 | -0.077008 | -0.09241 | -0.115512 | -0.015402 | -0.038504 |
| 15.0 | 8.0 | 0.361638 | 0.351497 | 0.336285 | -0.010141 | -0.025353 |

## Artifacts
- `outputs/posthoc_cost_stress/cost_sensitivity_top10_delta20.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_top10_delta50.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_by_mode_regime_exit.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_by_hour.csv`
