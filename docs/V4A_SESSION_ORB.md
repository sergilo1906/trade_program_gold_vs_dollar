# V4-A Session ORB (Asia -> London)

## Hypothesis
- La ruptura del rango de Asia (00:00-06:00 UTC) durante London open (07:00-10:00 UTC) puede entregar mejor calidad de trades bajo costes que el baseline actual.
- La ejecucion respeta `next-open`: senal en `close[t]`, entrada en `open[t+1]`.
- Datos usados: OHLC-only M5.

## Strategy Parameters
- `strategy_family`: `V4_SESSION_ORB`
- `v4_session_orb.asia_start`, `v4_session_orb.asia_end`
- `v4_session_orb.trade_start`, `v4_session_orb.trade_end`
- `v4_session_orb.buffer_atr_mult`
- `v4_session_orb.atr_period`
- `v4_session_orb.rr`
- `v4_session_orb.time_stop`
- `v4_session_orb.exit_at_trade_end`
- `v4_session_orb.stop_mode` (`box` | `break_wick`)

## Candidate Queue
- Folder: `configs/v4_candidates/`
- Grid:
  - `buffer_atr_mult`: `0.00`, `0.05`, `0.10`
  - `rr`: `1.0`, `1.5`
  - `stop_mode`: `box`, `break_wick`
  - `atr_period`: fijo `14`

## Commands
### 1) DEV queue (12 candidates)
```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v4_candidates --out-dir outputs/v4_dev_runs
```

### 2) Full validation for selected winner (reuse existing pipeline)
```powershell
python scripts/rolling_holdout_eval.py --data data/xauusd_m5_2010_2023_backtest_ready.csv --config <WINNER_V4_CONFIG> --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_v4 --resamples 5000 --seed 42
```

```powershell
python scripts/posthoc_cost_stress_batch.py --runs <RID_W1> <RID_W2> <RID_W3> <RID_W4> --window-map-csv outputs/rolling_holdout_v4/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_v4.csv
```

## Winner Rule
- Elegir candidato por OOS, no por in-sample:
  - pasa GO/NO-GO del repo
  - `trade retention > 90%` (vs baseline B4 en la misma muestra)
  - pasa stress post-hoc `+20%` y preferiblemente `+50%`.
