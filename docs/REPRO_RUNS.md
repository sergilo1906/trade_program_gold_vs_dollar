# Reproducibilidad de Runs (PowerShell)

## Estado de plantillas
- `_templates/plantillas_mejoradas.zip`: NO ENCONTRADO.

## Setup
```powershell
.\.venv\Scripts\python -c "import sys, pandas as pd; print(sys.version.split()[0]); print(pd.__version__)"
```

## 1) Crear run y etiquetarlo (run_meta + config_used)
```powershell
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_RANGE.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_TREND.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config.yaml
```

## 2) Diagnostico A-N
```powershell
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/<run_id>
```

## 3) Bootstrap de expectancy_R (offline)
```powershell
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/<run_id>
```

## 4) Comandos usados en esta fase
```powershell
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_200211
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_200726
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config.yaml
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_202210
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_200211 --resamples 5000 --seed 42
```

## 5) Comandos v3 (esta entrega)
```powershell
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_RANGE.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_TREND.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO.yaml

.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_210540
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_211849
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_213339

.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_210540 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_211849 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_213339 --resamples 5000 --seed 42
```

## 6) Session windows v3 AUTO (EXP_A / EXP_B / EXP_C)
```powershell
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_A.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_B.yaml
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_C.yaml

.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_221051
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_222629
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260218_224135

.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_221051 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_222629 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260218_224135 --resamples 5000 --seed 42

.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260218_221051 20260218_222629 20260218_224135 --output docs/SESSION_WINDOW_QA.csv
.\.venv\Scripts\python scripts/build_session_window_experiments.py --exp EXP_A=20260218_221051 --exp EXP_B=20260218_222629 --exp EXP_C=20260218_224135 --output docs/SESSION_WINDOW_EXPERIMENTS.md
```

## 7) Split DEV80 / HOLDOUT20 (esta entrega)
```powershell
.\.venv\Scripts\python scripts/make_holdout_split.py
.\.venv\Scripts\python scripts/append_holdout_validation_log.py
```

## 8) Walk-Forward en DEV80 (4 folds)
```powershell
.\.venv\Scripts\python scripts/walk_forward_windows.py

# Recuperacion Fold2 por espacio en disco:
.\.venv\Scripts\python scripts/run_and_tag.py --data data/tmp_wfa/Fold2_train.csv --config configs/config_v3_AUTO_EXP_A.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/run_and_tag.py --data data/tmp_wfa/Fold2_train.csv --config configs/config_v3_AUTO_EXP_B.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/run_and_tag.py --data data/tmp_wfa/Fold2_train.csv --config configs/config_v3_AUTO_EXP_C.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/run_and_tag.py --data data/tmp_wfa/Fold2_val.csv --config configs/config_v3_AUTO_EXP_C.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260219_104443
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260219_104443 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/wfa_rebuild_results.py
```

## 9) HOLDOUT final (WINNER_GLOBAL de WFA OOS)
```powershell
.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_HOLDOUT20.csv --config configs/config_v3_AUTO_EXP_B.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260219_104745
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260219_104745 --resamples 5000 --seed 42
.\.venv\Scripts\python scripts/build_holdout_report.py 20260219_104745 --output docs/HOLDOUT_REPORT.md
```

## 10) Cost stress HOLDOUT (+20% / +50%)
```powershell
rg -n "cost|spread|slippage|commission|multiplier" configs src/xauusd_bot -g "*.yaml" -g "*.py"

.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_HOLDOUT20.csv --config configs/config_v3_AUTO_EXP_B_COSTP20.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260219_105305
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260219_105305 --resamples 5000 --seed 42

.\.venv\Scripts\python scripts/run_and_tag.py --data data/xauusd_m5_HOLDOUT20.csv --config configs/config_v3_AUTO_EXP_B_COSTP50.yaml --runs-root outputs/runs
.\.venv\Scripts\python scripts/diagnose_run.py outputs/runs/20260219_105707
.\.venv\Scripts\python scripts/bootstrap_expectancy.py outputs/runs/20260219_105707 --resamples 5000 --seed 42

.\.venv\Scripts\python scripts/build_cost_stress_report.py --base-run 20260219_104745 --p20-run 20260219_105305 --p50-run 20260219_105707 --output docs/COST_STRESS.md
```

