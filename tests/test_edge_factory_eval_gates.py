from __future__ import annotations

try:
    from scripts.lib.edge_factory_eval import apply_gates
except ModuleNotFoundError:
    from lib.edge_factory_eval import apply_gates


def test_apply_gates_dev_robust_passes_when_metrics_ok() -> None:
    metrics = {
        "trades": 150,
        "pf": 1.22,
        "expectancy_R": 0.06,
        "crosses_zero": False,
        "retention_vs_b4_pct": 92.0,
        "cost_survives_1p2": True,
        "cost_survives_1p5": True,
        "temporal_pass": True,
    }
    stage_cfg = {
        "min_trades": 100,
        "min_pf": 1.1,
        "min_expectancy_r": 0.0,
        "require_ci_non_crossing_zero": True,
        "min_retention_vs_baseline_pct": 70.0,
        "require_cost_stress_survival_p20": True,
        "require_cost_stress_survival_p50": False,
        "require_temporal_stability": True,
    }
    out = apply_gates(metrics, stage_cfg, baseline_trades=120, stage_name="dev_robust")
    assert out["gate_all"] is True
    assert out["fail_reasons"] == []


def test_apply_gates_pending_metric_fails_only_in_dev_robust() -> None:
    metrics = {
        "trades": 80,
        "pf": 1.05,
        "expectancy_R": 0.01,
        "crosses_zero": False,
        "retention_vs_b4_pct": 88.0,
        "cost_survives_1p2": True,
        # temporal_pass intentionally missing
    }
    stage_cfg = {
        "min_trades": 20,
        "min_pf": 1.0,
        "min_expectancy_r": 0.0,
        "require_ci_non_crossing_zero": False,
        "min_retention_vs_baseline_pct": 50.0,
        "require_cost_stress_survival_p20": False,
        "require_cost_stress_survival_p50": False,
        "require_temporal_stability": True,
    }

    smoke_out = apply_gates(metrics, stage_cfg, baseline_trades=100, stage_name="smoke")
    assert smoke_out["gate_flags"]["gate_temporal"] is True
    assert smoke_out["gate_all"] is True
    assert "temporal_pass" in smoke_out["pending_metrics"]

    robust_out = apply_gates(metrics, stage_cfg, baseline_trades=100, stage_name="dev_robust")
    assert robust_out["gate_flags"]["gate_temporal"] is False
    assert robust_out["gate_all"] is False
    assert any("missing metric `temporal_pass`" in x for x in robust_out["fail_reasons"])
