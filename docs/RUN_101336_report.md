# Reporte de Backtest y Fiabilidad

## Resumen Ejecutivo

- Veredicto: **Aprobado**
- Prueba del ano usada: `last_365_days`
- Equity final (full): `18563.09`
- Equity final (ano): `21858.29`
- PF (ano): `3.673`
- MDD (ano): `9.20%`
- Expectancy R (ano): `0.761`
- Objetivo 4-8% mensual: `61.54%` de meses >=4%, mediana mensual = `6.29%`

Motivos del veredicto:
- Cumple umbrales de PF, DD, expectancy, meses positivos y robustez.

## Metricas Globales

| scope | total_return | final_equity | profit_factor | max_drawdown | winrate | expectancy_R | trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full | 0.8563 | 18563.0938 | 2.3635 | 0.1806 | 0.6667 | 0.4933 | 18 |
| year_test (last_365_days) | 1.1858 | 21858.2918 | 3.6734 | 0.0920 | 0.7857 | 0.7606 | 14 |

## Performance por Modo

### Full

| mode | trades | return | profit_factor | winrate | expectancy_R |
| --- | --- | --- | --- | --- | --- |
| RANGE | 18 | 0.8563 | 2.3635 | 0.6667 | 0.4933 |

### Year Test

| mode | trades | return | profit_factor | winrate | expectancy_R |
| --- | --- | --- | --- | --- | --- |
| RANGE | 14 | 1.1858 | 3.6734 | 0.7857 | 0.7606 |

## Bloqueos y Coste Efectivo

- Cost multiplier medio por entrada (full): `1.0000`
- Cost multiplier medio por entrada (ano): `1.0000`

### Bloqueos Full

| block_type | count |
| --- | --- |
| COST_FILTER_BLOCK | 5 |
| SESSION_BLOCK | 89 |
| SHOCK_BLOCK | 0 |
| BLOCKED_MAX_TRADES_DAY | 0 |
| MAX_TRADES_BLOCK | 0 |

### Bloqueos Year Test

| block_type | count |
| --- | --- |
| COST_FILTER_BLOCK | 3 |
| SESSION_BLOCK | 59 |
| SHOCK_BLOCK | 0 |
| BLOCKED_MAX_TRADES_DAY | 0 |
| MAX_TRADES_BLOCK | 0 |

### MAE/MFE (Full)

- MAE_R mean/median/p90: `0.583` / `0.556` / `1.123`
- MFE_R mean/median/p90: `1.195` / `1.314` / `2.198`

## Metricas Mensuales (Full)

- % meses positivos: `50.00%` | racha max meses negativos: `2` | mejor mes: `2026-02` | peor mes: `2024-12`

| month | return_compounded | return_simple | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-09 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10000.0000 | 10000.0000 |
| 2024-10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 10000.0000 | 10000.0000 |
| 2024-11 | -0.0863 | -0.0863 | 0.0000 | 0.0000 | 1 | -863.3544 | 10000.0000 | 9136.6456 |
| 2024-12 | -0.0954 | -0.0872 | 0.0000 | 0.0000 | 1 | -872.0805 | 9136.6456 | 8264.5651 |
| 2025-01 | 0.0276 | 0.0228 | 1.2930 | 0.0000 | 2 | 227.9072 | 8264.5651 | 8492.4723 |
| 2025-02 | 0.0817 | 0.0694 | 0.0000 | 0.0000 | 1 | 693.6568 | 8492.4723 | 9186.1291 |
| 2025-03 | 0.2451 | 0.2251 | 0.0000 | 0.0000 | 2 | 2251.3963 | 9186.1291 | 11437.5254 |
| 2025-04 | 0.0743 | 0.0850 | 0.0000 | 0.0000 | 1 | 849.5681 | 11437.5254 | 12287.0935 |
| 2025-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 12287.0935 | 12287.0935 |
| 2025-06 | -0.0895 | -0.1100 | 0.0000 | 0.0000 | 1 | -1100.0216 | 12287.0935 | 11187.0718 |
| 2025-07 | 0.0629 | 0.0704 | 0.0000 | 0.0000 | 1 | 703.7199 | 11187.0718 | 11890.7917 |
| 2025-08 | 0.1068 | 0.1270 | 0.0000 | 0.0000 | 1 | 1270.1021 | 11890.7917 | 13160.8938 |
| 2025-09 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 13160.8938 | 13160.8938 |
| 2025-10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 13160.8938 | 13160.8938 |
| 2025-11 | 0.0412 | 0.0542 | 1.4117 | 0.0877 | 2 | 542.1853 | 13160.8938 | 13703.0791 |
| 2025-12 | 0.0938 | 0.1285 | 0.0000 | 0.0000 | 1 | 1284.6891 | 13703.0791 | 14987.7682 |
| 2026-01 | -0.0215 | -0.0322 | 0.7613 | 0.0000 | 2 | -322.2848 | 14987.7682 | 14665.4834 |
| 2026-02 | 0.2658 | 0.3898 | 0.0000 | 0.0000 | 2 | 3897.6104 | 14665.4834 | 18563.0938 |

