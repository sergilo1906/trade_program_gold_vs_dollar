# Smoke Decision

## Resultado

- decision: **funciona**
- run_id: `20260220_085159`
- pipeline_ok: `True`
- trades: `13`
- expectancy_R: `0.33561769230769234`
- pf: `2.3926978827179606`
- winrate: `0.7692307692307693`
- ci_low/ci_high: `-0.0919189038461538` / `0.7598103269230767`
- crosses_zero: `True`

## Comando Unico

```powershell
python scripts/run_smoke.py --data data/sample_m5.csv --config configs/config_smoke_baseline.yaml --max-bars 1200 --resamples 500 --seed 42
```

## Artefactos

- runs_root run: `outputs/runs/20260220_085159`
- scoreboard csv: `outputs/smoke_runs/smoke_scoreboard.csv`
- scoreboard md: `outputs/smoke_runs/smoke_scoreboard.md`
- scoreboard summary: `outputs/smoke_runs/smoke_scoreboard_summary.json`
- snapshot dir: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/docs/_snapshots/smoke_20260220_085158`
- input materializado: `C:/Users/Sergi/OneDrive/Escritorio/App Oro Cork/data/tmp_smoke/smoke_input_20260220_085158.csv`

## Notas

- Smoke orientado a plumbing/reproducibilidad; no implica edge productivo.
- Estrategia baseline smoke: `strategy_family=V4_SESSION_ORB` con parametros permisivos.
