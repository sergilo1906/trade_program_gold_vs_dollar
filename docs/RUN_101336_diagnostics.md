# Run Diagnostics

## Resolved Columns & Rules
- run_dir: `outputs/runs/20260218_101336`
- R column used: `r_multiple`
- mode column used: `mode`
- entry timestamp column used: `entry_time` (parsed as UTC; naive assumed UTC)
- signals timestamp column used: `ts` (parsed as UTC; naive assumed UTC)
- signals state column used (J): `state`
- events timestamp column used: `timestamp` (parsed as UTC; naive assumed UTC)
- session bucket source: `derived by hour (ASIA 00-07, MODE_SESSION 07-17, OFF_SESSION 17-24 UTC)`
- risk denominator source: `risk_amount`
- event type source for blocks: `event_type`
- opportunities denominator: `112` from `signals.event_type == SIGNAL_DETECTED`
- opportunities by hour source (G/F): `no_hourly_signal_detected`
- regime enter events found (L/M/N): `1`

## Warnings
- Signals timestamp unavailable/invalid for SIGNAL_DETECTED; fallback to events for hourly opportunities.
- No valid hourly SIGNAL_DETECTED rows found for G_signals_by_hour_utc.
- L_regime_segments: fewer than 2 regime enter events; no closed segments.
- M_regime_time_share: no L segments available.
- N_signals_by_regime: no SIGNAL_DETECTED rows in signals.

## A) Performance by Mode
| mode | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| RANGE | 2.3077 | 0.4933 | 0.6667 | 0.4933 | 18 |

## B) Performance by Session Bucket
| session_bucket | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| ASIA | inf | 1.3699 | 1.0000 | 1.3699 | 3 |
| MODE_SESSION | 2.7383 | 0.5907 | 0.7000 | 0.5907 | 10 |
| OFF_SESSION | 0.6644 | -0.2276 | 0.4000 | -0.2276 | 5 |

## C) Performance by Hour UTC (60m)
| hour_utc | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| 6 | inf | 1.3699 | 1.0000 | 1.3699 | 3 |
| 7 | 1.9904 | 0.3668 | 0.6667 | 0.3668 | 6 |
| 16 | 4.1506 | 0.9267 | 0.7500 | 0.9267 | 4 |
| 17 | 0.6644 | -0.2276 | 0.4000 | -0.2276 | 5 |

## D) Cost_R Percentiles
| scope | mode | session_bucket | hour_utc | trades | cost_R_mean | cost_R_p50 | cost_R_p75 | cost_R_p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mode_session_bucket | RANGE | ASIA |  | 3 | 0.0011 | 0.0013 | 0.0013 | 0.0013 |
| mode_session_bucket | RANGE | MODE_SESSION |  | 10 | 0.0010 | 0.0009 | 0.0010 | 0.0014 |
| mode_session_bucket | RANGE | OFF_SESSION |  | 5 | 0.0011 | 0.0011 | 0.0011 | 0.0012 |
| mode_session_bucket_hour | RANGE | ASIA | 6 | 3 | 0.0011 | 0.0013 | 0.0013 | 0.0013 |
| mode_session_bucket_hour | RANGE | MODE_SESSION | 7 | 6 | 0.0009 | 0.0009 | 0.0010 | 0.0010 |
| mode_session_bucket_hour | RANGE | MODE_SESSION | 16 | 4 | 0.0012 | 0.0012 | 0.0014 | 0.0015 |
| mode_session_bucket_hour | RANGE | OFF_SESSION | 17 | 5 | 0.0011 | 0.0011 | 0.0011 | 0.0012 |

## E) Blocks
| block_type | count | pct_of_opportunities | opportunities_denom | denominator_source |
| --- | --- | --- | --- | --- |
| SESSION_BLOCK | 89 | 0.7946 | 112 | signals.event_type == SIGNAL_DETECTED |
| COST_FILTER_BLOCK | 5 | 0.0446 | 112 | signals.event_type == SIGNAL_DETECTED |
| SHOCK_BLOCK | 0 | 0.0000 | 112 | signals.event_type == SIGNAL_DETECTED |
| MAX_TRADES | 0 | 0.0000 | 112 | signals.event_type == SIGNAL_DETECTED |

## F) Blocks by Hour UTC
| hour_utc | opportunities | SESSION_BLOCK_count | SESSION_BLOCK_pct | COST_FILTER_BLOCK_count | COST_FILTER_BLOCK_pct | SHOCK_BLOCK_count | SHOCK_BLOCK_pct | MAX_TRADES_count | MAX_TRADES_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 8 |  | 0 |  | 0 |  | 0 |  |
| 1 | 0 | 1 |  | 0 |  | 0 |  | 0 |  |
| 2 | 0 | 7 |  | 0 |  | 0 |  | 0 |  |
| 3 | 0 | 6 |  | 0 |  | 0 |  | 0 |  |
| 4 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 5 | 0 | 3 |  | 0 |  | 0 |  | 0 |  |
| 6 | 0 | 0 |  | 2 |  | 0 |  | 0 |  |
| 7 | 0 | 0 |  | 1 |  | 0 |  | 0 |  |
| 8 | 0 | 4 |  | 0 |  | 0 |  | 0 |  |
| 9 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 10 | 0 | 4 |  | 0 |  | 0 |  | 0 |  |
| 11 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 12 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 13 | 0 | 4 |  | 0 |  | 0 |  | 0 |  |
| 14 | 0 | 3 |  | 0 |  | 0 |  | 0 |  |
| 15 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 16 | 0 | 0 |  | 0 |  | 0 |  | 0 |  |
| 17 | 0 | 0 |  | 0 |  | 0 |  | 0 |  |
| 18 | 0 | 0 |  | 2 |  | 0 |  | 0 |  |
| 19 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 20 | 0 | 6 |  | 0 |  | 0 |  | 0 |  |
| 21 | 0 | 3 |  | 0 |  | 0 |  | 0 |  |
| 22 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |
| 23 | 0 | 5 |  | 0 |  | 0 |  | 0 |  |

