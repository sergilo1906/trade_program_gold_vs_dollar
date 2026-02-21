# Edge Discovery Round 3 Plan

## Context

- objective: first real `candidates3` wave with minimal risk to existing pipeline.
- priority order:
  1. MR-Session Shock (Top 1): implemented end-to-end.
  2. Compression Breakout (Top 2): scaffolding + placeholders only in this iteration.

## Design choice (approved for this round)

- integration mode: **variant inside `strategy_family: VTM_VOL_MR`** (not a new family).
- reason:
  1. preserves current runner/reporting contracts.
  2. avoids extra strategy switch complexity in engine.
  3. enables fast falsifiable batch with minimal plumbing delta.

## MR-Session Shock MVP spec (implemented)

- config section: `vtm_vol_mr`
- mode flag: `signal_model: shock_session`
- parameters used:
  - `shock_threshold`
  - `atr_period`
  - `close_extreme_pct`
  - `entry_windows_utc` (mapped to canonical `entry_windows`)
  - `stop_atr`
  - `target_atr`
  - `holding_bars`
  - `max_trades_per_day` (top-level)
  - `cooldown_after_trade_bars` (top-level)

### Signal rule

- bar qualifies as shock if:
  - `bar_range = high - low >= shock_threshold * ATR`
- close extreme:
  - near low (`close <= low + close_extreme_pct * bar_range`) => contrarian **LONG**
  - near high (`close >= high - close_extreme_pct * bar_range`) => contrarian **SHORT**
- entry execution: next-open (existing engine behavior)

### Trade management

- stop distance: `stop_atr * ATR`
- target distance: `target_atr * ATR`
- TP set from next-open for distance consistency.
- time stop: existing `holding_bars` logic from VTM branch.

## Candidates created

Folder: `configs/edge_discovery_candidates3/`

- `mr_session_shock_london_t25_tp08.yaml`
- `mr_session_shock_london_t30_tp12.yaml`
- `mr_session_shock_nyopen_t25_tp08.yaml`
- `mr_session_shock_nyopen_t30_tp12.yaml`
- `mr_session_shock_uspm_t25_tp08.yaml`
- `mr_session_shock_uspm_t30_tp12.yaml`

## Compression Breakout scaffolding

Placeholders only (not executable yet):

- `configs/edge_discovery_candidates3_placeholders/compression_breakout_london_placeholder.yaml`
- `configs/edge_discovery_candidates3_placeholders/compression_breakout_nyopen_placeholder.yaml`

## Commands (round3)

### Smoke

```powershell
python scripts/run_edge_factory_batch.py --data data/xauusd_m5_test.csv --candidates-dir configs/edge_discovery_candidates3 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_round3_smoke --runs-root outputs/runs --resamples 500 --seed 42 --max-bars 4000 --gates-config configs/research_gates/default_edge_factory.yaml --stage smoke --snapshot-prefix edge_factory_round3_smoke
```

### Dev fast

```powershell
python scripts/run_edge_factory_batch.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates3 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_factory_round3_dev_fast --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 30000 --gates-config configs/research_gates/default_edge_factory.yaml --stage dev_fast --snapshot-prefix edge_factory_round3_dev_fast
```

### Expectancy audit

```powershell
python scripts/verify_expectancy_math.py --scoreboard outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv --scoreboard-fallback outputs/edge_factory_round3_dev_fast/edge_factory_scoreboard.csv --runs-root outputs/runs --out-dir docs/_snapshots/edge_factory_round3_expectancy_audit_20260221_2040
```

## Kill / promote criteria (round3)

- kill immediately if:
  - `trades < 20` in `dev_fast`
  - empty trades
  - expectancy <= 0 with weak PF
- promote to `dev_robust` only with:
  - `gate_all=true` under `dev_fast` gates
  - reasonable sample size (not single-trade artifacts)

