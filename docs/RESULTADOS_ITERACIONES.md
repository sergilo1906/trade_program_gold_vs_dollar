# Resultados de Iteraciones Parametricas

## Objetivo

Probar hasta 2 iteraciones controladas (solo parametros) para acercar robustez real y objetivo mensual, sin tocar logica.

## Corridas evaluadas

- Base: `configs/config.yaml` -> `outputs/runs/20260217_220016/report.md`
- Iteracion 1: `configs/iter1.yaml` -> `outputs/runs/20260217_220443/report.md`
- Iteracion 2: `configs/iter2.yaml` -> `outputs/runs/20260217_220838/report.md`

## Parametros por iteracion

- `iter1`: `body_ratio=0.65`, `wick_ratio_max=0.25`, `bos_lookback=5`, `trailing_mult=2.0`
- `iter2`: `body_ratio=0.75`, `wick_ratio_max=0.15`, `bos_lookback=8`, `trailing_mult=3.0`

## Comparativa (prueba del ultimo ano + robustez)

| setup | year_pf | year_mdd | year_expectancy_R | bad_cost_pf | bad_cost_mdd | mc_positive | pct_months_ge_4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0.8993 | 0.0223 | -0.0319 | 0.6971 | 0.0249 | 0.00% | 0.00% |
| iter1 | 0.8105 | 0.0223 | -0.0680 | 0.6119 | 0.0286 | 0.00% | 0.00% |
| iter2 | 0.5584 | 0.0263 | -0.1746 | 0.5015 | 0.0325 | 0.00% | 0.00% |

## Conclusiones

- Ninguna iteracion mejora el baseline: ambas reducen PF OOS y empeoran expectancy.
- En costes malos, `iter1` y `iter2` son menos robustas que base (PF mas bajo y DD mayor).
- Objetivo 4%-8% mensual sigue sin evidencias en los 3 casos (`%>=4` = 0.00%).

## Configuracion seleccionada

Se mantiene `configs/config.yaml` por ser la alternativa mas simple y la menos mala en robustez dentro de este set de pruebas.
