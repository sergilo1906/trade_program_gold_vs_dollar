# EDGE LOSS DELTA (RUN_GOOD vs RUN_BAD)

## Contexto
- RUN_BAD (malo): `outputs/runs/20260218_161547`
- RUN_GOOD (bueno): `outputs/runs/20260218_101336`
- Fuente: CSVs A?N generados por `scripts/diagnose_run.py` en ambos runs.

## Top Metrics Delta
```
            run       pf  expectancy_R  winrate  trades  opportunities  blocks_total  blocks_pct_total
20260218_161547 0.520000     -0.135098 0.375000      16             62            46          0.741935
20260218_101336 2.307687      0.493273 0.666667      18            112            94          0.839286
```

Notas:
- `opportunities` usa `E_blocks.opportunities_denom` (denominador expl?cito del diagn?stico).
- `blocks_pct_total = sum(block_count) / opportunities`.

## A) Performance por modo
### RUN_BAD `20260218_161547`
```
 mode   pf  expectancy_R  winrate     avg_R  trades
TREND 0.52     -0.135098    0.375 -0.135098      16
```

### RUN_GOOD `20260218_101336`
```
 mode       pf  expectancy_R  winrate    avg_R  trades
RANGE 2.307687      0.493273 0.666667 0.493273      18
```

## E) Blocks por tipo
### RUN_BAD `20260218_161547`
```
       block_type  count  pct_of_opportunities  opportunities_denom                    denominator_source
    SESSION_BLOCK     40              0.645161                   62 signals.event_type == SIGNAL_DETECTED
COST_FILTER_BLOCK      5              0.080645                   62 signals.event_type == SIGNAL_DETECTED
      SHOCK_BLOCK      1              0.016129                   62 signals.event_type == SIGNAL_DETECTED
       MAX_TRADES      0              0.000000                   62 signals.event_type == SIGNAL_DETECTED
```

### RUN_GOOD `20260218_101336`
```
       block_type  count  pct_of_opportunities  opportunities_denom                    denominator_source
    SESSION_BLOCK     89              0.794643                  112 signals.event_type == SIGNAL_DETECTED
COST_FILTER_BLOCK      5              0.044643                  112 signals.event_type == SIGNAL_DETECTED
      SHOCK_BLOCK      0              0.000000                  112 signals.event_type == SIGNAL_DETECTED
       MAX_TRADES      0              0.000000                  112 signals.event_type == SIGNAL_DETECTED
```

## D) Cost_R percentiles (scope=mode_session_bucket)
### RUN_BAD `20260218_161547`
```
              scope  mode session_bucket  hour_utc  trades  cost_R_mean  cost_R_p50  cost_R_p75  cost_R_p90
mode_session_bucket TREND   MODE_SESSION       NaN      16     0.018436    0.018409    0.018452    0.018543
```

### RUN_GOOD `20260218_101336`
```
              scope  mode session_bucket  hour_utc  trades  cost_R_mean  cost_R_p50  cost_R_p75  cost_R_p90
mode_session_bucket RANGE           ASIA       NaN       3     0.001096    0.001252    0.001303    0.001334
mode_session_bucket RANGE   MODE_SESSION       NaN      10     0.000996    0.000920    0.001022    0.001406
mode_session_bucket RANGE    OFF_SESSION       NaN       5     0.001055    0.001092    0.001150    0.001215
```

## H) Hour robust perf
### RUN_BAD `20260218_161547`
```
 hour_utc  trades  wins  losses  sum_R_pos  sum_R_neg_abs       pf  expectancy_R  winrate
        8       4     1       3    0.11671        1.58546 0.073613     -0.367188     0.25
        9       1     1       0    0.05697        0.00000      NaN      0.056970     1.00
       10       4     2       2    0.81883        0.65220 1.255489      0.041657     0.50
       11       2     0       2    0.00000        1.28907 0.000000     -0.644535     0.00
       14       1     0       1    0.00000        0.35470 0.000000     -0.354700     0.00
       15       4     2       2    1.34918        0.62182 2.169728      0.181840     0.50
```

### RUN_GOOD `20260218_101336`
```
 hour_utc  trades  wins  losses  sum_R_pos  sum_R_neg_abs       pf  expectancy_R  winrate
        6       3     3       0    4.10962        0.00000      NaN      1.369873 1.000000
        7       6     4       2    4.42250        2.22187 1.990440      0.366772 0.666667
       16       4     3       1    4.88331        1.17653 4.150604      0.926695 0.750000
       17       5     2       3    2.25326        3.39138 0.664408     -0.227624 0.400000
```

## G) Opportunities por hora
### RUN_BAD `20260218_161547`
```
 hour_utc  opportunities
        0              2
        1              0
        2              3
        3              4
        4              2
        5              1
        6              3
        7              3
        8              6
        9              1
       10              6
       11              3
       12              6
       13              0
       14              2
       15              4
       16              4
       17              1
       18              4
       19              3
       20              2
       21              1
       22              0
       23              1
```

### RUN_GOOD `20260218_101336`
(vacio)

## J) Signals state counts (global)
### RUN_BAD `20260218_161547`
```
 scope  hour_utc         state  count
global       NaN  WAIT_H1_BIAS    600
global       NaN WAIT_M5_ENTRY    170
global       NaN      IN_TRADE    146
```

