# STRATEGY FINAL v2.0 (Regime-Switch)

## 1) Regimen

La estrategia opera con tres regimenes:

- `TREND`
- `RANGE`
- `NO_TRADE`

El detector usa solo velas cerradas (H1/M15) y calcula:

- `trend_score`
- `range_score`

Con componentes de:

- alineacion EMA50/EMA200 H1
- separacion EMA en ATR
- pendiente EMA50 en ATR
- ATR relativo (`ATR_H1 / SMA(ATR_H1)`)
- penalizacion por shock y por ATR muerta
- coherencia direccional (EMA50/EMA200 alineadas con slope)

La transicion usa histeresis:

- entrada TREND con `regime_trend_enter_score`
- salida TREND con `regime_trend_exit_score`
- entrada RANGE con `regime_range_enter_score`
- salida RANGE con `regime_range_exit_score`

Y minimo tiempo en regimen:

- `trend_min_bars_m15`
- `range_min_bars_m15`

En v2.1 se elimina el punto "gratis" de tendencia: ya no suma por `ema_fast != ema_slow`.
Ahora solo suma si hay coherencia real:
- `ema_fast > ema_slow` y `slope > 0`
- o `ema_fast < ema_slow` y `slope < 0`

Eventos de auditoria:

- `REGIME_TREND_ENTER`, `REGIME_TREND_EXIT`
- `REGIME_RANGE_ENTER`, `REGIME_RANGE_EXIT`
- `REGIME_NO_TRADE_ENTER`

## 2) Motor TREND

Pipeline MTF:

- Bias H1 (EMA/ATR/slope + filtro lateralidad)
- Confirmacion M15 pullback + RSI pullback/recover
- Trigger M5 BOS + body ratio + filtro de mecha

Ejecucion:

- senal en cierre M5
- entrada en `open` de la siguiente vela

Gestion TREND:

- parcial en `tp1_r` (`PARTIAL_TP`)
- `BE_MOVE` tardio en `be_after_r`
- trailing 2 fases:
  - `TRAIL_PHASE1` antes de TP1
  - `TRAIL_PHASE2` tras TP1
- salida por flip de regimen: `REGIME_EXIT`

## 3) Motor RANGE

Bandas M15:

- `mid = EMA20_M15`
- `upper/lower = mid +/- k_atr_range * ATR14_M15`

Entrada por rechazo M5:

- toque/exceso de banda en M15
- re-entry dentro de banda en M5
- rechazo por wick ratio y body minimo
- filtro RSI M15 extremo:
  - LONG solo si `rsi14_m15 <= range_rsi_long_max`
  - SHORT solo si `rsi14_m15 >= range_rsi_short_min`

Persistencia de toque (v2.1):
- se guarda el ultimo toque de banda (`upper/lower`) al cierre M15
- se habilita ventana TTL en M5: `range_touch_ttl_m5_bars`
- solo se permite entrada RANGE si el toque sigue vigente dentro del TTL

Filtro de calidad RANGE (v2.2):
- se evita mean-reversion en zona neutral de RSI
- reduce sobreoperacion en consolidaciones sin extremo

Gestion RANGE:

- SL fuera de banda con buffer ATR
- TP en media (`mid`)
- kill-switch por flip a TREND: `KILL_SWITCH_REGIME_FLIP`

## 4) Sesiones y costes

Gating por modo:

- `trend_sessions`
- `range_sessions`
- `blocked_windows`

Bloqueo por sesion:

- `SESSION_BLOCK`

Modelo de coste:

- base: `spread_usd`, `slippage_usd`
- multiplicadores: `cost_mult_trend_session`, `cost_mult_off_session`, `cost_mult_asia`
- multiplicador guardado en `fills.csv` y `trades.csv`

Filtro coste/oportunidad pre-entrada:

- `cost_total <= cost_max_atr_mult * ATR_M5`
- `cost_total <= cost_max_sl_frac * sl_distance`

Filtro por modo (v2.1):
- TREND mantiene filtro ATR + distancia a SL
- RANGE usa ATR + oportunidad real al objetivo:
  - `cost_total <= cost_max_tp_frac_range * tp_distance`
  - donde `tp_distance = abs(tp_mid - entry_mid)`

Bloqueo:

- `COST_FILTER_BLOCK`

Ablacion (diagnostico rapido, sin romper CLI):
- `ablation_force_regime`: `AUTO | TREND | RANGE | NO_TRADE`
- `ablation_disable_cost_filter`: `true/false`
- `ablation_disable_session_gating`: `true/false`

## 5) Gobernanza y auditoria

Se mantiene:

- bloqueo diario/semanal/loss streak
- limite diario de trades (`BLOCKED_MAX_TRADES_DAY`)
- shock cooldown (`SHOCK_BLOCK`)

Outputs auditables:

- `events.csv`
- `signals.csv`
- `trades.csv`
- `fills.csv`

El reporte agrega:

- performance por modo (TREND/RANGE)
- resumen de bloqueos
- coste efectivo medio
- chequeo objetivo mensual 4-8%
