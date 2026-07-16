#!/usr/bin/env python3
"""Claudex-only parent lifecycle supervisor with exact rollover binding."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Pin child launches to this checkout; an inherited interpreter may belong to another worktree.
REPO_PYTHON = PROJECT_ROOT / ".venv/bin/python"
if __package__:
    from scripts.lib.session_record import canonical_state_root, validate_session_id
    from scripts.orchestration import thread_handoff
else:
    sys.path.insert(0, os.fspath(PROJECT_ROOT))
    from scripts.lib.session_record import canonical_state_root, validate_session_id
    from scripts.orchestration import thread_handoff

SCHEMA_VERSION = 1
REQUEST_TTL_SECONDS = 300
POLL_SECONDS = 0.2
TERMINATE_TIMEOUT_SECONDS = 5.0
RUN_ID_RE = re.compile(r"^[0-9a-f]{32}$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
RUNTIME_KEYS = {
    "schema_version",
    "run_id",
    "state",
    "created_at",
    "updated_at",
    "supervisor_pid",
    "child_pid",
    "launch_generation",
    "command_hash",
    "profile_id",
    "lead_model_id",
    "subagent_model_id",
    "agent",
    "epic",
    "session_id",
    "session_source",
    "session_model_id",
    "handoff_agent",
    "bound_at",
    "accepted_request_id",
    "exit_code",
}
REQUEST_KEYS = {
    "schema_version",
    "request_type",
    "request_id",
    "created_at",
    "expires_at",
    "run_id",
    "launch_generation",
    "source_session_id",
    "child_pid",
    "command_hash",
    "profile_id",
    "lead_model_id",
    "subagent_model_id",
    "agent",
    "epic",
    "handoff_agent",
    "lineage_id",
    "rollover_generation",
    "rollover_id",
    "native_family_id",
    "native_operation_id",
}


class SupervisorError(ValueError):
    """Supervisor state or a rollover request is invalid."""


def _timestamp(now: datetime | None = None) -> str:
    value = now or datetime.now(UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SupervisorError(f"{field} is malformed")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SupervisorError(f"{field} is malformed") from exc
    return parsed.astimezone(UTC)


def _safe_identity(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value.strip()
    else:
        raise SupervisorError(f"{field} is malformed")
    if allow_empty and not text:
        return ""
    if not IDENTITY_RE.fullmatch(text):
        raise SupervisorError(f"{field} is malformed")
    return text


def _safe_model(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SupervisorError(f"{field} is malformed")
    text = value.strip()
    if not MODEL_RE.fullmatch(text):
        raise SupervisorError(f"{field} is malformed")
    return text


def _ensure_private_dir(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        path.chmod(0o700)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    _ensure_private_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        path.chmod(0o600)
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            tmp_path.unlink()


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    _ensure_private_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp_path, path)
        except FileExistsError as exc:
            raise SupervisorError("a rollover request is already pending for this run") from exc
        path.chmod(0o600)
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            tmp_path.unlink()


def _load_json(path: Path, *, max_bytes: int = 65_536) -> dict[str, Any]:
    try:
        if path.stat().st_size > max_bytes:
            raise SupervisorError(f"runtime JSON exceeds {max_bytes} bytes")
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SupervisorError(f"cannot read runtime JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SupervisorError("runtime JSON must be an object")
    return data


def _validate_keys(payload: dict[str, Any], allowed: set[str], kind: str) -> None:
    unknown = set(payload) - allowed
    if unknown:
        raise SupervisorError(f"{kind} contains unsupported fields")


def _parse_option(argv: list[str], name: str) -> str:
    value = ""
    for index, arg in enumerate(argv):
        if arg == name and index + 1 < len(argv):
            value = argv[index + 1]
        elif arg.startswith(f"{name}="):
            value = arg.split("=", 1)[1]
    return value


def compute_command_hash(script_path: str, argv: list[str]) -> str:
    """Hash the exact argv vector without ambiguous string joining."""
    encoded = json.dumps(
        [os.fspath(Path(script_path).resolve()), *argv],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _route_contract(argv: list[str], env: dict[str, str]) -> dict[str, str]:
    profile_id = _safe_identity(env.get("LEARN_UKRAINIAN_PROFILE_ID"), "profile_id")
    lead_model = _safe_model(env.get("LEARN_UKRAINIAN_MAIN_MODEL_ID"), "lead_model_id")
    selected_model = _safe_model(_parse_option(argv, "--model"), "selected lead model")
    subagent_model = _safe_model(env.get("CLAUDE_CODE_SUBAGENT_MODEL"), "subagent_model_id")
    transport = env.get("LEARN_UKRAINIAN_TRANSPORT")
    trusted = env.get("LEARN_UKRAINIAN_TRUSTED")
    if transport != "claudex" or trusted != "1" or selected_model != lead_model:
        raise SupervisorError("Claudex route contract is untrusted or internally inconsistent")
    return {
        "profile_id": profile_id,
        "lead_model_id": lead_model,
        "subagent_model_id": subagent_model,
        "agent": _safe_identity(_parse_option(argv, "--agent"), "agent", allow_empty=True),
        "epic": _safe_identity(_parse_option(argv, "--epic"), "epic", allow_empty=True),
    }


def _run_dir(state_root: Path, run_id: str) -> Path:
    if not RUN_ID_RE.fullmatch(run_id):
        raise SupervisorError("run_id is malformed")
    return state_root.resolve() / ".agent" / "claudex-supervisors" / run_id


def _runtime_path(state_root: Path, run_id: str) -> Path:
    return _run_dir(state_root, run_id) / "runtime.json"


def _request_path(state_root: Path, run_id: str) -> Path:
    return _run_dir(state_root, run_id) / "request.json"


def _validate_runtime(payload: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    _validate_keys(payload, RUNTIME_KEYS, "runtime metadata")
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("run_id") != run_id:
        raise SupervisorError("runtime metadata identity is malformed")
    if payload.get("state") not in {
        "launching",
        "running",
        "restarting",
        "exited",
        "launch_failed",
    }:
        raise SupervisorError("runtime metadata state is malformed")
    supervisor_pid = payload.get("supervisor_pid")
    if (
        isinstance(supervisor_pid, bool)
        or not isinstance(supervisor_pid, int)
        or supervisor_pid <= 0
    ):
        raise SupervisorError("runtime metadata supervisor_pid is malformed")
    launch_generation = payload.get("launch_generation")
    if (
        isinstance(launch_generation, bool)
        or not isinstance(launch_generation, int)
        or launch_generation < 0
    ):
        raise SupervisorError("runtime metadata launch_generation is malformed")
    child_pid = payload.get("child_pid")
    if child_pid is not None and (
        isinstance(child_pid, bool) or not isinstance(child_pid, int) or child_pid <= 0
    ):
        raise SupervisorError("runtime metadata child_pid is malformed")
    command_hash = payload.get("command_hash")
    if not isinstance(command_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", command_hash):
        raise SupervisorError("runtime metadata command_hash is malformed")
    _safe_identity(payload.get("profile_id"), "profile_id")
    _safe_model(payload.get("lead_model_id"), "lead_model_id")
    _safe_model(payload.get("subagent_model_id"), "subagent_model_id")
    _safe_identity(payload.get("agent"), "agent", allow_empty=True)
    _safe_identity(payload.get("epic"), "epic", allow_empty=True)
    session_id = payload.get("session_id")
    if session_id is not None and (
        not isinstance(session_id, str) or not validate_session_id(session_id)
    ):
        raise SupervisorError("runtime metadata session_id is malformed")
    for field in ("session_source", "handoff_agent"):
        value = payload.get(field)
        if value is not None:
            _safe_identity(value, field, allow_empty=True)
    session_model = payload.get("session_model_id")
    if session_model is not None:
        _safe_model(session_model, "session_model_id")
    for field in ("created_at", "updated_at"):
        _parse_timestamp(payload.get(field), field)
    bound_at = payload.get("bound_at")
    if bound_at is not None:
        _parse_timestamp(bound_at, "bound_at")
    accepted_request_id = payload.get("accepted_request_id")
    if accepted_request_id is not None and (
        not isinstance(accepted_request_id, str)
        or not RUN_ID_RE.fullmatch(accepted_request_id)
    ):
        raise SupervisorError("runtime metadata accepted_request_id is malformed")
    exit_code = payload.get("exit_code")
    if exit_code is not None and (
        isinstance(exit_code, bool) or not isinstance(exit_code, int)
    ):
        raise SupervisorError("runtime metadata exit_code is malformed")
    return dict(payload)


def load_runtime(state_root: Path, run_id: str) -> dict[str, Any]:
    return _validate_runtime(_load_json(_runtime_path(state_root, run_id)), run_id=run_id)


def bind_session(
    *,
    state_root: Path,
    run_id: str,
    launch_generation: int,
    session_id: str,
    source: str | None,
    model_id: str | None,
    handoff_agent: str | None,
) -> dict[str, Any]:
    """Bind official SessionStart identity to the exact active child generation."""
    if not validate_session_id(session_id):
        raise SupervisorError("session_id is malformed")
    runtime = load_runtime(state_root, run_id)
    if runtime["state"] != "running" or runtime["launch_generation"] != launch_generation:
        raise SupervisorError("SessionStart does not match the active supervisor generation")
    bound_session_id = runtime.get("session_id")
    if bound_session_id is not None and bound_session_id != session_id:
        raise SupervisorError("active supervisor generation is already bound to another session")
    runtime.update(
        {
            "session_id": session_id,
            "session_source": _safe_identity(source, "session source", allow_empty=True),
            "session_model_id": (
                _safe_model(model_id, "session model") if model_id else None
            ),
            "handoff_agent": _safe_identity(
                handoff_agent, "handoff_agent", allow_empty=True
            ),
            "bound_at": _timestamp(),
            "updated_at": _timestamp(),
        }
    )
    _write_json_atomic(_runtime_path(state_root, run_id), runtime)
    return runtime


def _load_valid_lease(
    *,
    state_root: Path,
    runtime: dict[str, Any],
    lineage_id: str,
    rollover_generation: int,
    rollover_id: str,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    handoff_agent = runtime.get("handoff_agent")
    if not isinstance(handoff_agent, str) or not handoff_agent:
        raise SupervisorError("active session has no bound handoff agent")
    lineage_id = thread_handoff.normalize_lineage_id(lineage_id)
    rollover_id = thread_handoff.normalize_rollover_id(rollover_id)
    lease_path = state_root / thread_handoff.default_state_path(handoff_agent, lineage_id)
    state = _load_json(lease_path)
    replacement, error = thread_handoff.validate_live_lease(
        state, agent=handoff_agent, state_path=lease_path
    )
    if error or replacement is None:
        raise SupervisorError(f"rollover lease is invalid: {error or 'unknown error'}")
    active = state["active"]
    if active.get("thread_id") != runtime.get("session_id"):
        raise SupervisorError("rollover lease source thread does not match the bound session")
    if replacement.get("status") != "pending_start":
        raise SupervisorError("rollover lease is not awaiting a replacement start")
    if replacement.get("generation") != rollover_generation:
        raise SupervisorError("rollover lease generation does not match the request")
    if replacement.get("rollover_id") != rollover_id:
        raise SupervisorError("rollover lease id does not match the request")
    native = replacement.get("native_lifecycle")
    if not isinstance(native, dict) or native.get("source_thread_id") != runtime.get("session_id"):
        raise SupervisorError("rollover native lifecycle does not match the bound session")
    return state, replacement, lease_path


def create_rollover_request(
    *,
    state_root: Path,
    run_id: str,
    launch_generation: int,
    session_id: str,
    lineage_id: str,
    rollover_generation: int,
    rollover_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Write one typed, lease-validated request for the active supervised child."""
    runtime = load_runtime(state_root, run_id)
    if runtime["state"] != "running":
        raise SupervisorError("supervisor run is not active")
    if runtime["launch_generation"] != launch_generation:
        raise SupervisorError("request launch generation is stale")
    if runtime.get("session_id") != session_id:
        raise SupervisorError("request source session does not match the bound session")
    if runtime.get("session_model_id") not in {None, runtime["lead_model_id"]}:
        raise SupervisorError("bound SessionStart model does not match the lead route")
    _, replacement, _ = _load_valid_lease(
        state_root=state_root,
        runtime=runtime,
        lineage_id=lineage_id,
        rollover_generation=rollover_generation,
        rollover_id=rollover_id,
    )
    native = replacement["native_lifecycle"]
    created = now or datetime.now(UTC)
    request = {
        "schema_version": SCHEMA_VERSION,
        "request_type": "claudex-rollover",
        "request_id": uuid.uuid4().hex,
        "created_at": _timestamp(created),
        "expires_at": _timestamp(created + timedelta(seconds=REQUEST_TTL_SECONDS)),
        "run_id": run_id,
        "launch_generation": launch_generation,
        "source_session_id": session_id,
        "child_pid": runtime["child_pid"],
        "command_hash": runtime["command_hash"],
        "profile_id": runtime["profile_id"],
        "lead_model_id": runtime["lead_model_id"],
        "subagent_model_id": runtime["subagent_model_id"],
        "agent": runtime["agent"],
        "epic": runtime["epic"],
        "handoff_agent": runtime["handoff_agent"],
        "lineage_id": replacement["lineage_id"],
        "rollover_generation": replacement["generation"],
        "rollover_id": replacement["rollover_id"],
        "native_family_id": native["family_id"],
        "native_operation_id": native["operation_id"],
    }
    _write_json_once(_request_path(state_root, run_id), request)
    return request


