# Strategy Spec (MTF OHLC-only)

Este documento resume la logica operativa implementada para el backtest en `xauusd_bot`.

## 1) Flujo de estados

- `WAIT_H1_BIAS`: espera sesgo de tendencia en H1.
- `WAIT_M15_CONFIRM`: espera confirmacion de pullback en M15.
- `WAIT_M5_ENTRY`: espera trigger de entrada en M5.
- `IN_TRADE`: gestiona una unica posicion abierta.

No hay lookahead:
- H1 y M15 se calculan solo con velas cerradas (`end_time <= t`).
- La senal se genera en cierre M5(t) y la ejecucion ocurre en `open` de M5(t+1).

## 2) H1 Bias

Sesgo LONG:
- `EMA50_H1 > EMA200_H1`
- `close_H1 > EMA200_H1 + h1_bias_atr_mult * ATR_H1`
- pendiente EMA50 positiva con `h1_bias_slope_lookback`

Sesgo SHORT simetrico.

Filtro anti-lateralidad:
- `ema_sep = abs(EMA50_H1 - EMA200_H1)`
- si `ema_sep < h1_min_sep_atr_mult * ATR_H1` entonces `Bias.NONE` con motivo `H1_BIAS_NONE_FLAT`.

## 3) M15 Confirmation (pullback real)

LONG:
1. Pullback activo cuando `close_M15 <= EMA20_M15`.
2. Durante el pullback, RSI debe caer a `<= rsi_pullback_long_max`.
3. Confirmacion cuando `close_M15 > EMA20_M15` y `RSI >= rsi_recover_long_min`.

SHORT:
1. Pullback activo cuando `close_M15 >= EMA20_M15`.
2. Durante el pullback, RSI debe subir a `>= rsi_pullback_short_min`.
3. Confirmacion cuando `close_M15 < EMA20_M15` y `RSI <= rsi_recover_short_max`.

Caducidad:
- `confirm_valid_m15_bars` barras M15 despues de la confirmacion.

Reasons de auditoria:
- `M15_PULLBACK_STARTED`
- `M15_PULLBACK_RSI_OK`
- `M15_CONFIRM_OK`
- `M15_CONFIRM_EXPIRED`

## 4) M5 Entry

Para LONG (SHORT simetrico):
- bias LONG y confirm M15 valida
- `close > EMA20_M5`
- breakout BOS: `close > HH(bos_lookback)` de velas previas cerradas
- vela fuerte: `body_ratio >= body_ratio`
- filtro de wick direccional:
  - LONG: `upper_wick <= wick_ratio_max * range`
  - SHORT: `lower_wick <= wick_ratio_max * range`

Limites:
- maximo 1 posicion abierta.
- cooldown tras cierre: `cooldown_after_trade_bars`.
- limite diario de frecuencia: `max_trades_per_day` (bloqueo `BLOCKED_MAX_TRADES_DAY`).

## 5) Ejecucion y costes

Ejecucion siempre a mercado en `next open`.

Costes por fill (adversos):
- spread configurable (`spread_usd`)
- slippage configurable (`slippage_usd`)

Convencion:
- BUY: `mid + spread/2 + slippage`
- SELL: `mid - spread/2 - slippage`

## 6) Gestion de trade

- SL inicial estructural + floor ATR.
- sizing por riesgo (`risk_per_trade_pct`).
- TP1 parcial (`partial_pct`) en `tp1_r * R`.
- tras TP1: SL a break-even y trailing chandelier (`trailing_mult * ATR_M5`).
- time stop (`time_stop_bars`, `time_stop_min_r`).
- salida por fallo M15 en cierre confirmado (next open).
- cierre forzado por sesion.

Intrabar OHLC:
- SL/TP se evaluan con high/low de la vela.
- si SL y TP tocan en la misma vela, prioridad SL.

## 7) Gobernanza y robustez

Bloqueos de riesgo:
- daily stop (R y %)
- weekly stop (R y %)
- loss streak (bloqueo temporal)

Auditoria:
- `events.csv`, `signals.csv`, `trades.csv`, `fills.csv`.
- `report.md` incluye global, mensual, prueba del ano, costes, Monte Carlo, sensibilidad y chequeo de objetivo mensual (4%-8%).
