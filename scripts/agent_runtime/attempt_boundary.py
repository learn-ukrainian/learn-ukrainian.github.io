"""Review access: full matching checkout or isolated copied manifest evidence.

Both modes use the isolated launcher, private network and attempt-scoped sources
ledger. Full mode widens only the read set to the verified checkout, Git objects
and corpus. Sources runs outside the sandbox, connected by a byte-stream socket;
the receipt store, host services and real home remain unmounted.
This is separate from code-review isolation (#9251).
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts.common.repo_root import project_interpreter

from .attempt_safe_read import (
    MAX_ATTEMPT_READ_BYTES as MAX_ATTEMPT_READ_BYTES,
)
from .attempt_safe_read import (
    AttemptReadError as AttemptReadError,
)
from .attempt_safe_read import (
    safe_attempt_file_size as safe_attempt_file_size,
)
from .attempt_safe_read import (
    safe_read_attempt_file as safe_read_attempt_file,
)
from .env_sanitize import build_agent_env

# Claude account labels. A run carries one label; the default account is the
# one this host has always used. Which account a non-default label means lives
# only in private local configuration (see ``load_claude_account_binding``).
CLAUDE_ACCOUNT_KEY = "claude_account"
DEFAULT_CLAUDE_ACCOUNT = "a"
CLAUDE_ACCOUNT_LABELS = ("a", "b")
ENV_CLAUDE_ACCOUNTS_FILE = "LU_CLAUDE_ACCOUNTS_FILE"
CLAUDE_ACCOUNTS_FILE_NAME = "claude_accounts.json"
CLAUDE_ACCOUNTS_SCHEMA_VERSION = 1
_CLAUDE_AMBIENT_AUTH_ENV = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
)
_CLAUDE_BINDING_KEYS = frozenset({"config_dir", "account_uuid"})
_CLAUDE_ACCOUNT_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_CLAUDE_BINDING_MAX_BYTES = 65536
_CLAUDE_GLOBAL_CONFIG_MAX_BYTES = 16 * 1024 * 1024
_CLAUDE_SETTINGS_MAX_BYTES = 1024 * 1024
# User settings that would make Claude Code use a key, helper, provider or
# endpoint other than the account's own login (#10619). ``ANTHROPIC_*`` names
# keys, tokens, endpoints, headers and provider settings alike, so the whole
# namespace is refused.
_CLAUDE_SETTINGS_CREDENTIAL_KEYS = frozenset({"apiKeyHelper", "awsAuthRefresh", "awsCredentialExport"})
_CLAUDE_SETTINGS_CREDENTIAL_ENV = frozenset({*_CLAUDE_AMBIENT_AUTH_ENV, "CLAUDE_CONFIG_DIR"})
_CLAUDE_SETTINGS_CREDENTIAL_ENV_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_USE_", "CLAUDE_CODE_OAUTH_")
_PRIVATE_FILE_FAILURES = ("unavailable", "not_private", "oversized", "invalid")
# Every code a Claude account refusal may carry. Codes name no value or location.
CLAUDE_ACCOUNT_REFUSAL_CODES = frozenset(
    {
        "claude_account_unknown",
        "claude_account_seat_unsupported",
        "claude_account_route_unsealed",
        "claude_account_default_has_no_binding",
        "claude_account_binding_missing",
        "claude_account_ambient_conflict",
        "claude_account_config_dir_missing",
        "claude_account_config_dir_unavailable",
        "claude_account_config_dir_not_private",
        "claude_account_binding_is_default",
        "claude_account_unverified",
        "claude_account_platform_unsupported",
        "claude_account_credentials_missing",
        "claude_account_credentials_expired",
        "claude_account_identity_unavailable",
        "claude_account_settings_credential_source",
        "claude_account_auth_method_conflict",
        "claude_account_auth_status_unavailable",
        *(f"claude_account_credentials_{failure}" for failure in _PRIVATE_FILE_FAILURES),
        *(
            f"claude_account_{kind}_{failure}"
            for kind in ("binding", "config", "settings")
            for failure in _PRIVATE_FILE_FAILURES
        ),
    }
)


class ClaudeAccountRefused(ValueError):
    """A Claude account label or binding was refused; the code names no value or location."""

    def __init__(self, code: str):
        if code not in CLAUDE_ACCOUNT_REFUSAL_CODES:
            raise AssertionError(f"unregistered Claude account refusal code: {code}")
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ClaudeAccountBinding:
    """A label's private binding: Claude's config directory and the account it must hold."""

    label: str
    config_dir: Path = field(repr=False)
    account_uuid: str = field(repr=False)


def resolve_claude_account_label(raw: object) -> str:
    """The run's account label: omitted means the default; anything unknown is refused."""
    if raw is None:
        return DEFAULT_CLAUDE_ACCOUNT
    if isinstance(raw, str) and raw in CLAUDE_ACCOUNT_LABELS:
        return raw
    raise ClaudeAccountRefused("claude_account_unknown")


