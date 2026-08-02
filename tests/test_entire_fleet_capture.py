"""Lifecycle, privacy, and runner-boundary tests for Entire fleet capture."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.result import ParseResult
from scripts.entire import fleet_capture as capture


def _fake_run(hooks: list[tuple[str, dict[str, object]]]):
    def run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=b"")
        assert Path(kwargs["cwd"]) == Path(kwargs["env"]["ENTIRE_REPO_ROOT"])
        payload = json.loads(kwargs["input"])
        hooks.append((command[-1], payload))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return run


def test_exact_owned_host_lifecycle_is_private_and_ephemeral(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hooks: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/fake/entire")
    monkeypatch.setattr(capture.subprocess, "run", _fake_run(hooks))

    fleet = capture.FleetCapture.start(
        host_harness="hermes",
        runner_agent="deepseek",
        entrypoint="bridge",
        requested_model="deepseek-v4-flash",
        prompt="private-prompt-canary",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
        plan_metadata={
            "hermes": {
                "requested_provider": "deepseek",
                "requested_model": "deepseek-v4-flash",
            }
        },
    )
    assert fleet is not None
    assert stat.S_IMODE(fleet.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(fleet.session_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(fleet.transcript_path.stat().st_mode) == 0o600
    assert [name for name, _ in hooks] == ["session-start", "turn-start"]
    assert "private-prompt-canary" not in json.dumps(hooks[0][1]["raw_data"])
    assert hooks[1][1]["user_prompt"] == "private-prompt-canary"

    fleet.finish(
        response="private-response-canary",
        outcome="ok",
        returncode=0,
        actual_model="deepseek-v4.1",
        route_metadata={"actual_provider": "deepseek"},
    )
    assert [name for name, _ in hooks] == [
        "session-start",
        "turn-start",
        "turn-end",
        "session-end",
    ]
    assert not fleet.session_dir.exists()
    for name, payload in hooks:
        if name != "turn-start":
            assert "private-prompt-canary" not in json.dumps(payload["raw_data"])
        assert "private-response-canary" not in json.dumps(payload["raw_data"])


@pytest.mark.parametrize("host", [None, "", "codex", "claude-code", "opencode", "cursor", "kimi"])
def test_native_or_unowned_hosts_are_never_duplicated(tmp_path: Path, host: str | None) -> None:
    assert capture.FleetCapture.start(
        host_harness=host,
        runner_agent="fixture",
        entrypoint="runtime",
        requested_model="fixture",
        prompt="fixture",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
    ) is None


def test_entire_outage_is_fail_open_and_spool_is_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def timed_out(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=b"")
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 1))

    monkeypatch.setattr(capture.shutil, "which", lambda name: "/fake/entire")
    monkeypatch.setattr(capture.subprocess, "run", timed_out)
    fleet = capture.FleetCapture.start(
        host_harness="agy",
        runner_agent="agy",
        entrypoint="dispatch",
        requested_model="gemini-3.6-flash-high",
        prompt="fixture",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
    )
    assert fleet is not None
    fleet.finish(response="provider result", outcome="ok", returncode=0)
    assert not fleet.session_dir.exists()


def test_start_failure_cleans_private_spool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture, "_atomic_jsonl", lambda *_args: (_ for _ in ()).throw(OSError()))

    with pytest.raises(OSError):
        capture.FleetCapture.start(
            host_harness="grok",
            runner_agent="grok-build",
            entrypoint="bridge",
            requested_model="grok-4.5",
            prompt="fixture",
            repo_path=tmp_path,
            runtime_repo_root=tmp_path,
        )

    root = capture._capture_root(tmp_path)
    assert not list(root.glob("fleet-*"))


def test_stale_cleanup_removes_only_exact_session_directories(tmp_path: Path) -> None:
    valid = tmp_path / "fleet-0123456789abcdef0123456789abcdef"
    unrelated = tmp_path / "operator-files"
    malformed = tmp_path / "fleet-not-a-session"
    for directory in (valid, unrelated, malformed):
        directory.mkdir()
        os.utime(directory, (0, 0))
    capture._cleanup_stale(tmp_path, now=capture._STALE_SECONDS + 1)
    assert not valid.exists()
    assert unrelated.exists()
    assert malformed.exists()


def test_resolved_route_preserves_truthful_substitution() -> None:
    actual, metadata = capture.resolved_route(
        requested_model="deepseek-v4-flash",
        plan_metadata={
            "hermes": {
                "requested_provider": "deepseek",
                "requested_model": "deepseek-v4-flash",
            }
        },
        substitution={
            "requested_provider": "deepseek",
            "requested_model": "deepseek-v4-flash",
            "actual_provider": "openrouter",
            "actual_model": "deepseek/deepseek-v4.1",
        },
    )
    assert actual == "deepseek/deepseek-v4.1"
    assert metadata == {
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-flash",
        "actual_provider": "openrouter",
        "actual_model": "deepseek/deepseek-v4.1",
    }


def test_runner_starts_after_spawn_and_always_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from agent_runtime import runner as runtime_runner

    events: list[tuple[str, dict[str, object]]] = []

    class FakeCapture:
        @classmethod
        def start(cls, **kwargs):
            events.append(("start", kwargs))
            return cls()

        def finish(self, **kwargs):
            events.append(("finish", kwargs))

    class Adapter:
        def liveness_signal_paths(self, _plan):
            return ()

        def parse_response(self, **_kwargs):
            return ParseResult(ok=True, response="provider-ok")

    monkeypatch.setattr(runtime_runner, "FleetCapture", FakeCapture)
    python = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"
    outcome = runtime_runner._execute_invocation_plan(
        agent_name="deepseek",
        adapter=Adapter(),
        plan=InvocationPlan(
            cmd=[str(python), "-c", "print('provider-ok')"],
            cwd=tmp_path,
            host_harness="hermes",
        ),
        prompt="fixture",
        mode="read-only",
        cwd=tmp_path,
        model="deepseek-v4-flash",
        task_id="fixture",
        session_id=None,
        entrypoint="bridge",
        hard_timeout=30,
        stall_timeout=30,
    )
    assert outcome.parse.ok is True
    assert [name for name, _ in events] == ["start", "finish"]
    assert events[0][1]["host_harness"] == "hermes"
    assert events[1][1]["response"] == "provider-ok"
    assert events[1][1]["outcome"] == "ok"


def test_spawn_refusal_creates_no_entire_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from agent_runtime import runner as runtime_runner

    class NoCapture:
        @classmethod
        def start(cls, **_kwargs):
            raise AssertionError("capture started before subprocess spawn")

    class Adapter:
        def liveness_signal_paths(self, _plan):
            return ()

    monkeypatch.setattr(runtime_runner, "FleetCapture", NoCapture)
    monkeypatch.setattr(runtime_runner, "write_record", lambda _record: None)
    with pytest.raises(runtime_runner.AgentUnavailableError):
        runtime_runner._execute_invocation_plan(
            agent_name="agy",
            adapter=Adapter(),
            plan=InvocationPlan(
                cmd=[str(tmp_path / "missing-binary")],
                cwd=tmp_path,
                host_harness="agy",
            ),
            prompt="fixture",
            mode="read-only",
            cwd=tmp_path,
            model="fixture",
            task_id="fixture",
            session_id=None,
            entrypoint="dispatch",
            hard_timeout=30,
            stall_timeout=30,
        )
