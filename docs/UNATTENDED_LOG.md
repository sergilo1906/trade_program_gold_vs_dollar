# Unattended Execution Log

- Started: 2026-02-19T08:33:25Z

## Phase 0 - Inventory

### 0.1 Config listing command output
Command: `Get-ChildItem configs -File | Sort-Object Name | Format-Table -AutoSize`

```


    Directorio: C:\Users\Sergi\OneDrive\Escritorio\App Oro Cork\configs


Mode          LastWriteTime Length Name                          
----          ------------- ------ ----                          
-a---- 18/02/2026     21:04   3009 config.yaml                   
-a---- 18/02/2026     10:12   2805 config_ablation_nofilters.yaml
-a---- 18/02/2026     10:12   2808 config_ablation_range.yaml    
-a---- 18/02/2026     10:12   2808 config_ablation_trend.yaml    
-a---- 18/02/2026     10:12   2808 config_RANGE.yaml             
-a---- 18/02/2026     10:12    837 config_target_4_8.yaml        
-a---- 18/02/2026     10:12   2808 config_TREND.yaml             
-a---- 18/02/2026     21:04   3153 config_v3_AUTO.yaml           
-a---- 18/02/2026     22:10   2712 config_v3_AUTO_EXP_A.yaml     
-a---- 18/02/2026     22:10   2746 config_v3_AUTO_EXP_B.yaml     
-a---- 18/02/2026     22:10   2777 config_v3_AUTO_EXP_C.yaml     
-a---- 18/02/2026     21:04   3154 config_v3_RANGE.yaml          
-a---- 18/02/2026     21:04   3154 config_v3_TREND.yaml          
-a---- 17/02/2026     22:04     77 iter1.yaml                    
-a---- 17/02/2026     22:04     77 iter2.yaml
```

### 0.2 Base config output
Command: `Get-Content configs/config_v3_AUTO.yaml`

```yaml
output_dir: output
runs_output_dir: outputs/runs

starting_balance: 10000.0
risk_per_trade_pct: 0.005

# Indicator periods
ema_h1_fast: 50
ema_h1_slow: 200
ema_m15: 20
ema_m5: 20
rsi_period_m15: 14
atr_period: 14

# H1 bias core
h1_bias_slope_lookback: 3
h1_bias_atr_mult: 0.10
h1_min_sep_atr_mult: 0.25

# Regime detector (v2.0)
h1_slope_min_atr_mult: 0.05
h1_range_max_sep_atr_mult: 0.20
h1_range_max_slope_atr_mult: 0.05
atr_rel_lookback: 20
atr_rel_trend_min: 1.05
atr_rel_range_max: 0.95
atr_rel_dead_max: 0.70
regime_trend_enter_score: 3
regime_trend_exit_score: 2
regime_range_enter_score: 3
regime_range_exit_score: 2
trend_min_bars_m15: 4
range_min_bars_m15: 4

# M15 confirmation / M5 entry (trend motor)
confirm_valid_m15_bars: 3
bos_lookback: 5
body_ratio: 0.70
wick_ratio_max: 0.20
rsi_pullback_long_max: 35
rsi_recover_long_min: 40
rsi_pullback_short_min: 65
rsi_recover_short_max: 60
max_trades_per_day: 2

# Shock filter
shock_threshold: 3.0
shock_cooldown_bars: 12

# Risk and trade management
swing_lookback: 6
atr_floor_mult: 0.80
sl_buffer_mult: 0.10
tp1_r: 1.5
partial_pct: 0.50
trailing_mult: 2.5
trailing_mult_phase1: 2.0
trailing_mult_phase2: 1.0
be_after_r: 2.0
time_stop_bars: 12
time_stop_min_r: 0.50
cooldown_after_trade_bars: 6

# Strategy v3.0 (disabled by default)
enable_strategy_v3: true
v3_breakout_N1: 20
v3_atr_period_M: 14
v3_k_trend: 1.05
v3_k_range: 0.95
v3_atr_sl_trend: 1.2
v3_rr_trend: 2.0
v3_rsi_period: 14
v3_atr_sl_range: 1.0
v3_rr_range: 1.5
max_trades_per_session: 1
close_at_session_end: true

# Range motor
k_atr_range: 1.2
range_reject_wick_min: 0.45
range_body_min: 0.45
range_rsi_long_max: 40
range_rsi_short_min: 60
range_sl_atr_buffer: 0.5
range_touch_ttl_m5_bars: 12

# Execution costs
spread_usd: 0.41
slippage_usd: 0.05
cost_max_atr_mult: 0.25
cost_max_sl_frac: 0.15
cost_max_tp_frac_range: 0.20
cost_mult_trend_session: 1.0
cost_mult_off_session: 1.2
cost_mult_asia: 1.5

# Ablation / diagnostics
ablation_force_regime: AUTO  # AUTO | TREND | RANGE | NO_TRADE
ablation_disable_cost_filter: false
ablation_disable_session_gating: false

# Risk governance
daily_stop_r: -2.0
daily_stop_pct: -0.015
weekly_stop_r: -5.0
weekly_stop_pct: -0.04
loss_streak_limit: 3
loss_streak_block_hours: 24

# Legacy session (forced close compatibility)
force_session_close: false
session:
  mon_thu_start: "07:00"
  mon_thu_end: "17:00"
  fri_start: "07:00"
  fri_end: "15:00"

# Regime session gating (UTC)
trend_sessions:
  - "08:00-12:00"
  - "13:00-16:00"
range_sessions:
  - "06:00-08:00"
  - "16:00-19:00"
blocked_windows:
  - "21:50-22:10"

progress_every_days: 5
stdout_trade_events: false

# Year test mode: last_365_days | last_12_full_calendar_months
year_test_mode: last_365_days

# Monte Carlo
monte_carlo_sims: 300
monte_carlo_seed: 42

# One-at-a-time sensitivity values
sensitivity:
  trailing_mult: [2.0, 2.5, 3.0]
  body_ratio: [0.65, 0.70, 0.75]
  shock_threshold: [2.5, 3.0, 3.5]
  wick_ratio_max: [0.15, 0.20, 0.25]
  bos_lookback: [5, 7, 10]
```

