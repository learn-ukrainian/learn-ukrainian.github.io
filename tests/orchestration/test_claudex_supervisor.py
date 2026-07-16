from __future__ import annotations

import json
import os
import stat
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.orchestration import thread_handoff as th
from scripts.orchestration.claudex_supervisor import (
    ClaudexSupervisor,
    SupervisorError,
    _request_path,
    _validate_claimed_request,
    bind_session,
    compute_command_hash,
    create_rollover_request,
    load_runtime,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_PYTHON = _REPO_ROOT / ".venv/bin/python"
_SUPERVISOR = _REPO_ROOT / "scripts/orchestration/claudex_supervisor.py"
_SESSION_ID = "official-session-5265"
_HANDOFF_AGENT = "claude-infra"


def _route_env(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "LEARN_UKRAINIAN_PROFILE_ID": "sol_lead",
            "LEARN_UKRAINIAN_MAIN_MODEL_ID": "gpt-5.6-sol",
            "LEARN_UKRAINIAN_TRANSPORT": "claudex",
            "LEARN_UKRAINIAN_TRUSTED": "1",
            "CLAUDE_CODE_SUBAGENT_MODEL": "gpt-5.6-terra",
        }
    )
    env.update(overrides)
    return env


def _argv(*extra: str) -> list[str]:
    return [
        "--model",
        "gpt-5.6-sol",
        "--agent",
        "infra-orchestrator",
        "--epic",
        "harness",
        *extra,
    ]


def _seed_running_supervisor(
    tmp_path: Path,
    *,
    argv: list[str] | None = None,
    env: dict[str, str] | None = None,
    child_pid: int = 4242,
) -> ClaudexSupervisor:
    supervisor = ClaudexSupervisor(
        "/bin/true",
        argv or _argv(),
        state_root=tmp_path,
        env=env or _route_env(),
    )
    supervisor.child = SimpleNamespace(pid=child_pid)  # type: ignore[assignment]
    supervisor._write_runtime("running")
    return supervisor


def _bind(supervisor: ClaudexSupervisor) -> dict[str, Any]:
    return bind_session(
        state_root=supervisor.state_root,
        run_id=supervisor.run_id,
        launch_generation=supervisor.launch_generation,
        session_id=_SESSION_ID,
        source="startup",
        model_id="gpt-5.6-sol",
        handoff_agent=_HANDOFF_AGENT,
    )


def _prepare_lease(state_root: Path, *, session_id: str = _SESSION_ID) -> tuple[dict[str, Any], Path]:
    state = th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION},
        agent=_HANDOFF_AGENT,
        now=datetime(2026, 7, 16, 8, 0, tzinfo=UTC),
        active_thread_id=session_id,
        active_automation_id=None,
        context_percent=86.0,
        force_new_replacement=False,
        epic_title="Claudex lifecycle",
        goal="exact route continuity",
        phase="prepare",
        next_phase="restart",
        harness="codex-app",
    )
    state["replacement"]["source_checkout"] = {
        "full_head": "abc123def0456789",
        "clean": True,
    }
    path = state_root / th.default_state_path(_HANDOFF_AGENT, state["lineage_id"])
    th.write_json_atomic(path, state)
    return state, path