def _validate_request_shape(request: dict[str, Any]) -> None:
    _validate_keys(request, REQUEST_KEYS, "rollover request")
    if set(request) != REQUEST_KEYS:
        raise SupervisorError("rollover request is missing required fields")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise SupervisorError("rollover request schema is unsupported")
    if request.get("request_type") != "claudex-rollover":
        raise SupervisorError("rollover request type is unsupported")
    for field in ("request_id", "run_id"):
        value = request.get(field)
        if not isinstance(value, str) or not RUN_ID_RE.fullmatch(value):
            raise SupervisorError(f"rollover request {field} is malformed")
    child_pid = request.get("child_pid")
    if (
        isinstance(child_pid, bool)
        or not isinstance(child_pid, int)
        or child_pid <= 0
    ):
        raise SupervisorError("rollover request child_pid is malformed")
    for field in ("launch_generation", "rollover_generation"):
        value = request.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SupervisorError(f"rollover request {field} is malformed")
    source_session_id = request.get("source_session_id")
    if not isinstance(source_session_id, str) or not validate_session_id(
        source_session_id
    ):
        raise SupervisorError("rollover request source_session_id is malformed")
    command_hash = request.get("command_hash")
    if not isinstance(command_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", command_hash
    ):
        raise SupervisorError("rollover request command_hash is malformed")
    _safe_identity(request.get("profile_id"), "profile_id")
    _safe_model(request.get("lead_model_id"), "lead_model_id")
    _safe_model(request.get("subagent_model_id"), "subagent_model_id")
    _safe_identity(request.get("agent"), "agent", allow_empty=True)
    _safe_identity(request.get("epic"), "epic", allow_empty=True)
    _safe_identity(request.get("handoff_agent"), "handoff_agent")
    for field in ("native_family_id", "native_operation_id"):
        _safe_identity(request.get(field), field)
    lineage_id = request.get("lineage_id")
    rollover_id = request.get("rollover_id")
    if not isinstance(lineage_id, str) or not isinstance(rollover_id, str):
        raise SupervisorError("rollover request lifecycle identity is malformed")
    try:
        normalized_lineage = thread_handoff.normalize_lineage_id(lineage_id)
        normalized_rollover = thread_handoff.normalize_rollover_id(rollover_id)
    except ValueError as exc:
        raise SupervisorError("rollover request lifecycle identity is malformed") from exc
    if normalized_lineage != lineage_id or normalized_rollover != rollover_id:
        raise SupervisorError("rollover request lifecycle identity is malformed")
    _parse_timestamp(request.get("created_at"), "created_at")
    _parse_timestamp(request.get("expires_at"), "expires_at")


