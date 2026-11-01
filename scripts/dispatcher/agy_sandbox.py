"""OS-enforced read-only boundary for dispatched AGY runs (C-3027).

AGY has no per-run write lock of its own: ``--sandbox`` restricts only its terminal, and where that
sandbox is unavailable AGY continues in its default mode and edits. So a read-only AGY dispatch never
launches AGY directly. ``providers/agy.py`` returns this module's launcher, which:

* stages a private scratch with two parts. The writable runtime holds AGY's HOME (a regular-file copy
  of the AGY OAuth token, a Sources-only MCP config, AGY state and caches), TMPDIR and the AGY log.
  The read-only boundary directory holds the projected canary, egress forwarder and Sources stdio
  client, the namespace's passwd and group files, the canary plan and both sockets;
* serves Sources through a parent-owned relay that forwards only the tools the server annotates
  read-only (``sources_read_only``) and counts completed calls by matching call and result ids;
* lets AGY reach public HTTPS through the CONNECT-only egress proxy of formal review attempts
  (host and loopback addresses refused);
* runs AGY under bubblewrap (``review.isolation``). The root is empty except for read-only binds of
  the system runtime, the AGY binary, the task worktree, its Git metadata and the selected primary databases and their existing sidecars. PID, IPC, UTS and network namespaces and procfs are private, every capability is
  dropped and the root is remounted read-only, so the runtime (which holds TMPDIR) is the only
  writable path;
* copies each explicit input's hashed bytes into the private scratch and bind-mounts that
  copy read-only at ``/agy-inputs/<n>``. The host path is not mounted. A file that is missing or
  whose digest changed is refused before AGY starts;
* runs the canary as the sandbox's first process and starts AGY only after the launcher has checked
  every probe outcome: EROFS on the worktree, Git metadata and database targets; host credentials,
  control services and sockets unreachable; the scratch positive control succeeded;
* compares the worktree head and status before and after the run.

The receipt it writes beside the task record (outside the sandbox) is the run's only source of
sandbox evidence and Sources call count; ``verify`` checks it for the worker. Before the scratch
is removed, each saved Sources tool body is copied out with the adapter's existing inliner so the
worker can put that body, or a missing-body reason, on the retained stream. Any setup or canary
failure refuses the run, which never falls back to an unsandboxed AGY. A read-only bind is a live
view of host files, not a snapshot: input drift is detected by the before/after comparison, not
prevented.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import json
import os
import platform
import re
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.repo_root import main_checkout_root, project_interpreter
from scripts.common.scratch import ensure_scratch_root

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 1
REFUSED = 125
RECEIPT_SUFFIX = ".sandbox.json"
# Run by path under -I so neither the worktree (the launch cwd) nor PYTHONPATH supplies this code.
_BOOTSTRAP = (
    "import sys; sys.path.insert(0, sys.argv[1]); "
    "from scripts.dispatcher.agy_sandbox import main; raise SystemExit(main(sys.argv[2:]))"
)
_PROJECTED = {
    "canary.py": ROOT / "scripts" / "dispatcher" / "agy_canary.py",
    "forwarder.py": ROOT / "scripts" / "agent_runtime" / "attempt_forwarder.py",
    "stdio.py": ROOT / "scripts" / "agent_runtime" / "attempt_proxy.py",
}
_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_AGY_AUTH = ("AGY_API_KEY", "AGY_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")
# Host paths that hold credentials or project control state; each one present must be absent inside.
_HOST_SECRETS = (
    ".ssh", ".gnupg", ".netrc", ".git-credentials", ".gitconfig", ".config/gh", ".config/git",
    ".config/learn-ukrainian", ".codex", ".claude", ".claude-b", ".claude.json", ".gemini", ".cursor",
    ".docker", ".kube", ".aws", ".local/share/keyrings",
)
# The Monitor API and the Sources HTTP service listen on the host's loopback.
_CONTROL_PORTS = (8765, 8766)
_CONTROL_SOCKETS = ("/var/run/docker.sock", "/run/docker.sock", "/run/podman/podman.sock", "/run/dbus/system_bus_socket")
_SOURCES_METHODS = frozenset(
    {"initialize", "notifications/initialized", "notifications/cancelled", "ping", "tools/list", "tools/call"}
)
_MAX_LINE = 8 << 20
_CANARY_TIMEOUT = 60
_GIT_TIMEOUT = 120
# Explicit inputs stay outside the worktree. Each one is one read-only file bind, not a directory.
INPUT_MOUNT = "/agy-inputs"
MAX_INPUTS = 8
MAX_INPUT_BYTES = 8 << 20


class Refused(RuntimeError):
    """The boundary cannot be proven; AGY does not start."""


def unavailable() -> str | None:
    """Why this host cannot start the boundary, or None. Admission checks this; the launch proves it."""
    if platform.system() != "Linux":
        return "its bubblewrap read-only boundary runs on Linux only"
    from scripts.review.isolation import ReviewIsolationError, _resolve_fixed_system_executable

    try:
        _resolve_fixed_system_executable("bwrap", reject_roots=())
    except ReviewIsolationError:
        return "bubblewrap (bwrap) is not installed, so its read-only boundary cannot start"
    return None


def scratch(task_id: str) -> Path:
    """The task's private scratch; the launcher creates it and the worker removes whatever remains."""
    if not _TASK_ID.fullmatch(task_id):
        raise ValueError("agy read-only: the task id is unsafe as a scratch name")
    return ensure_scratch_root() / f"agy-read-only-{task_id}"


def log_file(task_id: str) -> Path:
    return scratch(task_id) / "runtime" / "logs" / "agy.log"


def receipt_file(final_file: Path) -> Path:
    return final_file.with_suffix(RECEIPT_SUFFIX)


def tool_results_file(final_file: Path) -> Path:
    """Private export of saved tool bodies, beside the task result and outside the scratch."""
    return final_file.with_suffix(".tool-results.json")


def _tool_results_from_receipt(receipt: Path) -> Path:
    suffix = ".sandbox.json"
    if not receipt.name.endswith(suffix):
        raise ValueError("agy tool results: receipt name is not the boundary receipt")
    return receipt.with_name(receipt.name[: -len(suffix)] + ".tool-results.json")


