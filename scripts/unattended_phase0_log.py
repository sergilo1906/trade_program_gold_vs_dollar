from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
LOG_PATH = DOCS_DIR / "UNATTENDED_LOG.md"
TEMPLATES_STATUS_PATH = DOCS_DIR / "TEMPLATES_STATUS.md"
EXPECTED_TEMPLATE_ZIP = ROOT / "_templates" / "plantillas_mejoradas.zip"


def run_ps(cmd: str) -> str:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "").rstrip()
    err = (proc.stderr or "").rstrip()
    if proc.returncode != 0:
        return f"[exit_code={proc.returncode}]\nSTDOUT:\n{out}\n\nSTDERR:\n{err}".rstrip()
    if err:
        return f"{out}\n\n[STDERR]\n{err}".rstrip()
    return out


def fenced(text: str, lang: str = "") -> str:
    marker = "```" + lang
    return f"{marker}\n{text.rstrip()}\n```"


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    cmd_configs = "Get-ChildItem configs -File | Sort-Object Name | Format-Table -AutoSize"
    cmd_base_cfg = "Get-Content configs/config_v3_AUTO.yaml"
    cmd_templates = (
        "Get-ChildItem -Path . -Recurse -File | "
        "Where-Object { $_.Name -match 'plantillas|mejoradas' -or $_.FullName -match '_templates' } | "
        "Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize"
    )

    out_configs = run_ps(cmd_configs)
    out_base_cfg = run_ps(cmd_base_cfg)
    out_templates = run_ps(cmd_templates)

    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines: list[str] = []
    lines.append("# Unattended Execution Log")
    lines.append("")
    lines.append(f"- Started: {started}")
    lines.append("")
    lines.append("## Phase 0 - Inventory")
    lines.append("")
    lines.append("### 0.1 Config listing command output")
    lines.append(f"Command: `{cmd_configs}`")
    lines.append("")
    lines.append(fenced(out_configs))
    lines.append("")
    lines.append("### 0.2 Base config output")
    lines.append(f"Command: `{cmd_base_cfg}`")
    lines.append("")
    lines.append(fenced(out_base_cfg, "yaml"))
    lines.append("")
    lines.append("### 0.3 Template search output")
    lines.append(f"Command: `{cmd_templates}`")
    lines.append("")
    lines.append(fenced(out_templates))
    lines.append("")
    lines.append("### 0.4 Template zip status")
    lines.append(f"- Expected template zip: `{EXPECTED_TEMPLATE_ZIP.as_posix()}`")
    if EXPECTED_TEMPLATE_ZIP.exists():
        stat = EXPECTED_TEMPLATE_ZIP.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        lines.append("- Status: FOUND")
        lines.append(f"- Size bytes: {stat.st_size}")
        lines.append(f"- LastWriteTime (UTC): {mtime}")
        if TEMPLATES_STATUS_PATH.exists():
            TEMPLATES_STATUS_PATH.unlink()
    else:
        lines.append("- Status: NOT FOUND")
        lines.append("- Action: continuing without templates and documenting status.")
        TEMPLATES_STATUS_PATH.write_text(
            "\n".join(
                [
                    "# Templates Status",
                    "",
                    f"- Checked path: `{EXPECTED_TEMPLATE_ZIP.as_posix()}`",
                    f"- Date (UTC): {started}",
                    "- Result: `./_templates/plantillas_mejoradas.zip` not found.",
                    "- Action: Continued execution using repository-native scripts/configs without template import.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    lines.append("")

    LOG_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {LOG_PATH.as_posix()}")
    if TEMPLATES_STATUS_PATH.exists():
        print(f"Wrote: {TEMPLATES_STATUS_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
