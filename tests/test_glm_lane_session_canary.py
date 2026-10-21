"""Tests for GLM session canary lane (T1.3, LOCAL-ONLY guarded)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.glm import _CI_ENV_VARS, GlmEgressForbiddenError
from scripts.session_canary import glm_lane

_REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("epic", ["../x", "/absolute", "Harness", "bad_name", "harness\n", "інфра"])
@pytest.mark.parametrize("command", ["status", "mint", "bootstrap"])
def test_cli_rejects_unsafe_epic_before_writing(tmp_path: Path, epic: str, command: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    if epic == "/absolute":
        epic = str(tmp_path / "absolute")
    extra = ["--stream", "epic:999999", "--out-dir", str(tmp_path / "out")] if command == "mint" else []
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.session_canary.glm_lane",
            "--repo",
            str(repo),
            command,
            f"--epic={epic}",
            *extra,
        ],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert proc.returncode == 2
    assert "error: epic must be a selector" in proc.stderr
    assert list(tmp_path.rglob("*")) == [repo]


@pytest.fixture
def clear_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_assert_glm_egress_allowed_passes_when_no_ci_env(clear_ci_env: None) -> None:
    glm_lane.assert_glm_egress_allowed("test")


@pytest.mark.parametrize("var", _CI_ENV_VARS)
def test_assert_glm_egress_allowed_raises_under_ci(monkeypatch: pytest.MonkeyPatch, var: str) -> None:
    monkeypatch.setenv(var, "true")
    with pytest.raises(GlmEgressForbiddenError, match="China-hosted"):
        glm_lane.assert_glm_egress_allowed("test")


def test_run_glm_probe_refused_under_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "1")
    with patch("subprocess.run") as mock_sub:
        receipt = glm_lane.run_glm_probe()
        assert receipt["status"] == "refused"
        assert receipt["reason"] == "ci_egress_forbidden"
        mock_sub.assert_not_called()


def test_score_fail_handoff_closes_exact_lease_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(glm_lane._gl, "cmd_score", lambda args: 2)
    monkeypatch.setattr(glm_lane, "_close_exact_lease", lambda repo, epic: True)

    assert glm_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert "FAIL-HANDOFF — exact lease closed" in capsys.readouterr().out


def test_hydrate_refuses_to_continue_when_capsule_is_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        glm_lane.shared_hydration,
        "build_hydration_capsule",
        lambda stream, lane, **_: {"execution_allowed": False},
    )

    assert glm_lane.main(["hydrate", "--epic", "harness"]) == 2
    assert "hydration blocked" in capsys.readouterr().err
