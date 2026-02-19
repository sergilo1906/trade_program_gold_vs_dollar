from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "outputs" / "runs"
WFA_SUMMARY = ROOT / "outputs" / "wfa" / "wfa_summary.json"
GO_NO_GO_PATH = ROOT / "docs" / "GO_NO_GO.md"
SUMMARY_PATH = ROOT / "docs" / "UNATTENDED_SUMMARY.md"
LOG_PATH = ROOT / "docs" / "UNATTENDED_LOG.md"
HOLDOUT_REPORT_PATH = ROOT / "docs" / "HOLDOUT_REPORT.md"
COST_STRESS_PATH = ROOT / "docs" / "COST_STRESS.md"

BASE_RUN = "20260219_104745"
P20_RUN = "20260219_105305"
P50_RUN = "20260219_105707"


def _trade_metrics(run_id: str) -> dict[str, Any]:
    trades = pd.read_csv(RUNS_ROOT / run_id / "trades.csv")
    r = pd.to_numeric(trades["r_multiple"], errors="coerce").dropna()
    gross_win = float(r[r > 0].sum()) if not r.empty else 0.0
    gross_loss = float((-r[r < 0]).sum()) if not r.empty else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else (float("inf") if gross_win > 0 else float("nan"))
    winrate = float((r > 0).mean()) if not r.empty else float("nan")
    expectancy = float(r.mean()) if not r.empty else float("nan")
    boot = pd.read_csv(RUNS_ROOT / run_id / "diagnostics" / "BOOT_expectancy_ci.csv").iloc[0]
    return {
        "run_id": run_id,
        "pf": pf,
        "expectancy_R": expectancy,
        "trades": int(r.size),
        "winrate": winrate,
        "ci_low": float(boot["ci_low"]),
        "ci_high": float(boot["ci_high"]),
        "crosses_zero": bool(boot["crosses_zero"]),
    }


def _hour_dependency(run_id: str) -> dict[str, Any]:
    hour_df = pd.read_csv(RUNS_ROOT / run_id / "diagnostics" / "H_perf_by_hour_robust.csv")
    hour_df["trades"] = pd.to_numeric(hour_df["trades"], errors="coerce").fillna(0)
    hour_df["expectancy_R"] = pd.to_numeric(hour_df["expectancy_R"], errors="coerce")
    total = float(hour_df["trades"].sum())
    if total <= 0:
        return {"top_hour": "NA", "top_share": 0.0, "negative_hours_ge10": []}
    top = hour_df.sort_values("trades", ascending=False).iloc[0]
    negative = hour_df[(hour_df["trades"] >= 10) & (hour_df["expectancy_R"] < 0)].copy()
    negative = negative.sort_values("expectancy_R")
    negative_rows = [
        {
            "hour_utc": int(row["hour_utc"]),
            "trades": int(row["trades"]),
            "expectancy_R": float(row["expectancy_R"]),
        }
        for _, row in negative.iterrows()
    ]
    return {
        "top_hour": int(top["hour_utc"]),
        "top_share": float(top["trades"] / total),
        "negative_hours_ge10": negative_rows,
    }


def _fmt(x: float) -> str:
    return f"{x:.6f}".rstrip("0").rstrip(".")


