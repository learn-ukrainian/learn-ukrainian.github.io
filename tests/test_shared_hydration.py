"""Contract tests for the bounded long-horizon hydration capsule."""

from __future__ import annotations

import signal
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.session_canary import shared_hydration as hydration


def _evidence() -> dict[str, object]:
    return {
        "driver_identity": {"agent": "gemini", "harness": "agy", "instance_id": "gemini-1"},
        "lease_state": {"lease": "active", "session": "open"},
        "fencing_token": 4,
        "next_drive_boundary": {"entry_id": 12, "instruction": "Run the focused tests."},
    }


def test_capsule_is_schema_and_format_checker_compliant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hydration, "_collect_stream_evidence", lambda stream_id: _evidence())
    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    validator = Draft202012Validator(hydration.HYDRATION_CAPSULE_V1_SCHEMA, format_checker=FormatChecker())
    assert list(validator.iter_errors(capsule)) == []
    assert capsule["state"] == "ready"
    assert capsule["execution_allowed"] is True
    assert capsule["blocked"] is False


def test_deadline_is_monotonic_and_degrades_without_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter((10.0, 10.02, 10.101, 10.101))
    monkeypatch.setattr(hydration.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(hydration, "_collect_stream_evidence", lambda stream_id: _evidence())

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "degraded"
    assert capsule["degradation_reasons"] == ["deadline-exceeded"]
    assert capsule["execution_allowed"] is True
    assert capsule["blocked"] is False


def test_unavailable_critical_evidence_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(stream_id: str) -> dict[str, object]:
        raise LookupError("missing")

    monkeypatch.setattr(hydration, "_collect_stream_evidence", unavailable)
    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "blocked"
    assert capsule["execution_allowed"] is False
    assert capsule["blocked"] is True
    assert capsule["lease_state"]["status"] != "ok"


def test_terminating_process_group_reaps_child_without_zombie(monkeypatch: pytest.MonkeyPatch) -> None:
    class Process:
        pid = 4242
        returncode: int | None = None

    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(hydration.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    monkeypatch.setattr(hydration.os, "waitpid", lambda pid, options: (pid, 0))

    process = Process()
    hydration.terminate_process_group(process)  # type: ignore[arg-type]

    assert calls == [(4242, signal.SIGTERM)]
    assert process.returncode == 0


def test_terminating_process_group_escalates_after_200ms(monkeypatch: pytest.MonkeyPatch) -> None:
    class Process:
        pid = 4242

    calls: list[tuple[int, int]] = []
    waits: list[float] = []
    results = iter((False, True))
    monkeypatch.setattr(hydration.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    monkeypatch.setattr(
        hydration,
        "_reap_pid",
        lambda process, timeout: waits.append(timeout) or next(results),
    )

    hydration.terminate_process_group(Process())  # type: ignore[arg-type]

    assert calls == [(4242, signal.SIGTERM), (4242, signal.SIGKILL)]
    assert waits == [0.200, 0.200]


def test_gh_queries_are_new_sessions_and_timeout_reaps(monkeypatch: pytest.MonkeyPatch) -> None:
    class Process:
        pid = 4242
        returncode: int | None = None

        def communicate(self, *, timeout: float) -> tuple[str, str]:
            raise hydration.subprocess.TimeoutExpired("gh", timeout)

    launched: dict[str, object] = {}
    monkeypatch.setattr(hydration.subprocess, "Popen", lambda *args, **kwargs: launched.update(kwargs) or Process())
    monkeypatch.setattr(hydration, "terminate_process_group", lambda process: launched.update(reaped=True))
    clock = iter((1.0, 1.0))
    monkeypatch.setattr(hydration.time, "monotonic", lambda: next(clock))

    assert hydration.run_gh_json(["issue", "view", "5512", "--json", "title"], deadline=1.1) is None
    assert launched["start_new_session"] is True
    assert launched["reaped"] is True


@pytest.mark.parametrize(
    "value",
    [
        {"path": Path(hydration.ROOT) / "scripts" / "lib" / "safe.py"},
        {"nested": [{"path": "scripts/lib/safe.py"}]},
    ],
)
def test_sanitizer_normalizes_repo_relative_paths(value: dict[str, object]) -> None:
    sanitized = hydration.sanitize_hydration_value(value)
    assert "scripts/lib/safe.py" in str(sanitized)


@pytest.mark.parametrize(
    "value",
    [
        {"raw_stdout": "not allowed"},
        {"credential": "ghp_" + ("a" * 26)},
        {"path": "/tmp/not-in-repository"},
    ],
)
def test_sanitizer_rejects_raw_output_secrets_and_external_paths(value: dict[str, str]) -> None:
    with pytest.raises(hydration.HydrationSanitizationError):
        hydration.sanitize_hydration_value(value)
