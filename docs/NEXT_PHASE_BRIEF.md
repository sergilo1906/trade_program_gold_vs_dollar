# Next Phase Brief (Deep Research)

## Hechos observados (run 20260218_161547)

1. Ejecución real concentrada en `TREND` (`16` trades; `PF=0.52`; `expectancy_R=-0.1351`).
2. Oportunidades detectadas: `62` (`SIGNAL_DETECTED`).
3. Bloqueos sobre oportunidades:
   - `SESSION_BLOCK: 40 (64.52%)`
   - `COST_FILTER_BLOCK: 5 (8.06%)`
   - `SHOCK_BLOCK: 1 (1.61%)`
4. Coste en R estable y bajo (`mean~0.0184R`, `p90~0.0185R`).
5. Pérdidas concentradas en horas UTC concretas (8, 11, 14), con mejor comportamiento en 10 y 15.
6. Share temporal de régimen:
   - `TREND 82.96%`
   - `NO_TRADE 16.86%`
   - `RANGE 0.18%`
7. Churn de régimen elevado entre TREND y NO_TRADE (altos conteos de `*_ENTER` / `*_EXIT`).
8. Asignación de oportunidades por régimen: `100% TREND`.

## Hipótesis testables (sin cambiar reglas)

1. El `expectancy_R` negativo está dominado por una franja horaria reducida, no por toda la sesión.
2. El `SESSION_BLOCK` está reduciendo oportunidades en horas con señal útil y podría estar desalineado con el perfil horario observado.
3. El coste no es driver principal de la pérdida neta; el driver principal es la calidad de entrada por contexto horario/regime state.
4. El churn TREND/NO_TRADE podría degradar continuidad del contexto (estado) alrededor de señales detectadas.
5. La ausencia práctica de RANGE en oportunidades ejecutables limita la comparación empírica TREND-only vs regime-switch en este dataset.

## Qué experimentar en Deep Research (diagnóstico/ablación)

1. **Ablación horaria offline**:
   - Recalcular KPIs excluyendo horas con peor `expectancy_R` (sin tocar engine), para medir sensibilidad de PF/expectancy.
2. **Matriz oportunidad->bloqueo por hora**:
   - Para cada hora: opportunities, block counts, block ratio, trades ejecutados.
3. **Análisis de secuencia de estados**:
   - Transiciones `WAIT_H1_BIAS -> WAIT_M5_ENTRY -> IN_TRADE` por hora y por régimen activo.
4. **Dwell/churn vs resultado**:
   - Relacionar duración del segmento de régimen previo a cada señal con outcome de trade asociado.
5. **Robustez de muestra**:
   - Bootstrap por hora/regime para intervalos de confianza de expectancy_R y winrate.

## Entregables esperados de la fase de research

1. Tabla de sensibilidad PF/expectancy por exclusión horaria incremental.
2. Informe de fricción de bloqueos por hora con denominador explícito.
3. Informe de churn y dwell con correlación a calidad de señal.
4. Decisión soportada por datos sobre arquitectura (trend-only vs regime-switch), basada en cobertura de régimen y performance estratificada.