def _create_valid_request(
    supervisor: ClaudexSupervisor,
    state: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    replacement = state["replacement"]
    return create_rollover_request(
        state_root=supervisor.state_root,
        run_id=supervisor.run_id,
        launch_generation=supervisor.launch_generation,
        session_id=_SESSION_ID,
        lineage_id=state["lineage_id"],
        rollover_generation=replacement["generation"],
        rollover_id=replacement["rollover_id"],
        now=now,
    )


def _wait_for_runtime(
    state_root: Path,
    *,
    state: str,
    generation: int = 0,
    timeout: float = 10.0,
) -> tuple[Path, dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        roots = list((state_root / ".agent/claudex-supervisors").glob("*/runtime.json"))
        if len(roots) == 1:
            payload = json.loads(roots[0].read_text(encoding="utf-8"))
            if payload.get("state") == state and payload.get("launch_generation") == generation:
                return roots[0], payload
        time.sleep(0.02)
    raise AssertionError(f"supervisor did not reach {state=} {generation=}")


def _write_child(path: Path, *, wait_on_first_launch: bool) -> None:
    wait_source = (
        "\nif generation == 0:\n"
        "    while True:\n"
        "        time.sleep(1)\n"
        if wait_on_first_launch
        else "\nsys.exit(7)\n"
    )
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "import time\n"
        "from pathlib import Path\n"
        "generation = int(os.environ['LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION'])\n"
        "record = {\n"
        "    'argv': sys.argv[1:],\n"
        "    'generation': generation,\n"
        "    'profile': os.environ['LEARN_UKRAINIAN_PROFILE_ID'],\n"
        "    'lead': os.environ['LEARN_UKRAINIAN_MAIN_MODEL_ID'],\n"
        "    'subagent': os.environ['CLAUDE_CODE_SUBAGENT_MODEL'],\n"
        "    'proxy_present': bool(os.environ.get('ANTHROPIC_BASE_URL')),\n"
        "    'auth_present': bool(os.environ.get('ANTHROPIC_AUTH_TOKEN')),\n"
        "}\n"
        "log = Path(os.environ['SUPERVISOR_CHILD_LOG'])\n"
        "with log.open('a', encoding='utf-8') as handle:\n"
        "    handle.write(json.dumps(record, sort_keys=True) + '\\n')\n"
        + wait_source,
        encoding="utf-8",
    )
    path.chmod(0o755)


def _wait_for_log(path: Path, count: int, timeout: float = 10.0) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            if len(rows) >= count:
                return rows
        time.sleep(0.02)
    raise AssertionError(f"child log did not reach {count} entries")


def test_command_hash_preserves_argv_boundaries() -> None:
    first = compute_command_hash("/bin/true", ["a b", "c"])
    second = compute_command_hash("/bin/true", ["a", "b c"])

    assert first != second
    assert len(first) == 64


def test_runtime_metadata_is_private_and_never_persists_route_secrets(tmp_path: Path) -> None:
    secret = "private-argument-value"
    supervisor = _seed_running_supervisor(
        tmp_path,
        argv=_argv("--secret-bearing-argument", secret),
        env=_route_env(
            ANTHROPIC_BASE_URL="https://proxy-with-private-route.invalid",
            ANTHROPIC_AUTH_TOKEN="private-authorization-value",
        ),
    )

    raw = supervisor.runtime_path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    assert secret not in raw
    assert "private-authorization-value" not in raw
    assert "proxy-with-private-route" not in raw
    assert "environment" not in payload
    assert "argv" not in payload
    assert payload["profile_id"] == "sol_lead"
    assert payload["lead_model_id"] == "gpt-5.6-sol"
    assert payload["subagent_model_id"] == "gpt-5.6-terra"
    assert stat.S_IMODE(supervisor.run_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(supervisor.runtime_path.stat().st_mode) == 0o600


def test_runtime_metadata_rejects_wrong_field_types(tmp_path: Path) -> None:
    supervisor = _seed_running_supervisor(tmp_path)
    payload = json.loads(supervisor.runtime_path.read_text(encoding="utf-8"))
    payload["session_source"] = {"unexpected": "object"}
    supervisor.runtime_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SupervisorError, match="session_source is malformed"):
        load_runtime(tmp_path, supervisor.run_id)


def test_session_binding_uses_official_identity_and_exact_generation(tmp_path: Path) -> None:
    supervisor = _seed_running_supervisor(tmp_path)

    runtime = _bind(supervisor)

    assert runtime["session_id"] == _SESSION_ID
    assert runtime["session_model_id"] == "gpt-5.6-sol"
    assert runtime["session_source"] == "startup"
    assert runtime["handoff_agent"] == _HANDOFF_AGENT
    with pytest.raises(SupervisorError, match="already bound to another session"):
        bind_session(
            state_root=tmp_path,
            run_id=supervisor.run_id,
            launch_generation=0,
            session_id="different-session",
            source="startup",
            model_id="gpt-5.6-sol",
            handoff_agent=_HANDOFF_AGENT,
        )
    with pytest.raises(SupervisorError, match="active supervisor generation"):
        bind_session(
            state_root=tmp_path,
            run_id=supervisor.run_id,
            launch_generation=1,
            session_id="different-session",
            source="startup",
            model_id="gpt-5.6-sol",
            handoff_agent=_HANDOFF_AGENT,
        )


def test_request_creation_requires_exact_session_and_is_atomic_once(tmp_path: Path) -> None:
    supervisor = _seed_running_supervisor(tmp_path)
    _bind(supervisor)
    state, _ = _prepare_lease(tmp_path)
    replacement = state["replacement"]

    with pytest.raises(SupervisorError, match="source session"):
        create_rollover_request(
            state_root=tmp_path,
            run_id=supervisor.run_id,
            launch_generation=0,
            session_id="wrong-session",
            lineage_id=state["lineage_id"],
            rollover_generation=replacement["generation"],
            rollover_id=replacement["rollover_id"],
        )

    request = _create_valid_request(supervisor, state)

    assert request["source_session_id"] == _SESSION_ID
    assert request["command_hash"] == supervisor.command_hash
    assert request["profile_id"] == "sol_lead"
    assert request["subagent_model_id"] == "gpt-5.6-terra"
    request_path = _request_path(tmp_path, supervisor.run_id)
    assert stat.S_IMODE(request_path.stat().st_mode) == 0o600
    with pytest.raises(SupervisorError, match="already pending"):
        _create_valid_request(supervisor, state)


def test_stale_and_route_mismatched_requests_are_rejected(tmp_path: Path) -> None:
    supervisor = _seed_running_supervisor(tmp_path)
    _bind(supervisor)
    state, _ = _prepare_lease(tmp_path)
    created = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
    request = _create_valid_request(supervisor, state, now=created)
    runtime = load_runtime(tmp_path, supervisor.run_id)

    with pytest.raises(SupervisorError, match="stale"):
        _validate_claimed_request(
            request=request,
            state_root=tmp_path,
            runtime=runtime,
            now=created + timedelta(minutes=6),
        )

    mismatched = dict(request)
    mismatched["subagent_model_id"] = "gpt-5.6-luna"
    with pytest.raises(SupervisorError, match="active subagent_model_id"):
        _validate_claimed_request(
            request=mismatched,
            state_root=tmp_path,
            runtime=runtime,
            now=created + timedelta(seconds=1),
        )


def test_malformed_request_is_quarantined_once_without_persisting_payload(
    tmp_path: Path,
) -> None:
    supervisor = _seed_running_supervisor(tmp_path)
    _bind(supervisor)
    request_path = _request_path(tmp_path, supervisor.run_id)
    request_path.write_text(
        json.dumps({"authorization": "private-rejected-value"}), encoding="utf-8"
    )
    request_path.chmod(0o600)

    assert supervisor._check_request() is None
    assert supervisor._check_request() is None

    rejected = list((supervisor.run_dir / "rejected").glob("*.json"))
    assert len(rejected) == 1
    raw = rejected[0].read_text(encoding="utf-8")
    assert "private-rejected-value" not in raw
    assert "unsupported fields" in raw
    assert not request_path.exists()
    assert not list((supervisor.run_dir / "processing").glob("*.json"))


def test_wrongly_typed_request_is_quarantined_without_crashing_supervisor(
    tmp_path: Path,
) -> None:
    supervisor = _seed_running_supervisor(tmp_path)
    _bind(supervisor)
    state, _ = _prepare_lease(tmp_path)
    request = _create_valid_request(supervisor, state)
    request["lineage_id"] = {"unexpected": "object"}
    request_path = _request_path(tmp_path, supervisor.run_id)
    request_path.write_text(json.dumps(request), encoding="utf-8")

    assert supervisor._check_request() is None
    assert load_runtime(tmp_path, supervisor.run_id)["state"] == "running"
    rejected = list((supervisor.run_dir / "rejected").glob("*.json"))
    assert len(rejected) == 1
    assert "lifecycle identity is malformed" in rejected[0].read_text(encoding="utf-8")


def test_ordinary_child_crash_never_relaunches(tmp_path: Path) -> None:
    child = tmp_path / "crash_child.py"
    child_log = tmp_path / "child.jsonl"
    _write_child(child, wait_on_first_launch=False)
    env = _route_env(
        CLAUDEX_SUPERVISOR_TEST_STATE_ROOT=os.fspath(tmp_path),
        SUPERVISOR_CHILD_LOG=os.fspath(child_log),
    )

    completed = subprocess.run(
        [os.fspath(_REPO_PYTHON), os.fspath(_SUPERVISOR), os.fspath(child), *_argv()],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 7, completed.stderr
    rows = _wait_for_log(child_log, 1)
    assert len(rows) == 1
    _, runtime = _wait_for_runtime(tmp_path, state="exited")
    assert runtime["exit_code"] == 7
    assert runtime["launch_generation"] == 0


def test_valid_rollover_relaunches_exact_route_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child = tmp_path / "rollover_child.py"
    child_log = tmp_path / "child.jsonl"
    _write_child(child, wait_on_first_launch=True)
    forwarded = _argv(
        "--resume",
        "existing-session",
        "--permission-mode",
        "bypassPermissions",
        "--custom-value",
        "value with spaces",
    )
    env = _route_env(
        CLAUDEX_SUPERVISOR_TEST_STATE_ROOT=os.fspath(tmp_path),
        SUPERVISOR_CHILD_LOG=os.fspath(child_log),
        ANTHROPIC_BASE_URL="https://private-proxy.invalid",
        ANTHROPIC_AUTH_TOKEN="private-token",
    )
    process = subprocess.Popen(
        [os.fspath(_REPO_PYTHON), os.fspath(_SUPERVISOR), os.fspath(child), *forwarded],
        cwd=_REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        runtime_path, runtime = _wait_for_runtime(tmp_path, state="running")
        _wait_for_log(child_log, 1)
        bind_session(
            state_root=tmp_path,
            run_id=runtime["run_id"],
            launch_generation=0,
            session_id=_SESSION_ID,
            source="startup",
            model_id="gpt-5.6-sol",
            handoff_agent=_HANDOFF_AGENT,
        )
        state, _ = _prepare_lease(tmp_path)
        replacement = state["replacement"]
        monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_RUN_ID", runtime["run_id"])
        monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION", "0")
        monkeypatch.setenv("LEARN_UKRAINIAN_SESSION_ID", _SESSION_ID)
        request = th.request_claudex_rollover(
            repo_root=_REPO_ROOT,
            state_root=tmp_path,
            lineage_id=state["lineage_id"],
            replacement=replacement,
        )
        assert request is not None
        assert request["run_id"] == runtime["run_id"]
        assert request["rollover_id"] == replacement["rollover_id"]
        stdout, stderr = process.communicate(timeout=20)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

    assert process.returncode == 0, f"{stdout}\n{stderr}"
    rows = _wait_for_log(child_log, 2)
    assert [row["generation"] for row in rows] == [0, 1]
    assert rows[0]["argv"] == forwarded
    assert rows[1]["argv"] == forwarded
    assert rows[0]["argv"].count("existing-session") == 1
    for row in rows:
        assert row["profile"] == "sol_lead"
        assert row["lead"] == "gpt-5.6-sol"
        assert row["subagent"] == "gpt-5.6-terra"
        assert row["proxy_present"] is True
        assert row["auth_present"] is True
    final_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    assert final_runtime["state"] == "exited"
    assert final_runtime["launch_generation"] == 1
    assert final_runtime["exit_code"] == 0
    consumed = list((runtime_path.parent / "consumed").glob("*.json"))
    assert len(consumed) == 1
    persisted = runtime_path.read_text(encoding="utf-8")
    assert "private-token" not in persisted
    assert "private-proxy" not in persisted


def test_relaunch_failure_leaves_handoff_lease_for_manual_recovery(tmp_path: Path) -> None:
    child = tmp_path / "removed_before_relaunch.py"
    child_log = tmp_path / "child.jsonl"
    _write_child(child, wait_on_first_launch=True)
    env = _route_env(
        CLAUDEX_SUPERVISOR_TEST_STATE_ROOT=os.fspath(tmp_path),
        SUPERVISOR_CHILD_LOG=os.fspath(child_log),
    )
    process = subprocess.Popen(
        [os.fspath(_REPO_PYTHON), os.fspath(_SUPERVISOR), os.fspath(child), *_argv()],
        cwd=_REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _, runtime = _wait_for_runtime(tmp_path, state="running")
        _wait_for_log(child_log, 1)
        bind_session(
            state_root=tmp_path,
            run_id=runtime["run_id"],
            launch_generation=0,
            session_id=_SESSION_ID,
            source="startup",
            model_id="gpt-5.6-sol",
            handoff_agent=_HANDOFF_AGENT,
        )
        state, lease_path = _prepare_lease(tmp_path)
        child.unlink()
        replacement = state["replacement"]
        create_rollover_request(
            state_root=tmp_path,
            run_id=runtime["run_id"],
            launch_generation=0,
            session_id=_SESSION_ID,
            lineage_id=state["lineage_id"],
            rollover_generation=replacement["generation"],
            rollover_id=replacement["rollover_id"],
        )
        _, stderr = process.communicate(timeout=20)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

    assert process.returncode != 0, stderr
    assert lease_path.exists()
    preserved = json.loads(lease_path.read_text(encoding="utf-8"))
    assert preserved["replacement"]["status"] == "pending_start"