## G) Signals by Hour UTC
_No data_

## H) Hour Robust Perf
| hour_utc | trades | wins | losses | sum_R_pos | sum_R_neg_abs | pf | expectancy_R | winrate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 3 | 3 | 0 | 4.1096 | 0.0000 |  | 1.3699 | 1.0000 |
| 7 | 6 | 4 | 2 | 4.4225 | 2.2219 | 1.9904 | 0.3668 | 0.6667 |
| 16 | 4 | 3 | 1 | 4.8833 | 1.1765 | 4.1506 | 0.9267 | 0.7500 |
| 17 | 5 | 2 | 3 | 2.2533 | 3.3914 | 0.6644 | -0.2276 | 0.4000 |

## I) Perf by regime_at_entry
| regime_at_entry | pf | expectancy_R | winrate | avg_R | trades |
| --- | --- | --- | --- | --- | --- |
| RANGE | 2.3077 | 0.4933 | 0.6667 | 0.4933 | 18 |

## J) Signals state counts
| scope | hour_utc | state | count |
| --- | --- | --- | --- |
| global |  | WAIT_M5_ENTRY | 318 |
| global |  | WAIT_H1_BIAS | 19 |
| global |  | IN_TRADE | 18 |
| hourly | 0 | WAIT_M5_ENTRY | 24 |
| hourly | 1 | WAIT_M5_ENTRY | 3 |
| hourly | 2 | WAIT_M5_ENTRY | 23 |
| hourly | 3 | WAIT_M5_ENTRY | 18 |
| hourly | 4 | WAIT_M5_ENTRY | 13 |
| hourly | 5 | WAIT_M5_ENTRY | 9 |
| hourly | 6 | WAIT_M5_ENTRY | 14 |
| hourly | 6 | IN_TRADE | 3 |
| hourly | 6 | WAIT_H1_BIAS | 2 |
| hourly | 7 | WAIT_M5_ENTRY | 13 |
| hourly | 7 | WAIT_H1_BIAS | 7 |
| hourly | 7 | IN_TRADE | 6 |
| hourly | 8 | WAIT_M5_ENTRY | 12 |
| hourly | 9 | WAIT_M5_ENTRY | 15 |
| hourly | 10 | WAIT_M5_ENTRY | 12 |
| hourly | 11 | WAIT_M5_ENTRY | 17 |
| hourly | 12 | WAIT_M5_ENTRY | 13 |
| hourly | 13 | WAIT_M5_ENTRY | 12 |
| hourly | 14 | WAIT_M5_ENTRY | 9 |
| hourly | 14 | WAIT_H1_BIAS | 1 |
| hourly | 15 | WAIT_M5_ENTRY | 15 |
| hourly | 16 | WAIT_M5_ENTRY | 8 |
| hourly | 16 | IN_TRADE | 4 |
| hourly | 16 | WAIT_H1_BIAS | 2 |
| hourly | 17 | WAIT_M5_ENTRY | 10 |
| hourly | 17 | IN_TRADE | 5 |
| hourly | 17 | WAIT_H1_BIAS | 5 |
| hourly | 18 | WAIT_M5_ENTRY | 6 |
| hourly | 19 | WAIT_M5_ENTRY | 15 |
| hourly | 20 | WAIT_M5_ENTRY | 20 |
| hourly | 20 | WAIT_H1_BIAS | 1 |
| hourly | 21 | WAIT_M5_ENTRY | 9 |
| hourly | 21 | WAIT_H1_BIAS | 1 |
| hourly | 22 | WAIT_M5_ENTRY | 13 |
| hourly | 23 | WAIT_M5_ENTRY | 15 |

## K) Regime event counts
| scope | hour_utc | event_type | count |
| --- | --- | --- | --- |
| global |  | REGIME_RANGE_ENTER | 1 |
| hourly | 14 | REGIME_RANGE_ENTER | 1 |

## L) Regime segments
_No data_

## M) Regime time share
_No data_

## N) Signals by regime
_No data_

## Outputs
- `outputs/runs/20260218_101336/diagnostics/A_perf_by_mode.csv`
- `outputs/runs/20260218_101336/diagnostics/B_perf_by_session_bucket.csv`
- `outputs/runs/20260218_101336/diagnostics/C_perf_by_hour_utc.csv`
- `outputs/runs/20260218_101336/diagnostics/D_costR_percentiles.csv`
- `outputs/runs/20260218_101336/diagnostics/E_blocks.csv`
- `outputs/runs/20260218_101336/diagnostics/F_blocks_by_hour_utc.csv`
- `outputs/runs/20260218_101336/diagnostics/G_signals_by_hour_utc.csv`
- `outputs/runs/20260218_101336/diagnostics/H_perf_by_hour_robust.csv`
- `outputs/runs/20260218_101336/diagnostics/I_perf_by_regime_at_entry.csv`
- `outputs/runs/20260218_101336/diagnostics/J_signals_state_counts.csv`
- `outputs/runs/20260218_101336/diagnostics/K_regime_event_counts.csv`
- `outputs/runs/20260218_101336/diagnostics/L_regime_segments.csv`
- `outputs/runs/20260218_101336/diagnostics/M_regime_time_share.csv`
- `outputs/runs/20260218_101336/diagnostics/N_signals_by_regime.csv`
- `outputs/runs/20260218_101336/diagnostics/diagnostics.md`
