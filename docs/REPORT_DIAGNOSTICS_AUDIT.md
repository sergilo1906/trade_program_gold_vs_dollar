# REPORT vs DIAGNOSTICS Audit

## Alcance
- Solo auditoria de coherencia de reportes y diagnosticos (sin cambios de estrategia/engine).
- plantilla `plantillas_mejoradas.zip`: NO encontrada en el repo.

## A) Enumeracion Top 10 Runs (mtime desc)
```
            run report_md report_size diag_md diag_size  trades_rows  signals_rows  events_rows
20260218_190312        si        7471      si     48822           16           916         1254
20260218_161547        no                  si     48822           16           916         1254
20260218_101336        si        7354      no                     18           355          591
20260218_100224        si        7658      no                     68          2040         1186
20260218_090154        si        7556      no                     47          1182         1544
20260218_085721        si        7460      no                     67          2039         1195
20260218_085323        si        7471      no                     16           339          673
20260218_084841        si        7471      no                     16           925         1257
20260217_230246        si        7471      no                     16           550          886
20260217_225627        si        7419      no                     16           550          886
```

## B) Runs clave
- RUN_LATEST: `outputs\runs\20260218_190312`
- RUN_LATEST_WITH_REPORT: `outputs\runs\20260218_190312`
- RUN_LATEST_WITH_DIAG: `outputs\runs\20260218_190312`

## C) Report y Diagnostics del mismo run auditado
- run auditado: `outputs\runs\20260218_190312`
- report.md: `outputs\runs\20260218_190312\report.md`
- diagnostics.md: `outputs\runs\20260218_190312\diagnostics\diagnostics.md`