def _validate_claimed_request(
    *,
    request: dict[str, Any],
    state_root: Path,
    runtime: dict[str, Any],
    now: datetime | None = None,
) -> None:
    _validate_request_shape(request)
    current = now or datetime.now(UTC)
    created_at = _parse_timestamp(request["created_at"], "created_at")
    expires_at = _parse_timestamp(request["expires_at"], "expires_at")
    if created_at > current + timedelta(seconds=30) or current > expires_at:
        raise SupervisorError("rollover request is stale")
    if expires_at - created_at > timedelta(seconds=REQUEST_TTL_SECONDS):
        raise SupervisorError("rollover request lifetime is invalid")
    comparisons = {
        "run_id": runtime["run_id"],
        "launch_generation": runtime["launch_generation"],
        "source_session_id": runtime.get("session_id"),
        "child_pid": runtime["child_pid"],
        "command_hash": runtime["command_hash"],
        "profile_id": runtime["profile_id"],
        "lead_model_id": runtime["lead_model_id"],
        "subagent_model_id": runtime["subagent_model_id"],
        "agent": runtime["agent"],
        "epic": runtime["epic"],
        "handoff_agent": runtime.get("handoff_agent"),
    }
    for field, expected in comparisons.items():
        if request.get(field) != expected:
            raise SupervisorError(f"rollover request does not match active {field}")
    _, replacement, _ = _load_valid_lease(
        state_root=state_root,
        runtime=runtime,
        lineage_id=request["lineage_id"],
        rollover_generation=request["rollover_generation"],
        rollover_id=request["rollover_id"],
    )
    native = replacement["native_lifecycle"]
    if request["native_family_id"] != native["family_id"]:
        raise SupervisorError("rollover request native family does not match the lease")
    if request["native_operation_id"] != native["operation_id"]:
        raise SupervisorError("rollover request native operation does not match the lease")


