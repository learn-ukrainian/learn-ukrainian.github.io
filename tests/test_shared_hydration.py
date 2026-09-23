"""Contract tests for the bounded long-horizon hydration capsule."""

from __future__ import annotations

import http.server
import json
import signal
import threading
import time
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

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
    monkeypatch.setattr(hydration, "_collect_stream_evidence", lambda stream_id, deadline: _evidence())
    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    validator = Draft202012Validator(hydration.HYDRATION_CAPSULE_V1_SCHEMA, format_checker=FormatChecker())
    assert list(validator.iter_errors(capsule)) == []
    assert capsule["state"] == "ready"
    assert capsule["execution_allowed"] is True
    assert capsule["blocked"] is False


def test_deadline_is_monotonic_and_degrades_without_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter((10.0, 10.02, 10.101, 10.101))
    monkeypatch.setattr(hydration.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(hydration, "_collect_stream_evidence", lambda stream_id, deadline: _evidence())

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "degraded"
    assert capsule["degradation_reasons"] == ["deadline-exceeded"]
    assert capsule["execution_allowed"] is True
    assert capsule["blocked"] is False


def test_unavailable_critical_evidence_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(stream_id: str, *, deadline: float) -> dict[str, object]:
        raise LookupError("missing")

    monkeypatch.setattr(hydration, "_collect_stream_evidence", unavailable)
    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "blocked"
    assert capsule["execution_allowed"] is False
    assert capsule["blocked"] is True
    assert capsule["lease_state"]["status"] != "ok"


def test_unsafe_stream_evidence_resets_driver_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    unsafe_evidence = _evidence()
    unsafe_evidence["driver_identity"] = {
        "agent": "gemini",
        "harness": "agy",
        "instance_id": "ghp_" + ("a" * 26),
    }
    monkeypatch.setattr(hydration, "_collect_stream_evidence", lambda stream_id, deadline: unsafe_evidence)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    for field in ("driver_identity", "lease_state", "fencing_token", "next_drive_boundary"):
        assert capsule[field] == {"status": "unavailable", "reason": "unsafe-stream-evidence"}


def _remote_stream(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    values = {
        "SESSION_STREAM_ID": "epic:5512",
        "SESSION_STREAM_SESSION_ID": "session-fixture",
        "SESSION_STREAM_LEASE_ID": "lease-fixture",
        "SESSION_STREAM_GENERATION": "2",
        "SESSION_STREAM_FENCING_TOKEN": "7",
        "SESSION_STREAM_AGENT": "gemini",
        "SESSION_STREAM_HARNESS": "agy",
        "SESSION_STREAM_INSTANCE_ID": "agy-fixture",
        "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_TASK_ID": "launcher-fixture",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("LU_MONITOR_HOST_ID", raising=False)
    return {
        "stream_id": "epic:5512",
        "lease": {
            "stream_id": "epic:5512",
            "session_id": "session-fixture",
            "lease_id": "lease-fixture",
            "generation": 2,
            "fencing_token": 7,
            "holder": {
                "agent": "gemini",
                "harness": "agy",
                "instance_id": "agy-fixture",
                "task_id": "launcher-fixture",
                "process_id": 1234,
                "holder_kind": "process",
                "host_id": None,
            },
            "state": "active",
            "session_state": "open",
            "expires_at": "2099-01-01T00:00:00Z",
        },
        "digest": {
            "stream_id": "epic:5512",
            "limit": 1,
            "pinned": [],
            "recent": [],
            "high_water_entry_id": 0,
        },
    }


def test_remote_launcher_lease_hydrates_without_next_action_or_local_db(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _remote_stream(monkeypatch)
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["execution_allowed"] is True
    assert capsule["next_drive_boundary"]["value"]["kind"] == "queue_orientation"
    assert capsule["next_drive_boundary"]["value"]["entry_id"] == 0
    assert capsule["fencing_token"]["value"] == 7


def test_remote_next_action_becomes_exact_drive_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _remote_stream(monkeypatch)
    response["digest"]["recent"] = [
        {
            "entry_id": 12,
            "stream_id": "epic:5512",
            "session_id": "session-fixture",
            "agent": "gemini",
            "harness": "agy",
            "ts": "2026-09-23T00:00:00Z",
            "type": "next_action",
            "body": "Reconcile issue 5512.",
            "body_sha256": "0" * 64,
            "idempotency_key": "fixture-next-action",
            "refs": [],
        }
    ]
    response["digest"]["high_water_entry_id"] = 12
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["execution_allowed"] is True
    assert capsule["next_drive_boundary"]["value"] == {
        "kind": "stream_next_action",
        "entry_id": 12,
        "instruction": "Reconcile issue 5512.",
    }


@pytest.mark.parametrize(
    "digest",
    [
        None,
        [],
        {},
        {"stream_id": "epic:5513", "limit": 1, "recent": []},
        {"stream_id": "epic:5512", "limit": 1, "recent": ["x"]},
        {"stream_id": "epic:5512", "limit": 1, "recent": [{}]},
        {"stream_id": "epic:5512", "limit": float("inf"), "recent": []},
    ],
)
def test_malformed_remote_digest_blocks_without_traceback(
    monkeypatch: pytest.MonkeyPatch, digest: object
) -> None:
    response = _remote_stream(monkeypatch)
    response["digest"] = digest
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "blocked"
    assert capsule["execution_allowed"] is False
    assert capsule["lease_state"]["reason"] == "stream-evidence-unavailable"


def test_remote_expiry_overflow_blocks_without_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _remote_stream(monkeypatch)
    response["lease"]["expires_at"] = "0001-01-01T00:00:00+05:00"
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["state"] == "blocked"
    assert capsule["execution_allowed"] is False
    assert capsule["lease_state"]["reason"] == "stream-evidence-unavailable"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stream_id", "epic:5513"),
        ("session_id", "session-other"),
        ("lease_id", "lease-other"),
        ("generation", 3),
        ("fencing_token", 8),
        ("holder.agent", "codex"),
        ("holder.harness", "codex-cli"),
        ("holder.instance_id", "other-instance"),
        ("holder.process_id", 4321),
        ("holder.task_id", "other-task"),
        ("holder.host_id", "other-host"),
        ("state", "closed"),
        ("session_state", "closed"),
        ("session_state", []),
        ("session_state", {}),
        ("expires_at", "2000-01-01T00:00:00Z"),
    ],
)
def test_remote_launcher_lease_mismatch_blocks(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    response = deepcopy(_remote_stream(monkeypatch))
    target = response["lease"]
    if field.startswith("holder."):
        target = target["holder"]
        field = field.split(".", 1)[1]
    elif field == "stream_id":
        target = response
    target[field] = value
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)

    capsule = hydration.build_hydration_capsule("epic:5512", "gemini")

    assert capsule["execution_allowed"] is False
    assert capsule["lease_state"]["reason"] == "stream-evidence-unavailable"


def test_missing_launcher_lease_or_remote_timeout_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _remote_stream(monkeypatch)
    monkeypatch.delenv("SESSION_STREAM_LEASE_ID")
    monkeypatch.setattr(hydration, "_fetch_remote_stream", lambda stream_id, deadline: response)
    assert hydration.build_hydration_capsule("epic:5512", "gemini")["execution_allowed"] is False

    monkeypatch.setenv("SESSION_STREAM_LEASE_ID", "lease-fixture")

    def timed_out(stream_id: str, *, deadline: float) -> dict[str, object]:
        raise TimeoutError("timeout")

    monkeypatch.setattr(hydration, "_fetch_remote_stream", timed_out)
    assert hydration.build_hydration_capsule("epic:5512", "gemini")["execution_allowed"] is False


def test_remote_hydration_transport_is_read_only_bounded_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class Socket:
        def settimeout(self, seconds: float) -> None:
            assert 0 < seconds <= 1
            calls["timeout_set"] = True

    class Connection:
        sock = Socket()

        def __init__(self, host: str, port: int, timeout: float) -> None:
            calls["timeout"] = timeout

        def request(self, method: str, path: str, headers: dict[str, str]) -> None:
            calls["request"] = (method, path)

        def getresponse(self) -> object:
            pieces = iter((b'{"stream_id":"epic:5512"}', b""))
            return SimpleNamespace(
                status=200,
                fp=SimpleNamespace(raw=SimpleNamespace(_sock=self.sock)),
                read=lambda size: next(pieces),
                isclosed=lambda: False,
                length=None,
            )

        def close(self) -> None:
            calls["closed"] = True

    monkeypatch.setattr(hydration.http.client, "HTTPConnection", Connection)
    result = hydration._fetch_remote_stream("epic:5512", deadline=time.monotonic() + 1)

    assert result == {"stream_id": "epic:5512"}
    assert calls["request"] == ("GET", "/api/epics/v1/epic:5512?limit=1")
    assert calls["timeout_set"] is True
    assert calls["closed"] is True


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (503, b"{}"),
        (200, b"not-json"),
        (200, b"[]"),
        (200, b"{" + b"x" * (hydration._MAX_STREAM_RESPONSE_BYTES + 1)),
    ],
)
def test_remote_transport_rejects_bad_responses_and_closes(
    monkeypatch: pytest.MonkeyPatch, status: int, body: bytes
) -> None:
    calls: dict[str, bool] = {}

    class Socket:
        def settimeout(self, seconds: float) -> None:
            assert seconds > 0

    class Response:
        fp = SimpleNamespace(raw=SimpleNamespace(_sock=Socket()))

        def __init__(self) -> None:
            self.status = status
            self.offset = 0
            self.length = len(body)

        def read(self, size: int) -> bytes:
            chunk = body[self.offset : self.offset + size]
            self.offset += len(chunk)
            self.length -= len(chunk)
            return chunk

        def isclosed(self) -> bool:
            return self.length == 0

    class Connection:
        sock = None  # HTTPConnection detaches its socket on Connection: close.

        def __init__(self, host: str, port: int, timeout: float) -> None:
            pass

        def request(self, method: str, path: str, headers: dict[str, str]) -> None:
            assert method == "GET"
            self.sock = Socket()

        def getresponse(self) -> Response:
            self.sock = None
            return Response()

        def close(self) -> None:
            calls["closed"] = True

    monkeypatch.setattr(hydration.http.client, "HTTPConnection", Connection)

    with pytest.raises(LookupError):
        hydration._fetch_remote_stream("epic:5512", deadline=time.monotonic() + 1)
    assert calls["closed"] is True


