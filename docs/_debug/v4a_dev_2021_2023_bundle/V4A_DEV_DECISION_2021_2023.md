# V4-A DEV Decision (2021-2023)

- generated_from: `outputs/v4_dev_runs/v4_candidates_scoreboard.csv`
- baseline_B4_run_id: `20260219_235935`
- baseline_B4_trades: `26`
- candidates_total: `12`
- candidates_gate_all_pass: `0`

## Top 5 candidates (gate_all desc, expectancy_R desc, pf desc)

| candidate | run_id | gate_all | expectancy_R | pf | trades | winrate | retention_vs_b4_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v4a_orb_07 | 20260220_015938 | False | -0.021048 | 0.890207 | 329 | 0.468085 | 1265.384615 |
| v4a_orb_03 | 20260220_005035 | False | -0.024517 | 0.87438 | 333 | 0.465465 | 1280.769231 |
| v4a_orb_11 | 20260220_004047 | False | -0.025457 | 0.867922 | 327 | 0.464832 | 1257.692308 |
| v4a_orb_05 | 20260220_012603 | False | -0.026466 | 0.861948 | 329 | 0.468085 | 1265.384615 |
| v4a_orb_01 | 20260220_001535 | False | -0.029869 | 0.846956 | 333 | 0.465465 | 1280.769231 |

## Notes
- trades demasiado bajos en mayoria: `NO`
- retencion <90% en mayoria: `NO`
- run note: wrapper command timed out in terminal; scoreboard reconstructed from completed run artifacts

## Recommendation
- decision: **NO-GO**
- rationale: Ningun candidato pasa gate_all y todos muestran expectancy_R negativa en DEV.

## Binary next step
- NO-GO: matar V4-A en su forma actual y evaluar otra arquitectura.