### 0.3 Template search output
Command: `Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Name -match 'plantillas|mejoradas' -or $_.FullName -match '_templates' } | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize`

```

FullName                                                                              Length LastWriteTime      
--------                                                                              ------ -------------      
C:\Users\Sergi\OneDrive\Escritorio\App Oro Cork\docs\TODO_ZIP_PLANTILLAS_MEJORADAS.md    588 16/02/2026 22:55:28
```

### 0.4 Template zip status
- Expected template zip: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/_templates/plantillas_mejoradas.zip`
- Status: NOT FOUND
- Action: continuing without templates and documenting status.

## Phase 1 - HOLDOUT Split

- logged_at_utc: 2026-02-19T08:34:43Z
- command: `python scripts/make_holdout_split.py`

### Validation FULL

- file: `data/xauusd_m5_backtest_ready.csv`
- rows: 100000
- min_timestamp: 2024-09-17 14:00:00
- max_timestamp: 2026-02-16 19:25:00

First 3 rows:

```
          timestamp     open     high      low    close  volume
2024-09-17 14:00:00 2573.575 2577.395 2573.575 2576.435       5
2024-09-17 14:05:00 2576.425 2578.795 2575.925 2578.245       5
2024-09-17 14:10:00 2578.278 2580.915 2578.185 2580.635       5
```

Last 3 rows:

```
          timestamp     open     high      low    close  volume
2026-02-16 19:15:00 4990.785 4996.025 4990.415 4991.345       5
2026-02-16 19:20:00 4991.365 4992.015 4990.619 4991.345       5
2026-02-16 19:25:00 4991.365 4991.785 4990.148 4990.375       4
```

### Validation DEV80

- file: `data/xauusd_m5_DEV80.csv`
- rows: 80000
- min_timestamp: 2024-09-17 14:00:00
- max_timestamp: 2025-11-03 20:50:00

First 3 rows:

```
          timestamp     open     high      low    close  volume
2024-09-17 14:00:00 2573.575 2577.395 2573.575 2576.435       5
2024-09-17 14:05:00 2576.425 2578.795 2575.925 2578.245       5
2024-09-17 14:10:00 2578.278 2580.915 2578.185 2580.635       5
```

Last 3 rows:

```
          timestamp     open     high      low    close  volume
2025-11-03 20:40:00 4009.145 4010.155 4006.915 4008.895       5
2025-11-03 20:45:00 4008.935 4009.625 4007.745 4008.785       5
2025-11-03 20:50:00 4008.885 4011.965 4008.885 4011.355       5
```

### Validation HOLDOUT20

- file: `data/xauusd_m5_HOLDOUT20.csv`
- rows: 20000
- min_timestamp: 2025-11-03 20:55:00
- max_timestamp: 2026-02-16 19:25:00

First 3 rows:

```
          timestamp     open     high      low    close  volume
2025-11-03 20:55:00 4011.325 4011.825 4008.955 4010.105       5
2025-11-03 21:00:00 4010.105 4010.105 4007.335 4009.265       5
2025-11-03 21:05:00 4009.219 4009.725 4005.025 4006.065       5
```

Last 3 rows:

```
          timestamp     open     high      low    close  volume
