# V3 Spec (Determinista)

## Alcance
- Mercado: XAUUSD intradia M5.
- Datos: OHLC-only.
- Ejecucion: siempre `next-open` (senal en close[t], entrada en open[t+1]).
- Compatibilidad: v2 intacta cuando `enable_strategy_v3=false`.

## Parametros v3
- `enable_strategy_v3`
- `v3_breakout_N1`
- `v3_atr_period_M`
- `v3_k_trend`
- `v3_k_range`
- `v3_atr_sl_trend`
- `v3_rr_trend`
- `v3_rsi_period`
- `v3_atr_sl_range`
- `v3_rr_range`
- `max_trades_per_session`
- `close_at_session_end`

## Indicadores
- `ATR(M)`: Wilder sobre True Range (`max(high-low, abs(high-prev_close), abs(low-prev_close))`).
- `ATR_MA`: SMA de `ATR` con ventana `M`.
- `RSI(P)`: Wilder.
- `highest(high,N1)` y `lowest(low,N1)` usando solo velas completas previas (`shift(1)`).

## Reglas TREND (Breakout)
- Precondicion: `regime == TREND`.
- Long: `close[t] > highest_prev_N1[t]`.
- Short: `close[t] < lowest_prev_N1[t]`.
- Filtro volatilidad: `ATR[t] >= v3_k_trend * ATR_MA[t]`.
- Entrada: `open[t+1]`.
- Distancias:
  - `SL_dist = v3_atr_sl_trend * ATR[t]`
  - `TP_dist = v3_rr_trend * SL_dist`

## Reglas RANGE (Mean-Reversion RSI)
- Precondicion: `regime == RANGE`.
- Long: `RSI[t] <= 30`.
- Short: `RSI[t] >= 70`.
- Filtro volatilidad: `ATR[t] <= v3_k_range * ATR_MA[t]`.
- Entrada: `open[t+1]`.
- Distancias:
  - `SL_dist = v3_atr_sl_range * ATR[t]`
  - `TP_dist = v3_rr_range * SL_dist`

## Gestion y limites
- `max_trades_per_session=1` (global por sesion activa).
- `close_at_session_end=true`: cierre en apertura de la primera vela fuera de ventana de sesion del modo.
- Salidas v3:
  - `V3_EXIT_TP`
  - `V3_EXIT_SL`
  - `V3_EXIT_SESSION_END`

## Eventos de auditoria
- Senales:
  - `V3_SIGNAL_TREND_BREAKOUT`
  - `V3_SIGNAL_RANGE_RSI`
- Entrada:
  - `V3_ENTRY`
- Bloqueos:
  - `V3_BLOCK_*` (session, cost, cooldown, max_trades_session, etc.)
- `details_json` incluye: `regime`, `direction`, `close_t`, `entry_open_t1`, `ATR`, `ATR_MA`, `RSI`, `N1 high/low`, distancias SL/TP y parametros activos.

## Configs creadas
- `configs/config_v3_TREND.yaml` (`ablation_force_regime: TREND`, `enable_strategy_v3: true`)
- `configs/config_v3_RANGE.yaml` (`ablation_force_regime: RANGE`, `enable_strategy_v3: true`)
- `configs/config_v3_AUTO.yaml` (`ablation_force_regime: AUTO`, `enable_strategy_v3: true`)
