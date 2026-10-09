"""Fail-closed interactive PreCompact policy and own-handoff proof (#10265)."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.orchestration import precompact_handoff_check as check
from scripts.orchestration import thread_handoff as th

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "agents_extensions/shared/hooks/precompact-handoff-guard.sh"
SESSION = "precompact-session"
AGENT = "claude-infra"
BLOCK_MESSAGE = (
    "Claude driver compaction refused: thread-rollover handoff is prepared; print HANDOFF-DONE <path> "
    "using its exact handoff path and exit for a fresh launcher restart.\n"
)


@pytest.fixture
def prepared(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    state = th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION},
        agent=AGENT,
        now=datetime(2026, 10, 6, tzinfo=UTC),
        active_thread_id=SESSION,
        active_automation_id=None,
        context_percent=80,
        force_new_replacement=False,
        harness="claude-code",
    )
    state["replacement"]["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    lease = root / th.default_state_path(AGENT, state["lineage_id"])
    lease.parent.mkdir(parents=True)
    lease.write_text(json.dumps(state), encoding="utf-8")
    handoff = root / state["replacement"]["handoff_path"]
    handoff.parent.mkdir(parents=True)
    handoff.write_text("# Prepared continuity\nNext: finish the assigned task.\n", encoding="utf-8")
    record = root / ".agent/sessions" / f"{SESSION}.json"
    record.parent.mkdir()
    record.write_text(
        json.dumps({"schema_version": 1, "session_id": SESSION, "rollover_mode": "operator_restart"}),
        encoding="utf-8",
    )
    return root, state, lease, handoff, record


def _run(prepared, *, payload=None, **extra_env):
    root = prepared[0]
    env = os.environ.copy()
    for key in (
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "CODEX_SESSION",
        "CLAUDE_NON_INTERACTIVE",
        "LEARN_UK_PIPELINE",
        "LEARN_UKRAINIAN_PIPELINE",
        "GEMINI_SESSION",
        "GROK_AGENT",
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
        "LEARN_UKRAINIAN_SESSION_RECORD",
        "LEARN_UKRAINIAN_SESSION_ID",
        "LEARN_UKRAINIAN_ROLLOVER_MODE",
    ):
        env.pop(key, None)
    env.update(
        CLAUDE_PROJECT_DIR=os.fspath(REPO),
        CODEX_CANONICAL_REPO_ROOT=os.fspath(root),
        THREAD_ROLLOVER_PYTHON=sys.executable,
        SESSION_BOUNDED_RUNNER=os.fspath(REPO / "scripts/agent_runtime/bounded_command.py"),
        SESSION_HANDOFF_AGENT=AGENT,
    )
    env.update(extra_env)
    if payload is None:
        payload = {"hook_event_name": "PreCompact", "trigger": "auto", "session_id": SESSION}
    return subprocess.run(
        [os.fspath(HOOK)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO,
        env=env,
        timeout=10,
        check=False,
    )


def _allowed(result):
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def _refused(result):
    assert result.returncode == 2
    assert result.stdout == ""
    assert "compaction refused" in result.stderr
    assert "thread-rollover" in result.stderr
    assert "HANDOFF-DONE <path>" in result.stderr


@pytest.mark.parametrize("trigger", ["auto", "manual"])
def test_valid_own_handoff_blocks_and_is_read_only(prepared, trigger):
    root, _, _, _, _ = prepared
    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = _run(prepared, payload={"hook_event_name": "PreCompact", "trigger": trigger, "session_id": SESSION})
    assert (result.returncode, result.stdout, result.stderr) == (2, "", BLOCK_MESSAGE)
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("component", [".agent", "thread-rollovers", "agent", "lineage", "generation", "packet"])
def test_each_symlinked_ancestor_refuses_driver_allows_worker(prepared, tmp_path, component):
    root, _, lease, handoff, _ = prepared
    paths = {
        ".agent": root / ".agent",
        "thread-rollovers": root / ".agent/thread-rollovers",
        "agent": lease.parent.parent,
        "lineage": lease.parent,
        "generation": handoff.parent.parent,
        "packet": handoff.parent,
    }
    path = paths[component]
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=True)
    before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
    _refused(_run(prepared))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))
    assert {p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("member", ["lease", "handoff", "record"])
@pytest.mark.parametrize("failure", ["missing", "symlink", "fifo", "directory", "unreadable"])
def test_unavailable_or_unsafe_file_refuses_driver_allows_worker(prepared, tmp_path, member, failure):
    _, _, lease, handoff, record = prepared
    path = {"lease": lease, "handoff": handoff, "record": record}[member]
    contents = path.read_bytes()
    path.unlink()
    if failure == "symlink":
        outside = tmp_path / "outside"
        outside.write_bytes(contents)
        path.symlink_to(outside)
    elif failure == "fifo":
        os.mkfifo(path)
    elif failure == "directory":
        path.mkdir()
    elif failure == "unreadable":
        # Invalid UTF-8 is unreadable even under a privileged test process.
        path.write_bytes(b"\xff")
    _refused(_run(prepared))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize("mutation", ["foreign", "schema", "identity", "outside", "started", "malformed", "nonobject"])
def test_invalid_or_foreign_lease_refuses_driver_allows_worker(prepared, mutation):
    _, state, lease, handoff, _ = prepared
    if mutation == "foreign":
        state["active"]["thread_id"] = "other-session"
    elif mutation == "schema":
        state["schema_version"] = 999
    elif mutation == "identity":
        state["replacement"]["canary_challenge"] = "forged"
    elif mutation == "outside":
        state["replacement"]["handoff_path"] = os.fspath(handoff)
    elif mutation == "started":
        state["replacement"]["status"] = "started"
    lease.write_text(
        "{bad json" if mutation == "malformed" else json.dumps([] if mutation == "nonobject" else state),
        encoding="utf-8",
    )
    _refused(_run(prepared))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize("mutation", ["foreign", "schema", "malformed", "nonobject", "continuation", "missing-mode"])
def test_invalid_or_other_profile_record_refuses_driver_allows_worker(prepared, mutation):
    record = prepared[4]
    data = json.loads(record.read_text())
    if mutation == "foreign":
        data["session_id"] = "other-session"
    elif mutation == "schema":
        data["schema_version"] = 999
    elif mutation == "continuation":
        data["rollover_mode"] = "continuation"
    elif mutation == "missing-mode":
        del data["rollover_mode"]
    record.write_text("{bad json" if mutation == "malformed" else json.dumps([] if mutation == "nonobject" else data))
    _refused(_run(prepared, LEARN_UKRAINIAN_ROLLOVER_MODE="operator_restart"))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize("content", ["", " \n\t"])
def test_empty_handoff_refuses_driver_allows_worker(prepared, content):
    prepared[3].write_text(content)
    _refused(_run(prepared))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize(
    "payload",
    [
        {"hook_event_name": "PreCompact", "session_id": SESSION},
        {"hook_event_name": "PostCompact", "trigger": "auto", "session_id": SESSION},
        {"hook_event_name": "PreCompact", "trigger": "auto", "session_id": "../foreign"},
        {"hook_event_name": "PreCompact", "trigger": "auto"},
        {"hook_event_name": "PreCompact", "trigger": "auto", "session_id": 1},
        "{bad json",
        "[]",
    ],
)
def test_missing_or_malformed_input_refuses_driver_allows_worker(prepared, payload):
    _refused(_run(prepared, payload=payload))
    _allowed(_run(prepared, payload=payload, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize(
    "extra_env",
    [
        {"SESSION_HANDOFF_AGENT": "codex"},
        {"SESSION_HANDOFF_AGENT": "grok"},
        {"SESSION_HANDOFF_AGENT": "gemini"},
        {"SESSION_HANDOFF_AGENT": "../../foreign"},
        {"CODEX_THREAD_ID": "native-thread"},
        {"CODEX_SESSION_ID": "native-session"},
        {"CODEX_SESSION": "1"},
        {"CLAUDE_NON_INTERACTIVE": "1"},
        {"LEARN_UK_PIPELINE": "1"},
        {"LEARN_UKRAINIAN_PIPELINE": "1"},
        {"GEMINI_SESSION": "1"},
        {"GROK_AGENT": "1"},
        {"LEARN_UKRAINIAN_DISPATCH_TASK_ID": "worker"},
    ],
)
def test_other_harness_and_workers_allow(prepared, extra_env):
    _allowed(_run(prepared, **extra_env))


def test_timeout_refuses_driver_allows_worker_and_discards_partial_output(prepared, tmp_path):
    runner = tmp_path / "slow-runner.py"
    runner.write_text("import time\nprint('prepared', flush=True)\ntime.sleep(30)\n")
    # Keep the real deadline runner; delay the checker by importing a shadow
    # module from a temporary project, without replacing any production file.
    project = tmp_path / "slow-project"
    module = project / "scripts/orchestration/precompact_handoff_check.py"
    module.parent.mkdir(parents=True)
    module.write_bytes(runner.read_bytes())
    started = time.monotonic()
    _refused(_run(prepared, CLAUDE_PROJECT_DIR=os.fspath(project)))
    _allowed(_run(prepared, CLAUDE_PROJECT_DIR=os.fspath(project), CLAUDE_NON_INTERACTIVE="1"))
    assert 2 <= time.monotonic() - started < 8


def test_validator_receives_descriptor_read_input_after_lease_redirect(prepared, tmp_path, monkeypatch):
    root, state, lease, _, _ = prepared
    real_open = check.safe_open_below
    real_validate = check.validate_live_lease
    reads = []
    validated = []

    def spy_open(parent, name, flags):
        fd = real_open(parent, name, flags)
        reads.append((name, os.fstat(parent), os.fstat(fd)))
        if name == "lease.json":
            lease.rename(tmp_path / "held-lease.json")
            outside = tmp_path / "foreign.json"
            outside.write_text('{"schema_version": 999}')
            lease.symlink_to(outside)
        return fd

    def spy_validate(payload, *, agent, state_path):
        assert payload == state
        assert agent == AGENT
        assert state_path == lease  # lexical canonical identity, never resolved
        validated.append(payload)
        return real_validate(payload, agent=agent, state_path=state_path)

    monkeypatch.setattr(check, "safe_open_below", spy_open)
    monkeypatch.setattr(check, "validate_live_lease", spy_validate)
    assert check.has_prepared_handoff(root, agent=AGENT, session_id=SESSION)
    assert len(validated) == 1
    assert [name for name, _, _ in reads] == [f"{SESSION}.json", "lease.json", "handoff.md"]
    assert reads[1][2].st_ino == (tmp_path / "held-lease.json").stat().st_ino


def test_every_component_open_uses_nofollow_and_relative_descriptor(prepared, monkeypatch):
    root, _, _, handoff, _ = prepared
    real_open = os.open
    opened = []

    def spy_open(path, flags, *args, dir_fd=None, **kwargs):
        opened.append((os.fspath(path), flags, dir_fd))
        return real_open(path, flags, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    assert check.has_prepared_handoff(root, agent=AGENT, session_id=SESSION)
    assert opened[0][0] == os.fspath(root)
    assert all(flags & os.O_NOFOLLOW for _, flags, _ in opened)
    assert all(dir_fd is not None and "/" not in path for path, _, dir_fd in opened[1:])
    for component in handoff.relative_to(root).parts:
        assert any(path == component for path, _, _ in opened)


def test_permission_error_and_validator_exception_allow(prepared, monkeypatch):
    root = prepared[0]

    def unreadable(*_args, **_kwargs):
        raise PermissionError("unreadable")

    with monkeypatch.context() as patch:
        patch.setattr(check, "safe_open_below", unreadable)
        assert not check.has_prepared_handoff(root, agent=AGENT, session_id=SESSION)
    monkeypatch.setattr(check, "validate_live_lease", unreadable)
    assert not check.has_prepared_handoff(root, agent=AGENT, session_id=SESSION)


def test_lineage_retained_from_predecessor_still_matches_current_session(prepared):
    root, state, lease, _, _ = prepared
    # A replacement session inherits its predecessor's lineage, then prepares
    # another handoff. Discovery must not assume lineage_id_for(current session).
    state["active"]["thread_id"] = "replacement-session"
    state["replacement"]["identity"]["predecessor_task_id"] = "replacement-session"
    lease.write_text(json.dumps(state))
    record = root / ".agent/sessions/replacement-session.json"
    record.write_text(
        json.dumps({"schema_version": 1, "session_id": "replacement-session", "rollover_mode": "operator_restart"})
    )
    assert check.has_prepared_handoff(root, agent=AGENT, session_id="replacement-session")


@pytest.mark.parametrize("component", ["root", "sessions"])
def test_symlinked_root_or_session_directory_refuses_driver_allows_worker(prepared, tmp_path, component):
    root = prepared[0]
    path = root if component == "root" else root / ".agent/sessions"
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=True)
    _refused(_run(prepared))
    _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize(
    "mutation", ["valid", "foreign", "bad-lease", "empty", "no-lineages", "invalid-agent", "invalid-session"]
)
def test_checker_direct_evidence_decisions(prepared, mutation):
    root, state, lease, handoff, _ = prepared
    session, agent = SESSION, AGENT
    if mutation == "foreign":
        state["active"]["thread_id"] = "foreign"
    elif mutation == "bad-lease":
        state["schema_version"] = 999
    elif mutation == "empty":
        handoff.write_text("")
    elif mutation == "no-lineages":
        lease.parent.rename(lease.parent.with_name("unrelated"))
    elif mutation == "invalid-agent":
        agent = "codex"
    elif mutation == "invalid-session":
        session = "../foreign"
    if mutation != "no-lineages":
        lease.write_text(json.dumps(state))
    assert check.has_prepared_handoff(root, agent=agent, session_id=session) is (mutation == "valid")


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"hook_event_name": "PreCompact", "trigger": "auto", "session_id": SESSION}, "prepared\n"),
        ({"hook_event_name": "PreCompact", "trigger": "manual", "session_id": SESSION}, ""),
        ({"hook_event_name": "PostCompact", "trigger": "auto", "session_id": SESSION}, ""),
        ({"hook_event_name": "PreCompact", "trigger": "auto", "session_id": None}, ""),
        ([], ""),
        ("{bad json", ""),
    ],
)
def test_checker_main_reads_official_payload_only(prepared, monkeypatch, capsys, payload, expected):
    monkeypatch.setattr(sys, "argv", ["check", "--state-root", os.fspath(prepared[0]), "--agent", AGENT])
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload if isinstance(payload, str) else json.dumps(payload)))
    assert check.main() == 0
    result = capsys.readouterr()
    assert (result.out, result.err) == (expected, "")


def test_settings_registers_both_triggers_and_shell_parses():
    settings = json.loads((REPO / "agents_extensions/shared/settings.json").read_text())
    registrations = [
        (entry.get("matcher"), hook)
        for entry in settings["hooks"]["PreCompact"]
        for hook in entry["hooks"]
        if "precompact-handoff-guard.sh" in hook.get("command", "")
    ]
    assert len(registrations) == 1
    matcher, registration = registrations[0]
    assert matcher == "manual|auto"
    assert registration["type"] == "command"
    assert "precompact-handoff-guard.sh" in registration["command"]
    assert "exit 2" in registration["command"]
    assert registration["timeout"] == 5
    result = subprocess.run(["bash", "-n", os.fspath(HOOK)], capture_output=True, text=True, check=False, timeout=30)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("trigger", ["auto", "manual"])
@pytest.mark.parametrize("session_class", ["interactive_driver", "headless_worker", "isolated_review"])
@pytest.mark.parametrize(
    "failure",
    [
        "no_handoff",
        "missing_runtime",
        "missing_runner",
        "exception",
        "partial_output",
        "unexpected_output",
        "unsafe_file",
        "timeout",
    ],
)
def test_compaction_denominator_and_failure_modes(prepared, tmp_path, trigger, session_class, failure):
    payload = {"hook_event_name": "PreCompact", "trigger": trigger, "session_id": SESSION}
    extra = {}
    if session_class == "headless_worker":
        extra["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = "worker"
    elif session_class == "isolated_review":
        extra["CLAUDE_NON_INTERACTIVE"] = "1"
    if failure == "no_handoff":
        prepared[3].unlink()
    elif failure == "unsafe_file":
        outside = tmp_path / "outside-handoff.md"
        outside.write_bytes(prepared[3].read_bytes())
        prepared[3].unlink()
        prepared[3].symlink_to(outside)
    elif failure == "missing_runtime":
        extra["THREAD_ROLLOVER_PYTHON"] = os.fspath(tmp_path / "missing-python")
    elif failure == "missing_runner":
        extra["SESSION_BOUNDED_RUNNER"] = os.fspath(tmp_path / "missing-runner")
    else:
        runner = tmp_path / "broken-runner.py"
        runner.write_text(
            {
                "exception": "raise RuntimeError('private diagnostic must not escape')\n",
                "partial_output": "print('prepared', flush=True)\nraise RuntimeError('private diagnostic must not escape')\n",
                "unexpected_output": "print('prepared\\nextra')\n",
                "timeout": "import time\nprint('prepared', flush=True)\ntime.sleep(30)\n",
            }[failure]
        )
        extra["SESSION_BOUNDED_RUNNER"] = os.fspath(runner)
    result = _run(prepared, payload=payload, **extra)
    if session_class == "interactive_driver":
        _refused(result)
        assert result.stderr != BLOCK_MESSAGE
        assert "private diagnostic" not in result.stderr
    else:
        _allowed(result)


def test_shell_exception_refuses_without_runtime_or_evidence(prepared, tmp_path):
    hook = tmp_path / HOOK.name
    hook.write_bytes(HOOK.read_bytes())
    hook.chmod(0o755)
    (tmp_path / "context-rollover-lib.sh").write_text("exit 7\n")
    # _run's interpreter/evidence environment stays identical to a healthy driver.
    import unittest.mock

    with unittest.mock.patch(__name__ + ".HOOK", hook):
        _refused(_run(prepared))
        _allowed(_run(prepared, CLAUDE_NON_INTERACTIVE="1"))


@pytest.mark.parametrize(
    "session_env",
    [
        {},
        {"CLAUDE_NON_INTERACTIVE": "1"},
        {"LEARN_UKRAINIAN_DISPATCH_TASK_ID": "worker"},
    ],
)
@pytest.mark.parametrize("exit_code", [None, 1, 7, 143])
def test_registration_refuses_driver_allows_exempt_sessions_if_hook_errors(
    tmp_path, monkeypatch, session_env, exit_code
):
    settings = json.loads((REPO / "agents_extensions/shared/settings.json").read_text())
    command = settings["hooks"]["PreCompact"][0]["hooks"][0]["command"]
    if exit_code is not None:
        hook = tmp_path / ".claude/hooks/precompact-handoff-guard.sh"
        hook.parent.mkdir(parents=True)
        hook.write_text(f"#!/bin/sh\nexit {exit_code}\n")
        hook.chmod(0o755)
    # Mirror the guard's clean driver fixture so the dispatch running pytest
    # cannot classify the isolated settings probe as an exempt worker.
    for key in (
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "CODEX_SESSION",
        "CLAUDE_NON_INTERACTIVE",
        "LEARN_UK_PIPELINE",
        "LEARN_UKRAINIAN_PIPELINE",
        "GEMINI_SESSION",
        "GROK_AGENT",
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
        "SESSION_HANDOFF_AGENT",
    ):
        monkeypatch.delenv(key, raising=False)
    result = subprocess.run(
        ["sh", "-c", command],
        env={**os.environ, "CLAUDE_PROJECT_DIR": os.fspath(tmp_path), **session_env},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if not session_env:
        _refused(result)
    else:
        assert result.returncode == 0
