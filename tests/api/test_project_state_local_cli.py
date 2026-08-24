"""CLI subprocess tests for scripts/api/project_state_local.py (#7188)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.api.test_project_state_collect import _init_repo

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_CLI = REPO_ROOT / "scripts" / "api" / "project_state_local.py"


def test_project_state_local_collect_dry_run_from_documented_invocation(
    tmp_path: Path,
) -> None:
    fixture_repo = _init_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(LOCAL_CLI),
            "--host-id",
            "mac-operator",
            "--repo-root",
            str(fixture_repo),
            "collect",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"
    assert payload["primary"]["head_sha"]
    assert len(payload["services"]) == 4


def test_project_state_local_direct_script_execution_outside_repo_root(
    tmp_path: Path,
) -> None:
    fixture_repo = _init_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(LOCAL_CLI),
            "--host-id",
            "mac-operator",
            "--repo-root",
            str(fixture_repo),
            "collect",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"


def test_project_state_local_documented_collect_dry_run(tmp_path: Path) -> None:
    fixture_repo = _init_repo(tmp_path)
    env = {**os.environ, "LU_MONITOR_HOST_ID": "mac-operator"}
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "api" / "project_state_local.py"),
            "collect",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=fixture_repo,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"


def test_project_state_local_documented_report_invocation(tmp_path: Path) -> None:
    fixture_repo = _init_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "api" / "project_state_local.py"),
            "--host-id",
            "mac-operator",
            "--repo-root",
            str(fixture_repo),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"