### RUN_GOOD `20260218_101336`
```
 scope  hour_utc         state  count
global       NaN WAIT_M5_ENTRY    318
global       NaN  WAIT_H1_BIAS     19
global       NaN      IN_TRADE     18
```

## K) Regime event counts (global)
### RUN_BAD `20260218_161547`
```
 scope  hour_utc            event_type  count
global       NaN REGIME_NO_TRADE_ENTER    194
global       NaN    REGIME_TREND_ENTER    192
global       NaN     REGIME_TREND_EXIT    192
global       NaN    REGIME_RANGE_ENTER      3
global       NaN     REGIME_RANGE_EXIT      3
```

### RUN_GOOD `20260218_101336`
```
 scope  hour_utc         event_type  count
global       NaN REGIME_RANGE_ENTER      1
```

## M) Regime time-share
### RUN_BAD `20260218_161547`
```
  regime  segments  total_minutes  pct_time  avg_minutes  p50_minutes  p90_minutes
   TREND       192       602385.0  0.829594  3137.421875       1260.0       8004.0
NO_TRADE       193       122415.0  0.168588   634.274611        405.0       1260.0
   RANGE         3         1320.0  0.001818   440.000000        240.0        864.0
```

### RUN_GOOD `20260218_101336`
(vacio)

## N) Opportunities por r?gimen (global)
### RUN_BAD `20260218_161547`
```
 scope regime  hour_utc  opportunities
global  TREND       NaN             62
```

### RUN_GOOD `20260218_101336`
(vacio)

## Que cambio (max 3)
- El modo dominante cambia de `RANGE` (RUN_GOOD) a `TREND` (RUN_BAD), con salto de `expectancy_R` de `+0.493` a `-0.135` y `PF` de `2.31` a `0.52`.
- El denominador de oportunidades cae (`112` -> `62`) pero la fricci?n por bloqueos sigue alta en ambos; RUN_GOOD presenta mayor ratio total de eventos de bloqueo por oportunidad (`~83.9%` vs `~74.2%`).
- En RUN_GOOD faltan series ricas de r?gimen/hora para se?ales (`G`, `L`, `M`, `N` vac?os o parciales), mientras RUN_BAD s? trae trazabilidad extensa de `REGIME_*` y segmentos.

## Hipotesis testables SIN cambiar estrategia
- Recalcular KPIs del mismo run por ventanas horarias/sesi?n (post-estratificaci?n offline) para medir sensibilidad de PF/expectancy por franja.
- Medir contribuci?n de cada tipo de bloqueo al delta de oportunidades ejecutadas (contrafactual offline con filtros desactivados solo en an?lisis, sin tocar engine).
- Comparar estabilidad de `r_multiple` y `pnl` por modo/regime_at_entry con bootstrap para cuantificar si el salto GOOD->BAD puede explicarse por varianza muestral.

## Evidencia de configuracion / causa del cambio
- Snapshot de config/metadata dentro de run dirs:
  - RUN_BAD `20260218_161547`: NO ENCONTRADO
  - RUN_GOOD `20260218_101336`: NO ENCONTRADO
- Evidencia disponible en artefactos de run: ambos contienen subcarpetas `cost_base|cost_bad|cost_good`, `sensitivity/`, `year_test/` + CSVs base; solo RUN_GOOD conserva `report.md` en el snapshot actual.
- Evidencia en codigo de reporting:
  - `report.md` se genera desde `src/xauusd_bot/main.py::_write_report` con scopes `full` y `year_test` (por defecto `last_365_days`).
  - `expectancy_R` usa `trades.r_multiple` y `profit_factor` usa `trades.pnl` (`src/xauusd_bot/reporting.py`).
- Log global `outputs/runs/run_full.log`:
```text
��D A T A   S U M M A R Y   ( R A W )   |   f i l e _ u s e d = C : \ U s e r s \ S e r g i \ O n e D r i v e \ E s c r i t o r i o \ A p p   O r o   C o r k \ d a t a \ x a u u s d _ m 5 _ b a c k t e s t _ r e a d y . c s v   |   r o w s = 1 0 0 0 0 0   |   m i n _ t s = 2 0 2 4 - 0 9 - 1 7   1 4 : 0 0 : 0 0   |   m a x _ t s = 2 0 2 6 - 0 2 - 1 6   1 9 : 2 5 : 0 0   |   u n i q u e _ d a y s = 4 4 2 
 
 D A T A   S U M M A R Y   ( C L E A N )   |   f i l e _ u s e d = C : \ U s e r s \ S e r g i \ O n e D r i v e \ E s c r i t o r i o \ A p p   O r o   C o r k \ d a t a \ x a u u s d _ m 5 _ b a c k t e s t _ r e a d y . c s v   |   r o w s = 1 0 0 0 0 0   |   m i n _ t s = 2 0 2 4 - 0 9 - 1 7   1 4 : 0 0 : 0 0   |   m a x _ t s = 2 0 2 6 - 0 2 - 1 6   1 9 : 2 5 : 0 0   |   u n i q u e _ d a y s = 4 4 2 
 
 
 
```
- El log muestra dataset usado (`data/xauusd_m5_backtest_ready.csv`) y progreso, pero no incluye mapeo expl?cito run_id->config para estos snapshots hist?ricos.