2026-02-16 19:15:00 4990.785 4996.025 4990.415 4991.345       5
2026-02-16 19:20:00 4991.365 4992.015 4990.619 4991.345       5
2026-02-16 19:25:00 4991.365 4991.785 4990.148 4990.375       4
```


## Phase 2 - Walk Forward

- DEV rows: 80000
- Started UTC: 2026-02-19T08:37:08Z


### Phase 2.1 - Fold2 recovery
- Fold2 train EXP_A run_id: `20260219_101829`
- Fold2 train EXP_B run_id: `20260219_102723`
- Fold2 train EXP_C run_id: `20260219_103558`
- Fold2 winner: `EXP_C`
- Fold2 VAL run_id: `20260219_104443`
- Updated: `outputs/wfa/wfa_train_runs.csv`, `outputs/wfa/wfa_val_runs.csv`, `outputs/wfa/wfa_summary.json`, `docs/WALK_FORWARD_RESULTS.md`

## Phase 10 - Route B Pivot (UNATTENDED)

- logged_at_utc: 2026-02-19T16:56:00Z
- template_zip_status: missing `./_templates/plantillas_mejoradas.zip`
- disk_free_gb_after_pivot_runs: `3.37`

### 10.1 Inputs analyzed (W4 fragility context)
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA_h13_h8.csv`
- `docs/COST_SENSITIVITY_ATTRIBUTION_ROUTEA_W4.md`
- W4 diagnostics from routeA runs (`outputs/runs/20260219_153455/diagnostics/*`, `outputs/runs/20260219_155141/diagnostics/*`)

### 10.2 Pivot candidate configs created
- `configs/config_v3_PIVOT_B1.yaml`
- `configs/config_v3_PIVOT_B2.yaml`
- `configs/config_v3_PIVOT_B3.yaml`
- `configs/config_v3_PIVOT_B4.yaml`

### 10.3 New/updated scripts
- New: `scripts/run_pivot_candidates.py`
- Patch: `scripts/run_pivot_candidates.py` (JSON serialization fix for numpy scalars in summary output)
- Patch: `scripts/run_pivot_candidates.py` (ranking update to enforce trade-loss control gate: overfilter >35% penalized before winner selection)

### 10.4 Commands executed
- `python scripts/run_pivot_candidates.py`
  - note: long run completed evaluations but failed at final JSON write (`TypeError: Object of type int64 is not JSON serializable`).
- `python -m py_compile scripts/run_pivot_candidates.py`
- `python scripts/v3_qa_check_param.py 20260219_164110 20260219_164425 20260219_164706 20260219_165006 --output docs/PIVOT_B4_QA.csv`
- score/doc recovery from generated csv:
  - `python` inline script to write:
    - `docs/PIVOT_SCOREBOARD.md`
    - `outputs/rolling_holdout_pivot/pivot_scoreboard_summary.json`

### 10.5 Route B run_ids by candidate
- B1: `20260219_160711`, `20260219_161020`, `20260219_161309`, `20260219_161610`
- B2: `20260219_161907`, `20260219_162157`, `20260219_162422`, `20260219_162708`
- B3: `20260219_162948`, `20260219_163238`, `20260219_163509`, `20260219_163817`
- B4 (winner): `20260219_164110`, `20260219_164425`, `20260219_164706`, `20260219_165006`

### 10.6 Outputs generated
- `outputs/rolling_holdout_pivot/pivot_scoreboard.csv`
- `outputs/rolling_holdout_pivot/pivot_scoreboard_summary.json`
- `outputs/rolling_holdout_pivot/config_v3_PIVOT_B1/rolling_holdout_runs.csv`
- `outputs/rolling_holdout_pivot/config_v3_PIVOT_B2/rolling_holdout_runs.csv`
- `outputs/rolling_holdout_pivot/config_v3_PIVOT_B3/rolling_holdout_runs.csv`
- `outputs/rolling_holdout_pivot/config_v3_PIVOT_B4/rolling_holdout_runs.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B1.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B2.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B3.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_config_v3_PIVOT_B4.csv`
- `docs/PIVOT_SCOREBOARD.md`
- `docs/PIVOT_B4_QA.csv`

### 10.7 Route B conclusion
- winner candidate under acceptance gates + trade-loss control: `config_v3_PIVOT_B4`
- +20% post-hoc: `4/4` windows pass (`PF > 1` and `expectancy_R > 0`)
- W4 +20% (`run_id 20260219_165006`): PF `1.076243`, expectancy_R `0.049967`, trades `42`
- global trade retention: `95.24%` (no overfilter flag)
- decision: continue with Route B base (`GO` for pivot baseline)