## 11) QA (WFA VAL + HOLDOUT + stress)
```powershell
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_085634 20260219_104443 20260219_093546 20260219_101410 --output docs/WFA_QA.csv
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_104745 20260219_105305 20260219_105707 --output docs/HOLDOUT_QA.csv
```

## 12) Post-run hardening (WFA report render)
```powershell
.\.venv\Scripts\python -m py_compile scripts/walk_forward_windows.py
.\.venv\Scripts\python scripts/wfa_rebuild_results.py
```

## 13) Post-hoc cost stress ideal (trade-set fijo)
```powershell
.\.venv\Scripts\python scripts/posthoc_cost_stress.py --run-dir outputs/runs/20260219_104745 --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/posthoc_cost_stress.csv
```

## 14) Rolling HOLDOUT OOS (winner EXP_B)
```powershell
.\.venv\Scripts\python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_AUTO_EXP_B.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout --resamples 5000 --seed 42
```

## 15) QA rolling HOLDOUT
```powershell
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_141334 20260219_141728 20260219_142049 20260219_142432 --output docs/ROLLING_HOLDOUT_QA.csv
```

## 16) Batch post-hoc cost stress (rolling run_ids)
```powershell
.\.venv\Scripts\python scripts/posthoc_cost_stress_batch.py --runs 20260219_141334 20260219_141728 20260219_142049 20260219_142432 --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv
```

## 17) Cost sensitivity attribution (holdout base per-trade)
```powershell
.\.venv\Scripts\python scripts/cost_sensitivity_attribution.py --per-trade outputs/posthoc_cost_stress/posthoc_cost_stress_per_trade.csv --output docs/COST_SENSITIVITY_ATTRIBUTION.md
```

## 18) Decision synthesis check (rolling post-hoc robustness)
```powershell
@'
import pandas as pd
p='outputs/posthoc_cost_stress/rolling_posthoc_cost_stress.csv'
df=pd.read_csv(p)
for f in (1.2,1.5):
    d=df[df['factor']==f].copy().sort_values('window')
    d['pf_gt_1']=d['pf']>1.0
    d['exp_gt_0']=d['expectancy_R']>0.0
    d['both']=d['pf_gt_1'] & d['exp_gt_0']
    print('\\nFACTOR',f)
    print(d[['window','run_id','pf','expectancy_R','pf_gt_1','exp_gt_0','both']].to_string(index=False))
    print('count_pf_gt_1',int(d['pf_gt_1'].sum()),'of',len(d))
    print('count_exp_gt_0',int(d['exp_gt_0'].sum()),'of',len(d))
    print('count_both',int(d['both'].sum()),'of',len(d))
'@ | python -
```

## 19) Route A config (surgical cuts)
```powershell
# Base winner clone + Route A fields
Copy-Item configs/config_v3_AUTO_EXP_B.yaml configs/config_v3_ROUTE_A.yaml -Force
```

## 20) Rolling HOLDOUT Route A (hour 13)
```powershell
.\.venv\Scripts\python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_ROUTE_A.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_routeA --resamples 5000 --seed 42
```

## 21) Post-hoc batch Route A (hour 13)
```powershell
.\.venv\Scripts\python scripts/posthoc_cost_stress_batch.py --runs 20260219_152419 20260219_152817 20260219_153128 20260219_153455 --window-map-csv outputs/rolling_holdout_routeA/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA.csv
```

