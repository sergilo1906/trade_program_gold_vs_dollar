# Diagnóstico Último Run (20260218_161547)

## Contexto operativo

- Run analizado: `outputs/runs/20260218_161547`
- Diagnóstico generado con: `scripts/diagnose_run.py`
- Universo de oportunidades (`SIGNAL_DETECTED`): `62`
- Trades ejecutados: `16`

## 1) Dónde se pierde edge

### Modo / régimen de entrada

- `A_perf_by_mode.csv`: solo existe `TREND`.
- Métricas TREND: `PF=0.52`, `expectancy_R=-0.1351`, `winrate=37.5%`, `trades=16`.
- `I_perf_by_regime_at_entry.csv`: entradas únicamente con `regime_at_entry=TREND`.

Lectura: el run no tiene diversificación por modo/régimen en ejecución real; toda la PnL depende del bloque TREND.

### Hora UTC

- `H_perf_by_hour_robust.csv`:
  - Horas con peor expectancy: `11h (-0.6445R, n=2)`, `8h (-0.3672R, n=4)`, `14h (-0.3547R, n=1)`.
  - Horas con mejor expectancy (muestra >1): `15h (+0.1818R, n=4)`, `10h (+0.0417R, n=4)`.
  - `9h` sale positiva pero con `n=1`.

Lectura: la cola negativa se concentra en pocas franjas horarias con muestra baja-media.

### Bloqueos

- `E_blocks.csv`:
  - `SESSION_BLOCK=40` (`64.52%` sobre 62 oportunidades)
  - `COST_FILTER_BLOCK=5` (`8.06%`)
  - `SHOCK_BLOCK=1` (`1.61%`)
  - `MAX_TRADES=0`
- Relación eventos de bloqueo / oportunidades: `(40+5+1+0)/62 = 74.19%`.
- `F_blocks_by_hour_utc.csv`: presión de bloqueo alta en horas 0–7 y 12,16–19 (en algunas horas el `%` supera 1 por múltiples eventos de bloqueo dentro de la misma hora).

Lectura: el principal cuello de botella de ejecución es sesión, no coste.

### Costes en unidades de riesgo (Cost_R)

- `D_costR_percentiles.csv` (mode+bucket):
  - `cost_R_mean=0.018436`
  - `p50=0.018409`
  - `p75=0.018452`
  - `p90=0.018543`
- Variación por hora muy baja (mismo orden de magnitud en todas las horas con trades).

Lectura: coste estable y bajo en R; no explica por sí solo el expectancy negativo.

## 2) Dwell time y churn de régimen

- `M_regime_time_share.csv`:
  - `TREND`: `602,385 min` (`82.96%`), `192` segmentos
  - `NO_TRADE`: `122,415 min` (`16.86%`), `193` segmentos
  - `RANGE`: `1,320 min` (`0.18%`), `3` segmentos
- `K_regime_event_counts.csv` (global):
  - `REGIME_TREND_ENTER=192`, `REGIME_TREND_EXIT=192`
  - `REGIME_NO_TRADE_ENTER=194`
  - `REGIME_RANGE_ENTER=3`, `REGIME_RANGE_EXIT=3`

Lectura: alternancia frecuente TREND/NO_TRADE (churn alto), con presencia residual de RANGE.

## 3) Oportunidades por régimen

- `N_signals_by_regime.csv`:
  - Global: `TREND=62`, `NO_TRADE=0`, `RANGE=0`, `UNKNOWN=0`.

Lectura: todas las oportunidades detectadas caen en TREND en este run.

## 4) Estado operativo de señales

- `J_signals_state_counts.csv` (global):
  - `WAIT_H1_BIAS=600`
  - `WAIT_M5_ENTRY=170`
  - `IN_TRADE=146`

Lectura: predominio de estados de espera/filtrado frente a ejecución efectiva.

## Conclusión factual

- El deterioro del edge en este run viene de combinación de:
  - baja tasa de acierto y expectancy negativo en TREND,
  - concentración de pérdidas en horas concretas,
  - y alta fricción por bloqueos de sesión sobre oportunidades.
- El coste unitario (`~0.018R`) es estable y secundario frente a la calidad temporal de entradas y al gating de sesión.
