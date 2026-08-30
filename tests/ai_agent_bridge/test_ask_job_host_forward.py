"""#7172 — notebook ask-* forwards to the job-host plane; plane-status fails clean."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from scripts.ai_agent_bridge import _acp_compat, _job_host_forward
from scripts.fleet_comms import cli as fleet_cli
from scripts.fleet_comms.paths import (
    RETIRED_LOCAL_MARKER,
    RETIRED_LOCAL_PLANE_MESSAGE,
    local_plane_is_retired,
)


def _plant_retire_marker(plane_root: Path) -> Path:
    plane_root.mkdir(parents=True, exist_ok=True)
    marker = plane_root / RETIRED_LOCAL_MARKER
    marker.write_text("canonical plane is on the job host\n", encoding="utf-8")
    return marker


def test_local_plane_is_retired_detects_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plane = tmp_path / "fleet-comms" / "v1"
    _plant_retire_marker(plane)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", raising=False)
    assert local_plane_is_retired() is True


def test_local_plane_is_retired_honors_shadow_allow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plane = tmp_path / "fleet-comms" / "v1"
    _plant_retire_marker(plane)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    assert local_plane_is_retired() is False


def test_plane_status_cli_prints_retire_message_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plane = tmp_path / "fleet-comms" / "v1"
    _plant_retire_marker(plane)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", raising=False)

    rc = fleet_cli.main(["plane-status"])
    captured = capsys.readouterr()
    assert rc == fleet_cli.EXIT_ERROR
    assert RETIRED_LOCAL_PLANE_MESSAGE in captured.err
    assert "Traceback" not in captured.err
    assert "PlaneRootAnchorError" not in captured.err


def test_resolve_ask_forward_target_prefers_job_dispatch_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LU_JOB_DISPATCH_HOST", "job-alias")
    monkeypatch.setenv("LU_JOB_REPO", "/home/ops/learn-ukrainian")
    monkeypatch.delenv("LU_SERVICES_SSH_HOST", raising=False)
    target = _job_host_forward.resolve_ask_forward_target()
    assert target is not None
    assert target.host == "job-alias"
    assert target.remote_repo == "/home/ops/learn-ukrainian"


def test_resolve_ask_forward_target_falls_back_to_services_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LU_JOB_DISPATCH_HOST", raising=False)
    monkeypatch.delenv("ATLAS_RUNNER_HOST", raising=False)
    monkeypatch.delenv("LU_JOB_REPO", raising=False)
    monkeypatch.setenv("LU_SERVICES_SSH_HOST", "services-alias")
    monkeypatch.setenv("LU_SERVICES_REMOTE_ROOT", "/home/ops/learn-ukrainian")
    target = _job_host_forward.resolve_ask_forward_target()
    assert target is not None
    assert target.host == "services-alias"


def test_maybe_forward_refuses_cleanly_when_retired_without_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plane = tmp_path / "fleet-comms" / "v1"
    _plant_retire_marker(plane)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", raising=False)
    monkeypatch.delenv("LU_JOB_DISPATCH_HOST", raising=False)
    monkeypatch.delenv("ATLAS_RUNNER_HOST", raising=False)
    monkeypatch.delenv("LU_SERVICES_SSH_HOST", raising=False)
    monkeypatch.delenv(_job_host_forward.ENV_FORWARD_DONE, raising=False)

    with pytest.raises(_job_host_forward.AskForwardError, match="retired") as excinfo:
        _job_host_forward.maybe_forward_compat_ask(
            "agy",
            "hello",
            task_id="7172-refuse",
            repo_root=tmp_path,
        )
    message = str(excinfo.value)
    assert "LU_JOB_DISPATCH_HOST" in message or "LU_SERVICES_SSH_HOST" in message
    assert "Traceback" not in message


def test_run_compat_ask_forwards_instead_of_plane_root_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: notebook ask must not raise PlaneRootAnchorError when configured."""
    plane = tmp_path / "batch_state" / "fleet-comms" / "v1"
    _plant_retire_marker(plane)
    # Anchor via FLEET_COMMS_ROOT so local_plane_is_retired sees the marker
    # without needing a real git primary layout under tmp_path.
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", raising=False)
    monkeypatch.setenv("LU_JOB_DISPATCH_HOST", "opaque-job")
    monkeypatch.setenv("LU_JOB_REPO", "/home/ops/learn-ukrainian")
    monkeypatch.delenv(_job_host_forward.ENV_FORWARD_DONE, raising=False)

    sentinel = SimpleNamespace(
        ok=True,
        response="forwarded-reply",
        stderr_excerpt=None,
        transport_outcome="replied",
        agent="agy",
        model="agy",
    )
    forward = MagicMock(return_value=sentinel)
    monkeypatch.setattr(_job_host_forward, "forward_compat_ask", forward)
    # Ensure AuthorityService is never opened on the notebook path.
    boom = MagicMock(side_effect=AssertionError("AuthorityService must not open locally"))
    monkeypatch.setattr(
        "scripts.fleet_comms.authority.AuthorityService",
        boom,
    )

    result = _acp_compat.run_compat_ask(
        "agy",
        "notebook critic please",
        task_id="7172-forward",
        source="claude",
    )
    assert result is sentinel
    forward.assert_called_once()
    assert boom.call_count == 0


def test_forward_compat_ask_invokes_ssh_without_leaking_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_JOB_DISPATCH_HOST", "secret-alias-must-not-leak")
    monkeypatch.setenv("LU_JOB_REPO", "/home/ops/secret-repo-must-not-leak")
    monkeypatch.delenv(_job_host_forward.ENV_FORWARD_DONE, raising=False)

    completed = SimpleNamespace(
        returncode=0,
        stdout=b"remote answer\n",
        stderr=b"deprecated ask-agy: ACP transport; outcome=replied\n",
    )

    def fake_run(argv, **kwargs):
        assert argv[0] == "ssh"
        assert "BatchMode=yes" in argv
        assert "secret-alias-must-not-leak" in argv
        assert kwargs.get("input")
        # Prompt travels in stdin script, not argv.
        joined = " ".join(argv)
        assert "notebook critic" not in joined
        return completed

    monkeypatch.setattr(_job_host_forward.subprocess, "run", fake_run)

    result = _job_host_forward.forward_compat_ask(
        "agy",
        "notebook critic",
        task_id="7172-ssh",
        source="claude",
        stdout_only=True,
    )
    assert result.ok is True
    assert result.response == "remote answer\n"
    captured = capsys.readouterr()
    assert "secret-alias-must-not-leak" not in captured.out
    assert "secret-alias-must-not-leak" not in captured.err
    assert "/home/ops/secret-repo-must-not-leak" not in captured.err


def test_forward_script_sets_loop_guard_and_stdout_only() -> None:
    script = _job_host_forward._build_remote_ask_script(
        command_target="kimi",
        remote_repo="/home/ops/learn-ukrainian",
        task_id="loop-guard",
        source="claude",
        model=None,
        effort="xhigh",
        data="attached",
        hard_timeout=1800,
        prompt="please review",
    )
    text = script.decode("utf-8")
    assert "LU_ASK_JOB_HOST_FORWARD=1" in text
    assert "ask-kimi" in text
    assert "--stdout-only" in text
    assert "--effort" in text
    assert "xhigh" in text
    assert "please review" not in text  # base64 only
