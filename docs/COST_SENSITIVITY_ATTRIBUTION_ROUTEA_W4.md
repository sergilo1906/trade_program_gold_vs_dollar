# Cost Sensitivity Attribution

- source_per_trade: `outputs/posthoc_cost_stress/rolling_per_trade/20260219_153455_posthoc_per_trade.csv`
- method: post-hoc trade-set fixed attribution (factors 1.0, 1.2, 1.5)

## Top 10 trades by R loss (1.0 -> 1.2)
| trade_id | entry_time | mode | regime_at_entry | direction | exit_reason | r_base | r_p20 | delta_R_20 | r_p50 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 2025-12-12T08:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.849317 | 1.81918 | -0.030137 | 1.773975 | -0.075341 |
| 22 | 2026-01-06T08:30:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.107841 | -1.129409 | -0.021568 | -1.161761 | -0.05392 |
| 10 | 2025-12-09T14:15:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.106813 | -1.128176 | -0.021363 | -1.16022 | -0.053407 |
| 11 | 2025-12-11T14:10:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.900082 | 1.880098 | -0.019984 | 1.850123 | -0.049959 |
| 6 | 2025-11-28T14:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.9001 | 1.88012 | -0.01998 | 1.850149 | -0.04995 |
| 9 | 2025-12-05T14:50:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.097519 | -1.117023 | -0.019504 | -1.146279 | -0.048759 |
| 25 | 2026-01-12T08:50:00 | TREND | TREND | LONG | V3_EXIT_SESSION_END | -0.038014 | -0.057401 | -0.019387 | -0.086482 | -0.048468 |
| 14 | 2025-12-15T14:15:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.096631 | -1.115957 | -0.019326 | -1.144946 | -0.048315 |
| 3 | 2025-11-25T08:40:00 | TREND | TREND | SHORT | V3_EXIT_TP | 1.905475 | 1.886569 | -0.018905 | 1.858212 | -0.047263 |
| 20 | 2025-12-26T14:35:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.087599 | -1.105119 | -0.01752 | -1.131399 | -0.0438 |

## Top 10 trades by R loss (1.0 -> 1.5)
| trade_id | entry_time | mode | regime_at_entry | direction | exit_reason | r_base | r_p20 | delta_R_20 | r_p50 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 2025-12-12T08:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.849317 | 1.81918 | -0.030137 | 1.773975 | -0.075341 |
| 22 | 2026-01-06T08:30:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.107841 | -1.129409 | -0.021568 | -1.161761 | -0.05392 |
| 10 | 2025-12-09T14:15:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.106813 | -1.128176 | -0.021363 | -1.16022 | -0.053407 |
| 11 | 2025-12-11T14:10:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.900082 | 1.880098 | -0.019984 | 1.850123 | -0.049959 |
| 6 | 2025-11-28T14:05:00 | TREND | TREND | LONG | V3_EXIT_TP | 1.9001 | 1.88012 | -0.01998 | 1.850149 | -0.04995 |
| 9 | 2025-12-05T14:50:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.097519 | -1.117023 | -0.019504 | -1.146279 | -0.048759 |
| 25 | 2026-01-12T08:50:00 | TREND | TREND | LONG | V3_EXIT_SESSION_END | -0.038014 | -0.057401 | -0.019387 | -0.086482 | -0.048468 |
| 14 | 2025-12-15T14:15:00 | TREND | TREND | SHORT | V3_EXIT_SL | -1.096631 | -1.115957 | -0.019326 | -1.144946 | -0.048315 |
| 3 | 2025-11-25T08:40:00 | TREND | TREND | SHORT | V3_EXIT_TP | 1.905475 | 1.886569 | -0.018905 | 1.858212 | -0.047263 |
| 20 | 2025-12-26T14:35:00 | TREND | TREND | LONG | V3_EXIT_SL | -1.087599 | -1.105119 | -0.01752 | -1.131399 | -0.0438 |

## Aggregation by mode / regime_at_entry / exit_reason
| mode | regime_at_entry | exit_reason | trades | exp_R_base | exp_R_p20 | exp_R_p50 | delta_R_20 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND | TREND | V3_EXIT_TP | 8 | 1.913932 | 1.896719 | 1.870899 | -0.017213 | -0.043034 |
| TREND | TREND | V3_EXIT_SESSION_END | 3 | 0.666003 | 0.652405 | 0.632008 | -0.013598 | -0.033995 |
| TREND | TREND | V3_EXIT_SL | 27 | -1.064293 | -1.077152 | -1.09644 | -0.012859 | -0.032147 |

## Aggregation by hour (derived from entry_time)
- note: entry_time parsed and hour_utc derived.
| hour_utc | trades | exp_R_base | exp_R_p20 | exp_R_p50 | delta_R_20 | delta_R_50 |
| --- | --- | --- | --- | --- | --- | --- |
| 8.0 | 6.0 | 0.084787 | 0.066447 | 0.038937 | -0.01834 | -0.04585 |
| 14.0 | 19.0 | -0.443373 | -0.458363 | -0.480849 | -0.01499 | -0.037476 |
| 15.0 | 13.0 | -0.270083 | -0.280147 | -0.295242 | -0.010064 | -0.025159 |

## Artifacts
- `outputs/posthoc_cost_stress/cost_sensitivity_routeA_W4_top10_delta20.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_routeA_W4_top10_delta50.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_routeA_W4_by_mode_regime_exit.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_routeA_W4_by_hour.csv`