def launcher(spec, agy_argv: list[str]) -> list[str]:
    """The argv of every read-only AGY launch: this boundary, which runs ``agy_argv`` inside it."""
    argv = [
        str(project_interpreter()), "-I", "-c", _BOOTSTRAP, str(ROOT),
        "--task-id", spec.task_id, "--worktree", str(spec.worktree), "--scratch", str(scratch(spec.task_id)),
        "--receipt", str(receipt_file(spec.final_file)),
    ]
    for item in _inputs_from_spec(spec):
        argv += ["--input", item["path"], "--input-sha256", item["sha256"]]
    argv += ["--", *agy_argv]
    return argv


def bind_inputs(paths: list[str], *, repo_root: Path, keep_bytes: bool = False) -> list[dict]:
    """Check explicit inputs and return the task-record fields. Raises ``ValueError`` before spawn.

    Nothing is skipped: the first path that cannot be mounted refuses the whole set. ``keep_bytes``
    retains the hashed payload for the private scratch copy. The task record never stores it.
    """
    if len(paths) > MAX_INPUTS:
        raise ValueError(f"agy_input_refused: more than {MAX_INPUTS} inputs")
    root, home = repo_root.resolve(), Path.home().resolve()
    items = [_bind_one(index, raw, root, home) for index, raw in enumerate(paths)]
    if not keep_bytes:
        for item in items:
            item.pop("data", None)
    return items


def confirm_inputs(items: list[dict], *, repo_root: Path) -> list[dict]:
    """Re-read every recorded input. A missing file or a new digest refuses the launch."""
    if not items:
        return []
    try:
        fresh = bind_inputs([item["path"] for item in items], repo_root=repo_root, keep_bytes=True)
    except ValueError as exc:
        raise Refused(str(exc)) from exc
    for old, new in zip(items, fresh, strict=True):
        if (old.get("sha256"), old.get("mount")) != (new["sha256"], new["mount"]):
            raise Refused("agy_input_refused: digest changed before start")
    return fresh


def _inputs_from_spec(spec) -> list[dict]:
    raw = getattr(spec, "options", {}).get("inputs")
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except ValueError as exc:
        raise ValueError("agy_input_refused: input record invalid") from exc
    if not isinstance(items, list) or not all(
        isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str)
        for item in items
    ):
        raise ValueError("agy_input_refused: input record invalid")
    return items


def _under_credential(path: Path, home: Path) -> bool:
    for relative in _HOST_SECRETS:
        secret = home / relative
        candidates = [secret]
        with contextlib.suppress(OSError):
            candidates.append(secret.resolve(strict=True))
        if any(path == item or path.is_relative_to(item) for item in candidates):
            return True
    return False


