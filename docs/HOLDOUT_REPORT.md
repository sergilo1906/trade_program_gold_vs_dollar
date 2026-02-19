# HOLDOUT Report

- run_id: `20260219_104745`
- run_dir: `outputs/runs/20260219_104745`

## KPIs
| run_id | pf | expectancy_R | trades | winrate |
| --- | --- | --- | --- | --- |
| 20260219_104745 | 1.019508 | 0.013004 | 44 | 0.363636 |

## Bootstrap CI
| run_id | n | mean | ci_low | ci_high | crosses_zero | resamples |
| --- | --- | --- | --- | --- | --- | --- |
| 20260219_104745 | 44 | 0.013004 | -0.402205 | 0.438432 | True | 5000 |

## Blocks (session/cost/shock/max_trades)
| block_type | count | pct_of_opportunities | opportunities_denom | denominator_source |
| --- | --- | --- | --- | --- |
| SESSION_BLOCK | 442 | 0.718699 | 615 | signals.event_type contains SIGNAL |
| MAX_TRADES | 62 | 0.100813 | 615 | signals.event_type contains SIGNAL |
| SHOCK_BLOCK | 60 | 0.097561 | 615 | signals.event_type contains SIGNAL |
| COST_FILTER_BLOCK | 1 | 0.001626 | 615 | signals.event_type contains SIGNAL |

## Hour Stability Summary
Negative expectancy hours with trades >= 10:
| hour_utc | trades | expectancy_R | pf | winrate |
| --- | --- | --- | --- | --- |
| 13.0 | 22.0 | -0.143829 | 0.8079 | 0.318182 |

Top hours by expectancy_R:
| hour_utc | trades | expectancy_R | pf | winrate |
| --- | --- | --- | --- | --- |
| 15.0 | 8.0 | 0.36164 | 1.684965 | 0.5 |
| 8.0 | 5.0 | 0.307276 | 1.692559 | 0.4 |
| 14.0 | 9.0 | -0.077009 | 0.89199 | 0.333333 |
| 13.0 | 22.0 | -0.143829 | 0.8079 | 0.318182 |