## Phase 3-5 Summary
- logged_at_utc: 2026-02-19T11:03:12Z
- HOLDOUT run_id: `20260219_104745`
- COST +20 run_id: `20260219_105305`
- COST +50 run_id: `20260219_105707`
- QA outputs: `docs/WFA_QA.csv`, `docs/HOLDOUT_QA.csv`
- Reports: `docs/HOLDOUT_REPORT.md`, `docs/COST_STRESS.md`, `docs/GO_NO_GO.md`, `docs/UNATTENDED_SUMMARY.md`

## Phase 4 - Cost Stress

- First rg attempt with Windows wildcard failed (os error 123); rerun used: `rg -n "cost|spread|slippage|commission|multiplier" configs src/xauusd_bot -g "*.yaml" -g "*.py"`
- Simple knobs detected: `spread_usd`, `slippage_usd` and session cost multipliers in config/engine.
- Stress configs created: `configs/config_v3_AUTO_EXP_B_COSTP20.yaml`, `configs/config_v3_AUTO_EXP_B_COSTP50.yaml`
- Runs: base `20260219_104745`, +20 `20260219_105305`, +50 `20260219_105707`

## Post-run hardening

- `scripts/walk_forward_windows.py` patched to avoid duplicated winner columns during markdown rendering.
- Added dedup safeguards in `_md_table` and bounded exception text in fold notes.
- Validation:
  - `python -m py_compile scripts/walk_forward_windows.py`
  - `python scripts/wfa_rebuild_results.py`

## Phase 6 - Post-hoc Cost Stress (trade-set fixed) + Rolling Holdouts

- logged_at_utc: 2026-02-19T14:28:30Z
- disk_free_gb_before_rolling: `8.13` (no prune needed)
- template_zip_status: missing `./_templates/plantillas_mejoradas.zip`

### 6.1 Trades inspection (base HOLDOUT run)
- run_dir: `outputs/runs/20260219_104745`
- trades.csv columns:
  - `trade_id, mode, regime_at_entry, direction, entry_time, entry_price, sl, tp, exit_time, exit_price, exit_reason, r_multiple, spread, entry_mid, exit_mid, size, closed_size, risk_amount, pnl, mae_r, mfe_r, tp1_hit, bars_in_trade, minutes_in_trade, cost_multiplier`
- detected cost model formula:
  - `gross_from_mid_minus_net`
  - `pnl_gross = (exit_mid - entry_mid) * sign(direction) * closed_size`
  - `cost = pnl_gross - pnl(net)`
  - `r_posthoc = (pnl_gross - factor*cost) / risk_amount`

### 6.2 New scripts created
- `scripts/posthoc_cost_stress.py`
- `scripts/rolling_holdout_eval.py`

### 6.3 Commands executed
- `python scripts/posthoc_cost_stress.py --run-dir outputs/runs/20260219_104745 --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
- `python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_B.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout --resamples 5000 --seed 42`
- `python scripts/v3_qa_check_param.py 20260219_141334 20260219_141728 20260219_142049 20260219_142432 --output docs/ROLLING_HOLDOUT_QA.csv`

### 6.4 Outputs generated
- post-hoc stress:
  - `outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
  - `outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv`
  - `outputs/posthoc_cost_stress/posthoc_cost_stress_meta.json`
  - `docs/POSTHOC_COST_STRESS.md`
- rolling holdout:
  - `outputs/rolling_holdout/rolling_holdout_runs.csv`
  - `outputs/rolling_holdout/rolling_holdout_summary.json`
  - `docs/ROLLING_HOLDOUT.md`
  - `docs/ROLLING_HOLDOUT_QA.csv`

### 6.5 Rolling run_ids (OOS windows)
- `W1`: `20260219_141334`
- `W2`: `20260219_141728`
- `W3`: `20260219_142049`
- `W4`: `20260219_142432`

### 6.6 Notes
- Initial PowerShell heredoc quoting failed for python inline (`python - <<'PY'`); switched to PowerShell-compatible here-string (`@' ... '@ | python -`).
- Rolling bootstrap ran at 5000 resamples for all windows (no fallback required).

## Phase 7 - Batch post-hoc stress + cost attribution

- logged_at_utc: 2026-02-19T15:05:00Z
- template_zip_status: missing `./_templates/plantillas_mejoradas.zip`

### 7.1 New scripts created
- `scripts/posthoc_cost_stress_batch.py`
- `scripts/cost_sensitivity_attribution.py`

