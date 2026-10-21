"""Unit tests for subprocess timeout bounds in scripts/lexicon/ (#7213 slice 8)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.reads_content, pytest.mark.usefixtures("github_command_boundary")]


def test_atlas_job_submit_launcher_timeout_rejects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon.runner import atlas_job

    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    monkeypatch.setattr(atlas_job, "registry_dir", lambda: tmp_path)
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "run-root"))

    def timeout_call(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, atlas_job.DEFAULT_LAUNCHER_SUBPROCESS_TIMEOUT_SECONDS)

    monkeypatch.setattr(atlas_job.subprocess, "call", timeout_call)
    plan = {
        "schema": "atlas-job.v1",
        "id": "timeout-submit-reject",
        "kind": "reenrich",
        "host": "atlas-runner",
        "args": ["--target", "missing-translation", "--no-poll"],
        "pointer_write": False,
        "result_sink": "restic",
        "denominator": 10,
        "issue": 6867,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=fake)
    assert rc == 124
    row = atlas_job.load_registry("timeout-submit-reject")
    assert row is not None
    assert row["state"] == "rejected"
    assert row["submit_exit"] == 124
