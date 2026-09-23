"""CLI subprocess tests for scripts/api/project_state_local.py (#7188)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.api.test_project_state_collect import _git, _init_repo, write_fake_lsof

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_CLI = REPO_ROOT / "scripts" / "api" / "project_state_local.py"


def _hermetic_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    """Service probes see an injected lsof and lane usage is off: no live host probing (#8591)."""
    env = {
        **os.environ,
        "LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT": str(tmp_path / "no-private-checkout"),
        "MONITOR_PROJECT_STATE_LANE_USAGE": "0",
        **extra,
    }
    if "SVC_LSOF_BIN" not in extra:
        env["SVC_LSOF_BIN"] = str(write_fake_lsof(tmp_path))
    return env


@pytest.fixture
def unresolvable_api_listener(tmp_path: Path) -> Iterator[subprocess.Popen[bytes]]:
    """A process that looks like the api service but runs from a checkout with no HEAD."""
    unborn = tmp_path / "unborn-checkout"
    unborn.mkdir()
    _git(unborn, "init", "-b", "main")
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)", "scripts.api.main:app"],
        cwd=unborn,
    )
    try:
        yield process
    finally:
        process.kill()
        process.wait(timeout=10)


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
        env=_hermetic_env(tmp_path),
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
        env=_hermetic_env(tmp_path),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"


def test_project_state_local_documented_collect_dry_run(tmp_path: Path) -> None:
    fixture_repo = _init_repo(tmp_path)
    env = _hermetic_env(tmp_path, LU_MONITOR_HOST_ID="mac-operator")
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
        env=_hermetic_env(tmp_path),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["host_id"] == "mac-operator"


def test_project_state_local_collect_reports_unresolvable_running_service(
    tmp_path: Path,
    unresolvable_api_listener: subprocess.Popen[bytes],
) -> None:
    """#8591: the issue's failing case — collect succeeds and names the unresolved service."""
    fixture_repo = _init_repo(tmp_path)
    fake_lsof = write_fake_lsof(
        tmp_path,
        listener_pid=unresolvable_api_listener.pid,
        cwd=tmp_path / "unborn-checkout",
    )
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
        env=_hermetic_env(tmp_path, SVC_LSOF_BIN=str(fake_lsof)),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    services = {row["name"]: row for row in json.loads(result.stdout)["services"]}
    assert services["api"]["state"] == "running"
    assert services["api"]["serving_mode"] == "unknown"
    assert services["api"]["unresolved_reason"] == "head_unresolvable"
    assert services["api"]["checkout_sha"] is None
    assert {services[name]["state"] for name in ("sources", "astro")} == {"stopped"}