## 22) Route A extension (hour 13 + 8)
```powershell
.\.venv\Scripts\python scripts/rolling_holdout_eval.py --data data/xauusd_m5_backtest_ready.csv --config configs/config_v3_ROUTE_A_H13_H8.yaml --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_routeA_h13_h8 --report docs/ROLLING_HOLDOUT_ROUTEA_H13_H8.md --resamples 5000 --seed 42

.\.venv\Scripts\python scripts/posthoc_cost_stress_batch.py --runs 20260219_154058 20260219_154459 20260219_154802 20260219_155141 --window-map-csv outputs/rolling_holdout_routeA_h13_h8/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_routeA_h13_h8.csv
```

## 23) QA Route A runs
```powershell
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_152419 20260219_152817 20260219_153128 20260219_153455 --output docs/ROUTEA_QA.csv
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_154058 20260219_154459 20260219_154802 20260219_155141 --output docs/ROUTEA_H13_H8_QA.csv
```

## 24) Route B Pivot batch (candidatos B1..B4)
```powershell
.\.venv\Scripts\python scripts/run_pivot_candidates.py --candidates configs/config_v3_PIVOT_B1.yaml configs/config_v3_PIVOT_B2.yaml configs/config_v3_PIVOT_B3.yaml configs/config_v3_PIVOT_B4.yaml --data data/xauusd_m5_backtest_ready.csv --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --resamples 5000 --seed 42 --equity-start 10000 --out-csv outputs/rolling_holdout_pivot/pivot_scoreboard.csv --out-json outputs/rolling_holdout_pivot/pivot_scoreboard_summary.json --out-md docs/PIVOT_SCOREBOARD.md
```

## 25) Route B QA (winner B4)
```powershell
.\.venv\Scripts\python scripts/v3_qa_check_param.py 20260219_164110 20260219_164425 20260219_164706 20260219_165006 --output docs/PIVOT_B4_QA.csv
```


## 26) GitHub bootstrap (public repo)
```powershell
git init -b main
python -m compileall -q src scripts tests
git add -A
git commit -m "chore: initial import"

# Preferred (requires authentication)
gh auth login
gh repo create trade_program_gold_vs_dollar --public --source=. --remote=origin --push

# Validate
git remote -v
git branch -vv
```

## 27) Commit + push for each change
```powershell
# Before starting a new change
git pull origin main

# After finishing changes
python -m compileall -q src scripts tests
powershell -ExecutionPolicy Bypass -File scripts/git_autopush.ps1
```

## 28) Update latest commit marker manually (fallback)
```powershell
python scripts/update_latest_commit.py
git add docs/LATEST_COMMIT.md
git commit -m "chore: update latest commit marker"
git push origin main
```


## 29) Import external long-history dataset (2010-2023)
```powershell
python scripts/prepare_external_m5_csv.py --input "c:\Users\Sergi\AppData\Local\Temp\8cdd5b57-94ea-429b-ae2b-337f70d37fc2_XAUUSD_2010-2023.csv.zip.fc2\XAUUSD_2010-2023.csv" --output data/xauusd_m5_2010_2023_backtest_ready.csv
python -m py_compile scripts/prepare_external_m5_csv.py
```

## 30) V4-A Session ORB candidate queue (DEV)
```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v4_candidates --out-dir outputs/v4_dev_runs --resamples 5000 --seed 42
```

## 31) V4 winner FULL validation (rolling + posthoc)
```powershell
python scripts/rolling_holdout_eval.py --data data/xauusd_m5_2010_2023_backtest_ready.csv --config <WINNER_V4_CONFIG> --windows "0.2:0.4,0.4:0.6,0.6:0.8,0.8:1.0" --runs-root outputs/runs --out-dir outputs/rolling_holdout_v4 --resamples 5000 --seed 42
```

```powershell
python scripts/posthoc_cost_stress_batch.py --runs <RID_W1> <RID_W2> <RID_W3> <RID_W4> --window-map-csv outputs/rolling_holdout_v4/rolling_holdout_runs.csv --factors 1.2 1.5 --seed 42 --resamples 5000 --out outputs/posthoc_cost_stress/rolling_posthoc_cost_stress_v4.csv
```