### report.md (copiado integro)
```md
# Reporte de Backtest y Fiabilidad

## Resumen Ejecutivo

- Veredicto: **No fiable**
- Prueba del ano usada: `last_365_days`
- Equity final (full): `9892.01`
- Equity final (ano): `9872.57`
- PF (ano): `0.332`
- MDD (ano): `1.29%`
- Expectancy R (ano): `-0.197`
- Objetivo 4-8% mensual: `0.00%` de meses >=4%, mediana mensual = `0.00%`

Motivos del veredicto:
- PF OOS bajo (0.33 < 1.30).
- Expectancy R bajo (-0.197 < 0.10).
- Porcentaje de meses positivos bajo (15.38% < 60%).
- Escenario de costes malo pierde robustez (PF=0.32 < 1.00).
- Monte Carlo insuficiente (0.00% positivos < 70%).

## Metricas Globales

| scope | total_return | final_equity | profit_factor | max_drawdown | winrate | expectancy_R | trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full | -0.0108 | 9892.0065 | 0.5195 | 0.0168 | 0.3750 | -0.1351 | 16 |
| year_test (last_365_days) | -0.0127 | 9872.5729 | 0.3322 | 0.0129 | 0.3846 | -0.1968 | 13 |

## Performance por Modo

### Full

| mode | trades | return | profit_factor | winrate | expectancy_R |
| --- | --- | --- | --- | --- | --- |
| TREND | 16 | -0.0108 | 0.5195 | 0.3750 | -0.1351 |

### Year Test

| mode | trades | return | profit_factor | winrate | expectancy_R |
| --- | --- | --- | --- | --- | --- |
| TREND | 13 | -0.0127 | 0.3322 | 0.3846 | -0.1968 |

## Bloqueos y Coste Efectivo

- Cost multiplier medio por entrada (full): `1.0000`
- Cost multiplier medio por entrada (ano): `1.0000`

### Bloqueos Full

| block_type | count |
| --- | --- |
| COST_FILTER_BLOCK | 5 |
| SESSION_BLOCK | 40 |
| SHOCK_BLOCK | 1 |
| BLOCKED_MAX_TRADES_DAY | 0 |
| MAX_TRADES_BLOCK | 0 |

### Bloqueos Year Test

| block_type | count |
| --- | --- |
| COST_FILTER_BLOCK | 1 |
| SESSION_BLOCK | 32 |
| SHOCK_BLOCK | 0 |
| BLOCKED_MAX_TRADES_DAY | 0 |
| MAX_TRADES_BLOCK | 0 |

### MAE/MFE (Full)

- MAE_R mean/median/p90: `0.396` / `0.393` / `0.720`
- MFE_R mean/median/p90: `0.542` / `0.384` / `1.217`

## Metricas Mensuales (Full)

- % meses positivos: `16.67%` | racha max meses negativos: `3` | mejor mes: `2024-11` | peor mes: `2025-09`

| month | return_compounded | return_simple | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-09 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10000.0000 | 10000.0000 |
| 2024-10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10000.0000 | 10000.0000 |
| 2024-11 | 0.0046 | 0.0046 | 7.7099 | 0.0000 | 2 | 46.3229 | 10000.0000 | 10046.3229 |
| 2024-12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10046.3229 | 10046.3229 |
| 2025-01 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10046.3229 | 10046.3229 |
| 2025-02 | -0.0027 | -0.0027 | 0.0000 | 0.0000 | 1 | -26.6385 | 10046.3229 | 10019.6844 |
| 2025-03 | -0.0022 | -0.0022 | 0.0000 | 0.0005 | 2 | -22.4064 | 10019.6844 | 9997.2780 |
| 2025-04 | -0.0012 | -0.0012 | 0.3289 | 0.0018 | 2 | -11.9064 | 9997.2780 | 9985.3716 |
| 2025-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9985.3716 | 9985.3716 |
| 2025-06 | 0.0021 | 0.0021 | 0.0000 | 0.0000 | 2 | 21.4325 | 9985.3716 | 10006.8042 |
| 2025-07 | -0.0030 | -0.0030 | 0.4294 | 0.0024 | 3 | -29.5436 | 10006.8042 | 9977.2606 |
| 2025-08 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9977.2606 | 9977.2606 |
| 2025-09 | -0.0037 | -0.0037 | 0.0000 | 0.0000 | 1 | -36.7515 | 9977.2606 | 9940.5091 |
| 2025-10 | -0.0035 | -0.0035 | 0.0000 | 0.0000 | 1 | -35.2727 | 9940.5091 | 9905.2364 |
| 2025-11 | -0.0028 | -0.0027 | 0.0000 | 0.0000 | 1 | -27.2520 | 9905.2364 | 9877.9844 |
| 2025-12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9877.9844 | 9877.9844 |
| 2026-01 | 0.0014 | 0.0014 | 0.0000 | 0.0000 | 1 | 14.0221 | 9877.9844 | 9892.0065 |
| 2026-02 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9892.0065 | 9892.0065 |

## Metricas por ano (Full)

| year | return | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024.0 | 0.0046 | 7.7099 | 0.0000 | 2.0 | 46.3229 | 10000.0000 | 10046.3229 |
| 2025.0 | -0.0168 | 0.2272 | 0.0141 | 13.0 | -168.3385 | 10046.3229 | 9877.9844 |
| 2026.0 | 0.0014 | 0.0000 | 0.0000 | 1.0 | 14.0221 | 9877.9844 | 9892.0065 |

## Prueba del ano (last_365_days)

- % meses positivos: `15.38%` | racha max meses negativos: `3` | mejor mes: `2025-06` | peor mes: `2025-09`

| month | return_compounded | return_simple | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-02 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10000.0000 | 10000.0000 |
| 2025-03 | -0.0022 | -0.0022 | 0.0000 | 0.0005 | 2 | -22.3624 | 10000.0000 | 9977.6376 |
| 2025-04 | -0.0012 | -0.0012 | 0.3289 | 0.0018 | 2 | -11.8830 | 9977.6376 | 9965.7546 |
| 2025-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9965.7546 | 9965.7546 |
| 2025-06 | 0.0021 | 0.0021 | 0.0000 | 0.0000 | 2 | 21.3904 | 9965.7546 | 9987.1451 |
| 2025-07 | -0.0030 | -0.0029 | 0.4294 | 0.0024 | 3 | -29.4856 | 9987.1451 | 9957.6595 |
| 2025-08 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9957.6595 | 9957.6595 |
| 2025-09 | -0.0037 | -0.0037 | 0.0000 | 0.0000 | 1 | -36.6793 | 9957.6595 | 9920.9802 |
| 2025-10 | -0.0035 | -0.0035 | 0.0000 | 0.0000 | 1 | -35.2034 | 9920.9802 | 9885.7769 |
| 2025-11 | -0.0028 | -0.0027 | 0.0000 | 0.0000 | 1 | -27.1985 | 9885.7769 | 9858.5784 |
| 2025-12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9858.5784 | 9858.5784 |
| 2026-01 | 0.0014 | 0.0014 | 0.0000 | 0.0000 | 1 | 13.9945 | 9858.5784 | 9872.5729 |
| 2026-02 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 9872.5729 | 9872.5729 |

## Chequeo Objetivo Mensual (4-8%)

| scope | avg_monthly_return | median_monthly_return | pct_months_ge_4 | pct_months_ge_8 |
| --- | --- | --- | --- | --- |
| full | -0.0006 | 0.0000 | 0.0000 | 0.0000 |
| year_test (last_365_days) | -0.0010 | 0.0000 | 0.0000 | 0.0000 |

## Robustez de Costes

| scenario | spread_usd | slippage_usd | total_return | profit_factor | max_drawdown |
| --- | --- | --- | --- | --- | --- |
| base | 0.4100 | 0.0500 | -0.0108 | 0.5195 | 0.0168 |
| bad | 0.7000 | 0.1500 | -0.0065 | 0.3161 | 0.0069 |
| good | 0.3000 | 0.0000 | -0.0161 | 0.4337 | 0.0183 |

## Monte Carlo de Ejecucion

- Simulaciones: `300`
- Retorno P5/P50/P95: `-1.44%` / `-1.38%` / `-1.32%`
- DD P5/P50/P95: `1.46%` / `1.52%` / `1.58%`
- % simulaciones positivas: `0.00%`

## Sensibilidad Rapida

| parameter | value | total_return | profit_factor | max_drawdown | trades |
| --- | --- | --- | --- | --- | --- |
| trailing_mult | 2.0000 | -0.0127 | 0.3322 | 0.0129 | 13 |
| trailing_mult | 2.5000 | -0.0127 | 0.3322 | 0.0129 | 13 |
| trailing_mult | 3.0000 | -0.0127 | 0.3322 | 0.0129 | 13 |
| body_ratio | 0.6500 | -0.0127 | 0.3322 | 0.0129 | 13 |
| body_ratio | 0.7000 | -0.0127 | 0.3322 | 0.0129 | 13 |
| body_ratio | 0.7500 | -0.0127 | 0.3322 | 0.0129 | 13 |
| shock_threshold | 2.5000 | -0.0110 | 0.3653 | 0.0129 | 12 |
| shock_threshold | 3.0000 | -0.0127 | 0.3322 | 0.0129 | 13 |
| shock_threshold | 3.5000 | -0.0127 | 0.3322 | 0.0129 | 13 |

## Recomendaciones

- No usar en produccion sin rediseno de logica de entrada/salida.
- Replantear filtros de regimen y gestion de riesgo antes de re-evaluar.
```

