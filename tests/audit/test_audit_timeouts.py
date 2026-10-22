"""Unit tests for subprocess timeouts in scripts/audit/ modules (#7213 slice 6)."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.reads_content, pytest.mark.usefixtures("github_command_boundary")]


def _completed(
    args: list[str] | None = None,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args or [],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# 23. lint_opsec_leaks.py
# ---------------------------------------------------------------------------
def test_lint_opsec_leaks_timeouts() -> None:
    from scripts.audit import lint_opsec_leaks as lol

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if cmd[1] == "show":
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"content")
        if "-z" in cmd:
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"file1\x00file2\x00")
        return _completed(cmd, returncode=0, stdout="line1\nline2\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert lol.get_git_content("file.txt") == "content"
        assert lol.run_git_nul_separated(["git", "diff", "-z"]) == ["file1", "file2"]
        assert lol.run_git_lines(["git", "status"]) == ["line1", "line2"]

    assert len(calls) == 3
    for c in calls:
        assert c["timeout"] == lol.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], lol.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert lol.get_git_content("file.txt") is None


# ---------------------------------------------------------------------------
# 26. run_gemini_1x17_sweep.py
# ---------------------------------------------------------------------------
def test_run_gemini_1x17_sweep_timeouts() -> None:
    from scripts.audit import run_gemini_1x17_sweep as rgs

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "codexbar" in cmd[0]:
            return _completed(
                cmd,
                returncode=0,
                stdout=json.dumps({
                    "id": "antigravity-quota-summary-gemini-5h",
                    "window": {"usedPercent": 50.0, "resetsAt": "2026-08-24T18:00:00Z"},
                }),
            )
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        used, _mins = rgs._throttle_quota()
        assert used == 50.0

    assert len(calls) == 1
    assert calls[0]["timeout"] == rgs.DEFAULT_CODEXBAR_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["codexbar"], rgs.DEFAULT_CODEXBAR_TIMEOUT_SECONDS),
    ):
        with pytest.raises(RuntimeError) as exc:
            rgs._throttle_quota()
        assert "codexbar timed out after 30.0s" in str(exc.value)


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")