### 7.2 Commands executed
- `python -m py_compile scripts/posthoc_cost_stress.py scripts/posthoc_cost_stress_batch.py scripts/cost_sensitivity_attribution.py`
- `python scripts/posthoc_cost_stress.py --run-dir outputs/runs/20260219_104745 --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/posthoc_cost_stress.csv`
- `python scripts/posthoc_cost_stress_batch.py --runs 20260219_141334 20260219_141728 20260219_142049 20260219_142432 --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- `python scripts/cost_sensitivity_attribution.py --per-trade outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv --output docs/COST_SENSITIVITY_ATTRIBUTION.md`

### 7.3 Outputs generated
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_summary.json`
- `outputs/posthoc_cost_stress/rolling_per_trade/20260219_141334_posthoc_per_trade.csv`
- `outputs/posthoc_cost_stress/rolling_per_trade/20260219_141728_posthoc_per_trade.csv`
- `outputs/posthoc_cost_stress/rolling_per_trade/20260219_142049_posthoc_per_trade.csv`
- `outputs/posthoc_cost_stress/rolling_per_trade/20260219_142432_posthoc_per_trade.csv`
- `docs/COST_SENSITIVITY_ATTRIBUTION.md`
- `outputs/posthoc_cost_stress/cost_sensitivity_top10_delta20.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_top10_delta50.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_by_mode_regime_exit.csv`
- `outputs/posthoc_cost_stress/cost_sensitivity_by_hour.csv`

### 7.4 Notes
- First batch execution failed due import path (`ModuleNotFoundError: No module named 'scripts'`); fixed with robust local import fallback in `scripts/posthoc_cost_stress_batch.py`.
- `docs/UNATTENDED_SUMMARY.md` reviewed for duplicate header/section blocks; no duplicates found, no factual edits required.

## Phase 8 - Decision synthesis (analysis only)

- logged_at_utc: 2026-02-19T15:18:00Z
- template_zip_status: missing `./_templates/plantillas_mejoradas.zip`

### 8.1 Artifacts read
- `outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv`
- `docs/COST_SENSITIVITY_ATTRIBUTION.md`
- `docs/GO_NO_GO.md`
- `docs/UNATTENDED_SUMMARY.md`

### 8.2 Commands executed
- `python` summary check for rolling robustness by factor (PF>1 / expectancy_R>0 / both).

### 8.3 Docs updated
- `docs/GO_NO_GO.md`
  - Added decision-phase section with rolling post-hoc robustness (+20/+50), attribution highlights, and Route A/Route B proposals.
- `docs/UNATTENDED_SUMMARY.md`
  - Added rolling post-hoc robustness summary and concise decision routes.

## Phase 9 - Route A implementation and validation

- logged_at_utc: 2026-02-19T16:00:00Z
- template_zip_status: missing `./_templates/plantillas_mejoradas.zip`

### 9.1 Code changes (minimal, config-driven, reversible)
- `src/xauusd_bot/configuration.py`
  - Added config defaults/validation for:
    - `trade_filter.hour_blacklist_utc`
    - `trade_filter.hour_whitelist_utc`
    - `cost_gate_overrides_by_hour.<hour>.max_cost_multiplier`
- `src/xauusd_bot/engine.py`
  - Added hour trade filter (whitelist/blacklist) pretrade:
    - event/log rule ids: `HOUR_BLACKLIST`, `HOUR_NOT_IN_WHITELIST`
  - Added hour-specific cost gate override pretrade:
    - event/log rule id: `COST_GATE_OVERRIDE_HOUR`
  - Defaults keep old behavior when config is empty.
- `src/xauusd_bot/reporting.py`
  - Extended `block_summary` to include new rule counters.
- `scripts/diagnose_run.py`
  - Added diagnostics outputs:
    - `O_trades_blocked_by_rule.csv`
    - `P_trades_blocked_by_hour.csv`
  - Added markdown sections O/P in diagnostics report.

### 9.2 Configs created
- `configs/config_v3_ROUTE_A.yaml` (initial)
  - `hour_blacklist_utc: [13]`
  - `cost_gate_overrides_by_hour: {13: {max_cost_multiplier: 1.0}}`
- `configs/config_v3_ROUTE_A_H13_H8.yaml` (extension)
  - `hour_blacklist_utc: [8, 13]`
  - `cost_gate_overrides_by_hour: {8: {max_cost_multiplier: 1.0}, 13: {max_cost_multiplier: 1.0}}`