def main() -> int:
    wfa = json.loads(WFA_SUMMARY.read_text(encoding="utf-8"))
    base = _trade_metrics(BASE_RUN)
    p20 = _trade_metrics(P20_RUN)
    p50 = _trade_metrics(P50_RUN)
    dep = _hour_dependency(BASE_RUN)

    holdout_positive = base["expectancy_R"] > 0.0
    holdout_pf_ok = base["pf"] > 1.10
    survives_p20 = (p20["expectancy_R"] > 0.0) and (p20["pf"] > 1.0)
    brutal_hour_dependency = dep["top_share"] >= 0.50 and len(dep["negative_hours_ge10"]) > 0
    go = holdout_positive and holdout_pf_ok and survives_p20 and (not brutal_hour_dependency)
    decision = "GO" if go else "NO-GO"

    go_lines: list[str] = []
    go_lines.append("# GO / NO-GO")
    go_lines.append("")
    go_lines.append(f"- decision: **{decision}**")
    go_lines.append("")
    go_lines.append("## Metrics")
    go_lines.append(f"- HOLDOUT run_id: `{BASE_RUN}`")
    go_lines.append(f"- HOLDOUT expectancy_R: `{_fmt(base['expectancy_R'])}`")
    go_lines.append(f"- HOLDOUT PF: `{_fmt(base['pf'])}`")
    go_lines.append(f"- HOLDOUT trades: `{base['trades']}`")
    go_lines.append(f"- HOLDOUT winrate: `{_fmt(base['winrate'])}`")
    go_lines.append(f"- HOLDOUT bootstrap CI: [`{_fmt(base['ci_low'])}`, `{_fmt(base['ci_high'])}`]")
    go_lines.append("")
    go_lines.append(f"- +20% costs run_id: `{P20_RUN}`")
    go_lines.append(f"- +20% expectancy_R: `{_fmt(p20['expectancy_R'])}`")
    go_lines.append(f"- +20% PF: `{_fmt(p20['pf'])}`")
    go_lines.append(f"- +20% bootstrap CI: [`{_fmt(p20['ci_low'])}`, `{_fmt(p20['ci_high'])}`]")
    go_lines.append("")
    go_lines.append(f"- +50% costs run_id: `{P50_RUN}`")
    go_lines.append(f"- +50% expectancy_R: `{_fmt(p50['expectancy_R'])}`")
    go_lines.append(f"- +50% PF: `{_fmt(p50['pf'])}`")
    go_lines.append(f"- +50% bootstrap CI: [`{_fmt(p50['ci_low'])}`, `{_fmt(p50['ci_high'])}`]")
    go_lines.append("")
    go_lines.append("## Hour Concentration")
    go_lines.append(f"- top hour share on HOLDOUT: `{_fmt(dep['top_share'] * 100)}%` (hour `{dep['top_hour']}`)")
    if dep["negative_hours_ge10"]:
        for row in dep["negative_hours_ge10"]:
            go_lines.append(
                f"- negative hour >=10 trades: hour `{row['hour_utc']}`, trades `{row['trades']}`, expectancy_R `{_fmt(row['expectancy_R'])}`"
            )
    else:
        go_lines.append("- negative hour >=10 trades: none")
    GO_NO_GO_PATH.write_text("\n".join(go_lines) + "\n", encoding="utf-8")

    summary_lines: list[str] = []
    summary_lines.append("# Unattended Summary")
    summary_lines.append("")
    summary_lines.append("## WINNER_GLOBAL (WFA OOS)")
    summary_lines.append(
        f"- `{wfa.get('winner_global_label')}` (`{wfa.get('winner_global_config_path')}`)"
    )
    summary_lines.append("")
    summary_lines.append("## HOLDOUT Result")
    summary_lines.append(
        f"- run_id `{BASE_RUN}` | PF `{_fmt(base['pf'])}` | expectancy_R `{_fmt(base['expectancy_R'])}` | "
        f"trades `{base['trades']}` | winrate `{_fmt(base['winrate'])}`"
    )
    summary_lines.append(
        f"- bootstrap CI [`{_fmt(base['ci_low'])}`, `{_fmt(base['ci_high'])}`], crosses_zero `{base['crosses_zero']}`"
    )
    summary_lines.append("")
    summary_lines.append("## Cost Stress")
    summary_lines.append(
        f"- BASE `{BASE_RUN}`: PF `{_fmt(base['pf'])}`, expectancy_R `{_fmt(base['expectancy_R'])}`, "
        f"CI [`{_fmt(base['ci_low'])}`, `{_fmt(base['ci_high'])}`]"
    )
    summary_lines.append(
        f"- +20 `{P20_RUN}`: PF `{_fmt(p20['pf'])}`, expectancy_R `{_fmt(p20['expectancy_R'])}`, "
        f"CI [`{_fmt(p20['ci_low'])}`, `{_fmt(p20['ci_high'])}`]"
    )
    summary_lines.append(
        f"- +50 `{P50_RUN}`: PF `{_fmt(p50['pf'])}`, expectancy_R `{_fmt(p50['expectancy_R'])}`, "
        f"CI [`{_fmt(p50['ci_low'])}`, `{_fmt(p50['ci_high'])}`]"
    )
    summary_lines.append("")
    summary_lines.append("## Decision")
    summary_lines.append(f"- `{decision}`")
    summary_lines.append("")
    summary_lines.append("## Relevant run_ids")
    summary_lines.append("- WFA VAL: `20260219_085634`, `20260219_104443`, `20260219_093546`, `20260219_101410`")
    summary_lines.append("- HOLDOUT base: `20260219_104745`")
    summary_lines.append("- HOLDOUT cost: `20260219_105305`, `20260219_105707`")
    SUMMARY_PATH.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    log_lines = [
        "",
        "## Phase 3-5 Summary",
        f"- logged_at_utc: {now}",
        f"- HOLDOUT run_id: `{BASE_RUN}`",
        f"- COST +20 run_id: `{P20_RUN}`",
        f"- COST +50 run_id: `{P50_RUN}`",
        "- QA outputs: `docs/WFA_QA.csv`, `docs/HOLDOUT_QA.csv`",
        "- Reports: `docs/HOLDOUT_REPORT.md`, `docs/COST_STRESS.md`, `docs/GO_NO_GO.md`, `docs/UNATTENDED_SUMMARY.md`",
    ]
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    print(f"Wrote: {GO_NO_GO_PATH.as_posix()}")
    print(f"Wrote: {SUMMARY_PATH.as_posix()}")
    print(f"Decision: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
