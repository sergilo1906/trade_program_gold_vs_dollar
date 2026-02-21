# NEXT STEPS TOMORROW

## Decision de arranque

- estado overnight: `NO VIABLE (de momento)` para la tanda `edge_discovery_candidates`.
- objetivo manana: encontrar un edge con n suficiente y CI menos ambigua, manteniendo pipeline actual.

## Tareas (ordenadas)

1. Ejecutar una ronda nueva centrada en **frecuencia + simplicidad** (6 configs max por familia).
   - Familia A: trend-following minimal (EMA/ADX + ATR stop).
   - Familia B: mean-reversion minimal (zscore/EMA + time-stop).
2. Mantener falsacion igual para todos los candidatos:
   - run + diagnose + bootstrap (2000 rapido, 5000 para finalistas)
   - post-hoc +20/+50
   - segmentacion temporal 4 bloques + hourly negativos >=10 trades.
3. Gate operativo de promocion (estricto):
   - expectancy_R > 0
   - CI no cruza 0
   - trades >= 100 (DEV analizado)
   - PF > 1.1 (orientativo minimo).
4. Si no aparece ningun candidato que pase gates:
   - cortar exploracion incremental y pivotar arquitectura a framework mas simple de dos motores (Trend/MR) con menos parametros.
5. Consolidar evidencia en snapshot unico para decision ejecutiva.

## Comandos exactos propuestos

Ronda controlada overnight (si ya existe set de configs nuevo):

```powershell
python scripts/run_edge_discovery_overnight.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates2 --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_discovery_overnight2 --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000
```

Reconstruccion limpia si hay timeout:

```powershell
python scripts/run_vtm_candidates.py --data data/tmp_vtm/vtm_input_<STAMP>.csv --candidates-dir configs/edge_discovery_candidates2 --out-dir outputs/edge_discovery_overnight2_clean --runs-root outputs/runs --baseline-config configs/config_v3_PIVOT_B4.yaml --rebuild-only
```

## Que NO tocar todavia

- No tocar la logica legacy de B4 en produccion.
- No meter filtros ad-hoc por hora para "forzar" metricas.
- No hacer grids amplios ni tuning masivo sin potencia estadistica.
