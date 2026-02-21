# EDGE DISCOVERY OVERNIGHT

- date_utc: `2026-02-21`
- repo: `trade_program_gold_vs_dollar`
- scope: busqueda nocturna de edge nuevo viable para XAUUSD M5 con pipeline existente
- template_status: `./_templates/plantillas_mejoradas.zip` -> **MISSING** (continuado con referencia `_zip_template_ref_audit_20260216` y estilo repo)

## Resumen Ejecutivo

- Se hizo ciclo corto repetido: hipotesis -> test rapido -> diagnostico -> matar/promover.
- Se integraron y evaluaron 5 prototipos ejecutables (`configs/edge_discovery_candidates/*`).
- Scoreboard limpio reconstruido desde runs estables (sin runs contaminados por timeout).
- Resultado estadistico: **0/5 pasa gate_all** (expectancy>0, CI no cruza 0, trades>=100).
- Audit de expectancy: **PIPELINE_BUG_SUSPECTED=NO** (scoreboard cuadra con `trades.csv`).
- Cost stress post-hoc (+20/+50) solo sobrevive en el candidato con 2 trades, no operable.
- Los candidatos con frecuencia suficiente (127-140 trades) muestran expectancy negativa y deterioro por costes.
- Veredicto operativo de esta ronda: **NO VIABLE (de momento)**.

## 1) Integracion real del repo (verificada)

- Mapa tecnico: `docs/_debug/edge_discovery_engine_map.md`
- Entrypoint de runs: `scripts/run_and_tag.py`
- Motor/selector: `src/xauusd_bot/engine.py`
- Queue runner: `scripts/run_vtm_candidates.py`
- Orquestador 1 comando: `scripts/run_edge_discovery_overnight.py`
- Diagnostico/bootstrap:
  - `scripts/diagnose_run.py`
  - `scripts/bootstrap_expectancy.py`
  - `scripts/posthoc_cost_stress_batch.py`

## 2) Hipotesis candidatas (12-20)

| id | familia | entrada/salida (resumen) | params aprox | por que podria funcionar en oro | riesgo sobreajuste | integracion |
| --- | --- | --- | --- | --- | --- | --- |
| H01 | Trend | EMA M15 pullback + BOS M5, salida RR fija | 6-8 | continuation intradia en sesiones liquidas | medio | alta |
| H02 | Trend | breakout apertura Londres + time-exit | 5-7 | expansion de rango apertura | medio | alta |
| H03 | Trend | Donchian 20 + ATR stop | 4-6 | captura de desplazamientos direccionales | medio | media |
| H04 | Trend | ADX filtro + EMA cross | 6-9 | evita chop extremo | alto | media |
| H05 | MR | VTM (barra extendida vs ATR + cierre en extremo) + target SMA | 8-12 | agotamiento de micro-impulsos | medio | alta |
| H06 | MR | RSI extremo + reentrada a EMA | 5-7 | mean reversion post overreaction | medio | media |
| H07 | MR | zscore close/EMA con time-stop | 5-7 | reversions en microestructura M5 | medio | media |
| H08 | MR | pinbar extremo + ATR stop corto | 6-8 | rechazo en zonas liquidas | alto | media |
| H09 | Breakout | ORB Asia->London | 7-10 | compresion Asia / expansion Londres | medio | alta |
| H10 | Breakout | NY open range break | 6-8 | volatilidad estructural apertura US | medio | media |
| H11 | Pullback vol | Tendencia H1 + pullback M5 si ATR_rel alto | 6-9 | continua impulsos en vol alta | medio | alta |
| H12 | Reversal vol | Vela de rango extremo + close extremo + holding corto | 6-10 | reversions violentas de exceso | medio | alta |
| H13 | Regime switch | trend y MR con switch simple ATR_rel | 8-12 | alternancia de regimenes | alto | media |
| H14 | Session MR | solo horas de menor impulso con target al VWAP proxy | 6-9 | intradia de retorno a media | alto | baja |
| H15 | Plumbing baseline | always/near-always trigger con SL/TP fijos | 3-4 | validar tuberia robusta | bajo | alta |

## 3) Edges prototipados (3-5) y resultados

