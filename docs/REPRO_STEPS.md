# REPRO STEPS (LOCAL)

## 1) Setup

```powershell
# 1. (Opcional) Descomprimir ZIP del repo
Expand-Archive -Path "C:\Users\Sergi\OneDrive\Escritorio\App Oro Cork (3).zip" -DestinationPath "C:\Users\Sergi\OneDrive\Escritorio" -Force

# 2. Ir al repo
Set-Location "C:\Users\Sergi\OneDrive\Escritorio\App Oro Cork"

# 3. Crear entorno virtual
py -3.11 -m venv .venv

# 4. Instalar dependencias
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e .

# 5. Verificar CLI real
.\.venv\Scripts\python -m xauusd_bot --help
```

## 2) Backtest (run)

```powershell
.\.venv\Scripts\python -m xauusd_bot run --data data/xauusd_m5_backtest_ready.csv --config configs/config.yaml
```

## 3) Detectar último run

```powershell
Get-ChildItem outputs/runs | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime
```

## 4) Diagnóstico A–N

```powershell
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/<RUN_ID>
```

## 5) Artefactos esperados

Ruta: `outputs/runs/<RUN_ID>/diagnostics/`

- `A_perf_by_mode.csv`
- `B_perf_by_session_bucket.csv`
- `C_perf_by_hour_utc.csv`
- `D_costR_percentiles.csv`
- `E_blocks.csv`
- `F_blocks_by_hour_utc.csv`
- `G_signals_by_hour_utc.csv`
- `H_perf_by_hour_robust.csv`
- `I_perf_by_regime_at_entry.csv`
- `J_signals_state_counts.csv`
- `K_regime_event_counts.csv`
- `L_regime_segments.csv`
- `M_regime_time_share.csv`
- `N_signals_by_regime.csv`
- `diagnostics.md`

## 6) Verificaciones rápidas

```powershell
Get-ChildItem outputs/runs/<RUN_ID>/diagnostics | Select-Object Name,Length
Get-Content outputs/runs/<RUN_ID>/diagnostics/diagnostics.md -TotalCount 80
```
