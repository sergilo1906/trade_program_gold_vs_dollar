from __future__ import annotations

import argparse
import shutil
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from xauusd_bot.csv_utils import read_csv_tolerant
from xauusd_bot.configuration import load_config
from xauusd_bot.data_loader import load_m5_csv
from xauusd_bot.engine import SimulationEngine
from xauusd_bot.logger import CsvLogger
from xauusd_bot.reporting import (
    MetricsBundle,
    average_entry_cost_multiplier,
    block_summary,
    compute_metrics_bundle,
    markdown_table,
    mode_performance,
    monte_carlo_execution,
    monthly_health,
)
from xauusd_bot.watch import watch_signals


def _run_backtest_once(data: pd.DataFrame, config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    cfg = dict(config)
    cfg["output_dir"] = str(output_dir)

    logger = CsvLogger(output_dir=output_dir, reset=True)
    engine = SimulationEngine(config=cfg, logger=logger)
    summary = engine.run(data)

    read_warnings: list[str] = []
    trades = read_csv_tolerant(logger.trades_path, label="trades", warnings=read_warnings)
    fills = read_csv_tolerant(logger.fills_path, label="fills", warnings=read_warnings)
    events = read_csv_tolerant(logger.events_path, label="events", warnings=read_warnings)
    period_start = pd.Timestamp(data["timestamp"].min()) if not data.empty else pd.NaT
    period_end = pd.Timestamp(data["timestamp"].max()) if not data.empty else pd.NaT
    starting_equity = float(cfg.get("starting_balance", 10_000.0))
    bundle = compute_metrics_bundle(trades, starting_equity, period_start, period_end)
    month_health = monthly_health(bundle.monthly)
    mode_df = mode_performance(trades, starting_equity)
    blocks_df = block_summary(events)
    avg_cost_mult = average_entry_cost_multiplier(fills)
    return {
        "summary": summary,
        "logger": logger,
        "trades": trades,
        "fills": fills,
        "events": events,
        "bundle": bundle,
        "month_health": month_health,
        "mode_df": mode_df,
        "blocks_df": blocks_df,
        "avg_cost_multiplier": avg_cost_mult,
        "period_start": period_start,
        "period_end": period_end,
        "starting_equity": starting_equity,
        "read_warnings": read_warnings,
    }


def _slice_year_data(data: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, str, pd.Timestamp, pd.Timestamp]:
    if data.empty:
        return data.copy(), "empty", pd.NaT, pd.NaT

    max_ts = pd.Timestamp(data["timestamp"].max())
    min_ts = pd.Timestamp(data["timestamp"].min())

    if mode == "last_12_full_calendar_months":
        first_this_month = max_ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_exclusive = first_this_month
        start = (end_exclusive - pd.DateOffset(months=12)).replace(hour=0, minute=0, second=0, microsecond=0)
        year_df = data[(data["timestamp"] >= start) & (data["timestamp"] < end_exclusive)].copy()
        if year_df.empty:
            start = max_ts - pd.Timedelta(days=365)
            year_df = data[data["timestamp"] >= start].copy()
            label = "fallback_last_365_days"
        else:
            label = "last_12_full_calendar_months"
        return year_df, label, pd.Timestamp(year_df["timestamp"].min()), pd.Timestamp(year_df["timestamp"].max())

    start = max_ts - pd.Timedelta(days=365)
    year_df = data[data["timestamp"] >= start].copy()
    if year_df.empty:
        year_df = data.copy()
        label = "full_dataset_fallback"
    else:
        label = "last_365_days"
    return year_df, label, pd.Timestamp(year_df["timestamp"].min()), pd.Timestamp(year_df["timestamp"].max())


def _format_pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def _verdict(
    year_metrics: dict[str, Any],
    year_month_health: dict[str, Any],
    bad_cost_metrics: dict[str, Any],
    monte_carlo: dict[str, Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    fails = 0

    pf = float(year_metrics.get("profit_factor", 0.0))
    mdd = float(year_metrics.get("max_drawdown", 0.0))
    expectancy = float(year_metrics.get("expectancy_R", 0.0))
    pos_months = float(year_month_health.get("positive_months_pct", 0.0))
    bad_pf = float(bad_cost_metrics.get("profit_factor", 0.0))
    bad_mdd = float(bad_cost_metrics.get("max_drawdown", 0.0))
    mc_pos = float(monte_carlo.get("positive_pct", 0.0))

    if pf < 1.3:
        fails += 1
        reasons.append(f"PF OOS bajo ({pf:.2f} < 1.30).")
    if mdd > 0.30:
        fails += 1
        reasons.append(f"MDD OOS alto ({_format_pct(mdd)} > 30%).")
    elif mdd > 0.20:
        reasons.append(f"MDD OOS por encima del ideal ({_format_pct(mdd)} > 20%).")
    if expectancy < 0.10:
        fails += 1
        reasons.append(f"Expectancy R bajo ({expectancy:.3f} < 0.10).")
    if pos_months < 0.60:
        fails += 1
        reasons.append(f"Porcentaje de meses positivos bajo ({_format_pct(pos_months)} < 60%).")
    if bad_pf < 1.0:
        fails += 1
        reasons.append(f"Escenario de costes malo pierde robustez (PF={bad_pf:.2f} < 1.00).")
    if bad_mdd > 0.35:
        fails += 1
        reasons.append(f"Escenario de costes malo con DD elevado ({_format_pct(bad_mdd)} > 35%).")
    if mc_pos < 0.70:
        fails += 1
        reasons.append(f"Monte Carlo insuficiente ({_format_pct(mc_pos)} positivos < 70%).")

    if pf < 1.0 or expectancy < 0.0 or fails >= 4:
        return "No fiable", reasons
    if fails >= 1:
        return "Dudoso", reasons
    return "Aprobado", reasons or ["Cumple umbrales de PF, DD, expectancy, meses positivos y robustez."]


def _write_report(
    report_path: Path,
    full_result: dict[str, Any],
    year_result: dict[str, Any],
    year_label: str,
    cost_df: pd.DataFrame,
    mc: dict[str, Any],
    sensitivity_df: pd.DataFrame,
    verdict: str,
    verdict_reasons: list[str],
) -> None:
    full_g = full_result["bundle"].global_metrics
    full_m = full_result["bundle"].monthly
    full_y = full_result["bundle"].yearly
    full_h = full_result["month_health"]
    full_mode = full_result["mode_df"]
    full_blocks = full_result["blocks_df"]
    full_avg_cost = float(full_result["avg_cost_multiplier"])

    year_g = year_result["bundle"].global_metrics
    year_m = year_result["bundle"].monthly
    year_y = year_result["bundle"].yearly
    year_h = year_result["month_health"]
    year_mode = year_result["mode_df"]
    year_blocks = year_result["blocks_df"]
    year_avg_cost = float(year_result["avg_cost_multiplier"])

    compare_df = pd.DataFrame(
        [
            {
                "scope": "full",
                "total_return": full_g["total_return"],
                "final_equity": full_g["final_equity"],
                "profit_factor": full_g["profit_factor"],
                "max_drawdown": full_g["max_drawdown"],
                "winrate": full_g["winrate"],
                "expectancy_R": full_g["expectancy_R"],
                "trades": full_g["trades"],
            },
            {
                "scope": f"year_test ({year_label})",
                "total_return": year_g["total_return"],
                "final_equity": year_g["final_equity"],
                "profit_factor": year_g["profit_factor"],
                "max_drawdown": year_g["max_drawdown"],
                "winrate": year_g["winrate"],
                "expectancy_R": year_g["expectancy_R"],
                "trades": year_g["trades"],
            },
        ]
    )

    lines: list[str] = []
    lines.append("# Reporte de Backtest y Fiabilidad")
    lines.append("")
    lines.append("## Resumen Ejecutivo")
    lines.append("")
    lines.append(f"- Veredicto: **{verdict}**")
    lines.append(f"- Prueba del ano usada: `{year_label}`")
    lines.append(f"- Equity final (full): `{full_g['final_equity']:.2f}`")
    lines.append(f"- Equity final (ano): `{year_g['final_equity']:.2f}`")
    lines.append(f"- PF (ano): `{year_g['profit_factor']:.3f}`")
    lines.append(f"- MDD (ano): `{_format_pct(year_g['max_drawdown'])}`")
    lines.append(f"- Expectancy R (ano): `{year_g['expectancy_R']:.3f}`")
    lines.append(
        "- Objetivo 4-8% mensual: "
        f"`{_format_pct(year_h['pct_months_ge_4'])}` de meses >=4%, "
        f"mediana mensual = `{_format_pct(year_h['median_monthly_return'])}`"
    )
    lines.append("")
    lines.append("Motivos del veredicto:")
    for reason in verdict_reasons:
        lines.append(f"- {reason}")
    lines.append("")
    lines.append("## Metricas Globales")
    lines.append("")
    lines.append(markdown_table(compare_df, float_cols={"total_return", "final_equity", "profit_factor", "max_drawdown", "winrate", "expectancy_R"}))
    lines.append("")
    lines.append("## Performance por Modo")
    lines.append("")
    lines.append("### Full")
    lines.append("")
    lines.append(markdown_table(full_mode, float_cols={"return", "profit_factor", "winrate", "expectancy_R"}))
    lines.append("")
    lines.append("### Year Test")
    lines.append("")
    lines.append(markdown_table(year_mode, float_cols={"return", "profit_factor", "winrate", "expectancy_R"}))
    lines.append("")
    lines.append("## Bloqueos y Coste Efectivo")
    lines.append("")
    lines.append(f"- Cost multiplier medio por entrada (full): `{full_avg_cost:.4f}`")
    lines.append(f"- Cost multiplier medio por entrada (ano): `{year_avg_cost:.4f}`")
    lines.append("")
    lines.append("### Bloqueos Full")
    lines.append("")
    lines.append(markdown_table(full_blocks))
    lines.append("")
    lines.append("### Bloqueos Year Test")
    lines.append("")
    lines.append(markdown_table(year_blocks))
    lines.append("")
    lines.append("### MAE/MFE (Full)")
    lines.append("")
    lines.append(
        f"- MAE_R mean/median/p90: `{full_g['mae_r_mean']:.3f}` / `{full_g['mae_r_median']:.3f}` / `{full_g['mae_r_p90']:.3f}`"
    )
    lines.append(
        f"- MFE_R mean/median/p90: `{full_g['mfe_r_mean']:.3f}` / `{full_g['mfe_r_median']:.3f}` / `{full_g['mfe_r_p90']:.3f}`"
    )
    lines.append("")
    lines.append("## Metricas Mensuales (Full)")
    lines.append("")
    lines.append(
        f"- % meses positivos: `{_format_pct(full_h['positive_months_pct'])}` | racha max meses negativos: `{full_h['max_negative_streak']}` | "
        f"mejor mes: `{full_h['best_month']}` | peor mes: `{full_h['worst_month']}`"
    )
    lines.append("")
    lines.append(markdown_table(full_m, float_cols={"return_compounded", "return_simple", "profit_factor", "max_drawdown", "pnl", "equity_start", "equity_end"}))
    lines.append("")
    lines.append("## Metricas por ano (Full)")
    lines.append("")
    lines.append(markdown_table(full_y, float_cols={"return", "profit_factor", "max_drawdown", "pnl", "equity_start", "equity_end"}))
    lines.append("")
    lines.append(f"## Prueba del ano ({year_label})")
    lines.append("")
    lines.append(
        f"- % meses positivos: `{_format_pct(year_h['positive_months_pct'])}` | racha max meses negativos: `{year_h['max_negative_streak']}` | "
        f"mejor mes: `{year_h['best_month']}` | peor mes: `{year_h['worst_month']}`"
    )
    lines.append("")
    lines.append(markdown_table(year_m, float_cols={"return_compounded", "return_simple", "profit_factor", "max_drawdown", "pnl", "equity_start", "equity_end"}))
    lines.append("")
    lines.append("## Chequeo Objetivo Mensual (4-8%)")
    lines.append("")
    monthly_target_df = pd.DataFrame(
        [
            {
                "scope": "full",
                "avg_monthly_return": full_h["avg_monthly_return"],
                "median_monthly_return": full_h["median_monthly_return"],
                "pct_months_ge_4": full_h["pct_months_ge_4"],
                "pct_months_ge_8": full_h["pct_months_ge_8"],
            },
            {
                "scope": f"year_test ({year_label})",
                "avg_monthly_return": year_h["avg_monthly_return"],
                "median_monthly_return": year_h["median_monthly_return"],
                "pct_months_ge_4": year_h["pct_months_ge_4"],
                "pct_months_ge_8": year_h["pct_months_ge_8"],
            },
        ]
    )
    lines.append(
        markdown_table(
            monthly_target_df,
            float_cols={"avg_monthly_return", "median_monthly_return", "pct_months_ge_4", "pct_months_ge_8"},
        )
    )
    lines.append("")
    lines.append("## Robustez de Costes")
    lines.append("")
    lines.append(markdown_table(cost_df, float_cols={"spread_usd", "slippage_usd", "total_return", "profit_factor", "max_drawdown"}))
    lines.append("")
    lines.append("## Monte Carlo de Ejecucion")
    lines.append("")
    lines.append(f"- Simulaciones: `{mc['sims']}`")
    lines.append(f"- Retorno P5/P50/P95: `{_format_pct(mc['return_p5'])}` / `{_format_pct(mc['return_p50'])}` / `{_format_pct(mc['return_p95'])}`")
    lines.append(f"- DD P5/P50/P95: `{_format_pct(mc['dd_p5'])}` / `{_format_pct(mc['dd_p50'])}` / `{_format_pct(mc['dd_p95'])}`")
    lines.append(f"- % simulaciones positivas: `{_format_pct(mc['positive_pct'])}`")
    lines.append("")
    lines.append("## Sensibilidad Rapida")
    lines.append("")
    lines.append(markdown_table(sensitivity_df, float_cols={"value", "total_return", "profit_factor", "max_drawdown"}))
    lines.append("")
    lines.append("## Recomendaciones")
    lines.append("")
    if verdict == "Aprobado":
        lines.append("- Mantener auditoria periodica de costes reales y drift de slippage.")
        lines.append("- Revisar trimestralmente estabilidad de parametros en ventana rodante.")
    elif verdict == "Dudoso":
        lines.append("- Reducir riesgo por trade y repetir analisis en subperiodos.")
        lines.append("- Priorizar mejora de robustez en escenario de costes malo.")
    else:
        lines.append("- No usar en produccion sin rediseno de logica de entrada/salida.")
        lines.append("- Replantear filtros de regimen y gestion de riesgo antes de re-evaluar.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_command(data_path: str, config_path: str) -> int:
    config = load_config(config_path)
    data = load_m5_csv(data_path)
    data_path_abs = Path(data_path).resolve()

    print("")
    print("DATA SUMMARY")
    print(f"file_used: {data_path_abs}")
    print(f"rows: {len(data)}")
    print(f"min_ts: {data['timestamp'].min() if len(data) else 'N/A'}")
    print(f"max_ts: {data['timestamp'].max() if len(data) else 'N/A'}")
    print(f"unique_days: {int(data['timestamp'].dt.date.nunique()) if len(data) else 0}")

    run_stamp = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(config["runs_output_dir"]) / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    output_dir = Path(config["output_dir"])
    full_result = _run_backtest_once(data, config, output_dir=output_dir)
    for warning in full_result.get("read_warnings", []):
        print(f"WARN: {warning}")

    for name in ("events.csv", "trades.csv", "signals.csv", "fills.csv"):
        src = output_dir / name
        if src.exists():
            shutil.copy2(src, run_dir / name)

    year_data, year_label, year_start, year_end = _slice_year_data(data, str(config.get("year_test_mode", "last_365_days")))
    year_result = _run_backtest_once(year_data, config, output_dir=run_dir / "year_test")
    for warning in year_result.get("read_warnings", []):
        print(f"WARN: {warning}")

    cost_scenarios = [
        {"scenario": "base", "spread_usd": 0.41, "slippage_usd": 0.05},
        {"scenario": "bad", "spread_usd": 0.70, "slippage_usd": 0.15},
        {"scenario": "good", "spread_usd": 0.30, "slippage_usd": 0.00},
    ]
    cost_rows: list[dict[str, Any]] = []
    cost_metrics_map: dict[str, dict[str, Any]] = {}
    for item in cost_scenarios:
        cfg_case = dict(config)
        cfg_case["spread_usd"] = item["spread_usd"]
        cfg_case["slippage_usd"] = item["slippage_usd"]
        case_result = _run_backtest_once(data, cfg_case, output_dir=run_dir / f"cost_{item['scenario']}")
        for warning in case_result.get("read_warnings", []):
            print(f"WARN: {warning}")
        g = case_result["bundle"].global_metrics
        cost_rows.append(
            {
                "scenario": item["scenario"],
                "spread_usd": item["spread_usd"],
                "slippage_usd": item["slippage_usd"],
                "total_return": g["total_return"],
                "profit_factor": g["profit_factor"],
                "max_drawdown": g["max_drawdown"],
            }
        )
        cost_metrics_map[item["scenario"]] = g
    cost_df = pd.DataFrame(cost_rows)

    mc = monte_carlo_execution(
        trades=year_result["trades"],
        fills=year_result["fills"],
        starting_equity=float(config.get("starting_balance", 10_000.0)),
        sims=int(config.get("monte_carlo_sims", 300)),
        seed=int(config.get("monte_carlo_seed", 42)),
        spread_low=0.30,
        spread_high=0.70,
        slip_low=0.00,
        slip_high=0.15,
    )

    sensitivity_cfg = config.get("sensitivity", {})
    sensitivity_rows: list[dict[str, Any]] = []
    for param in ("trailing_mult", "body_ratio", "shock_threshold"):
        values = sensitivity_cfg.get(param, [])
        for value in values:
            cfg_case = dict(config)
            cfg_case[param] = float(value)
            case_result = _run_backtest_once(
                year_data,
                cfg_case,
                output_dir=run_dir / "sensitivity" / f"{param}_{str(value).replace('.', '_')}",
            )
            for warning in case_result.get("read_warnings", []):
                print(f"WARN: {warning}")
            g = case_result["bundle"].global_metrics
            sensitivity_rows.append(
                {
                    "parameter": param,
                    "value": float(value),
                    "total_return": g["total_return"],
                    "profit_factor": g["profit_factor"],
                    "max_drawdown": g["max_drawdown"],
                    "trades": g["trades"],
                }
            )
    sensitivity_df = pd.DataFrame(sensitivity_rows)

    verdict, verdict_reasons = _verdict(
        year_metrics=year_result["bundle"].global_metrics,
        year_month_health=year_result["month_health"],
        bad_cost_metrics=cost_metrics_map.get("bad", {}),
        monte_carlo=mc,
    )

    report_path = run_dir / "report.md"
    _write_report(
        report_path=report_path,
        full_result=full_result,
        year_result=year_result,
        year_label=year_label,
        cost_df=cost_df,
        mc=mc,
        sensitivity_df=sensitivity_df,
        verdict=verdict,
        verdict_reasons=verdict_reasons,
    )

    full_g = full_result["bundle"].global_metrics
    year_g = year_result["bundle"].global_metrics

    print("")
    print("Simulation finished")
    print(f"events.csv: {full_result['summary']['events_path']}")
    print(f"trades.csv: {full_result['summary']['trades_path']}")
    print(f"signals.csv: {full_result['summary']['signals_path']}")
    print(f"fills.csv: {full_result['summary']['fills_path']}")
    print(f"closed_trades: {full_result['summary']['closed_trades']}")
    print(f"states_visited: {', '.join(full_result['summary']['states_visited'])}")
    print("")
    print("SIM SUMMARY")
    print(f"sim_start_ts: {full_result['summary']['sim_start_ts']}")
    print(f"sim_end_ts: {full_result['summary']['sim_end_ts']}")
    print(f"sim_days: {full_result['summary']['sim_days']}")
    print(f"closed_trades: {full_result['summary']['closed_trades']}")
    print(f"final_equity: {full_g['final_equity']:.2f}")
    print(f"total_return: {_format_pct(full_g['total_return'])}")
    print(f"PF: {full_g['profit_factor']:.3f}")
    print(f"MDD: {_format_pct(full_g['max_drawdown'])}")
    print(f"winrate: {_format_pct(full_g['winrate'])}")
    print(f"expectancy_R: {full_g['expectancy_R']:.3f}")
    print("")
    print("YEAR TEST")
    print(f"mode: {year_label}")
    print(f"period_start: {year_start}")
    print(f"period_end: {year_end}")
    print(f"year_final_equity: {year_g['final_equity']:.2f}")
    print(f"year_total_return: {_format_pct(year_g['total_return'])}")
    print(f"year_PF: {year_g['profit_factor']:.3f}")
    print(f"year_MDD: {_format_pct(year_g['max_drawdown'])}")
    print(f"year_expectancy_R: {year_g['expectancy_R']:.3f}")
    print(
        "year_monthly_target: "
        f"pct>=4={_format_pct(year_result['month_health']['pct_months_ge_4'])} | "
        f"pct>=8={_format_pct(year_result['month_health']['pct_months_ge_8'])} | "
        f"median={_format_pct(year_result['month_health']['median_monthly_return'])}"
    )
    print("")
    print(f"quick_verdict: {verdict}")
    print(f"report_path: {report_path.resolve()}")
    return 0


def watch_command(file_path: str, tail: int, once: bool, poll_interval: float) -> int:
    return watch_signals(file_path=file_path, tail=tail, once=once, poll_interval=poll_interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xauusd_bot", description="XAUUSD H1->M15->M5 simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run simulator/backtest")
    run_parser.add_argument("--data", required=True, help="Path to M5 CSV file")
    run_parser.add_argument("--config", required=True, help="Path to config YAML")

    watch_parser = subparsers.add_parser("watch", help="Tail relevant signal events from signals.csv")
    watch_parser.add_argument("--file", required=True, help="Path to signals CSV (e.g., output/signals.csv)")
    watch_parser.add_argument("--tail", type=int, default=30, help="Print last N relevant lines before following")
    watch_parser.add_argument("--once", action="store_true", help="Print tail and exit (no follow loop)")
    watch_parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds for follow mode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_command(data_path=args.data, config_path=args.config)
    if args.command == "watch":
        return watch_command(file_path=args.file, tail=args.tail, once=args.once, poll_interval=args.poll_interval)
    parser.print_help()
    return 1

