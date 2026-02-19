# Ablation Hours Summary

- run_dir: `outputs\runs\20260218_161547`
- trades source: `outputs\runs\20260218_161547\trades.csv`
- R column detected: `r_multiple`
- timestamp column detected: `entry_time`

## Results

| scenario | excluded_hours_utc | pf | expectancy_R | winrate | trades |
| --- | --- | --- | --- | --- | --- |
| BASE |  | 0.5200000000000001 | -0.1350975 | 0.375 | 16 |
| EXCL_8_11_14 | 8,11,14 | 1.7464247029089024 | 0.10566222222222221 | 0.5555555555555556 | 9 |
| EXCL_0_7 | 0,1,2,3,4,5,6,7 | 0.5200000000000001 | -0.1350975 | 0.375 | 16 |
| EXCL_16_19 | 16,17,18,19 | 0.5200000000000001 | -0.1350975 | 0.375 | 16 |

- output_csv: `outputs\runs\20260218_161547\diagnostics\ABLAT_hours.csv`