## Metricas por ano (Full)

| year | return | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024.0 | -0.1735 | 0.0000 | 0.0954 | 2.0 | -1735.4349 | 10000.0000 | 8264.5651 |
| 2025.0 | 0.8135 | 3.1044 | 0.0895 | 12.0 | 6723.2031 | 8264.5651 | 14987.7681 |
| 2026.0 | 0.2385 | 3.6484 | 0.0000 | 4.0 | 3575.3256 | 14987.7681 | 18563.0938 |

## Prueba del ano (last_365_days)

- % meses positivos: `61.54%` | racha max meses negativos: `1` | mejor mes: `2026-02` | peor mes: `2025-06`

| month | return_compounded | return_simple | profit_factor | max_drawdown | trades | pnl | equity_start | equity_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-02 | 0.0817 | 0.0817 | 0.0000 | 0.0000 | 1 | 816.7901 | 10000.0000 | 10816.7901 |
| 2025-03 | 0.2451 | 0.2651 | 0.0000 | 0.0000 | 2 | 2651.0493 | 10816.7901 | 13467.8394 |
| 2025-04 | 0.0743 | 0.1000 | 0.0000 | 0.0000 | 1 | 1000.3778 | 13467.8394 | 14468.2173 |
| 2025-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 14468.2173 | 14468.2173 |
| 2025-06 | -0.0895 | -0.1295 | 0.0000 | 0.0000 | 1 | -1295.2902 | 14468.2173 | 13172.9270 |
| 2025-07 | 0.0629 | 0.0829 | 0.0000 | 0.0000 | 1 | 828.6396 | 13172.9270 | 14001.5667 |
| 2025-08 | 0.1068 | 0.1496 | 0.0000 | 0.0000 | 1 | 1495.5622 | 14001.5667 | 15497.1289 |
| 2025-09 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 15497.1289 | 15497.1289 |
| 2025-10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 15497.1289 | 15497.1289 |
| 2025-11 | 0.0412 | 0.0638 | 1.4117 | 0.0877 | 2 | 638.4305 | 15497.1289 | 16135.5593 |
| 2025-12 | 0.0938 | 0.1513 | 0.0000 | 0.0000 | 1 | 1512.7386 | 16135.5593 | 17648.2979 |
| 2026-01 | -0.0215 | -0.0379 | 0.7613 | 0.0000 | 2 | -379.4946 | 17648.2979 | 17268.8033 |
| 2026-02 | 0.2658 | 0.4589 | 0.0000 | 0.0000 | 2 | 4589.4885 | 17268.8033 | 21858.2918 |

## Chequeo Objetivo Mensual (4-8%)

| scope | avg_monthly_return | median_monthly_return | pct_months_ge_4 | pct_months_ge_8 |
| --- | --- | --- | --- | --- |
| full | 0.0392 | 0.0138 | 0.4444 | 0.2778 |
| year_test (last_365_days) | 0.0662 | 0.0629 | 0.6154 | 0.3846 |

## Robustez de Costes

| scenario | spread_usd | slippage_usd | total_return | profit_factor | max_drawdown |
| --- | --- | --- | --- | --- | --- |
| base | 0.4100 | 0.0500 | 0.8563 | 2.3635 | 0.1806 |
| bad | 0.7000 | 0.1500 | 0.3202 | 2.0511 | 0.1117 |
| good | 0.3000 | 0.0000 | 0.5006 | 1.6361 | 0.2461 |

## Monte Carlo de Ejecucion

- Simulaciones: `300`
- Retorno P5/P50/P95: `111.55%` / `114.01%` / `116.51%`
- DD P5/P50/P95: `9.40%` / `10.01%` / `10.55%`
- % simulaciones positivas: `100.00%`

## Sensibilidad Rapida

| parameter | value | total_return | profit_factor | max_drawdown | trades |
| --- | --- | --- | --- | --- | --- |
| trailing_mult | 2.0000 | 1.1858 | 3.6734 | 0.0920 | 14 |
| trailing_mult | 2.5000 | 1.1858 | 3.6734 | 0.0920 | 14 |
| trailing_mult | 3.0000 | 1.1858 | 3.6734 | 0.0920 | 14 |
| body_ratio | 0.6500 | 1.1858 | 3.6734 | 0.0920 | 14 |
| body_ratio | 0.7000 | 1.1858 | 3.6734 | 0.0920 | 14 |
| body_ratio | 0.7500 | 1.1858 | 3.6734 | 0.0920 | 14 |
| shock_threshold | 2.5000 | 0.9074 | 3.3444 | 0.0920 | 13 |
| shock_threshold | 3.0000 | 1.1858 | 3.6734 | 0.0920 | 14 |
| shock_threshold | 3.5000 | 1.1858 | 3.6734 | 0.0920 | 14 |

## Recomendaciones

- Mantener auditoria periodica de costes reales y drift de slippage.
- Revisar trimestralmente estabilidad de parametros en ventana rodante.
