"""Tests for the consolidated SessionStart gate (scripts/hooks/session_start_gate.py).

The load-bearing property (issue #6411): a CRASHED helper must surface as
"could not determine", never as a business verdict such as a lease conflict.
Every guard test here fails if the crash→verdict mapping regresses.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_SETUP_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "session-setup.sh"

sys.path.insert(0, str(REPO_ROOT))

from scripts.hooks import session_start_gate as gate


def _args(**overrides: object) -> argparse.Namespace:
    base: dict[str, object] = {
        "repo_root": str(REPO_ROOT),
        "project_dir": str(REPO_ROOT),
        "agent": "claude-testlane",
        "session_id": "test-session-0001",
        "record_session_id": "",
        "transcript_path": "",
        "source": "",
        "observed_model": "",
        "agent_type": "",
        "profile_id": "",
        "task_family": "",
        "claim_lease": True,
        "detect": True,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


# --- python-level phase behavior ---------------------------------------------


def test_session_record_uses_record_session_id_not_thread_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """The official session record must be keyed by the hook-supplied session
    id (record_session_id), not the durable thread-lease/rollover identity
    (session_id) — context-monitor.sh still reads records back by the former
    (CF review on #6414 finding 1)."""
    from scripts.lib import session_record

    captured: dict[str, object] = {}

    def _fake_update_session(*, session_id: str, **kwargs: object) -> dict[str, object]:
        captured["session_id"] = session_id
        return {"schema_version": 1, "session_id": session_id}

    monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
    monkeypatch.setattr(session_record, "update_session", _fake_update_session)
    result = gate.phase_session_record(
        _args(session_id="thread-lease-id", record_session_id="hook-session-id")
    )
    assert captured["session_id"] == "hook-session-id"
    assert result["status"] == "ok"


def test_session_record_falls_back_to_session_id_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Direct/test invocations that omit --record-session-id still work."""
    from scripts.lib import session_record

    captured: dict[str, object] = {}

    def _fake_update_session(*, session_id: str, **kwargs: object) -> dict[str, object]:
        captured["session_id"] = session_id
        return {"schema_version": 1, "session_id": session_id}

    monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
    monkeypatch.setattr(session_record, "update_session", _fake_update_session)
    result = gate.phase_session_record(_args(session_id="thread-lease-id", record_session_id=""))
    assert captured["session_id"] == "thread-lease-id"
    assert result["status"] == "ok"


def test_lease_helper_crash_is_unknown_not_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> object:
        raise ImportError("cannot import name 'context_canary' from 'scripts' (unknown location)")

    monkeypatch.setattr(gate, "_import_thread_handoff", _boom)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "crashed"
    assert "UNKNOWN" in result["context"]
    assert "CONFLICT" not in result["context"].upper().replace("LEASE CLAIM", "")


def test_lease_structured_refusal_is_a_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(json.dumps({"status": "conflict", "owner_thread_id": "other"}))
            return 1

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "stop"
    assert "DURABLE THREAD LEASE CONFLICT" in result["context"]


def test_lease_conflict_on_stderr_is_still_a_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    """The old shell hook merged stdout+stderr (``2>&1``) before scanning for
    protocol JSON. A helper that prints its structured conflict payload to
    stderr instead of stdout must still be classified as a real conflict, not
    silently degraded to crashed/unknown (CF review round 2 on #6414,
    retained finding 3).

    Mutation-check: change ``_parse_protocol_payload`` back to reading only
    ``out`` (drop the ``err`` fallback) -> this test fails because the
    payload is never found. Restore the fallback -> passes.
    """

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(json.dumps({"status": "conflict", "owner_thread_id": "other"}), file=sys.stderr)
            return 1

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "stop"
    assert "DURABLE THREAD LEASE CONFLICT" in result["context"]


def test_lease_structured_error_is_not_a_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    """A structured-but-non-conflict status (e.g. {"status": "error"}) is a
    HELPER FAILURE, not a business refusal — restricting the DURABLE THREAD
    LEASE CONFLICT label to the exact "conflict" status (CF review on #6414
    finding 3; the #6411 mislabel class)."""

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(json.dumps({"status": "error", "error": "lock backend unavailable"}))
            return 1

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "crashed"
    assert "UNKNOWN" in result["context"]
    assert "DURABLE THREAD LEASE CONFLICT" not in result["context"]


def test_lease_rc0_malformed_json_is_not_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """rc == 0 alone is not proof of a claim — malformed/empty JSON on a
    clean exit must not fall through to an unconditional ok (CF review on
    #6414 finding 2)."""

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print("not json")
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "crashed"
    assert "UNKNOWN" in result["context"]


def test_lease_rc0_without_acquired_status_is_not_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """rc == 0 with a parseable but non-"acquired" status (e.g. a stale
    "conflict" payload on an otherwise clean exit) must not be treated as a
    successful claim (CF review on #6414 finding 2)."""

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(json.dumps({"status": "conflict", "owner_thread_id": "other"}))
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "crashed"
    assert "UNKNOWN" in result["context"]


def test_lease_unstructured_failure_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print("Traceback (most recent call last): boom")
            return 1

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "crashed"
    assert "UNKNOWN" in result["context"]
    assert "DURABLE THREAD LEASE CONFLICT" not in result["context"]


def test_lease_acquired_reports_generation_and_takeover(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "status": "acquired",
                        "generation": 7,
                        "replaced_owner_thread_id": "dead-owner",
                        "takeover_reason": "owner process not found",
                    }
                )
            )
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_thread_lease(_args())
    assert result["status"] == "ok"
    assert result["generation"] == "7"
    assert "THREAD LEASE TAKEOVER" in result["takeover_banner"]
    assert "dead-owner" in result["takeover_banner"]