## D) Resumen tabular A / I / E / G
### A_perf_by_mode.csv
```
 mode   pf  expectancy_R  winrate     avg_R  trades
TREND 0.52     -0.135098    0.375 -0.135098      16
```

### I_perf_by_regime_at_entry.csv
```
regime_at_entry   pf  expectancy_R  winrate     avg_R  trades
          TREND 0.52     -0.135098    0.375 -0.135098      16
```

### E_blocks.csv
```
       block_type  count  pct_of_opportunities  opportunities_denom                    denominator_source
    SESSION_BLOCK     40              0.645161                   62 signals.event_type == SIGNAL_DETECTED
COST_FILTER_BLOCK      5              0.080645                   62 signals.event_type == SIGNAL_DETECTED
      SHOCK_BLOCK      1              0.016129                   62 signals.event_type == SIGNAL_DETECTED
       MAX_TRADES      0              0.000000                   62 signals.event_type == SIGNAL_DETECTED
```

### G_signals_by_hour_utc.csv
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

- Sum opportunities (G): `62`

### Parse report.md y comparacion minima
```
           metric  report diagnostics status
          PF full  0.5195        0.52     OK
Expectancy_R full -0.1351   -0.135098     OK
      Trades full      16          16     OK
        Mode full   TREND       TREND     OK
```

- report PF year_test: `0.3322`
- report Expectancy_R year_test: `-0.1968`
- report Trades year_test: `13`

## E) Contradiccion RANGE aprobada vs TREND negativa
### Hallazgo de run con "Aprobado / RANGE / PF alto"
- `20260218_101336`

### Tabla de veredicto/mode por run con report.md
```
            run veredicto mode_full pf_ano
20260217_185748 No fiable                 
20260217_190320 No fiable            1.046
20260217_220016 No fiable            0.899
20260217_220443 No fiable            0.810
20260217_220838 No fiable            0.558
20260217_225040 No fiable     TREND  0.332
20260217_225627 No fiable     TREND  0.332
20260217_230246 No fiable     TREND  0.332
20260218_084841 No fiable     TREND  0.332
20260218_085323 No fiable     TREND  0.332
20260218_085721 No fiable     RANGE  1.208
20260218_090154 No fiable     RANGE  0.658
20260218_100224 No fiable     RANGE  1.054
20260218_101336  Aprobado     RANGE  3.673
20260218_190312 No fiable     TREND  0.332
```

### Determinacion
- Para el run auditado, `report.md` y `diagnostics.md` son consistentes (coherentes).
- La contradiccion "Aprobado/RANGE/PF alto" vs "TREND negativa" se explica por comparar runs distintos:
  - run auditado actual: `20260218_190312` => No fiable / TREND / PF bajo
  - run con Aprobado/RANGE: `20260218_101336`
- Adicionalmente, el reporte usa dos scopes (full y year_test last_365_days), por lo que siempre hay diferencias full vs year_test dentro del mismo run (esperado, no error).

### Evidencia de calculo (codigo)
- CLI run exige --data y --config (src/xauusd_bot/main.py, build_parser).
- run_command carga dataset con load_m5_csv(data_path) y config con load_config(config_path).
- report.md se escribe en _write_report(...) dentro de src/xauusd_bot/main.py.
- veredicto usa year_test (last_365_days por defecto), ver _slice_year_data y _verdict en src/xauusd_bot/main.py.
- metricas de expectancy_R en reporting usan trades.r_multiple (src/xauusd_bot/reporting.py).
- profit_factor en reporting usa trades.pnl (src/xauusd_bot/reporting.py).

## F) Veredicto de coherencia
- **COHERENTE**
- causa exacta: report y diagnostics del mismo run usan la misma base (trades/pnl/r_multiple) y coinciden en PF/expectancy/trades/mode dentro de tolerancia de redondeo.

## Comandos exactos para reproducir
```powershell
.\.venv\Scripts\python -m xauusd_bot run --data data/xauusd_m5_backtest_ready.csv --config configs/config.yaml
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_190312
```
