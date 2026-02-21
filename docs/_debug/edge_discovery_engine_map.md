# Edge Discovery Engine Map

- audited_at_utc: `2026-02-21T08:15:00Z`
- template_status: `./_templates/plantillas_mejoradas.zip` -> MISSING (se uso estilo actual del repo + referencia `_zip_template_ref_audit_20260216`)

## Puntos de integracion [VERIFICADO]

- Data contract:
  - `src/xauusd_bot/data_loader.py`
  - columnas minimas: `timestamp, open, high, low, close`
- Entrada de simulacion:
  - `scripts/run_and_tag.py` llama `python -m xauusd_bot run --data ... --config ...`
  - artefactos por run en `outputs/runs/<run_id>/` (`run_meta.json`, `config_used.yaml`, `trades.csv`, `diagnostics/*`)
- Router de estrategia:
  - `src/xauusd_bot/engine.py` con `strategy_family`
  - familias activas detectadas en codigo: `V3_CLASSIC`, `V4_SESSION_ORB`, `VTM_VOL_MR`
- Ejecucion:
  - `src/xauusd_bot/engine.py` agenda entradas para siguiente barra (`next-open`)
- Metricas:
  - KPIs desde `trades.csv` (R por trade), bootstrap en `scripts/bootstrap_expectancy.py`
  - diagnostico de run en `scripts/diagnose_run.py`

## Flujo mas rapido para testear un edge nuevo [VERIFICADO]

Comando unico (orquestado):

```powershell
python scripts/run_edge_discovery_overnight.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/edge_discovery_candidates --baseline-config configs/config_v3_PIVOT_B4.yaml --out-dir outputs/edge_discovery_overnight --runs-root outputs/runs --resamples 2000 --seed 42 --max-bars 60000
```

Este wrapper ejecuta:

1. queue de candidatos (`scripts/run_vtm_candidates.py`)
2. post-hoc cost stress batch (`scripts/posthoc_cost_stress_batch.py`)
3. estabilidad temporal (`scripts/edge_temporal_review.py`)

## Nota operativa [VERIFICADO]

- Para reconstruccion cuando hay timeout:
  - `scripts/run_vtm_candidates.py --rebuild-only`
- Para control de disco:
  - `python scripts/cleanup_outputs.py --runs-root outputs/runs --keep-referenced-in docs`
