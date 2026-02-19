# Cost Stress (HOLDOUT20)

- Simple cost knob used: `spread_usd` and `slippage_usd` scaled from winner config.
- Winner config base: `configs/config_v3_AUTO_EXP_B.yaml`
- Stress configs: `configs/config_v3_AUTO_EXP_B_COSTP20.yaml`, `configs/config_v3_AUTO_EXP_B_COSTP50.yaml`

## Stress Table
| scenario | run_id | spread_usd | slippage_usd | pf | expectancy_R | trades | boot_ci_low | boot_ci_high | boot_crosses_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | 20260219_104745 | 0.41 | 0.05 | 1.019508 | 0.013004 | 44 | -0.402205 | 0.438432 | True |
| +20% COST | 20260219_105305 | 0.492 | 0.06 | 1.101903 | 0.066337 | 44 | -0.347144 | 0.49096 | True |
| +50% COST | 20260219_105707 | 0.615 | 0.075 | 1.053998 | 0.035853 | 42 | -0.393653 | 0.475998 | True |