@pytest.mark.parametrize("case", ["valid", "oversize", "truncated"])
def test_remote_transport_real_loopback_connection_close(
    monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    payload = (
        b"x" * (hydration._MAX_STREAM_RESPONSE_BYTES + 1)
        if case == "oversize"
        else json.dumps({"stream_id": "epic:5512"}).encode()
    )

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            assert self.path == "/api/epics/v1/epic:5512?limit=1"
            self.send_response(200)
            length = len(payload) + 10 if case == "truncated" else len(payload)
            self.send_header("Content-Length", str(length))
            self.send_header("Connection", "close")
            self.end_headers()
            with suppress(BrokenPipeError, ConnectionResetError):
                self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", f"http://127.0.0.1:{server.server_port}")
    try:
        if case != "valid":
            with pytest.raises(LookupError, match=r"too large|incomplete"):
                hydration._fetch_remote_stream("epic:5512", deadline=time.monotonic() + 1)
        else:
            assert hydration._fetch_remote_stream("epic:5512", deadline=time.monotonic() + 1) == {
                "stream_id": "epic:5512"
            }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_remote_transport_real_loopback_stalled_headers_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    received = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            received.set()
            time.sleep(0.2)
            try:
                self.send_response(200)
                self.end_headers()
            except BrokenPipeError:
                pass

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", f"http://127.0.0.1:{server.server_port}")
    try:
        with pytest.raises(LookupError) as error:
            hydration._fetch_remote_stream("epic:5512", deadline=time.monotonic() + 0.05)
        assert received.is_set()
        assert isinstance(error.value.__cause__, TimeoutError)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


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
        "./this sentence has spaces /.. and is not a file path",
        ".agent/this sentence has spaces /.. and is not a file path",
    ],
)
def test_sanitizer_preserves_sentence_like_strings_with_slashes(value: str) -> None:
    assert hydration.sanitize_hydration_value(value) == value


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