def claude_accounts_file(environ: Mapping[str, str] | None = None) -> Path | None:
    """``LU_CLAUDE_ACCOUNTS_FILE`` if set (empty means none), else the user config file."""
    env = os.environ if environ is None else environ
    if ENV_CLAUDE_ACCOUNTS_FILE in env:
        value = env[ENV_CLAUDE_ACCOUNTS_FILE]
        return Path(value) if value else None
    base = env.get("XDG_CONFIG_HOME")
    if not base or not Path(base).is_absolute():
        base = str(Path.home() / ".config")
    return Path(base) / "learn-ukrainian" / CLAUDE_ACCOUNTS_FILE_NAME


def _unique_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def _read_private_json(
    path: Path, *, limit: int, code: str, dir_fd: int | None = None, forbidden_mode: int = 0o077
) -> Any:
    """Owner-only regular file, read without following links; ``None`` when absent.

    ``forbidden_mode`` names the permission bits the file must not carry
    (default: any group or other access). Every failure is
    ``ClaudeAccountRefused`` with ``code`` and a fixed suffix.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    except FileNotFoundError:
        return None
    except OSError:
        raise ClaudeAccountRefused(f"{code}_unavailable") from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & forbidden_mode:
            raise ClaudeAccountRefused(f"{code}_not_private")
        raw = os.read(fd, limit + 1)
    except OSError:
        raise ClaudeAccountRefused(f"{code}_unavailable") from None
    finally:
        os.close(fd)
    if len(raw) > limit:
        raise ClaudeAccountRefused(f"{code}_oversized")
    try:
        # A decode or duplicate-key error is a ValueError; its text is never kept.
        return json.loads(raw, object_pairs_hook=_unique_json_keys)
    except ValueError:
        raise ClaudeAccountRefused(f"{code}_invalid") from None


def load_claude_account_binding(label: str, *, environ: Mapping[str, str] | None = None) -> ClaudeAccountBinding:
    """The private binding for a non-default label, from local configuration only.

    The file is a JSON object ``{"schema_version": 1, "accounts": {"<label>":
    {"config_dir": "<absolute directory>", "account_uuid": "<account UUID>"}}}``.
    The default label has no binding: it is always the host's own account.
    """
    if resolve_claude_account_label(label) == DEFAULT_CLAUDE_ACCOUNT:
        raise ClaudeAccountRefused("claude_account_default_has_no_binding")
    path = claude_accounts_file(environ)
    data = (
        None
        if path is None
        else _read_private_json(path, limit=_CLAUDE_BINDING_MAX_BYTES, code="claude_account_binding")
    )
    if data is None:
        raise ClaudeAccountRefused("claude_account_binding_missing")
    if not isinstance(data, dict) or set(data) != {"schema_version", "accounts"}:
        raise ClaudeAccountRefused("claude_account_binding_invalid")
    version, accounts = data["schema_version"], data["accounts"]
    if type(version) is not int or version != CLAUDE_ACCOUNTS_SCHEMA_VERSION or not isinstance(accounts, dict):
        raise ClaudeAccountRefused("claude_account_binding_invalid")
    non_default = set(CLAUDE_ACCOUNT_LABELS) - {DEFAULT_CLAUDE_ACCOUNT}
    if not set(accounts) <= non_default:
        raise ClaudeAccountRefused("claude_account_binding_invalid")
    entry = accounts.get(label)
    if entry is None:
        raise ClaudeAccountRefused("claude_account_binding_missing")
    if not isinstance(entry, dict) or set(entry) != _CLAUDE_BINDING_KEYS:
        raise ClaudeAccountRefused("claude_account_binding_invalid")
    config_dir, account_uuid = entry["config_dir"], entry["account_uuid"]
    if (
        not isinstance(config_dir, str)
        or not config_dir
        or not Path(config_dir).is_absolute()
        or any(ord(c) < 32 or ord(c) == 127 for c in config_dir)
        or not isinstance(account_uuid, str)
        or not _CLAUDE_ACCOUNT_UUID_RE.fullmatch(account_uuid)
    ):
        raise ClaudeAccountRefused("claude_account_binding_invalid")
    return ClaudeAccountBinding(label=label, config_dir=Path(config_dir), account_uuid=account_uuid)


def _claude_config_account_uuid(global_config: Path, *, dir_fd: int | None = None) -> str | None:
    """The account Claude Code recorded at login in its global config, if any."""
    data = _read_private_json(
        global_config, limit=_CLAUDE_GLOBAL_CONFIG_MAX_BYTES, code="claude_account_config", dir_fd=dir_fd
    )
    if data is None:
        return None
    account = data.get("oauthAccount") if isinstance(data, dict) else None
    value = account.get("accountUuid") if isinstance(account, dict) else None
    return value if isinstance(value, str) else None


def _refuse_claude_settings_credential_source(directory: int) -> None:
    """Refuse a login directory whose user settings name another key source (#10619).

    Claude Code applies the ``settings.json`` in its config directory after the
    environment is sanitized, so a key, helper, provider switch or endpoint
    set there would replace the verified login. Only names are inspected; no
    value is kept or reported. The file may be readable by others, not
    writable by them.
    """
    data = _read_private_json(
        Path("settings.json"),
        limit=_CLAUDE_SETTINGS_MAX_BYTES,
        code="claude_account_settings",
        dir_fd=directory,
        forbidden_mode=0o022,
    )
    if data is None:
        return
    env = data.get("env", {}) if isinstance(data, dict) else None
    if not isinstance(env, dict):
        raise ClaudeAccountRefused("claude_account_settings_invalid")
    names = {name.upper() for name in env}
    if (
        _CLAUDE_SETTINGS_CREDENTIAL_KEYS & set(data)
        or names & _CLAUDE_SETTINGS_CREDENTIAL_ENV
        or any(name.startswith(_CLAUDE_SETTINGS_CREDENTIAL_ENV_PREFIXES) for name in names)
    ):
        raise ClaudeAccountRefused("claude_account_settings_credential_source")


@contextlib.contextmanager
def _open_claude_directory(path: Path) -> Iterator[int]:
    """Walk from root using checked no-follow descriptors; keep the selected handle."""
    if not path.is_absolute() or ".." in path.parts:
        raise ClaudeAccountRefused("claude_account_config_dir_not_private")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = None
    try:
        fd = os.open(path.anchor, flags)
        parts = path.parts[1:]
        for index in range(len(parts) + 1):
            info = os.fstat(fd)
            selected = index == len(parts)
            owners = {os.getuid()} if selected else {0, os.getuid()}
            if not stat.S_ISDIR(info.st_mode) or info.st_uid not in owners or info.st_mode & 0o022:
                raise ClaudeAccountRefused("claude_account_config_dir_not_private")
            if selected:
                break
            child = os.open(parts[index], flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    except FileNotFoundError:
        raise ClaudeAccountRefused("claude_account_config_dir_missing") from None
    except OSError as exc:
        code = "not_private" if exc.errno in {errno.ELOOP, errno.ENOTDIR} else "unavailable"
        raise ClaudeAccountRefused(f"claude_account_config_dir_{code}") from None
    finally:
        if fd is not None:
            os.close(fd)


def _claude_selected_identity(token: str) -> str:
    """Ask the provider about the exact material selected for use, with no redirects."""
    connection = None
    try:
        connection = http.client.HTTPSConnection("api.anthropic.com", timeout=10)
        connection.request(
            "GET",
            "/api/oauth/profile",
            headers={
                "Authorization": f"Bearer {token}",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        raw = response.read(65537)
        if response.status != 200 or len(raw) > 65536:
            raise ClaudeAccountRefused("claude_account_identity_unavailable")
        profile = json.loads(raw, object_pairs_hook=_unique_json_keys)
        identity = profile["account"]["uuid"]
        if not isinstance(identity, str) or not _CLAUDE_ACCOUNT_UUID_RE.fullmatch(identity):
            raise ClaudeAccountRefused("claude_account_identity_unavailable")
        return identity
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError):
        raise ClaudeAccountRefused("claude_account_identity_unavailable") from None
    finally:
        if connection is not None:
            with contextlib.suppress(OSError, http.client.HTTPException):
                connection.close()


def _validated_claude_selection(
    label: str, *, environ: Mapping[str, str] | None = None
) -> tuple[ClaudeAccountBinding, str]:
    """Validate and select once, reading both files through the same checked directory."""
    from scripts.review.isolation import ReviewIsolationError

    env = os.environ if environ is None else environ
    if any(env.get(key) for key in _CLAUDE_AMBIENT_AUTH_ENV):
        raise ClaudeAccountRefused("claude_account_ambient_conflict")
    try:
        binding = load_claude_account_binding(label, environ=env)
        if platform.system() != "Linux":
            raise ClaudeAccountRefused("claude_account_platform_unsupported")
        with _open_claude_directory(binding.config_dir) as directory:
            selected = os.fstat(directory)
            ambient = env.get("CLAUDE_CONFIG_DIR")
            if ambient:
                with _open_claude_directory(Path(ambient).expanduser()) as ambient_fd:
                    other = os.fstat(ambient_fd)
                    if (selected.st_dev, selected.st_ino) != (other.st_dev, other.st_ino):
                        raise ClaudeAccountRefused("claude_account_ambient_conflict")
            home = Path.home()
            for default in (home, home / ".claude"):
                try:
                    info = default.stat()
                except FileNotFoundError:
                    continue
                if (selected.st_dev, selected.st_ino) == (info.st_dev, info.st_ino):
                    raise ClaudeAccountRefused("claude_account_binding_is_default")
            if _claude_config_account_uuid(home / ".claude.json") == binding.account_uuid:
                raise ClaudeAccountRefused("claude_account_binding_is_default")
            if _claude_config_account_uuid(Path(".claude.json"), dir_fd=directory) != binding.account_uuid:
                raise ClaudeAccountRefused("claude_account_unverified")
            _refuse_claude_settings_credential_source(directory)
            try:
                token = _claude_access_token(Path(".credentials.json"), dir_fd=directory)
            except ReviewIsolationError as exc:
                suffix = str(exc).removeprefix("attempt_claude_auth_")
                raise ClaudeAccountRefused(f"claude_account_credentials_{suffix}") from None
            if token is None:
                raise ClaudeAccountRefused("claude_account_credentials_missing")
            if _claude_selected_identity(token) != binding.account_uuid:
                raise ClaudeAccountRefused("claude_account_unverified")
            return binding, token
    except (OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, ClaudeAccountRefused):
            raise
        raise ClaudeAccountRefused("claude_account_config_dir_unavailable") from None


def verify_claude_account(label: str, *, environ: Mapping[str, str] | None = None) -> ClaudeAccountBinding | None:
    """Complete preflight, including the selected state; repeat validation at use.

    The default label returns ``None`` and keeps legacy selection unchanged.
    """
    if resolve_claude_account_label(label) == DEFAULT_CLAUDE_ACCOUNT:
        return None
    binding, _ = _validated_claude_selection(label, environ=environ)
    return binding


def _claude_access_token(path: Path, *, dir_fd: int | None = None) -> str | None:
    """A fresh access token from a Claude credentials file; ``None`` when absent."""
    from scripts.review.isolation import ReviewIsolationError

    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ReviewIsolationError("attempt_claude_auth_unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ReviewIsolationError("attempt_claude_auth_not_private")
        raw = os.read(fd, 65537)
        if len(raw) > 65536:
            raise ReviewIsolationError("attempt_claude_auth_oversized")
        oauth = json.loads(raw)["claudeAiOauth"]
        token, expires = oauth["accessToken"], oauth["expiresAt"]
        if not isinstance(expires, int) or isinstance(expires, bool) or expires / 1000 <= time.time() + 60:
            raise ReviewIsolationError("attempt_claude_auth_expired")
        if not isinstance(token, str) or not 20 <= len(token) <= 8192 or any(c in token for c in "\n\r\0"):
            raise ReviewIsolationError("attempt_claude_auth_invalid")
        return token
    except (ValueError, KeyError, TypeError) as exc:
        raise ReviewIsolationError("attempt_claude_auth_invalid") from exc
    finally:
        os.close(fd)


def linux_claude_auth(account: str | None = None) -> dict[str, str]:
    """Select only a fresh access token; --bare ignores file-backed login.

    The existing auth staging supports keychain selection on Darwin. Linux
    needs equivalent selection from its credential file, never a home grant,
    refresh token, login mutation or copied credential store.

    ``account`` is the run's label. The default label (or none) keeps the
    legacy selection: an ambient credential, else the default credential file.
    A non-default label reads only its verified bound account's credential
    file and refuses every conflicting source before anything is returned.
    """
    from scripts.review.isolation import ReviewIsolationError

    try:
        label = resolve_claude_account_label(account)
        if label != DEFAULT_CLAUDE_ACCOUNT:
            _, token = _validated_claude_selection(label)
            return {"CLAUDE_CODE_OAUTH_TOKEN": token}
    except ClaudeAccountRefused as exc:
        raise ReviewIsolationError(exc.code) from None
    for key in _CLAUDE_AMBIENT_AUTH_ENV:
        if value := os.environ.get(key):
            return {key: value}
    if platform.system() != "Linux":
        return {}
    token = _claude_access_token(Path.home() / ".claude" / ".credentials.json")
    return {} if token is None else {"CLAUDE_CODE_OAUTH_TOKEN": token}


def authorized_closure(manifest: dict[str, Any], root: Path) -> dict[str, bytes]:
    """All eligible manifest pins, and only those pins, verified before copying.

    `module_digest` and `upstream_lessons` are lesson inputs under the existing
    schema. A re-review additionally admits exactly previous review, previous
    ledger and diff. No file referred to by an input's contents is opened.
    """
    from scripts.build.fresh.manifest import pinned_entries
    from scripts.review.isolation import ReviewIsolationError
    from scripts.review.prompts.eligibility import pin_refusals

    if manifest.get("kind") not in {"plan", "lesson"}:
        raise ReviewIsolationError("attempt_manifest_kind")
    if pin_refusals(manifest, root):
        raise ReviewIsolationError("attempt_manifest_ineligible")
    copied: dict[str, bytes] = {}
    for location, entry in pinned_entries(manifest):
        path = root / entry["path"]
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ReviewIsolationError("attempt_input_hash_mismatch")
        # Previous receipts are projected, never exposed as a browsable store.
        destination = "authorized/previous-ledger.jsonl" if location == "previous_attempt.ledger" else entry["path"]
        if destination.startswith("batch_state/"):
            raise ReviewIsolationError("attempt_shared_state_input")
        copied[destination] = data
    return copied


class SourcesConnection:
    """Parent-only stdio backend. The seat can speak MCP but cannot browse it."""

    def __init__(self, endpoint: Path, server: dict[str, Any]):
        self.server = server
        self.endpoint = endpoint
        self.listener = socket.socket(socket.AF_UNIX)
        if platform.system() == "Linux":
            directory = os.open(endpoint.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                self.listener.bind(f"/proc/self/fd/{directory}/{endpoint.name}")
            finally:
                os.close(directory)
        else:
            self.listener.bind(str(endpoint))
        self.listener.listen()
        self.listener.settimeout(0.1)
        self.stopped = threading.Event()
        self.processes: list[subprocess.Popen] = []
        self.connections: list[socket.socket] = []
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

    def _accept(self) -> None:
        while not self.stopped.is_set():
            try:
                connection, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with self.lock:
                self.connections.append(connection)
            threading.Thread(target=self._serve, args=(connection,), daemon=True).start()

    def _serve(self, connection: socket.socket) -> None:
        proc = None
        try:
            with self.lock:
                if self.stopped.is_set():
                    return
                proc = subprocess.Popen(
                    [self.server["command"], *self.server["args"]],
                    env={**os.environ, **self.server["env"]},
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                self.processes.append(proc)

            def send() -> None:
                try:
                    while data := connection.recv(65536):
                        proc.stdin.write(data)
                        proc.stdin.flush()
                except (OSError, ValueError):
                    pass
                finally:
                    with contextlib.suppress(OSError, ValueError):
                        proc.stdin.close()

            threading.Thread(target=send, daemon=True).start()
            while data := os.read(proc.stdout.fileno(), 65536):
                connection.sendall(data)
        except OSError:
            pass
        finally:
            connection.close()
            if proc is not None:
                with contextlib.suppress(OSError):
                    proc.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=5)

    def cleanup(self) -> None:
        self.stopped.set()
        self.listener.close()
        self.thread.join(timeout=1)
        with self.lock:
            for connection in self.connections:
                with contextlib.suppress(OSError):
                    connection.shutdown(socket.SHUT_RDWR)
                connection.close()
            processes = list(self.processes)
        for proc in processes:
            if proc.poll() is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)


def runtime_files(binary: Path) -> list[Path]:
    """Exact native binary, or its installed Node package and dependencies.

    Never grant a native executable's parent (which may be the user's bin).
    Python's dedicated installation is needed by the byte-only MCP proxy.
    """
    from scripts.review.isolation import ReviewIsolationError

    executable = binary.resolve(strict=True)
    roots = [executable]
    with executable.open("rb") as handle:
        first = handle.readline(256)
    if first.startswith(b"#!"):
        if b"node" not in first:
            raise ReviewIsolationError("attempt_unsupported_script_runtime")
        node = shutil.which("node")
        if not node:
            raise ReviewIsolationError("attempt_node_unavailable")
        roots.append(Path(node).resolve(strict=True))
        package = next((p for p in executable.parents if (p / "package.json").is_file()), None)
        if package is None:
            raise ReviewIsolationError("attempt_node_package_unknown")
        roots.append(package)
        # Codex resolves an architecture-specific sibling package.
        if package.name == "codex" and package.parent.name == "@openai":
            roots.extend(p for p in package.parent.glob("codex-*") if (p / "package.json").is_file())
    interpreter = project_interpreter().resolve(strict=True)
    roots.extend([interpreter, interpreter.parent.parent / "lib"])
    return roots


class AttemptBoundary:
    def __init__(self, *, agent: str, tool_config: dict[str, Any]):
        from scripts.review.isolation import ReviewIsolationError, stage_engine_auth

        from .attempt_network import AttemptEgress, load_allowlist
        from .review_mcp import SUPPORTED_HARNESSES, verify_review_attempt_paths

        # Claude's adapter must land with its own eligible cross-family review
        # before formal attempts can stage credentials or launch any process.
        self.full = tool_config.get("review_access") == "full"
        if agent == "claude" and not self.full:
            raise ReviewIsolationError("attempt_boundary_claude_adapter_pending")
        if agent not in SUPPORTED_HARNESSES:
            raise ReviewIsolationError("attempt_harness_unsupported")
        config = Path(tool_config["mcp_config_path"])
        verify_review_attempt_paths(config)
        self.config_path = config
        server = json.loads(config.read_bytes())["mcpServers"]["sources"]
        access = "full" if self.full else "isolated"
        if server["env"].get("LU_REVIEW_ACCESS") != access:
            raise ReviewIsolationError("attempt_review_access_mismatch")
        manifest_path = Path(tool_config["review_manifest"])
        data = manifest_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != server["env"]["LU_REVIEW_MANIFEST_SHA256"]:
            raise ReviewIsolationError("attempt_manifest_hash_mismatch")
        if server["env"]["LU_REVIEW_ATTEMPT_ID"] != tool_config["attempt_id"]:
            raise ReviewIsolationError("attempt_identity_mismatch")
        root = Path(tool_config["review_input_root"]).resolve(strict=True)
        closure = {} if self.full else authorized_closure(yaml.safe_load(data), root)
        temporary_parent = tool_config.get("read_only_tmp_root")
        self.temp = tempfile.TemporaryDirectory(prefix="attempt-", dir=temporary_parent)
        self.connection = None
        self.egress = None
        self.agent = agent
        try:
            if platform.system() != "Linux":
                raise ReviewIsolationError(
                    "full_review_bwrap_unavailable" if self.full else "attempt_network_namespace_unavailable"
                )
            base = Path(self.temp.name).resolve()
            self.workspace = Path(tool_config["review_cwd"]).resolve(strict=True) if self.full else base / "inputs"
            self.write_root = base / "runtime"
            if not self.full:
                self.workspace.mkdir(mode=0o700)
            self.write_root.mkdir(mode=0o700)
            for name, content in closure.items():
                destination = self.workspace / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            home = self.write_root / "home"
            (self.write_root / "tmp").mkdir()
            self.env = build_agent_env(provider=agent)
            home.mkdir()
            if agent != "agy":
                self.env.update(stage_engine_auth(agent, write_home=home))
            if agent == "claude":
                self.env.update(linux_claude_auth(tool_config.get(CLAUDE_ACCOUNT_KEY)))
            self.env.update(HOME=str(home), TMPDIR=str(self.write_root / "tmp"))
            # Native CLI shell discovery calls getpwuid. Supply only this
            # namespace's account, never the host's passwd/group databases.
            self.passwd = self.write_root / "passwd"
            self.group = self.write_root / "group"
            self.passwd.write_text(f"review:x:{os.getuid()}:{os.getgid()}:Review seat:{home}:/bin/bash\n")
            self.group.write_text(f"review:x:{os.getgid()}:\n")
            self.env.update(USER="review", LOGNAME="review", SHELL="/bin/bash")
            self.env.pop("GIT_DIR", None)
            self.env.pop("GIT_WORK_TREE", None)
            proxy = self.write_root / "stdio.py"
            proxy.write_bytes(Path(__file__).with_name("attempt_proxy.py").read_bytes())
            endpoint = self.write_root / "sources.sock"
            self.endpoint = endpoint
            self.connection = SourcesConnection(endpoint, server)
            self.egress_endpoint = self.write_root / "egress.sock"
            self.egress = AttemptEgress(self.egress_endpoint, load_allowlist(agent))
            self.forwarder = self.write_root / "forwarder.py"
            self.forwarder.write_bytes(Path(__file__).with_name("attempt_forwarder.py").read_bytes())
            proxy_server = {
                "command": str(project_interpreter().resolve(strict=True)),
                "args": [str(proxy), str(endpoint)],
            }
            proxy_config = self.write_root / "mcp.json"
            proxy_config.write_text(json.dumps({"mcpServers": {"sources": proxy_server}}))
            self.tool_config = {
                **tool_config,
                "mcp_config_path": str(proxy_config),
                "review_write_root": str(self.write_root),
                "review_attempt_boundary": self,
            }
            self.tool_config.pop("read_only_tmp_root", None)
            if agent == "codex":
                from .review_mcp import _render_codex_review_config

                codex_home = home / ".codex"
                (codex_home / "config.toml").write_text(
                    _render_codex_review_config(Path(proxy_server["command"]), proxy, {}).replace(
                        f'args = ["{proxy}"]', f'args = ["{proxy}", "{endpoint}"]'
                    )
                )
                self.tool_config["codex_home_override"] = str(codex_home)
                self.tool_config["attempt_os_sandbox"] = True
            elif agent == "agy":
                from .agy_hook_config import GUARD_NAME, guard_registration
                from .review_mcp import (
                    _create_file,
                    _open_owned_dir,
                    _real_agy_token,
                    agy_review_mcp_config_path,
                    agy_review_settings,
                )

                target = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(_real_agy_token(), target)
                target.chmod(0o600)
                mcp = agy_review_mcp_config_path(home)
                mcp.parent.mkdir(parents=True, exist_ok=True)
                mcp.write_bytes(proxy_config.read_bytes())
                home_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                gemini_fd = config_fd = None
                try:
                    gemini_fd = _open_owned_dir(".gemini", dir_fd=home_fd)
                    config_fd = _open_owned_dir("config", dir_fd=gemini_fd)
                    _create_file("hooks.json", config_fd, json.dumps({GUARD_NAME: guard_registration()}).encode())
                finally:
                    for descriptor in (config_fd, gemini_fd, home_fd):
                        if descriptor is not None:
                            os.close(descriptor)
                settings = target.parent / "settings.json"
                fd = os.open(settings, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "w") as handle:
                    handle.write(json.dumps(agy_review_settings(access, checkout_root=self.workspace)))
                self.tool_config["agy_home_override"] = str(home)
                self.env["AGY_APP_DATA_DIR"] = str(target.parent)
            else:
                if not self.full:
                    self.tool_config["allowed_tools"] = "Read,Glob,Grep," + str(tool_config.get("allowed_tools", ""))
        except BaseException:
            self.cleanup()
            raise

    def wrap(self, cmd: list[str], env_overrides: dict[str, str]) -> tuple[list[str], dict[str, str]]:
        from scripts.review.isolation import ReviewIsolationError, prepare_host_sandbox, wrap_argv_with_sandbox

        binary = Path(shutil.which(cmd[0]) or cmd[0]).resolve(strict=True)
        runtime = runtime_files(binary)
        reject = Path(self.tool_config["review_input_root"]).resolve()
        if not self.full and any(p.is_relative_to(reject) or reject.is_relative_to(p) for p in runtime):
            raise ReviewIsolationError("attempt_runtime_overlaps_repository")
        full_reads, hidden = full_review_reads(self.workspace) if self.full else ([], [])
        self.sandbox = prepare_host_sandbox(
            engine=self.agent,
            snapshot_root=self.workspace,
            write_root=self.write_root,
            reject_root=Path(self.tool_config["review_input_root"]),
            runtime_reads=[*runtime, *full_reads, self.endpoint],
            network_allowed=False,
        )
        if self.egress is None or not self.egress.thread.is_alive():
            raise ReviewIsolationError("attempt_egress_unavailable")
        argv = [
            str(project_interpreter().resolve(strict=True)),
            str(self.forwarder),
            str(self.egress_endpoint),
            str(binary),
            *cmd[1:],
        ]
        env = {**self.env, **env_overrides}
        env["HOME"] = self.env["HOME"]
        env["TMPDIR"] = self.env["TMPDIR"]
        env["PATH"] = "/usr/bin:/bin:" + str(binary.parent)
        for name in list(env):
            if name.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}:
                env.pop(name)
        wrapped = wrap_argv_with_sandbox(argv, self.sandbox)
        if self.sandbox.mechanism == "linux-bwrap":
            # A private procfs supports native executable discovery without
            # exposing host processes, descriptors, cwd or environment.
            masks = [argument for path in hidden for argument in ("--tmpfs", str(path), "--remount-ro", str(path))]
            wrapped[-len(argv) : -len(argv)] = [
                *masks,
                "--ro-bind",
                str(self.passwd),
                "/etc/passwd",
                "--ro-bind",
                str(self.group),
                "/etc/group",
                "--cap-drop",
                "ALL",
                "--proc",
                "/proc",
                "--chdir",
                str(self.workspace),
            ]
        return wrapped, env

    def verify_seat(self, cmd: list[str], env_overrides: dict[str, str]) -> None:
        """Probe CLI compatibility and effective MCP inside the full OS boundary."""
        if not self.full:
            return
        from scripts.review.isolation import CLAUDE_MIN_SUPPORTED_CLI_VERSION, ReviewIsolationError

        from .review_mcp import _config_flags, verify_agy_review_effective_mcp, verify_codex_review_effective_mcp

        if self.agent == "codex":
            verify_codex_review_effective_mcp(
                config_path=self.config_path,
                cwd=self.workspace,
                codex_bin=cmd[0],
                config_flags=_config_flags(cmd),
                boundary=self,
            )
            return
        version_cmd, env = self.wrap([cmd[0], "--version"], env_overrides)
        version = subprocess.run(version_cmd, env=env, capture_output=True, text=True, timeout=5, check=False)
        if self.agent == "claude":
            from scripts.utils.claude_version import _parse_claude_semver

            parsed = _parse_claude_semver(version.stdout + version.stderr)
            if version.returncode != 0 or parsed is None or parsed < CLAUDE_MIN_SUPPORTED_CLI_VERSION:
                raise ReviewIsolationError("full_review_claude_version_unverified")
        else:
            from .adapters.agy import _AGY_MIN_BACKGROUND_WAIT_VERSION, _AGY_VERSION_RE

            match = _AGY_VERSION_RE.search(version.stdout)
            parsed = tuple(int(match.group(name)) for name in ("major", "minor", "patch")) if match else None
            if version.returncode != 0 or parsed is None or parsed < _AGY_MIN_BACKGROUND_WAIT_VERSION:
                raise ReviewIsolationError("full_review_agy_version_unverified")
            verify_agy_review_effective_mcp(
                config_path=self.config_path,
                cwd=self.workspace,
                env=env,
                agy_bin=cmd[0],
                boundary=self,
            )

    def cleanup(self) -> None:
        try:
            if self.egress is not None:
                self.egress.cleanup()
        finally:
            try:
                if self.connection is not None:
                    self.connection.cleanup()
            finally:
                self.temp.cleanup()


def verify_full_review_tree(manifest_path: Path, cwd: Path) -> None:
    """Verify the actual full checkout against every manifest pin before launch.

    A separate review tree is allowed only when its pinned bytes match. Other
    repository files are context, never evidence without a sources receipt.
    """
    from scripts.build.fresh.manifest import pinned_entries
    from scripts.review.isolation import ReviewIsolationError
    from scripts.review.prompts.eligibility import pin_refusals

    try:
        manifest = yaml.safe_load(manifest_path.read_bytes())
        for _, entry in pinned_entries(manifest):
            data = safe_read_attempt_file(cwd / entry["path"], trusted_root=cwd)
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ReviewIsolationError("full_review_tree_mismatch")
        if pin_refusals(manifest, cwd):
            raise ReviewIsolationError("full_review_manifest_ineligible")
        checkout = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=30, check=False
        )
        if checkout.returncode or Path(checkout.stdout.strip()).resolve() != cwd.resolve():
            raise ReviewIsolationError("full_review_checkout_missing")
        sparse = subprocess.run(
            ["git", "config", "--bool", "core.sparseCheckout"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if sparse.returncode not in (0, 1) or sparse.stdout.strip() == "true":
            raise ReviewIsolationError("full_review_requires_full_checkout")
    except (OSError, ValueError, AttemptReadError, subprocess.SubprocessError) as exc:
        raise ReviewIsolationError("full_review_tree_mismatch") from exc


def full_review_reads(workspace: Path) -> tuple[list[Path], list[Path]]:
    """Exact linked-worktree Git context and corpus, never the owning checkout.

    Git follows the checkout's .git file to its own metadata and the shared
    objects/refs. Do not grant the shared metadata's other worktrees or its
    checkout. Host task/receipt stores and nested checkouts are masked even
    when present in the reviewed tree. External object alternates are refused.
    """
    from scripts.review.isolation import ReviewIsolationError

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise ReviewIsolationError("full_review_git_context_unavailable")
        git_dir, common = (Path(p).resolve(strict=True) for p in result.stdout.splitlines())
        alternates = common / "objects/info/alternates"
        if alternates.exists() and alternates.read_bytes().strip():
            raise ReviewIsolationError("full_review_git_alternates_unsupported")
        reads = []
        if not git_dir.is_relative_to(workspace):
            reads.append(git_dir)
        if not common.is_relative_to(workspace):
            reads.extend(
                path
                for name in ("objects", "refs", "packed-refs", "config", "shallow")
                if (path := common / name).exists()
            )
        # Corpus can be absent in a fixture; linked checkouts normally share it.
        corpus = common.parent / "data"
        if common.name == ".git" and corpus.is_dir() and not corpus.is_relative_to(workspace):
            reads.append(corpus.resolve(strict=True))
        hidden = [
            p for p in (workspace / "batch_state", workspace / ".worktrees", workspace / ".git/worktrees") if p.is_dir()
        ]
        for root in (workspace, *reads):
            if root.is_dir():
                for directory, subdirs, files in os.walk(root, followlinks=False):
                    subdirs[:] = [name for name in subdirs if Path(directory) / name not in hidden]
                    for name in (*subdirs, *files):
                        mode = (Path(directory) / name).lstat().st_mode
                        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode) or stat.S_ISLNK(mode)):
                            raise ReviewIsolationError("full_review_special_file_refused")
        return reads, hidden
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ReviewIsolationError("full_review_git_context_unavailable") from exc


def prepare_attempt_boundary(agent: str, mode: str, session_id: str | None, tool_config: dict | None):
    """Use the isolated boundary with only a wider read set for full attempts."""
    tc = tool_config or {}
    if not (tc.get("review_id") or tc.get("attempt_id")):
        return None
    from scripts.review.isolation import ReviewIsolationError

    required = ("review_id", "attempt_id", "review_manifest", "review_input_root", "mcp_config_path")
    if mode != "read-only" or session_id is not None or not tc.get("strict_mcp_config"):
        raise ReviewIsolationError("attempt_requires_fresh_read_only_sources")
    if any(not tc.get(key) for key in required):
        raise ReviewIsolationError("attempt_boundary_inputs_missing")
    access = tc.get("review_access", "isolated")  # legacy runtime callers remain isolated
    if access == "isolated":
        return AttemptBoundary(agent=agent, tool_config=tc)
    if access != "full":
        raise ReviewIsolationError("review_access_invalid")
    from .review_mcp import SUPPORTED_HARNESSES, verify_review_attempt_paths

    if agent not in SUPPORTED_HARNESSES:
        raise ReviewIsolationError("full_review_harness_unsupported")
    if any(tc.get(key) for key in ("review_isolation", "attempt_os_sandbox", "review_attempt_boundary")):
        raise ReviewIsolationError("full_review_write_denial_conflict")
    config = Path(tc["mcp_config_path"])
    verify_review_attempt_paths(config)
    server = json.loads(config.read_bytes())["mcpServers"]["sources"]
    if (
        hashlib.sha256(Path(tc["review_manifest"]).read_bytes()).hexdigest()
        != server["env"]["LU_REVIEW_MANIFEST_SHA256"]
    ):
        raise ReviewIsolationError("attempt_manifest_hash_mismatch")
    if server["env"]["LU_REVIEW_ATTEMPT_ID"] != tc["attempt_id"]:
        raise ReviewIsolationError("attempt_identity_mismatch")
    if not tc.get("review_cwd"):
        raise ReviewIsolationError("full_review_cwd_missing")
    if agent == "claude" and (not tc.get("reviewer_tools") or tc.get("allowed_tools")):
        raise ReviewIsolationError("full_review_write_denial_missing")
    verify_full_review_tree(Path(tc["review_manifest"]), Path(tc["review_cwd"]))
    return AttemptBoundary(agent=agent, tool_config=tc)
