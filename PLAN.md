## Objetivo

Implementar una estrategia MTF realista y auditable en el proyecto actual, manteniendo el CLI existente y generando en un solo comando:

1. Backtest completo
2. Prueba del último año
3. Métricas globales, mensuales y por año
4. Robustez de costes, Monte Carlo y sensibilidad
5. `report.md` con veredicto final

## Arquitectura existente detectada

- Entrada CLI: `src/xauusd_bot/main.py`
- Motor de simulación: `src/xauusd_bot/engine.py`
- Reglas por timeframe: `src/xauusd_bot/strategy/*.py`
- Indicadores: `src/xauusd_bot/indicators.py`
- Resample HTF: `src/xauusd_bot/timeframes.py`
- Riesgo: `src/xauusd_bot/risk.py`
- Persistencia CSV: `src/xauusd_bot/logger.py`
- Configuración: `configs/config.yaml`

## Cambios planeados

### 1) Core cuantitativo

- Indicadores exactos:
  - EMA con init SMA
  - TR
  - ATR Wilder
  - RSI Wilder
  - Rolling HH/LL para BOS
- Resample M15/H1 y uso exclusivo de velas HTF cerradas.

### 2) Estado y ejecución

- Mantener estados:
  - `WAIT_H1_BIAS`
  - `WAIT_M15_CONFIRM`
  - `WAIT_M5_ENTRY`
  - `IN_TRADE`
- Entrada en next-bar open (señal en cierre M5 -> ejecución en open M5 siguiente).
- Intrabar con OHLC para SL/TP y regla SL-priority si colisión en misma vela.
- 1 posición máximo, cooldown tras cierre, shock cooldown.
- Gestión avanzada:
  - SL estructural + ATR floor
  - sizing por riesgo porcentual de equity
  - TP1 parcial + BE
  - trailing chandelier tras TP1
  - time stop
  - M15 failure exit
  - forced close por sesión
- Costes por fill (spread + slippage adverso).

### 3) Gobernanza de riesgo

- Daily stop (R y %equity)
- Weekly stop (R y %equity)
- Loss streak (3 pérdidas -> 24h block)
- Trazabilidad de bloqueos con eventos `BLOCKED_*`.

### 4) Outputs y auditoría

- Mantener:
  - `output/events.csv`
  - `output/trades.csv`
  - `output/signals.csv`
- Añadir:
  - `output/fills.csv`
- Crear carpeta de corrida:
  - `outputs/runs/<timestamp>/`
  - copia de CSV principales
  - `report.md`

### 5) Métricas y fiabilidad práctica

- Globales: retorno, equity final, MDD, PF, winrate, payoff, expectancy_R, MAE/MFE, trades/mes.
- Mensuales: retorno simple/compuesto, PF, DD, #trades, meses positivos, racha negativa, mejor/peor mes.
- Por año: agregado anual.
- Prueba del año: últimos 365 días.
- Robustez costes: base/malo/bueno.
- Monte Carlo ejecución: 300 simulaciones por defecto, percentiles retorno/DD y ratio de paths positivos.
- Sensibilidad rápida: trailing/body_ratio/shock threshold en grilla pedida.

### 6) QA mínimo anti-lookahead

- Test de EMA.
- Test de ATR Wilder.
- Test de next-open entry (no misma vela).
- Test de alineación HTF cerrada.

## Criterios de aceptación

- `python -m xauusd_bot run --data <csv> --config <yaml>` ejecuta todo el pipeline.
- No hay lookahead HTF.
- Los resultados son deterministas para mismos inputs/config.
- Se genera `report.md` con veredicto y razones concretas.