Dataset de esta ronda: `data/tmp_vtm/vtm_input_20260221_062745.csv` (subset DEV, ~60k barras, 2023).  
Scoreboard limpio: `outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard.csv`

| candidate | run_id | PF | expectancy_R | trades | CI | gate_all |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `config_edge_vtm_reversal_fast_v1` | `20260221_075421` | 1.321 | 0.1828 | 2 | cruza 0 | no |
| `config_edge_v4_orb_wide_v1` | `20260221_063806` | 0.634 | -0.0946 | 140 | no cruza 0 (negativa) | no |
| `config_edge_vtm_mr_balanced_v1` | `20260221_064929` | 0.648 | -0.1263 | 4 | cruza 0 | no |
| `config_edge_v3_trend_lite_v1` | `20260221_074352` | 0.786 | -0.1601 | 127 | cruza 0 | no |
| `config_edge_vtm_mr_strict_v1` | `20260221_070041` | n/a | n/a | 0 | n/a | no |

## 4) Falsacion minima aplicada

- Expectancy audit:
  - `docs/_snapshots/edge_discovery_expectancy_audit_20260221/expectancy_audit.md`
  - resultado: `PIPELINE_BUG_SUSPECTED=NO`
- Cost stress post-hoc (trade-set fixed):
  - `outputs/posthoc_cost_stress/edge_discovery_overnight_clean_posthoc.csv`
  - candidatos con frecuencia real (127-140 trades) permanecen en expectancy negativa en +20 y +50.
  - solo 1/4 candidatos pasa PF>1 y expectancy>0 en +20/+50, pero con **2 trades**.
- Estabilidad temporal:
  - `outputs/edge_discovery_overnight_clean/edge_discovery_temporal_segments.csv`
  - `outputs/edge_discovery_overnight_clean/edge_discovery_hourly.csv`
  - ORB wide: 4/4 segmentos negativos; trend_lite: 3/4 segmentos negativos.

## 5) Comparacion honesta vs edge actual

Referencia edge actual no viable (legacy): `docs/GO_NO_GO.md`
- holdout base legacy: PF ~1.0195, expectancy ~0.013, 44 trades, CI cruza 0.

Ronda overnight:
- No mejora robusta: ningun prototipo pasa gates minimos.
- Se obtuvo mas frecuencia en 2 prototipos (127-140 trades), pero con expectancy negativa persistente.
- Complejidad de reglas contenida (5 prototipos simples), sin over-stack de filtros.
- Conclusion: no hay superioridad clara frente al estado actual en esta ronda.

## 6) Ideas descartadas rapido y por que

- VTM strict: descartada por falta de senal (0 trades).
- VTM balanced: descartada por muestra insuficiente (4 trades) y expectancy negativa.
- VTM reversal fast: descartada por muestra no operable (2 trades), CI extremadamente ambigua.
- V3 trend lite: descartada por expectancy negativa y fragilidad temporal.
- V4 ORB wide: descartada por PF<1 y 4/4 segmentos negativos.

## 7) Finalistas y nivel de confianza

- Finalista tecnico (solo para seguir iterando, no para deploy): `config_edge_vtm_reversal_fast_v1`.
- Estado real: no cumple criterio operativo por n demasiado bajo.
- Nivel de confianza del veredicto NO-VIABLE en esta ronda: **84%**.

## 8) Veredicto de esta noche

**NO VIABLE (de momento).**

Motivos:
1. `gate_all = 0/5` en scoreboard limpio.
2. Las variantes con n suficiente son negativas en expectancy.
3. La unica expectancy positiva util viene con 2 trades (no inferible).
4. Cost stress no rescata candidatos de frecuencia util.
5. Estabilidad temporal pobre (segmentos/hora negativos dominantes).

## 9) Artefactos versionados

- Snapshot principal:
  - `docs/_snapshots/edge_discovery_overnight_20260221_080630_clean/`
- Audit expectancy:
  - `docs/_snapshots/edge_discovery_expectancy_audit_20260221/`
- Scoreboard runtime:
  - `outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard.csv`
  - `outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard.md`
  - `outputs/edge_discovery_overnight_clean/vtm_candidates_scoreboard_summary.json`

