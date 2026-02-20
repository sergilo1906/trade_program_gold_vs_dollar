from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from scripts import run_and_tag
from xauusd_bot.csv_utils import read_csv_tolerant


def test_read_csv_tolerant_skips_bad_lines() -> None:
    csv_path = Path("tests/fixtures/events_corrupt.csv")
    warnings: list[str] = []
    df = read_csv_tolerant(csv_path, label="events_test", warnings=warnings)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert any("fallback" in w.lower() for w in warnings)


def test_run_and_tag_writes_meta_even_when_run_fails(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "mini.csv"
    data_path.write_text(
        "timestamp,open,high,low,close\n"
        "2026-01-01 00:00:00,1,1,1,1\n"
        "2026-01-01 00:05:00,1,1,1,1\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text("output_dir: outputs/output\nruns_output_dir: outputs/runs\n", encoding="utf-8")
    runs_root = tmp_path / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    created_run = runs_root / "20260101_000001"

    def fake_subprocess_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd0 = str(cmd[0]) if cmd else ""
        if cmd0 == "git":
            return subprocess.CompletedProcess(cmd, 0, stdout="deadbeef\n", stderr="")
        if "-m" in cmd and "xauusd_bot" in cmd:
            created_run.mkdir(parents=True, exist_ok=True)
            raise subprocess.CalledProcessError(returncode=2, cmd=cmd)
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(run_and_tag.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_and_tag.py",
            "--data",
            str(data_path),
            "--config",
            str(config_path),
            "--runs-root",
            str(runs_root),
        ],
    )

    rc = run_and_tag.main()
    assert rc == 2
    meta_path = created_run / "run_meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["postprocess_ok"] is False
    assert int(meta["process_returncode"]) == 2
    assert "postprocess_error" in meta
    assert (created_run / "config_used.yaml").exists()
