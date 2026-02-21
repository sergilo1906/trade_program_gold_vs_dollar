# Round 2 Candidate Rationale

| config | family | hypothesis | expected signal profile | kill criteria |
| --- | --- | --- | --- | --- |
| `config_edge_tf_simple_core_v1` | trend (V3) | trend-only + lighter structure filters should improve hit-rate vs strict legacy trend | medium frequency, session-concentrated | `trades<20` or (`expectancy<=0` and `pf<1`) |
| `config_edge_tf_simple_freq_v2` | trend (V3) | allowing 3 trades/session may raise sample size without changing edge logic | higher frequency than core, similar shape | retention rises but `expectancy` worsens strongly |
| `config_edge_tf_simple_entry_loose_v3` | trend (V3) | lower body ratio should capture more continuation bars | medium-high frequency | improved count but unstable (`crosses_zero=True` + weak PF) |
| `config_edge_tf_simple_rr_compact_v4` | trend (V3) | smaller RR target may improve realized win-rate in noisy intraday moves | medium frequency, higher win-rate expectation | PF remains <1 or expectancy <=0 after +20% cost |
| `config_edge_mr_vtm_core_v1` | MR (VTM) | moderate volatility-triggered MR with simple exits can produce stable intraday reversions | medium frequency, all-day except blocked window | `trades<20` or high CI ambiguity |
| `config_edge_mr_vtm_thr22_v2` | MR (VTM) | higher trigger threshold filters weak spikes, should trade less but cleaner | lower frequency than MR core | too few trades (<20) or no PF improvement |
| `config_edge_mr_vtm_stop12_v3` | MR (VTM) | wider stop could reduce stop-out noise on gold spikes | similar/medium frequency, lower stop-hit rate expected | worse expectancy + worse cost sensitivity |
| `config_edge_mr_vtm_hold4_v4` | MR (VTM) | shorter hold should reduce drift risk when reversion is slow | medium frequency, shorter duration | exits too early and collapses expectancy |

## Selection rules for Phase 4 (locked)

- Rank by: `expectancy_R desc`, then `pf desc`, then `trades desc`.
- Prefer candidates with `trades >= 30` for minimum power.
- Mark low-power if `trades < 30`; non-operable if `trades < 20`.
- Fragile if:
  - `crosses_zero=True` and low trades,
  - fails +20% cost (`PF<=1` or `expectancy<=0`),
  - hourly concentration with negative expectancy and `trades>=10`.