def test_lease_without_session_id_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    result = gate.phase_thread_lease(_args(session_id=""))
    assert result["status"] == "stop"
    assert "did not provide a current thread id" in result["context"]


def test_detect_crash_is_crashed_not_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> object:
        raise ModuleNotFoundError("No module named 'scripts'")

    monkeypatch.setattr(gate, "_import_thread_handoff", _boom)
    result = gate.phase_rollover_detect(_args())
    assert result["status"] == "crashed"


def test_detect_none_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(json.dumps({"status": "none"}))
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_rollover_detect(_args())
    assert result == {"status": "ok", "detect_status": "none"}


def test_detect_ambiguous_on_stderr_still_formats_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same stderr-payload guard as the lease phase, for detect (CF review
    round 2 on #6414, retained finding 3).

    Mutation-check: change ``_parse_protocol_payload`` back to reading only
    ``out`` -> this test fails because ``detect_status`` never resolves to
    "ambiguous" and the formatted stop context is never produced. Restore
    the ``err`` fallback -> passes.
    """

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            if "--format" in argv and argv[argv.index("--format") + 1] == "json":
                print(json.dumps({"status": "ambiguous"}), file=sys.stderr)
            else:
                print("ROLLOVER PACKET: follow the thread-rollover workflow.")
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_rollover_detect(_args())
    assert result["status"] == "stop"
    assert "ROLLOVER PACKET" in result["context"]
    assert result["detect_status"] == "ambiguous"


def test_detect_pending_returns_formatted_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            if "--format" in argv and argv[argv.index("--format") + 1] == "json":
                print(json.dumps({"status": "pending_start"}))
            else:
                print("ROLLOVER PACKET: follow the thread-rollover workflow.")
            return 0

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    result = gate.phase_rollover_detect(_args())
    assert result["status"] == "stop"
    assert "ROLLOVER PACKET" in result["context"]
    assert result["detect_status"] == "pending_start"


def test_python_version_matches_pin() -> None:
    # The suite runs on the canonical venv python, which must match the pin.
    result = gate.phase_python_version(_args())
    assert result == {"status": "ok"}


def test_python_version_mismatch_is_issue(tmp_path: Path) -> None:
    (tmp_path / ".python-version").write_text("2.7.99\n")
    result = gate.phase_python_version(_args(repo_root=str(tmp_path)))
    assert result["status"] == "issue"
    assert "VENV WRONG PYTHON" in result["verdict"]


def test_lease_verdict_is_authoritative_over_detect(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """detect must not run once the lease phase says stop/crashed.

    The old version of this test mocked ``_import_thread_handoff`` to raise
    for BOTH phases and only asserted ``rc == 0`` — but ``main()`` always
    returns 0 once it produces JSON (see its docstring), regardless of
    whether detect ran or was skipped. That assertion could not fail even if
    the "skip detect" gating were deleted entirely. This version uses a
    phase-specific fake with a call counter so it proves detect's ``main``
    was never invoked, not just that the gate didn't crash.

    Mutation-check: delete the ``if lease_status in {"stop", "crashed"}:
    skip`` gating in ``main()`` (call ``phase_rollover_detect`` unconditionally)
    -> ``detect_calls`` becomes 1 and this test fails. Restore it -> passes.
    """

    detect_calls = 0

    class FakeTH:
        @staticmethod
        def main(argv: list[str]) -> int:
            nonlocal detect_calls
            if "claim-thread-lease" in argv:
                print(json.dumps({"status": "conflict", "owner_thread_id": "other"}))
                return 1
            if "detect" in argv:
                detect_calls += 1
                print(json.dumps({"status": "none"}))
                return 0
            raise AssertionError(f"unexpected thread_handoff invocation: {argv}")

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: FakeTH)
    rc = gate.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--project-dir",
            str(REPO_ROOT),
            "--agent",
            "claude-testlane",
            "--session-id",
            "s-1",
            "--claim-lease",
            "--detect",
        ]
    )
    assert rc == 0
    result = json.loads(capsys.readouterr().out)
    assert result["thread_lease"]["status"] == "stop"
    assert result["rollover_detect"] == {
        "status": "skipped",
        "reason": "lease verdict is authoritative",
    }
    assert detect_calls == 0, "detect ran despite an authoritative lease stop verdict"


# --- shell-level verdict mapping ---------------------------------------------

FAKE_RUNNER = '''
import json, os, sys
joined = " ".join(sys.argv)
if "session_start_gate" in joined:
    rc = int(os.environ.get("FAKE_GATE_RC", "0"))
    if rc == 0:
        sys.stdout.write(os.environ.get("FAKE_GATE_JSON", "{}"))
    sys.exit(rc)
sys.exit(0)
'''

BASE_GATE_RESULT = {
    "session_record": {"status": "ok"},
    "python_version": {"status": "ok"},
    "primary_main": {"status": "ok"},
    "thread_lease": {"status": "ok", "generation": "3", "takeover_banner": ""},
    "rollover_detect": {"status": "ok", "detect_status": "none"},
}


def _run_hook(tmp_path: Path, extra_env: dict[str, str]) -> str:
    hook = tmp_path / "session-setup.sh"
    shutil.copy2(SESSION_SETUP_HOOK, hook)
    runner = tmp_path / "fake_runner.py"
    runner.write_text(FAKE_RUNNER)

    environment = os.environ.copy()
    for key in tuple(environment):
        if key.startswith(("LEARN_UKRAINIAN_", "CODEX_", "SESSION_", "CLAUDE_ENV")):
            environment.pop(key, None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(REPO_ROOT),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(REPO_ROOT),
            "HOME": os.fspath(tmp_path / "home"),
            "SESSION_HANDOFF_AGENT": "claude-testlane",
            "SESSION_BOUNDED_RUNNER": os.fspath(runner),
            # Hermetic interpreter injection (worktrees carry no venv — F001 r5).
            "CLAUDE_SESSION_RECORD_PYTHON": sys.executable,
        }
    )
    environment.update(extra_env)
    completed = subprocess.run(
        ["bash", os.fspath(hook)],
        input=json.dumps({"session_id": "shell-test-0001", "source": "startup"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=40,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]


def test_shell_maps_lease_crash_to_unknown_never_conflict(tmp_path: Path) -> None:
    result = dict(BASE_GATE_RESULT)
    result["thread_lease"] = {
        "status": "crashed",
        "error": "ImportError: shadowed scripts package",
        "context": (
            "ERROR: LEASE CLAIM HELPER CRASHED — stop; lease state UNKNOWN; do NOT "
            "force-release.\nError: ImportError: shadowed scripts package"
        ),
    }
    result["rollover_detect"] = {"status": "skipped", "reason": "lease verdict is authoritative"}
    context = _run_hook(tmp_path, {"FAKE_GATE_JSON": json.dumps(result)})
    assert "lease state UNKNOWN" in context
    assert "DURABLE THREAD LEASE CONFLICT" not in context


def test_shell_passes_real_conflict_through(tmp_path: Path) -> None:
    result = dict(BASE_GATE_RESULT)
    result["thread_lease"] = {
        "status": "stop",
        "context": (
            "ERROR: DURABLE THREAD LEASE CONFLICT — stop; do not cold-start or drive "
            'this queue.\nOutput:\n{"status": "conflict"}'
        ),
    }
    result["rollover_detect"] = {"status": "skipped", "reason": "lease verdict is authoritative"}
    context = _run_hook(tmp_path, {"FAKE_GATE_JSON": json.dumps(result)})
    assert "DURABLE THREAD LEASE CONFLICT" in context


def test_shell_maps_gate_failure_to_could_not_run(tmp_path: Path) -> None:
    context = _run_hook(tmp_path, {"FAKE_GATE_RC": "1"})
    assert "SESSION GATE COULD NOT RUN" in context
    assert "lease state UNKNOWN" in context
    assert "DURABLE THREAD LEASE CONFLICT" not in context


def test_shell_surfaces_takeover_banner(tmp_path: Path) -> None:
    result = dict(BASE_GATE_RESULT)
    result["thread_lease"] = {
        "status": "ok",
        "generation": "9",
        "takeover_banner": "THREAD LEASE TAKEOVER: this session (generation 9) replaced owner x -- reason: dead.",
    }
    context = _run_hook(tmp_path, {"FAKE_GATE_JSON": json.dumps(result)})
    assert "THREAD LEASE TAKEOVER" in context
