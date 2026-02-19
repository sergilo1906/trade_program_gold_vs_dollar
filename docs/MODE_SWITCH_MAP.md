# MODE SWITCH MAP

Busqueda realizada en `configs/*.yaml` y `configs/*.yml` para claves:
- `mode`
- `default_mode`
- `force_mode`
- `enabled_modes`
- `regime_switch`
- `ablation_force_regime`

## Hallazgos

### Clave que fija el modo
- Clave activa detectada: `ablation_force_regime`
- Valores validos (segun comentario en config): `AUTO | TREND | RANGE | NO_TRADE`

### Evidencia en archivos
- `configs/config.yaml`: `ablation_force_regime: AUTO  # AUTO | TREND | RANGE | NO_TRADE`
- `configs/config_ablation_nofilters.yaml`: `ablation_force_regime: AUTO`
- `configs/config_ablation_range.yaml`: `ablation_force_regime: RANGE`
- `configs/config_ablation_trend.yaml`: `ablation_force_regime: TREND`
- `configs/config_target_4_8.yaml`: `ablation_force_regime: RANGE`
- `configs/config_RANGE.yaml`: `ablation_force_regime: RANGE`
- `configs/config_TREND.yaml`: `ablation_force_regime: TREND`

### Archivos sin clave de modo detectada
- `configs/iter1.yaml`
- `configs/iter2.yaml`

## Configs usadas en esta fase
- `configs/config_RANGE.yaml` -> fuerza `RANGE`
- `configs/config_TREND.yaml` -> fuerza `TREND`

## Plantillas mejoradas
- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.