def _launch_child_gate(ready_file: Path, command: list[str]) -> int:
    deadline = time.monotonic() + 15.0
    while not ready_file.exists():
        if time.monotonic() >= deadline:
            print("[supervisor-child] launch gate timed out", file=sys.stderr)
            return 1
        time.sleep(0.01)
    with contextlib.suppress(OSError):
        ready_file.unlink()
    os.execvpe(command[0], command, os.environ)
    return 1


class ClaudexSupervisor:
    """Own one exact child process and relaunch it only for a validated request."""

    def __init__(
        self,
        script_path: str,
        forward_argv: list[str],
        *,
        state_root: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.script_path = os.fspath(Path(script_path).resolve())
        self.forward_argv = list(forward_argv)
        self.base_env = dict(env or os.environ)
        self.state_root = (state_root or canonical_state_root(PROJECT_ROOT)).resolve()
        self.contract = _route_contract(self.forward_argv, self.base_env)
        self.command_hash = compute_command_hash(self.script_path, self.forward_argv)
        self.run_id = uuid.uuid4().hex
        self.run_dir = _run_dir(self.state_root, self.run_id)
        self.runtime_path = _runtime_path(self.state_root, self.run_id)
        self.request_path = _request_path(self.state_root, self.run_id)
        self.child: subprocess.Popen[bytes] | None = None
        self.launch_generation = 0
        self.processed_request_ids: set[str] = set()
        self.created_at = _timestamp()
        _ensure_private_dir(self.run_dir)

    def _runtime_payload(self, state: str, **updates: Any) -> dict[str, Any]:
        current: dict[str, Any] = {}
        if self.runtime_path.exists():
            current = load_runtime(self.state_root, self.run_id)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "state": state,
            "created_at": current.get("created_at", self.created_at),
            "updated_at": _timestamp(),
            "supervisor_pid": os.getpid(),
            "child_pid": self.child.pid if self.child is not None else None,
            "launch_generation": self.launch_generation,
            "command_hash": self.command_hash,
            **self.contract,
            **{
                key: current[key]
                for key in (
                    "session_id",
                    "session_source",
                    "session_model_id",
                    "handoff_agent",
                    "bound_at",
                    "accepted_request_id",
                    "exit_code",
                )
                if key in current
            },
            **updates,
        }
        _validate_runtime(payload, run_id=self.run_id)
        return payload

    def _write_runtime(self, state: str, **updates: Any) -> dict[str, Any]:
        payload = self._runtime_payload(state, **updates)
        _write_json_atomic(self.runtime_path, payload)
        return payload

    def _launch(self) -> None:
        ready_file = self.run_dir / f"launch-{self.launch_generation}.ready"
        with contextlib.suppress(OSError):
            ready_file.unlink()
        launch_env = self.base_env.copy()
        launch_env.update(
            {
                "LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH": "1",
                "LEARN_UKRAINIAN_CLAUDEX_RUN_ID": self.run_id,
                "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION": str(
                    self.launch_generation
                ),
            }
        )
        command = [self.script_path, *self.forward_argv]
        gate_command = [
            os.fspath(REPO_PYTHON),
            os.fspath(Path(__file__).resolve()),
            "_launch-child",
            os.fspath(ready_file),
            *command,
        ]
        self._write_runtime("launching")
        try:
            self.child = subprocess.Popen(gate_command, env=launch_env)
            self._write_runtime(
                "running",
                session_id=None,
                session_source=None,
                session_model_id=None,
                handoff_agent=None,
                bound_at=None,
                accepted_request_id=None,
                exit_code=None,
            )
            ready_file.touch(mode=0o600)
        except OSError:
            if self.child is not None and self.child.poll() is None:
                self.child.terminate()
            self._write_runtime("launch_failed")
            raise
        print(
            f"[supervisor] child launched run={self.run_id[:8]} "
            f"generation={self.launch_generation} profile={self.contract['profile_id']}",
            file=sys.stderr,
        )

    def _claim_request(self) -> Path | None:
        if not self.request_path.exists():
            return None
        processing_dir = self.run_dir / "processing"
        _ensure_private_dir(processing_dir)
        claim = processing_dir / f"{uuid.uuid4().hex}.json"
        try:
            os.replace(self.request_path, claim)
        except FileNotFoundError:
            return None
        claim.chmod(0o600)
        return claim

    def _reject_claim(self, claim: Path, reason: str) -> None:
        with contextlib.suppress(OSError):
            claim.unlink()
        rejected_dir = self.run_dir / "rejected"
        rejection_id = uuid.uuid4().hex
        _write_json_atomic(
            rejected_dir / f"{rejection_id}.json",
            {
                "schema_version": SCHEMA_VERSION,
                "rejection_id": rejection_id,
                "rejected_at": _timestamp(),
                "reason": reason,
            },
        )
        print(f"[supervisor] rejected rollover request: {reason}", file=sys.stderr)

    def _consume_claim(self, claim: Path, request_id: str) -> None:
        consumed_dir = self.run_dir / "consumed"
        _ensure_private_dir(consumed_dir)
        target = consumed_dir / f"{request_id}.json"
        os.replace(claim, target)
        target.chmod(0o600)
        self.processed_request_ids.add(request_id)

    def _validated_claim(self, claim: Path) -> tuple[dict[str, Any] | None, str | None]:
        try:
            request = _load_json(claim)
            request_id = request.get("request_id")
            if isinstance(request_id, str) and request_id in self.processed_request_ids:
                raise SupervisorError("rollover request was already consumed")
            runtime = load_runtime(self.state_root, self.run_id)
            if runtime["state"] != "running":
                raise SupervisorError("supervisor child is not in a running state")
            if self.child is None or runtime["child_pid"] != self.child.pid:
                raise SupervisorError("runtime child identity does not match the owned process")
            _validate_claimed_request(
                request=request,
                state_root=self.state_root,
                runtime=runtime,
            )
            return request, None
        except (FileNotFoundError, SupervisorError, ValueError) as exc:
            return None, str(exc)

    def _terminate_owned_child(self) -> None:
        if self.child is None or self.child.poll() is not None:
            return
        self.child.terminate()
        try:
            self.child.wait(timeout=TERMINATE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait()

    def _check_request(self) -> tuple[dict[str, Any], Path] | None:
        claim = self._claim_request()
        if claim is None:
            return None
        request, error = self._validated_claim(claim)
        if request is None:
            self._reject_claim(claim, error or "rollover request is invalid")
            return None
        return request, claim

    def run(self) -> int:
        while True:
            try:
                self._launch()
            except OSError as exc:
                print(f"[supervisor] child launch failed: {type(exc).__name__}", file=sys.stderr)
                return 1
            assert self.child is not None
            accepted: tuple[dict[str, Any], Path] | None = None
            try:
                while self.child.poll() is None:
                    accepted = self._check_request()
                    if accepted is not None:
                        break
                    time.sleep(POLL_SECONDS)
            except KeyboardInterrupt:
                self._terminate_owned_child()
                self._write_runtime("exited", exit_code=130)
                return 130

            if accepted is None:
                accepted = self._check_request()
            if accepted is None:
                exit_code = self.child.wait()
                self._write_runtime("exited", exit_code=exit_code)
                return exit_code

            request, claim = accepted
            request_id = request["request_id"]
            self._write_runtime("restarting", accepted_request_id=request_id)
            self._terminate_owned_child()
            self._consume_claim(claim, request_id)
            self.launch_generation += 1
            print(
                f"[supervisor] accepted rollover request {request_id[:8]}; "
                f"relaunching generation={self.launch_generation}",
                file=sys.stderr,
            )


def _state_root_from_args(value: Path | None) -> Path:
    if value is not None:
        return value.resolve()
    test_override = os.environ.get("CLAUDEX_SUPERVISOR_TEST_STATE_ROOT")
    if test_override:
        return Path(test_override).resolve()
    return canonical_state_root(PROJECT_ROOT)


def _env_int(name: str) -> int | None:
    value = os.environ.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise SupervisorError(f"{name} must be an integer") from exc


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "_launch-child":
        if len(sys.argv) < 4:
            return 2
        return _launch_child_gate(Path(sys.argv[2]), sys.argv[3:])

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    bind_parser = subparsers.add_parser("bind-session")
    bind_parser.add_argument("--state-root", type=Path)
    bind_parser.add_argument(
        "--run-id", default=os.environ.get("LEARN_UKRAINIAN_CLAUDEX_RUN_ID")
    )
    bind_parser.add_argument(
        "--launch-generation",
        type=int,
        default=_env_int("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"),
    )
    bind_parser.add_argument("--session-id", required=True)
    bind_parser.add_argument("--source")
    bind_parser.add_argument("--model")
    bind_parser.add_argument("--handoff-agent")

    request_parser = subparsers.add_parser("request-rollover")
    request_parser.add_argument("--state-root", type=Path)
    request_parser.add_argument(
        "--run-id", default=os.environ.get("LEARN_UKRAINIAN_CLAUDEX_RUN_ID")
    )
    request_parser.add_argument(
        "--launch-generation",
        type=int,
        default=_env_int("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"),
    )
    request_parser.add_argument(
        "--session-id", default=os.environ.get("LEARN_UKRAINIAN_SESSION_ID")
    )
    request_parser.add_argument("--lineage-id", required=True)
    request_parser.add_argument("--rollover-generation", required=True, type=int)
    request_parser.add_argument("--rollover-id", required=True)

    if len(sys.argv) >= 2 and sys.argv[1] in {"bind-session", "request-rollover"}:
        args = parser.parse_args()
        try:
            state_root = _state_root_from_args(args.state_root)
            if not args.run_id or args.launch_generation is None:
                raise SupervisorError("supervisor run identity is unavailable")
            if args.command == "bind-session":
                runtime = bind_session(
                    state_root=state_root,
                    run_id=args.run_id,
                    launch_generation=args.launch_generation,
                    session_id=args.session_id,
                    source=args.source,
                    model_id=args.model,
                    handoff_agent=args.handoff_agent,
                )
                print(
                    json.dumps(
                        {
                            "run_id": runtime["run_id"],
                            "launch_generation": runtime["launch_generation"],
                            "session_id": runtime["session_id"],
                        },
                        sort_keys=True,
                    )
                )
                return 0
            if not args.session_id:
                raise SupervisorError("bound session identity is unavailable")
            request = create_rollover_request(
                state_root=state_root,
                run_id=args.run_id,
                launch_generation=args.launch_generation,
                session_id=args.session_id,
                lineage_id=args.lineage_id,
                rollover_generation=args.rollover_generation,
                rollover_id=args.rollover_id,
            )
            print(
                json.dumps(
                    {
                        "request_id": request["request_id"],
                        "run_id": request["run_id"],
                        "rollover_id": request["rollover_id"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        except (FileNotFoundError, OSError, SupervisorError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        return 2
    state_root = _state_root_from_args(None)
    try:
        supervisor = ClaudexSupervisor(
            sys.argv[1], sys.argv[2:], state_root=state_root
        )
        return supervisor.run()
    except SupervisorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