### 9.3 Commands executed
- `python -m py_compile src/xauusd_bot/configuration.py src/xauusd_bot/engine.py src/xauusd_bot/reporting.py scripts/diagnose_run.py`
- `python scripts/run_and_tag.py --data data/sample_m5.csv --config configs/config_v3_ROUTE_A.yaml --runs-root outputs/runs` (smoke run)
- `python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_ROUTE_A.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_routeA --resamples 5000 --seed 42`
- `python scripts/posthoc_cost_stress_batch.py --runs 20260219_152419 20260219_152817 20260219_153128 20260219_153455 --window-map-csv outputs/rolling_holdout_routeA/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA.csv`
- `python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_ROUTE_A_H13_H8.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_routeA_h13_h8 --report docs/ROLLING_HOLDOUT_ROUTEA_H13_H8.md --resamples 5000 --seed 42`
- `python scripts/posthoc_cost_stress_batch.py --runs 20260219_154058 20260219_154459 20260219_154802 20260219_155141 --window-map-csv outputs/rolling_holdout_routeA_h13_h8/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA_h13_h8.csv`
- `python scripts/v3_qa_check_param.py 20260219_152419 20260219_152817 20260219_153128 20260219_153455 --output docs/ROUTEA_QA.csv`
- `python scripts/v3_qa_check_param.py 20260219_154058 20260219_154459 20260219_154802 20260219_155141 --output docs/ROUTEA_H13_H8_QA.csv`

### 9.4 Route A run_ids and outcomes
- Route A initial (`config_v3_ROUTE_A.yaml`) run_ids:
  - `W1=20260219_152419`, `W2=20260219_152817`, `W3=20260219_153128`, `W4=20260219_153455`
  - post-hoc +20/+50 pass windows: `3/4` (W4 fails)
- Route A extension (`config_v3_ROUTE_A_H13_H8.yaml`) run_ids:
  - `W1=20260219_154058`, `W2=20260219_154459`, `W3=20260219_154802`, `W4=20260219_155141`
  - post-hoc +20/+50 pass windows: `3/4` (W4 fails, worse than initial)

### 9.5 W4 acceptance check (vs baseline W4 trades=44)
- Initial Route A W4 (`20260219_153455`):
  - +20%: PF `0.589845`, expectancy_R `-0.314530` (fail)
  - trades retained: `38/44 = 86.36%`
- Extension Route A W4 (`20260219_155141`):
  - +20%: PF `0.521906`, expectancy_R `-0.385963` (fail)
  - trades retained: `32/44 = 72.73%`

### 9.6 Decision
- Route A cannot make W4 robust under +20% post-hoc cost stress.
- Final recommendation moved to Route B pivot (strategy-base change path).


### Phase 2.1 - Fold2 recovery
- Fold2 train EXP_A run_id: `20260219_101829`
- Fold2 train EXP_B run_id: `20260219_102723`
- Fold2 train EXP_C run_id: `20260219_103558`
- Fold2 winner: `EXP_C`
- Fold2 VAL run_id: `20260219_104443`
- Updated: `outputs/wfa/wfa_train_runs.csv`, `outputs/wfa/wfa_val_runs.csv`, `outputs/wfa/wfa_summary.json`, `docs/WALK_FORWARD_RESULTS.md`


## Phase 11 - GitHub public repo bootstrap

