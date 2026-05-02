from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_v7_build_dry_run_emits_module_start() -> None:
    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/build/v7_build.py",
            "a1",
            "my-morning",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    events = [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    assert events[0]["event"] == "module_start"
    assert events[0]["level"] == "a1"
    assert events[0]["slug"] == "my-morning"


def test_v7_build_dry_run_accepts_writer_alias() -> None:
    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/build/v7_build.py",
            "a1",
            "my-morning",
            "--writer",
            "gemini",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    events = [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    assert events[-1]["event"] == "module_done"
    assert events[-1]["dry_run"] is True
