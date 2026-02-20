# Pivot Plan: Trend or Mean-Reversion (Post V4B NO-GO)

## Trigger

Use this pivot plan because `gate_all=0` in `docs/V4B_DEV_DECISION_2021_2023_V2.md`.

## Route 1: Trend-Following Simple

Hypothesis:
- The current ORB variants do not keep confidence interval away from zero.
- A simpler trend family with stronger directional filter may reduce false breakout churn.

Candidate set (6 configs):
- `configs/v5_candidates_trend/v5_trend_01.yaml`
- `configs/v5_candidates_trend/v5_trend_02.yaml`
- `configs/v5_candidates_trend/v5_trend_03.yaml`
- `configs/v5_candidates_trend/v5_trend_04.yaml`
- `configs/v5_candidates_trend/v5_trend_05.yaml`
- `configs/v5_candidates_trend/v5_trend_06.yaml`

Parameter axes (small grid):
- trend strength threshold (low/med/high)
- ATR stop multiplier (tight/medium)
- RR target (1.2 / 1.8)

## Route 2: Mean-Reversion Simple

Hypothesis:
- If edge is weak in breakout mode, a controlled pullback reversion setup may stabilize expectancy under costs.

Candidate set (6 configs):
- `configs/v5_candidates_mr/v5_mr_01.yaml`
- `configs/v5_candidates_mr/v5_mr_02.yaml`
- `configs/v5_candidates_mr/v5_mr_03.yaml`
- `configs/v5_candidates_mr/v5_mr_04.yaml`
- `configs/v5_candidates_mr/v5_mr_05.yaml`
- `configs/v5_candidates_mr/v5_mr_06.yaml`

Parameter axes (small grid):
- entry deviation threshold (low/high)
- ATR stop multiplier (tight/medium)
- time stop length (short/medium)

## Commands (after creating candidate YAMLs)

Trend queue:

```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v5_candidates_trend --out-dir outputs/v5_dev_runs_trend --resamples 5000 --seed 42
python scripts/build_v4_scoreboard_from_runs.py --data data_local/xauusd_m5_DEV_2021_2023.csv --baseline-config configs/config_v3_PIVOT_B4.yaml --candidates-dir configs/v5_candidates_trend --runs-root outputs/runs --out-dir outputs/v5_dev_runs_trend --note "v5 trend reconstructed"
```

Mean-reversion queue:

```powershell
python scripts/run_v4_candidates.py --data data_local/xauusd_m5_DEV_2021_2023.csv --candidates-dir configs/v5_candidates_mr --out-dir outputs/v5_dev_runs_mr --resamples 5000 --seed 42
python scripts/build_v4_scoreboard_from_runs.py --data data_local/xauusd_m5_DEV_2021_2023.csv --baseline-config configs/config_v3_PIVOT_B4.yaml --candidates-dir configs/v5_candidates_mr --runs-root outputs/runs --out-dir outputs/v5_dev_runs_mr --note "v5 mr reconstructed"
```

## GO/NO-GO Criteria

- `gate_all >= 1` minimum.
- no candidate accepted if `crosses_zero=True`.
- reject candidate if improvement only appears with trade collapse (`retention_vs_b4_pct < 90`).

## Engine Compatibility Note

Current engine strategy switch is centered on `strategy_family` in `src/xauusd_bot/engine.py`.
- If Trend/MR candidates can be expressed with existing families (`AUTO`, `V4_SESSION_ORB`, existing v3 keys), no engine change is needed.
- If a new family is required, implement it in `src/xauusd_bot/engine.py` at the `strategy_family` dispatch and signal-evaluation branch, keeping next-open and OHLC-only constraints unchanged.