- logged_at_utc: 2026-02-19T17:25:00Z
- requested_repo_name: `trade_program_gold_vs_dollar`
- project_root_detected: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork`

### 11.1 Safety and ignore setup
- Added `.gitignore` for Python caches/venv, logs, local env files, heavy outputs, and temp generated datasets.
- Ignore decisions:
  - ignored: `outputs/`, `output*/`, `data/tmp_rolling/`, `data/tmp_wfa/`
  - tracked: main `data/*.csv` files for reproducibility.
- Secret scan executed with `rg` patterns for common tokens/keys.
- Result: no actionable secrets detected in project code/config/docs; only false positives on variable names and reference template text.

### 11.2 Templates ZIP status
- expected: `./_templates/plantillas_mejoradas.zip`
- status: MISSING
- documented in `README.md` and this log.

### 11.3 Git bootstrap commands
- `git init -b main`
- `python -m compileall -q src scripts tests`
- `git add -A`
- `git commit -m "chore: initial import"`
- `gh --version`
- `gh auth status`
- `gh repo create trade_program_gold_vs_dollar --public --source=. --remote=origin --push`

### 11.4 GitHub creation/push result
- `gh` is installed, but authentication is missing (`gh auth status` not logged in).
- repo create/push blocked by auth requirement.
- local repository initialized and first commit created successfully.

### 11.5 Files added for ongoing push flow
- `scripts/git_autopush.ps1`
- `scripts/update_latest_commit.py`
- `.github/workflows/ci.yml`
- `docs/LATEST_COMMIT.md`


### 11.6 Autopush validation and fix
- Initial `scripts/git_autopush.ps1` run failed due PowerShell here-string terminator parsing.
- Script fixed to build markdown content with array join instead of here-string.
- Validation run:
  - `powershell -ExecutionPolicy Bypass -File scripts/git_autopush.ps1`
  - produced commits: `d8cff81` (code change), `6d68c61` (latest marker update)
  - push still blocked because `origin` is not configured.


## Phase 12 - GitHub publish attempt (second pass)

- logged_at_utc: 2026-02-19T17:12:00Z
- quick audit:
  - git initialized: yes (`main`)
  - `outputs/` size: ~9325.79 MB
  - `data/` size: ~32.89 MB
  - secret scan: no actionable secrets; only false positives on variable names/docs text
  - key/env file scan: only certifi bundle under `.venv`, no project `.env`/private key files

### 12.1 GitHub CLI checks
- `gh --version`: installed (`2.51.0`)
- `gh auth status`: not logged in
- attempted `gh auth login --hostname github.com --git-protocol https --web`: timed out in unattended terminal
- result: cannot create/push public repo until interactive login is completed by user session

### 12.2 Hardening updates
- `.gitignore` updated with generic `output*/`
- Added VS Code task: `.vscode/tasks.json` (`Git: Autopush`)
- README updated with quick autopush command and exact gh login/create commands

### 12.3 Final create/push attempt
- `gh repo create trade_program_gold_vs_dollar --public --source=. --remote=origin --push`
- result: blocked by missing `gh auth login`.


## Phase 13 - GitHub repo created and push unblocked

- logged_at_utc: 2026-02-19T17:30:16Z
- github_repo: `https://github.com/sergilo1906/trade_program_gold_vs_dollar`
- remote: `origin https://github.com/sergilo1906/trade_program_gold_vs_dollar.git`

### 13.1 Auth and scope resolution
- Initial push failed because token lacked `workflow` scope when trying to create `.github/workflows/ci.yml`.
- User re-authenticated `gh` and granted `workflow` scope.
- Successful push command:
  - `git push origin main`

### 13.2 Final publish state
- Branch `main` is now published remotely.
- CI workflow file is included in remote history.
- Ongoing one-command flow is enabled via:
  - `powershell -ExecutionPolicy Bypass -File scripts/git_autopush.ps1 -Message "<msg>"`


## Phase 14 - External long-history dataset integrated (2010-2023)

- logged_at_utc: 2026-02-19T18:09:12Z
- source_file: `c:/Users/Sergi/AppData/Local/Temp/8cdd5b57-94ea-429b-ae2b-337f70d37fc2_XAUUSD_2010-2023.csv.zip.fc2/XAUUSD_2010-2023.csv`
- output_file: `data/xauusd_m5_2010_2023_backtest_ready.csv`
- normalization_script: `scripts/prepare_external_m5_csv.py`

### 14.1 Normalization result
- rows_out: `986004`
- range: `2010-01-03 18:00:00` -> `2023-12-29 16:55:00`
- unique_days: `4353`
- median_delta_minutes: `5.00`
- schema_out: `timestamp,open,high,low,close,volume`
- dropped_na_rows: `0`
- dropped_duplicate_timestamps: `0`
- output_size_mb: `53.09`

### 14.2 GitHub push note
- Push succeeded to `origin/main` with large-file warning:
  - `data/xauusd_m5_2010_2023_backtest_ready.csv` ~52 MB (above recommended 50 MB, below hard 100 MB).
- Decision: keep tracked directly for now; migrate to Git LFS if dataset size grows further.


## Phase 15 - FULL/DEV data_local integration + integrity + smoke

- logged_at_utc: 2026-02-19T19:37:01Z
- template_ref_used: `_zip_template_ref_audit_20260216.zip` (workspace reference, style/checklist basis)

### 15.1 Added artifacts
- `.gitignore` updated for `data_local/**`, `*.csv.gz`, `data/tmp_rolling*`, `outputs/**`
- `data_local/.gitkeep`
- `scripts/data/make_dev_from_full.py`
- `scripts/data/validate_m5_integrity.py`
- `scripts/smoke_test_b4_dev.py`
- `docs/DATASETS.md`
- `docs/RUN_FULL_VALIDATION.md`

### 15.2 Execution (because FULL now available in workspace)
1) Prepared FULL in data_local:
- copied `data/xauusd_m5_2010_2023_backtest_ready.csv` -> `data_local/xauusd_m5_2010_2023.csv`

