# QA Checklist (Diagnostico + Reproducibilidad)

| Check | Status | Evidencia |
| --- | --- | --- |
| diagnose A-N presentes | OK | `outputs/runs/20260218_200211/diagnostics/`, `outputs/runs/20260218_200726/diagnostics/`, `outputs/runs/20260218_202210/diagnostics/` |
| M no vacio en RANGE y TREND | OK | `outputs/runs/20260218_200211/diagnostics/M_regime_time_share.csv` (1 fila), `outputs/runs/20260218_200726/diagnostics/M_regime_time_share.csv` (1 fila), `share` suma 1.0 |
| run_meta.json existe y tiene campos minimos | OK | `outputs/runs/20260218_202210/run_meta.json` con `run_id`, `created_utc`, `data_path`, `config_path`, `config_hash`, `ablation_force_regime`, `git_commit`, `python_version`, `pandas_version` |
| config_used.yaml existe | OK | `outputs/runs/20260218_202210/config_used.yaml` |
| scripts/run_and_tag.py funciona | OK | comando ejecutado con `configs/config.yaml`, run creado: `20260218_202210` |
| bootstrap genera CI | OK | `outputs/runs/20260218_200211/diagnostics/BOOT_expectancy_ci.csv` + `docs/RANGE_EDGE_VALIDATION.md` |
| docs/BASELINES.md actualizado | OK | `docs/BASELINES.md` incluye `BASELINE_RANGE`, `BASELINE_TREND`, `BASELINE_AUTO` |
| plantillas_mejoradas.zip localizado | FAIL | `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO |

## QA V3 (fase actual)

| Check | Status | Evidencia |
| --- | --- | --- |
| Configs v3 creadas | OK | `configs/config_v3_RANGE.yaml`, `configs/config_v3_TREND.yaml`, `configs/config_v3_AUTO.yaml` |
| Flag `enable_strategy_v3` preserva v2 cuando `false` | OK | ruta v3 condicionada en `src/xauusd_bot/engine.py`; runs v2 siguen generando output normal |
| Eventos V3 presentes | OK | `events.csv` contiene `V3_SIGNAL_*`, `V3_ENTRY`, `V3_EXIT_*`, `V3_BLOCK_*` en `20260218_210540`, `20260218_211849`, `20260218_213339` |
| Next-open validado | OK | `scripts/v3_qa_check.py` reporta `next_open_matches` = `70/70`, `331/331`, `263/263` |
| Max trades por sesion = 1 | OK | `scripts/v3_qa_check.py`: `max_trades_per_session_seen=1` en los 3 runs v3 |
| Diagnose A-N en runs v3 | OK | `outputs/runs/20260218_210540/diagnostics/`, `outputs/runs/20260218_211849/diagnostics/`, `outputs/runs/20260218_213339/diagnostics/` |
| Bootstrap ejecutado en runs v3 | OK | `BOOT_expectancy_ci.csv` generado en los 3 runs v3 |
