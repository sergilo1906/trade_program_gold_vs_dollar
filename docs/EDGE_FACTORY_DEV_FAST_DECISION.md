# EDGE FACTORY DEV_FAST Decision (Round 3 / candidates3)

## 1) Command executed

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates3 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_round3_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 30000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_round3_dev_fast
```

## 2) Dataset and parameters

- data: `data_local/xauusd_m5_DEV_2021_2023.csv`
- stage: `dev_fast`
- resamples: `2000`
- seed: `42`
- max_bars: `30000`
- gates config: `configs/research_gates/default_edge_factory.yaml`
- rebuild-only used: **No** (full run completed)

## 3) Artifacts generated

- `outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv`
- `outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.md`
- `outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard_summary.json`
- `outputs/edge_factory_round3_dev_fast/edge_factory_manifest.json`
- snapshot:
  - `docs/_snapshots/edge_factory_round3_dev_fast_20260221_204029/`
  - includes `meta.json`

## 4) Scoreboard summary

- baseline_run_id: `20260221_204030`
- baseline_trades: `3`
- candidates: `6`
- run_ids_ok: `3`
- pass_count (`gate_all`): **0**

### Candidate outcome (dev_fast)

| candidate | status | trades | pf | expectancy_R | retention_vs_b4_pct | gate_all | key fail reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mr_session_shock_london_t25_tp08 | ok | 1 | inf | 0.63822 | 33.33 | false | trades<20, retention<50 |
| mr_session_shock_nyopen_t25_tp08 | ok | 1 | inf | 0.63822 | 33.33 | false | trades<20, retention<50 |
| mr_session_shock_uspm_t25_tp08 | ok | 1 | inf | 0.63822 | 33.33 | false | trades<20, retention<50 |
| mr_session_shock_london_t30_tp12 | failed | 0 | n/a | n/a | 0.00 | false | empty_trades |
| mr_session_shock_nyopen_t30_tp12 | failed | 0 | n/a | n/a | 0.00 | false | empty_trades |
| mr_session_shock_uspm_t30_tp12 | failed | 0 | n/a | n/a | 0.00 | false | empty_trades |

## 5) Expectancy audit

Command:

```powershell
python scripts/verify_expectancy_math.py --scoreboard outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv --scoreboard-fallback outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv --runs-root outputs/runs --out-dir docs/_snapshots/edge_factory_round3_expectancy_audit_20260221_2040
```

Result:
- `PIPELINE_BUG_SUSPECTED=YES`

Classification:
- **not a core pipeline mismatch**
- root cause is audit-tool handling of `PF=inf` rows (`inf - inf` => NaN delta, then `pf_match=False`)
- expectancy/trades/winrate match for non-empty rows; baseline row fully consistent.

## 6) Shortlist decision for dev_robust

### Promoted

- **None promoted** in this iteration (`dev_fast gate_all=0`).

### Watchlist (for next parameter tweak, not promotion)

1. `mr_session_shock_london_t25_tp08` (1 trade, positive R but sample too small)
2. `mr_session_shock_nyopen_t25_tp08` (same profile)
3. `mr_session_shock_uspm_t25_tp08` (same profile)

Reason:
- statistical power is insufficient (single-trade artifacts), so promotion would be overfitting risk.

## 7) Risks / limitations observed

1. Frequency is too low with current thresholds (`shock_threshold 2.5/3.0`, narrow windows, 1h buckets).
2. Baseline sample in this 30k slice is also small (`3 trades`), making retention gate strict.
3. Audit script false-positive when PF is infinite; needs robustness tweak before using as strict blocker.

## 8) Suggested next command (finalists-only policy kept)

No `dev_robust` run yet. First expand frequency on MR-Session Shock (keep strategy unchanged) and rerun `dev_fast`:

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates3 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_round3_dev_fast_r2 --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_round3_dev_fast_r2
```

## 9) GO / NO-GO (for tomorrow)

- **GO to continue round3 discovery**, **NO-GO to promote candidates to dev_robust yet**.