2) FULL integrity:
- command: `python scripts/data/validate_m5_integrity.py --input data_local/xauusd_m5_2010_2023.csv --expected_tf_minutes 5 --max_report_rows 20`
- result: `SUMMARY: WARN`
- notes: dominant delta 5m PASS, columns/timestamps/OHLC PASS, large gaps WARN (market closures/holidays).

3) DEV build from FULL (>=2021-01-01):
- command: `python scripts/data/make_dev_from_full.py --input data_local/xauusd_m5_2010_2023.csv --output data_local/xauusd_m5_DEV_2021_2023.csv --start "2021-01-01"`
- rows_after: `203408`
- range: `2021-01-03 18:00:00` -> `2023-12-29 16:55:00`

4) DEV integrity:
- command: `python scripts/data/validate_m5_integrity.py --input data_local/xauusd_m5_DEV_2021_2023.csv --expected_tf_minutes 5 --max_report_rows 20`
- result: `SUMMARY: WARN`
- notes: same pattern (5m PASS + closure gaps WARN).

5) Smoke B4 end-to-end:
- command: `python scripts/smoke_test_b4_dev.py --data data_local/xauusd_m5_DEV_2021_2023.csv --config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/smoke_dev_b4`
- first attempt: failed due `runs_output_dir` mismatch in winner config vs custom out-dir
- fix applied: smoke wrapper now writes temporary config overriding only `runs_output_dir` to out-dir
- final result: `SMOKE_RESULT status=OK`, `run_id=20260219_192134`, `trades=26`, `run_dir=outputs/smoke_dev_b4/20260219_192134`

### 15.3 Smoke wrapper UX adjustment
- `scripts/smoke_test_b4_dev.py` updated to avoid printing full captured simulator stdout on success.
- Current behavior: concise final summary (`SMOKE_RESULT`) and full stdout only on failure.


## Phase 16 - V4-A Session ORB implementation + candidate queue

- logged_at_utc: 2026-02-19T20:08:00Z
- template_ref_used: `_zip_template_ref_audit_20260216.zip` (reference style/checklist)

### 16.1 Source-of-truth read before edits
- `src/xauusd_bot/engine.py`
- `src/xauusd_bot/data_loader.py`
- `scripts/run_and_tag.py`
- `scripts/rolling_holdout_eval.py`
- `docs/GO_NO_GO.md`
- `docs/PIVOT_SCOREBOARD.md`

### 16.2 Additive implementation (no B4 changes)
- Engine/config support for strategy family `V4_SESSION_ORB`:
  - `src/xauusd_bot/engine.py`
  - `src/xauusd_bot/configuration.py`
- New wrapper:
  - `scripts/run_v4_candidates.py`
- New candidate configs:
  - `configs/v4_candidates/v4a_orb_01.yaml` ... `configs/v4_candidates/v4a_orb_12.yaml`
- New strategy doc:
  - `docs/V4A_SESSION_ORB.md`

### 16.3 Validation commands executed
1) Static checks + tests:
- `python -m py_compile src/xauusd_bot/engine.py src/xauusd_bot/configuration.py scripts/run_v4_candidates.py`
- `python -m pytest -q`
- result: `22 passed`

2) Candidate wrapper smoke (small data):
- `python scripts/run_v4_candidates.py --data data/sample_m5.csv --candidates-dir configs/v4_candidates --out-dir outputs/v4_dev_runs_smoke2 --resamples 500 --seed 42`
- artifacts:
  - `outputs/v4_dev_runs_smoke2/v4_candidates_scoreboard.csv`
  - `outputs/v4_dev_runs_smoke2/v4_candidates_scoreboard_summary.json`
  - `outputs/v4_dev_runs_smoke2/v4_candidates_scoreboard.md`
- baseline run_id: `20260219_194850`
- candidate run_ids_ok:
  - `20260219_194855`, `20260219_194904`, `20260219_194912`, `20260219_194921`
  - `20260219_194929`, `20260219_194938`, `20260219_194946`, `20260219_194955`
  - `20260219_195004`, `20260219_195013`, `20260219_195022`, `20260219_195030`

3) One direct run on larger dataset to confirm V4 branch generates trades:
- `python scripts/run_and_tag.py --data data/xauusd_m5_test.csv --config configs/v4_candidates/v4a_orb_01.yaml --runs-root outputs/runs`
- run_id: `20260219_195358`
- result excerpt: `closed_trades: 180`, strategy path active with next-open flow.

### 16.4 Repro docs updated
- `docs/REPRO_RUNS.md`:
  - added V4 DEV queue command
  - added V4 FULL rolling + posthoc commands
