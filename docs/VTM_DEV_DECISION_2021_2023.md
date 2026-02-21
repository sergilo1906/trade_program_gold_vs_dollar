# VTM DEV Decision 2021-2023

- dataset: `data_local/xauusd_m5_DEV_2021_2023.csv`
- scoreboard: `outputs/vtm_dev_runs/vtm_candidates_scoreboard.csv`
- summary: `outputs/vtm_dev_runs/vtm_candidates_scoreboard_summary.json`
- expectancy audit: `docs/_snapshots/vtm_expectancy_audit_2021_2023/expectancy_audit.md`
- latest snapshot: `docs/_snapshots/vtm_dev_2021_2023_20260221_015844/`

## Hypothesis (VTM)

VTM intenta capturar reversión a media tras velas M5 de rango anómalo (rango relativo a ATR) cuando el cierre queda en extremo de vela, con salida por retorno a SMA o por time-stop. La premisa era que picos de volatilidad generan sobreextensión y rebote/reversión en barras siguientes.

## Gates

- GO: `expectancy_R > 0` AND `CI95 no cruza 0` AND `trades >= 100`
- HOLD: `expectancy_R > 0` con `CI95 cruza 0`

## Resultado Global

- candidates_total: `12`
- pass_count (GO): `0`
- hold_count: `0`
- decision: **NO-GO**
- PIPELINE_BUG_SUSPECTED: `NO`

## Top 5 Candidates

| candidate | run_id | expectancy_R | pf | trades | ci_low | ci_high | crosses_zero | gate_all |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| vtm_edge2_slow_atr | 20260221_004727 | -0.208539 | 0.625629 | 358 | -0.328684 | -0.085761 | False | False |
| vtm_edge3_slope01_strict | 20260221_012253 | -0.297521 | 0.506162 | 270 | -0.428032 | -0.162987 | False | False |
| vtm_edge1_stop12 | 20260220_204728 | -0.348327 | 0.407802 | 1312 | -0.398783 | -0.297261 | False | False |
| vtm_edge1_thr22 | 20260221_014104 | -0.381316 | 0.446957 | 878 | -0.454379 | -0.306995 | False | False |
| vtm_edge1_thr26 | 20260221_001050 | -0.399648 | 0.457272 | 264 | -0.547457 | -0.246658 | False | False |

## Notes

- Todas las variantes con CI disponible quedan completamente por debajo de cero.
- El problema no parece ser de cálculo de métricas (`expectancy audit` cuadra con `trades.csv`).
- El edge VTM en esta formulación no sobrevive en DEV 2021-2023.

## Repro Commands

Quick (<10 min aprox):

```powershell
python scripts/run_vtm_candidates.py --data data/xauusd_m5_test.csv --candidates-dir configs/vtm_candidates --out-dir outputs/vtm_smoke --runs-root outputs/runs --resamples 500 --seed 42 --max-bars 4000
```

Full DEV:

```powershell
python scripts/run_vtm_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/vtm_candidates --out-dir outputs/vtm_dev_runs --runs-root outputs/runs --resamples 5000 --seed 42
```

Rebuild scoreboard from existing runs:

```powershell
python scripts/run_vtm_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/vtm_candidates --out-dir outputs/vtm_dev_runs --runs-root outputs/runs --resamples 5000 --seed 42 --rebuild-only
```
