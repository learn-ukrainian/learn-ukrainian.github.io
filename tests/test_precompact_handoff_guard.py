"""Own-handoff proof and no-follow redirects for PreCompact(auto) (#9790)."""

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
    "Automatic compaction paused: this session has prepared its rollover handoff. Restart the session to continue.\n"
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


def test_valid_own_handoff_blocks_and_is_read_only(prepared):
    root, _, _, _, _ = prepared
    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = _run(prepared)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", BLOCK_MESSAGE)
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("component", [".agent", "thread-rollovers", "agent", "lineage", "generation", "packet"])
def test_each_symlinked_ancestor_allows_even_with_valid_outside_packet(prepared, tmp_path, component):
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
    _allowed(_run(prepared))
    assert {p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("member", ["lease", "handoff", "record"])
@pytest.mark.parametrize("failure", ["missing", "symlink", "fifo", "directory", "unreadable"])
def test_unavailable_or_unsafe_file_allows(prepared, tmp_path, member, failure):
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
    _allowed(_run(prepared))


@pytest.mark.parametrize("mutation", ["foreign", "schema", "identity", "outside", "started", "malformed", "nonobject"])
def test_invalid_or_foreign_lease_allows(prepared, mutation):
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
    _allowed(_run(prepared))


@pytest.mark.parametrize("mutation", ["foreign", "schema", "malformed", "nonobject", "continuation", "missing-mode"])
def test_invalid_or_other_profile_record_allows(prepared, mutation):
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
    _allowed(_run(prepared, LEARN_UKRAINIAN_ROLLOVER_MODE="operator_restart"))


@pytest.mark.parametrize("content", ["", " \n\t"])
def test_empty_handoff_allows(prepared, content):
    prepared[3].write_text(content)
    _allowed(_run(prepared))


@pytest.mark.parametrize(
    "payload",
    [
        {"hook_event_name": "PreCompact", "trigger": "manual", "session_id": SESSION},
        {"hook_event_name": "PreCompact", "session_id": SESSION},
        {"hook_event_name": "PostCompact", "trigger": "auto", "session_id": SESSION},
        {"hook_event_name": "PreCompact", "trigger": "auto", "session_id": "../foreign"},
        {"hook_event_name": "PreCompact", "trigger": "auto"},
        {"hook_event_name": "PreCompact", "trigger": "auto", "session_id": 1},
        "{bad json",
        "[]",
    ],
)
def test_manual_missing_or_malformed_input_allows(prepared, payload):
    _allowed(_run(prepared, payload=payload))


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
        {"THREAD_ROLLOVER_PYTHON": "/nonexistent/interpreter"},
        {"SESSION_BOUNDED_RUNNER": "/nonexistent/runner"},
    ],
)
def test_other_harness_workers_or_missing_runtime_allow(prepared, extra_env):
    _allowed(_run(prepared, **extra_env))


def test_timeout_allows_and_does_not_trust_partial_prepared_output(prepared, tmp_path):
    runner = tmp_path / "slow-runner.py"
    runner.write_text("import time\nprint('prepared', flush=True)\ntime.sleep(30)\n")
    # Keep the real deadline runner; delay the checker by importing a shadow
    # module from a temporary project, without replacing any production file.
    project = tmp_path / "slow-project"
    module = project / "scripts/orchestration/precompact_handoff_check.py"
    module.parent.mkdir(parents=True)
    module.write_bytes(runner.read_bytes())
    started = time.monotonic()
    _allowed(_run(prepared, CLAUDE_PROJECT_DIR=os.fspath(project)))
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

    def spy_open(path, flags, mode=0o777, *, dir_fd=None):
        opened.append((os.fspath(path), flags, dir_fd))
        return real_open(path, flags, mode, dir_fd=dir_fd)

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
def test_symlinked_root_or_session_directory_allows(prepared, tmp_path, component):
    root = prepared[0]
    path = root if component == "root" else root / ".agent/sessions"
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=True)
    _allowed(_run(prepared))


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


def test_settings_registers_only_auto_guard_and_shell_parses():
    settings = json.loads((REPO / "agents_extensions/shared/settings.json").read_text())
    registrations = [
        (entry.get("matcher"), hook)
        for entry in settings["hooks"]["PreCompact"]
        for hook in entry["hooks"]
        if "precompact-handoff-guard.sh" in hook.get("command", "")
    ]
    assert registrations == [
        (
            "auto",
            {
                "type": "command",
                "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/precompact-handoff-guard.sh",
                "timeout": 5,
            },
        )
    ]
    result = subprocess.run(["bash", "-n", os.fspath(HOOK)], capture_output=True, text=True, check=False, timeout=30)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
