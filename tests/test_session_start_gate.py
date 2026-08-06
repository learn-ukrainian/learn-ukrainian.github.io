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


def test_lease_verdict_is_authoritative_over_detect(monkeypatch: pytest.MonkeyPatch) -> None:
    """detect must not run once the lease phase says stop/crashed."""

    def _boom() -> object:
        raise ImportError("shadowed")

    monkeypatch.setattr(gate, "_import_thread_handoff", _boom)
    rc = 0
    out_path = os.devnull
    with open(out_path, "w") as devnull:
        stdout = sys.stdout
        sys.stdout = devnull
        try:
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
        finally:
            sys.stdout = stdout
    assert rc == 0


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