def _bind_one(index: int, raw: str, root: Path, home: Path) -> dict:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = Path(os.path.abspath(candidate))
    if candidate.is_symlink():
        raise ValueError("agy_input_refused: symlink")
    try:
        descriptor = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("agy_input_refused: symlink") from exc
        raise ValueError("agy_input_refused: not a readable regular file") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("agy_input_refused: not a regular file")
        if info.st_nlink > 1:
            raise ValueError("agy_input_refused: hard link")
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ValueError("agy_input_refused: not a readable regular file") from exc
        if resolved != candidate:
            raise ValueError("agy_input_refused: symlink")
        if info.st_size > MAX_INPUT_BYTES:
            raise ValueError(f"agy_input_refused: larger than {MAX_INPUT_BYTES} bytes")
        if _under_credential(resolved, home):
            raise ValueError("agy_input_refused: path is under a credential directory")
        if resolved == root or resolved.is_relative_to(root):
            raise ValueError("agy_input_refused: path is inside the primary checkout")
        # The policy checks name `resolved`. The bytes come from the descriptor. Refuse when
        # those are not the same file, which a parent-directory swap between the two can cause.
        try:
            checked = os.stat(resolved)
        except OSError as exc:
            raise ValueError("agy_input_refused: not a readable regular file") from exc
        if (checked.st_dev, checked.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("agy_input_refused: path changed before read")
        # `stat` looks the caller's path up again, so a later parent swap can make it
        # name the descriptor's file while `resolved` still names a different path.
        # The descriptor's own kernel path is the file the bytes come from.
        try:
            linked = os.readlink(f"/proc/self/fd/{descriptor}")
        except OSError as exc:
            raise ValueError("agy_input_refused: not a readable regular file") from exc
        fd_path = Path(linked)
        if not fd_path.is_absolute() or linked.endswith(" (deleted)"):
            raise ValueError("agy_input_refused: path changed before read")
        if _under_credential(fd_path, home):
            raise ValueError("agy_input_refused: path is under a credential directory")
        if fd_path == root or fd_path.is_relative_to(root):
            raise ValueError("agy_input_refused: path is inside the primary checkout")
        if fd_path != resolved:
            raise ValueError("agy_input_refused: path changed before read")
        data = _read_exact(descriptor, info.st_size)
        if os.fstat(descriptor).st_nlink > 1:
            raise ValueError("agy_input_refused: hard link")
    finally:
        os.close(descriptor)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("agy_input_refused: not a readable regular file")
    return {
        "bytes": len(data), "data": data, "index": index, "mount": f"{INPUT_MOUNT}/{index}",
        "path": str(resolved), "sha256": hashlib.sha256(data).hexdigest(),
    }


def _read_exact(descriptor: int, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        block = os.read(descriptor, remaining)
        if not block:
            break
        chunks.append(block)
        remaining -= len(block)
    data = b"".join(chunks)
    if len(data) != size or os.read(descriptor, 1):
        raise ValueError("agy_input_refused: not a readable regular file")
    return data


def _input_proof(items: list[dict]) -> list[dict]:
    return [{"bytes": item["bytes"], "mount": item["mount"], "sha256": item["sha256"]} for item in items]


def _input_mismatch(record: dict, receipt: dict) -> str | None:
    options = record.get("options")
    raw = options.get("inputs") if isinstance(options, dict) else None
    if not raw:
        return None
    try:
        expected = json.loads(raw)
    except ValueError:
        return "agy_read_only_boundary: input digest mismatch"
    if not isinstance(expected, list):
        return "agy_read_only_boundary: input digest mismatch"
    if receipt.get("inputs") != _input_proof(expected):
        return "agy_read_only_boundary: input digest mismatch"
    return None


def discard(task_id: str) -> str | None:
    """Remove a scratch the launcher could not (it was killed), with its credential copy.

    Never raises, so cleanup cannot stop the worker publishing the task; returns the residue error.
    """
    try:
        _remove(scratch(task_id))
    except (OSError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"[:300]
    return None


def apply_tool_results(stdout_path: Path, final_file: Path, task_id: str) -> tuple[int, int]:
    """Write exported Sources bodies onto the retained stream, then drop the export.

    If the launcher could not export before deleting the scratch, read the files
    that are still there. The read is the adapter's inliner either way.
    """
    from scripts.agent_runtime.adapters.agy import export_saved_step_outputs, merge_saved_step_outputs

    export = tool_results_file(final_file)
    saved: list[dict] = []
    if export.is_file():
        try:
            payload = json.loads(export.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            payload = None
        if (
            isinstance(payload, dict)
            and payload.get("schema") == "agy-tool-results.v1"
            and isinstance(payload.get("calls"), list)
        ):
            saved = payload["calls"]
    if not saved:
        app = scratch(task_id) / "runtime" / "home" / ".gemini" / "antigravity-cli"
        if app.is_dir():
            saved = export_saved_step_outputs(app)
    if not stdout_path.is_file():
        return 0, 0
    text = stdout_path.read_text(encoding="utf-8", errors="replace")
    merged, retained, missing = merge_saved_step_outputs(text, saved)
    if merged != text:
        temporary = stdout_path.with_name(f".{stdout_path.name}.{uuid.uuid4().hex}")
        temporary.write_text(merged, encoding="utf-8")
        os.replace(temporary, stdout_path)
    if export.is_file():
        export.unlink()
    return retained, missing


def verify(final_file: Path, task_id: str, record: dict) -> tuple[dict, int | None, str | None]:
    """The receipt summary, the Sources call count and a refusal for the worker.

    Fails closed: a missing, foreign or malformed receipt, a refused boundary, a failed canary or any
    change to the reviewed head or worktree status refuses the run, and only a verified receipt
    supplies a count.
    """
    try:
        receipt = json.loads(receipt_file(final_file).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, None, "agy_read_only_boundary: receipt missing or unreadable"
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA or receipt.get("task_id") != task_id:
        return {}, None, "agy_read_only_boundary: receipt invalid"
    summary = {key: receipt.get(key) for key in (
        "status", "reason", "wrapper_sha256", "argv_sha256", "bwrap", "input", "canary", "sources", "egress",
    )}
    if receipt.get("status") != "ran":
        return summary, None, f"agy_read_only_boundary: refused: {receipt.get('reason') or 'unknown'}"
    canary = receipt.get("canary")
    if not isinstance(canary, dict) or canary.get("passed") is not True:
        return summary, None, "agy_read_only_boundary: canary did not pass"
    expected = record.get("worktree_base_sha")
    pinned = record.get("pinned_head")
    states = receipt.get("input") if isinstance(receipt.get("input"), dict) else {}
    start, end = states.get("start"), states.get("end")
    if not (isinstance(start, dict) and isinstance(end, dict) and start.get("clean") is True and end.get("clean") is True
            and start.get("head") == end.get("head") == expected and pinned in (None, expected)):
        return summary, None, "review_input_drift: the reviewed worktree changed or left the dispatched head"
    sources = receipt.get("sources") if isinstance(receipt.get("sources"), dict) else {}
    count = sources.get("completed")
    if mismatch := _input_mismatch(record, receipt):
        return summary, None, mismatch
    return summary, count if type(count) is int and count >= 0 else None, None


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _open_directory(name: str, parent: int | None = None) -> int:
    """Open a directory for listing after restoring its owner's access, never through a link.

    The sandbox may have left any mode (even 000) on a scratch directory. An O_PATH descriptor needs
    no permission on the directory itself, and with O_NOFOLLOW and O_DIRECTORY it can only name a
    real directory, so its mode is restored through that descriptor before it is reopened.
    """
    anchor = os.open(name, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
    try:
        own = f"/proc/self/fd/{anchor}"
        os.chmod(own, 0o700)
        return os.open(own, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    finally:
        os.close(anchor)


def _open_below(root: int, parts: tuple[str, ...]) -> int:
    descriptor = os.dup(root)
    for part in parts:
        child = _open_directory(part, descriptor)
        os.close(descriptor)
        descriptor = child
    return descriptor


def _remove(path: Path) -> None:
    """Delete a tree the sandbox could write, never following a link in it.

    Only directories are made accessible (``_open_directory``), because unlinking needs only the
    parent's permission; a link is unlinked, never followed. The walk is iterative, so no nesting
    depth stops it.
    """
    try:
        if not stat.S_ISDIR(os.lstat(path).st_mode):
            os.unlink(path)
            return
    except FileNotFoundError:
        return
    root = _open_directory(str(path))
    try:
        stack: list[tuple[str, ...]] = [()]
        while stack:
            parts = stack[-1]
            descriptor = _open_below(root, parts)
            try:
                children = []
                for entry in os.scandir(descriptor):
                    if entry.is_dir(follow_symlinks=False):
                        children.append((*parts, entry.name))
                    else:
                        os.unlink(entry.name, dir_fd=descriptor)
            finally:
                os.close(descriptor)
            if children:
                stack.extend(children)  # emptied first; this directory is revisited afterwards
                continue
            stack.pop()
            if parts:
                parent = _open_below(root, parts[:-1])
                try:
                    os.rmdir(parts[-1], dir_fd=parent)
                finally:
                    os.close(parent)
    finally:
        os.close(root)
    os.rmdir(path)


def _write_private(path: Path, data: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, mode)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _write_receipt(path: Path, receipt: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
    _write_private(temporary, json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8"))
    os.replace(temporary, path)


def _git(worktree: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(worktree), *args], capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}, stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        raise Refused(f"git {args[0]} failed in the worktree")
    return result.stdout


def _input_state(worktree: Path) -> dict:
    """The reviewed head and whether the worktree matches it (no staged, unstaged or untracked change)."""
    try:
        head = _git(worktree, "rev-parse", "--verify", "HEAD^{commit}").strip()
        status = _git(worktree, "status", "--porcelain=v1", "-z", "--ignore-submodules=none")
    except (Refused, OSError, subprocess.SubprocessError):
        return {"head": None, "clean": False}
    return {"head": head, "clean": status == ""}


class SourcesRelay:
    """Parent-owned Sources MCP for one sandbox: read-only tools only, completed calls counted.

    Each connection gets its own stdio server from this checkout (never the reviewed worktree).
    Client messages are re-serialized after the check, so the server receives exactly what was
    checked; batches, unknown methods and non-read-only tools are refused. Every forwarded request
    holds its id until answered, so no other request can share it, and a response with an id
    nobody holds is dropped. A call counts once, when the response to its own id is a tool result
    with content and no error.
    """

    def __init__(self, endpoint: Path, readers: frozenset[str], env: dict[str, str]):
        from scripts.agent_runtime.sources_read_only import SERVER_PATH

        self.server = [str(project_interpreter()), str(SERVER_PATH)]
        self.readers, self.env = readers, env
        self.completed = self.failed = 0
        self.tools: dict[str, int] = {}
        self.refused: dict[str, int] = {}  # by method, or by tool for a refused call
        self.lock = threading.Lock()
        self.stopped = False
        self.processes: list[subprocess.Popen] = []
        self.connections: list[socket.socket] = []
        self.listener = socket.socket(socket.AF_UNIX)
        directory = os.open(endpoint.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:  # the descriptor path avoids the sockaddr_un length limit
            self.listener.bind(f"/proc/self/fd/{directory}/{endpoint.name}")
        finally:
            os.close(directory)
        self.listener.listen()
        self.listener.settimeout(0.2)
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

    def evidence(self) -> dict:
        with self.lock:
            return {"completed": self.completed, "failed": self.failed, "tools": dict(sorted(self.tools.items())),
                    "refused": dict(sorted(self.refused.items()))}

    def _accept(self) -> None:
        while not self.stopped:
            try:
                connection, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with self.lock:
                self.connections.append(connection)
            threading.Thread(target=self._serve, args=(connection,), daemon=True).start()

    def _serve(self, connection: socket.socket) -> None:
        with self.lock:
            if self.stopped:
                connection.close()
                return
            # Same process group as the launcher, so a killed task takes its servers with it.
            process = subprocess.Popen(self.server, cwd=ROOT, env=self.env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.processes.append(process)
        pending: dict[str, tuple[str, str | None]] = {}
        pending_lock, send_lock = threading.Lock(), threading.Lock()

        def reply(message: dict) -> None:
            with send_lock:
                connection.sendall(json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")

        def upstream() -> None:
            try:
                reader = connection.makefile("rb")
                while line := reader.readline(_MAX_LINE + 1):
                    if len(line) > _MAX_LINE:
                        break
                    if not line.strip():
                        continue
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        break  # batches and non-objects end the connection
                    if self._admit(message, pending, pending_lock, reply):
                        process.stdin.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")
                        process.stdin.flush()
            except (OSError, ValueError):
                pass
            finally:
                with contextlib.suppress(OSError, ValueError):
                    process.stdin.close()

        threading.Thread(target=upstream, daemon=True).start()
        try:
            while line := process.stdout.readline():
                try:
                    message = json.loads(line)
                except ValueError:
                    continue
                if isinstance(message, dict) and (message := self._settle(message, pending, pending_lock)) is not None:
                    reply(message)
        except OSError:
            pass
        finally:
            with contextlib.suppress(OSError):
                connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            with contextlib.suppress(OSError):
                process.kill()
            process.wait()

    def _admit(self, message: dict, pending: dict, pending_lock: threading.Lock, reply) -> bool:
        method = message.get("method")
        if method is None:
            return False  # the server sends no requests, so the client has nothing to answer
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        name = params.get("name") if method == "tools/call" else None
        request_id = message.get("id")
        allowed = method in _SOURCES_METHODS and (method != "tools/call" or name in self.readers)
        if allowed and "id" in message:
            key = json.dumps(request_id)
            with pending_lock:
                allowed = type(request_id) in (int, str) and key not in pending
                if allowed:
                    pending[key] = (method, name)
        elif allowed and method in ("tools/call", "tools/list"):
            allowed = False  # a call without an id could never be matched to its result
        if not allowed:
            label = f"tools/call:{name}" if method == "tools/call" else str(method)[:64]
            with self.lock:
                self.refused[label] = self.refused.get(label, 0) + 1
            if "id" in message:
                reply({"jsonrpc": "2.0", "id": request_id,
                       "error": {"code": -32601, "message": "refused by the read-only Sources boundary"}})
        return allowed

    def _settle(self, message: dict, pending: dict, pending_lock: threading.Lock) -> dict | None:
        if "method" in message:
            return None if "id" in message else message  # notifications pass; server requests do not
        with pending_lock:
            entry = pending.pop(json.dumps(message.get("id")), None)
        if entry is None:
            return None  # no forwarded request holds this id
        method, name = entry
        result = message.get("result")
        if method == "tools/list" and isinstance(result, dict) and isinstance(result.get("tools"), list):
            result["tools"] = [tool for tool in result["tools"] if isinstance(tool, dict) and tool.get("name") in self.readers]
        elif method == "tools/call":
            completed = ("error" not in message and isinstance(result, dict) and result.get("isError") is not True
                         and isinstance(result.get("content"), list))
            with self.lock:
                if completed:
                    self.completed += 1
                    self.tools[name] = self.tools.get(name, 0) + 1
                else:
                    self.failed += 1
        return message

    def cleanup(self) -> None:
        with self.lock:
            self.stopped = True
            connections, processes = list(self.connections), list(self.processes)
        self.listener.close()
        self.thread.join(timeout=2)
        for connection in connections:
            with contextlib.suppress(OSError):
                connection.shutdown(socket.SHUT_RDWR)
            connection.close()
        for process in processes:
            with contextlib.suppress(OSError):
                process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=5)


def _host_abstract_socket() -> str | None:
    """One listening abstract Unix socket of the host's network namespace, if any."""
    with contextlib.suppress(OSError):
        for line in Path("/proc/net/unix").read_text(errors="replace").splitlines()[1:]:
            fields = line.split()
            # State 01 is listening; the path field starts with @ for an abstract name.
            if len(fields) >= 8 and fields[5] == "01" and fields[7].startswith("@") and fields[7][1:].isprintable():
                return fields[7][1:]
    return None


_GIT_CONFIG_KEYS = re.compile(
    r"(core\.(repositoryformatversion|filemode|bare|logallrefupdates|ignorecase|precomposeunicode|symlinks"
    r"|autocrlf|eol|safecrlf|checkstat|trustctime|quotepath|sparsecheckout|sparsecheckoutcone|splitindex"
    r"|untrackedcache)|extensions\.[a-z0-9]+)"
)


def _safe_git_config(source: Path) -> bytes:
    """A copy of a Git config holding only the repository-format keys a read-only Git needs."""
    listed = subprocess.run(["git", "config", "--file", str(source), "--no-includes", "--null", "--list"],
                            capture_output=True, timeout=_GIT_TIMEOUT, check=False, stdin=subprocess.DEVNULL)
    if listed.returncode:
        raise Refused("the Git config cannot be read for sanitizing")
    lines = []
    for entry in listed.stdout.split(b"\0"):
        key, _, value = entry.decode("utf-8", "replace").partition("\n")
        if _GIT_CONFIG_KEYS.fullmatch(key) and re.fullmatch(r"[A-Za-z0-9._-]*", value):
            section, _, name = key.rpartition(".")
            lines.append(f"[{section}]\n\t{name} = {value}\n")
    return "".join(lines).encode()


def _empty_store_slot(worktree: Path, relative: str) -> None:
    """Inspect every component without following branch-controlled symlinks."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        with contextlib.ExitStack() as stack:
            descriptor = os.open(worktree, flags)
            stack.callback(os.close, descriptor)
            parts = Path(relative).parts
            for part in parts[:-1]:
                descriptor = os.open(part, flags, dir_fd=descriptor)
                stack.callback(os.close, descriptor)
            try:
                os.stat(parts[-1], dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise Refused("worktree_local_store")
    except FileNotFoundError:
        return
    except OSError:
        raise Refused("worktree_local_store") from None


def _trusted_database(worktree: Path, repository: Path, relative: str) -> Path:
    """Select only from the agreed primary, independently of worktree content."""
    from scripts.storage.topology import STORE_FILES, inspect_selector

    if relative not in {f"data/{STORE_FILES[name][0]}" for name in ("sources", "vesum")}:
        raise Refused("unsupported_read_store")
    _empty_store_slot(worktree, relative)
    trusted = repository / relative
    try:
        if os.path.realpath(trusted.parent) != str(trusted.parent):
            raise Refused("store_parent_not_real_directory")
        if not stat.S_ISDIR(trusted.parent.lstat().st_mode):
            raise Refused("store_parent_not_real_directory")
        if relative == f"data/{STORE_FILES['sources'][0]}":
            selection = inspect_selector(trusted)
            if selection.layout not in {"selector", "legacy_file"} or selection.generation is None:
                raise Refused(selection.reason)
            trusted = selection.generation
        if not stat.S_ISREG(trusted.lstat().st_mode):
            raise Refused("store_not_regular_file")
    except OSError:
        raise Refused("store_unavailable") from None
    return trusted


def _store_sidecars(target: Path) -> list[Path]:
    """Only a selected file's own existing regular sidecars may be exposed."""
    result = []
    for suffix in ("-wal", "-shm"):
        path = target.with_name(target.name + suffix)
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode):
            raise Refused("store_sidecar_not_regular_file")
        result.append(path)
    return result


def _store_read_expectation(store: str, target: Path, sidecars: list[Path]) -> list[dict]:
    read = {"status": "read", "store": store, "reason": None}
    with target.open("rb") as stream:
        header = stream.read(20)
    wal = header.startswith(b"SQLite format 3\0") and header[18:20] == b"\x02\x02"
    if wal and target.with_name(target.name + "-shm") not in sidecars:
        return [read, {"status": "refused", "store": store, "reason": "wal_sidecars_unavailable"}]
    return [read]


def _probe_passed(probe: dict) -> bool:
    expected = probe.get("expect")
    if probe.get("op") == "store_read":
        return isinstance(expected, list) and probe.get("outcome") in expected
    return probe.get("outcome") == expected


def _write_error(path: Path) -> str:
    """The error a write-open must give inside: EROFS, or EACCES first for a file whose mode denies writes.

    The kernel checks a file's permission bits before the mount's read-only flag, so a host file
    without write permission (sources.db is 0444) cannot show EROFS on open; its ``chmod`` probe can.
    """
    return "EROFS" if os.access(path, os.W_OK) else "EACCES"


class _Boundary:
    def __init__(self, args: argparse.Namespace, receipt: dict):
        self.args, self.receipt = args, receipt
        self.worktree = Path(args.worktree).resolve(strict=True)
        self.base = Path(args.scratch)
        self.relay = self.egress = self.process = self.fixture = None
        self.created = False
        self.confirmed_inputs: list[dict] = []

    def _requested_inputs(self) -> list[dict]:
        paths, digests = self.args.input or [], self.args.input_sha256 or []
        if len(paths) != len(digests):
            raise Refused("agy_input_refused: input digest missing")
        if len(paths) > MAX_INPUTS:
            raise Refused(f"agy_input_refused: more than {MAX_INPUTS} inputs")
        return [
            {"mount": f"{INPUT_MOUNT}/{index}", "path": path, "sha256": digest}
            for index, (path, digest) in enumerate(zip(paths, digests, strict=True))
        ]

    def _stage_input_copies(self) -> None:
        """Write the hashed bytes into the scratch and drop them from memory.

        The copy sits beside the boundary directory, not inside it, so the runtime read list does
        not publish it. Bubblewrap then bind-mounts the copy, not the caller's path.
        """
        if not self.confirmed_inputs:
            return
        store = self.base / "inputs"
        store.mkdir(mode=0o700)
        for item in self.confirmed_inputs:
            data = item.pop("data", None)
            if not isinstance(data, bytes) or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise Refused("agy_input_refused: input digest missing")
            dest = store / str(item["index"])
            _write_private(dest, data, 0o644)
            item["copy"] = str(dest)

    def run(self) -> int:
        from scripts.agent_runtime.agy_hook_config import GUARD_NAME, guard_registration
        from scripts.agent_runtime.attempt_boundary import full_review_reads, runtime_files
        from scripts.agent_runtime.attempt_network import AttemptEgress, load_allowlist
        from scripts.agent_runtime.review_mcp import _real_agy_token, agy_review_settings
        from scripts.agent_runtime.sources_read_only import sources_tool_sets
        from scripts.dispatcher import runtime_context
        from scripts.dispatcher.git import DATABASE_LINKS
        from scripts.dispatcher.review_tools import guard_runtime_reads, hooks
        from scripts.review.isolation import prepare_host_sandbox, wrap_argv_with_sandbox

        requested = self._requested_inputs()
        if requested:
            # Before bubblewrap and before AGY: a changed or missing file never starts the sandbox.
            common = Path(_git(
                self.worktree, "rev-parse", "--path-format=absolute", "--git-common-dir",
            ).strip()).resolve(strict=True)
            repository = common.parent
            if main_checkout_root(self.worktree).resolve(strict=True) != repository:
                raise Refused("store_primary_disagreement")
            self.confirmed_inputs = confirm_inputs(requested, repo_root=repository)
            self.receipt["inputs"] = _input_proof(self.confirmed_inputs)
        if reason := unavailable():
            raise Refused(reason)
        command = self.args.command[1:] if self.args.command[:1] == ["--"] else self.args.command
        found = shutil.which(command[0]) if command else None
        if not found:
            raise Refused("the agy executable was not found")
        agy = Path(found).resolve(strict=True)
        start = _input_state(self.worktree)
        self.receipt["input"] = {"start": start}
        if not start["clean"]:
            raise Refused("the worktree differs from its head before launch")
        git_dir = Path(_git(self.worktree, "rev-parse", "--absolute-git-dir").strip()).resolve(strict=True)
        common = Path(_git(self.worktree, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).resolve(
            strict=True)
        repository = common.parent
        if main_checkout_root(self.worktree).resolve(strict=True) != repository:
            raise Refused("store_primary_disagreement")
        self.common = common

        self.base.mkdir(mode=0o700)  # exclusive: an existing scratch is never reused or removed
        self.created = True
        self._stage_input_copies()
        boundary, runtime = self.base / "boundary", self.base / "runtime"
        boundary.mkdir(mode=0o700)
        runtime.mkdir(mode=0o700)
        home, tmp, logs = runtime / "home", runtime / "tmp", runtime / "logs"
        for directory in (home, tmp, logs):
            directory.mkdir(mode=0o700)
        app = home / ".gemini" / "antigravity-cli"
        config = home / ".gemini" / "config"
        app.mkdir(mode=0o700, parents=True)
        config.mkdir(mode=0o700)
        try:
            token = _real_agy_token().read_bytes()
        except OSError as exc:
            raise Refused("the AGY OAuth token is unavailable") from exc
        _write_private(app / "antigravity-oauth-token", token)  # a regular-file copy: no shared link or inode
        projected = {name: source.read_bytes() for name, source in _PROJECTED.items()}
        # The canary imports these trusted contracts, never branch-controlled code.
        for relative in ("scripts/storage/topology.py", "scripts/lib/readonly_sqlite.py", "scripts/common/repo_root.py"):
            projected[f"store_contract/{relative}"] = (ROOT / relative).read_bytes()
        for package in ("scripts", "scripts/storage", "scripts/lib", "scripts/common"):
            projected[f"store_contract/{package}/__init__.py"] = b""
        import psutil

        locality_package = Path(psutil.__file__).parent
        for source in locality_package.iterdir():
            if source.is_file() and source.suffix in {".py", ".so"}:
                if source.is_symlink():
                    raise Refused("store_locality_runtime_not_regular_file")
                projected[f"store_contract/psutil/{source.name}"] = source.read_bytes()
        for name, data in projected.items():
            (boundary / name).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            _write_private(boundary / name, data, 0o500)
        digest = hashlib.sha256(Path(__file__).read_bytes())
        for name in sorted(projected):
            digest.update(name.encode() + b"\0" + hashlib.sha256(projected[name]).digest())
        self.receipt["wrapper_sha256"] = digest.hexdigest()
        interpreter = project_interpreter().resolve(strict=True)
        readers, _ = sources_tool_sets()
        _write_private(config / "mcp_config.json", json.dumps({"mcpServers": {"sources": {
            "command": str(interpreter), "args": [str(boundary / "stdio.py"), str(boundary / "sources.sock")],
        }}}).encode())
        # Defense in depth only: the relay is what refuses these tools.
        settings = agy_review_settings("full", checkout_root=self.worktree)
        settings["permissions"]["allow"] += [f"read_file({root})" for root in runtime_context.read_roots()]
        if self.confirmed_inputs:
            settings["permissions"]["allow"].append(f"read_file({INPUT_MOUNT})")
        _write_private(app / "settings.json", json.dumps(settings).encode())
        _write_private(config / "hooks.json", json.dumps({
            GUARD_NAME: guard_registration(), "dispatch-review-guards": hooks(harness="agy", review=True),
        }).encode())
        uid, gid = os.getuid(), os.getgid()
        _write_private(boundary / "passwd", f"review:x:{uid}:{gid}:Review seat:{home}:/bin/bash\n".encode(), 0o444)
        _write_private(boundary / "group", f"review:x:{gid}:\n".encode(), 0o444)

        reads, hidden = full_review_reads(self.worktree)
        corpus = (repository / "data").resolve()
        reads = [path for path in reads if path != corpus]
        databases = []
        for relative in DATABASE_LINKS:
            _empty_store_slot(self.worktree, relative)
            if os.path.lexists(repository / relative):
                databases.append((self.worktree / relative, _trusted_database(self.worktree, repository, relative)))
        sidecars = [path for _, target in databases for path in _store_sidecars(target)]
        # Git reads only these copies: remotes, credentials, URL rewrites, helpers and includes stay outside.
        overlays = []
        for name, source in (("gitconfig", common / "config"), ("gitconfig.worktree", git_dir / "config.worktree")):
            if os.path.lexists(source):
                _write_private(boundary / name, _safe_git_config(source), 0o600)
                overlays.append((boundary / name, source))
        nonce = uuid.uuid4().hex
        self.fixture = git_dir / f"agy-canary-{nonce}"
        _write_private(self.fixture, b"sacrificial fixture of the read-only AGY canary\n")
        tracked = next((self.worktree / name for name in _git(self.worktree, "ls-files", "-z").split("\0")
                        if name and (self.worktree / name).is_file() and not (self.worktree / name).is_symlink()), None)
        if tracked is None:
            raise Refused("the worktree has no tracked regular file to probe")
        probes = self._probes(tracked, git_dir, overlays, databases, repository, tmp / f"canary-{nonce}", nonce)
        for slot, target in databases:
            store = "sources" if slot.name == "sources.db" else "vesum"
            probes.append({"op": "store_read", "path": str(self.worktree), "store": store,
                           "expect": _store_read_expectation(store, target, sidecars)})
            for suffix in ("-wal", "-shm"):
                path = target.with_name(target.name + suffix)
                if path not in sidecars:
                    probes.append({"op": "create", "path": str(path), "expect": "EROFS"})
        for path in sidecars:
            probes.extend([{"op": "write_open", "path": str(path), "expect": _write_error(path)},
                           {"op": "chmod", "path": str(path), "expect": "EROFS"}])
        for item in self.confirmed_inputs:
            # The staged copy is owner-writable. The mount is read-only, so open fails with EROFS.
            probes.extend([
                {"op": "stat", "path": item["mount"], "expect": "OK"},
                {"op": "write_open", "path": item["mount"], "expect": "EROFS"},
                {"op": "chmod", "path": item["mount"], "expect": "EROFS"},
            ])
        if self.confirmed_inputs:
            absent = f"{INPUT_MOUNT}/not-provided"
            probes.extend([
                {"op": "stat", "path": absent, "expect": "ENOENT"},
                {"op": "create", "path": absent, "expect": "EROFS"},
            ])
        self.receipt["canary"] = {"targets": sorted({probe["path"] for probe in probes}), "passed": False}

        env_keep = {name: os.environ[name] for name in ("PATH", "HOME", "LANG", "TMPDIR") if name in os.environ}
        self.relay = SourcesRelay(boundary / "sources.sock", frozenset(readers), env_keep)
        self.egress = AttemptEgress(boundary / "egress.sock", load_allowlist("agy"), public_internet=True)
        sandbox = prepare_host_sandbox(
            engine="agy", snapshot_root=self.worktree, write_root=runtime, reject_root=repository,
            runtime_reads=[*runtime_files(agy), *guard_runtime_reads(),
                           *reads, *(target for _, target in databases), *sidecars,
                           *runtime_context.read_roots(), boundary],
            network_allowed=False,
        )
        self.receipt["bwrap"] = str(sandbox.binary)
        report_read, report_write = os.pipe()
        go_read, go_write = os.pipe()
        plan = {"report_fd": report_write, "go_fd": go_read, "probes": probes}
        _write_private(boundary / "plan.json", json.dumps(plan).encode(), 0o444)
        inner = [str(interpreter), str(boundary / "canary.py"), str(boundary / "plan.json"), "--",
                 str(interpreter), str(boundary / "forwarder.py"), str(boundary / "egress.sock"), str(agy), *command[1:]]
        argv = wrap_argv_with_sandbox(inner, sandbox)
        masks = [argument for path in hidden for argument in ("--tmpfs", str(path), "--remount-ro", str(path))]
        masks += [argument for copy, source in overlays for argument in ("--ro-bind", str(copy), str(source))]
        for link, target in databases:
            primary = repository / link.relative_to(self.worktree)
            if primary != target:
                # Present inspect_selector's exact layout without mounting over the host link.
                masks += ["--symlink", str(target.relative_to(primary.parent)), str(primary)]
        input_mounts = []
        if self.confirmed_inputs:
            # The directory is created on the empty root. Only the private copy is bound into it.
            input_mounts += ["--dir", INPUT_MOUNT]
            for item in self.confirmed_inputs:
                input_mounts += ["--ro-bind", item["copy"], item["mount"]]
        argv[-len(inner):-len(inner)] = [
            *masks, *input_mounts, "--ro-bind", str(boundary / "passwd"), "/etc/passwd",
            "--ro-bind", str(boundary / "group"),
            "/etc/group", "--cap-drop", "ALL", "--proc", "/proc", "--chdir", str(self.worktree),
            # Last: the empty root becomes read-only, leaving the runtime bind as the only writable path.
            "--remount-ro", "/",
        ]
        self.receipt["argv_sha256"] = hashlib.sha256(json.dumps(argv).encode()).hexdigest()
        env = {
            "HOME": str(home), "TMPDIR": str(tmp), "PATH": f"/usr/bin:/bin:{agy.parent}",
            "LANG": os.environ.get("LANG", "C.UTF-8"), "USER": "review", "LOGNAME": "review", "SHELL": "/bin/bash",
            "AGY_APP_DATA_DIR": str(app), **{name: os.environ[name] for name in _AGY_AUTH if name in os.environ},
            "LU_TASKS_DIR": str(runtime_context.read_roots()[1]),
        }
        try:
            self.process = subprocess.Popen(argv, env=env, cwd=self.worktree, pass_fds=(report_write, go_read))
        finally:
            os.close(report_write)
            os.close(go_read)
        try:
            report = self._report(report_read)
            outcomes = report.get("probes") if isinstance(report, dict) else None
            failed = [probe for probe in outcomes or [] if not _probe_passed(probe)]
            passed = isinstance(outcomes, list) and len(outcomes) == len(probes) and not failed and all(
                {key: probe.get(key) for key in planned} == planned for probe, planned in zip(outcomes, probes, strict=True))
            self.receipt["canary"].update(probes=outcomes, passed=passed)
            if not passed:
                raise Refused("the sandbox canary failed: " + ", ".join(
                    f"{probe.get('op')} {probe.get('path')} gave {probe.get('outcome')}" for probe in failed[:5]))
            os.write(go_write, b"1")
        finally:
            os.close(go_write)
            os.close(report_read)
        self.receipt["status"] = "ran"
        returncode = self.process.wait()
        self.receipt["returncode"] = returncode
        return returncode

    def _probes(self, tracked, git_dir, overlays, databases, repository, positive, nonce) -> list[dict]:
        probes = []

        def expect(op: str, path: Path | str, outcome: str, port: int | None = None) -> None:
            probes.append({"op": op, "path": str(path), "expect": outcome, **({"port": port} if port else {})})

        # The kernel checks the mount before the name, so a rename or unlink of an absent name on a
        # read-only mount fails with EROFS too, and the worktree's own files are never at risk.
        absent = self.worktree / f".agy-canary-{nonce}"
        expect("write_open", tracked, _write_error(tracked))
        expect("chmod", tracked, "EROFS")
        for op in ("create", "mkdir", "rename", "unlink"):
            expect(op, absent, "EROFS")
        expect("write_open", git_dir / "HEAD", _write_error(git_dir / "HEAD"))
        expect("create", git_dir / f"agy-canary-{nonce}.new", "EROFS")
        for op in ("rename", "unlink", "write_open"):
            expect(op, self.fixture, "EROFS")
        for copy, source in overlays:  # the sanitized copy is what the sandbox sees at the source path
            expect("write_open", source, _write_error(copy))
            expect("chmod", source, "EROFS")
        expect("create", self.common / "refs" / "heads" / f"agy-canary-{nonce}", "EROFS")
        for link, target in databases:
            expect("write_open", link, "ENOENT")
            expect("chmod", link, "ENOENT")
            expect("create", link, "EROFS")
            expect("write_open", target, _write_error(target))
            expect("chmod", target, "EROFS")
            if target.parent.name == "sources-generations":
                expect("stat", target.with_name(target.name + ".receipt.json"), "ENOENT")
                from scripts.storage.topology import is_generation_name

                absent_generation = next((path for path in sorted(target.parent.iterdir())
                                          if path != target and is_generation_name(path.name)),
                                         target.with_name("sources.19000101T000000Z-000000000000.db"))
                if absent_generation == target:
                    absent_generation = target.with_name("sources.19000101T000000Z-111111111111.db")
                expect("stat", absent_generation, "ENOENT")
        home = Path.home()
        # A host path the launcher cannot even stat is unreachable inside too, so only present ones are probed.
        for relative in _HOST_SECRETS:
            if os.path.lexists(home / relative):
                expect("stat", home / relative, "ENOENT")
        if os.path.lexists(repository / "AGENTS.md"):
            expect("stat", repository / "AGENTS.md", "ENOENT")  # the primary checkout stays unmounted
        for port in _CONTROL_PORTS:
            expect("connect_tcp", "127.0.0.1", "ECONNREFUSED", port)
        if (name := _host_abstract_socket()) is not None:
            expect("connect_abstract", name, "ECONNREFUSED")
        runtime_dir = Path(f"/run/user/{os.getuid()}")
        for path in (runtime_dir / "bus", os.environ.get("SSH_AUTH_SOCK"), *_CONTROL_SOCKETS):
            if path and os.path.lexists(path):
                expect("connect_unix", path, "ENOENT")
        expect("scratch_cycle", positive, "OK")
        return probes

    def _report(self, descriptor: int) -> dict | None:
        chunks, deadline = [], time.monotonic() + _CANARY_TIMEOUT
        while (remaining := deadline - time.monotonic()) > 0:
            ready, _, _ = select.select([descriptor], [], [], remaining)
            if not ready:
                break
            chunk = os.read(descriptor, 65536)
            if not chunk:
                with contextlib.suppress(ValueError):
                    return json.loads(b"".join(chunks))
                return None
            chunks.append(chunk)
        raise Refused("the sandbox canary did not report in time")

    def cleanup(self) -> None:
        if self.process is not None and self.process.poll() is None:
            # bwrap's pid namespace dies with it (--die-with-parent, --unshare-pid).
            with contextlib.suppress(OSError):
                self.process.kill()
            self.process.wait()
        for helper in (self.relay, self.egress):
            if helper is not None:
                with contextlib.suppress(Exception):
                    helper.cleanup()
        if self.relay is not None:
            self.receipt["sources"] = self.relay.evidence()
        if self.egress is not None:
            self.receipt["egress"] = list(self.egress.records)
        if self.fixture is not None:
            with contextlib.suppress(FileNotFoundError):
                self.fixture.unlink()
        if "start" in self.receipt.get("input", {}):
            self.receipt["input"]["end"] = _input_state(self.worktree)
        exported = False
        if self.created:
            try:
                self._export_tool_results()
                exported = True
            except (OSError, ValueError):
                # Leave the scratch so the worker can still read the files, then discard it.
                self.receipt["tool_results"] = "export_failed"
        if self.created and exported:
            try:
                _remove(self.base)
            except OSError as exc:  # the worker's discard retries; residue never voids the run's evidence
                self.receipt["cleanup"] = f"residue: {type(exc).__name__}"

    def _export_tool_results(self) -> None:
        """Copy saved step bodies out with the existing inliner, before ``_remove`` deletes them."""
        from scripts.agent_runtime.adapters.agy import export_saved_step_outputs

        app = self.base / "runtime" / "home" / ".gemini" / "antigravity-cli"
        payload = {"schema": "agy-tool-results.v1", "calls": export_saved_step_outputs(app)}
        _write_private(
            _tool_results_from_receipt(Path(self.args.receipt)),
            json.dumps(payload, ensure_ascii=False).encode(),
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.dispatcher.agy_sandbox",
        description="Run AGY inside the dispatcher's read-only bubblewrap boundary (C-3027).\n"
                    "Internal launcher returned by providers/agy.py for --mode read-only; not run by hand.",
        epilog="Outputs: AGY's stdout and stderr; the boundary receipt at --receipt.\n"
               f"Exit codes: AGY's status, or {REFUSED} when the boundary refuses to start AGY.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--input", action="append", help="Host path of one recorded input")
    parser.add_argument("--input-sha256", action="append", help="SHA-256 recorded for the matching --input")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    receipt = {"schema": SCHEMA, "task_id": args.task_id, "status": "refused", "started_at": _now()}
    boundary = None

    def cancelled(_signum, _frame):
        raise Refused("cancelled")

    previous = signal.signal(signal.SIGTERM, cancelled)
    try:
        boundary = _Boundary(args, receipt)
        return boundary.run()
    except Exception as exc:  # every failure refuses; nothing falls back to an unsandboxed AGY
        if receipt["status"] != "ran":
            receipt["reason"] = str(exc) if isinstance(exc, Refused) else f"setup failed: {type(exc).__name__}: {exc}"[:500]
            print(f"agy read-only boundary refused: {receipt['reason']}", file=sys.stderr)
            return REFUSED
        # AGY started but the launcher could not see it finish: the run proves nothing.
        receipt.update(status="interrupted", reason=f"{exc if isinstance(exc, Refused) else type(exc).__name__}")
        return REFUSED
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            if boundary is not None:
                boundary.cleanup()
        finally:
            receipt["finished_at"] = _now()
            _write_receipt(Path(args.receipt), receipt)
            signal.signal(signal.SIGTERM, previous)
