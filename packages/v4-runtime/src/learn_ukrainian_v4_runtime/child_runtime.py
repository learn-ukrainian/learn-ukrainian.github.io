"""Fixed bwrap child plan, bounded capture and parsing owned by the API parent.

The profile is an immutable reviewed release resource. No invocation accepts
argv, executable, model, MCP configuration, environment or parser overrides.
Only installed adapters whose complete runtime closure is pinned are eligible.
"""

from __future__ import annotations

import base64
import ctypes
import fcntl
import json
import os
import re
import selectors
import signal
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, canonical_bytes, digest
from learn_ukrainian_v4_runtime.resources import resource_root

MAX_CAPTURE_BYTES = 1048576
# Versioned reviewed public release; historical v1 is never an active profile.
PRODUCTION_CHILD_PROFILE_SHA256 = "462d73fefcc49a22776d4f2fe071146e7759f2184779d2ecc1325302f1a81088"
# Required native network data only; no directory or arbitrary /etc mount.
_NETWORK_DATA_TARGETS = frozenset({"/etc/resolv.conf", "/etc/ssl/certs/ca-certificates.crt"})
MAX_CREDENTIAL_BYTES = 65536
CREDENTIAL_SCHEMA = "hramatka-v4-provider-credential.v1"
CODEX_AUTH_DESTINATION = "/home/v4/.codex/auth.json"
# Linux UAPI values also support CPython builds made against older headers.
_F_ADD_SEALS = 1033
_AUTH_SEALS = 0x0001 | 0x0002 | 0x0004 | 0x0008


def _credential_json(raw: bytes) -> dict:
    def invalid_constant(_):
        raise ValueError

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        if not 0 < len(raw) <= MAX_CREDENTIAL_BYTES:
            raise ValueError
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid_constant)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeError, RecursionError):
        # Parser exceptions can contain credential bytes. Never chain them.
        raise OperationRefused("provider_credential_schema") from None


def _token(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 16384 or any(not 33 <= ord(char) <= 126 for char in value):
        raise OperationRefused("provider_credential_token")


def _fresh(expiry: int) -> None:
    if type(expiry) is not int or not time.time() + 60 < expiry < 253402300800:
        raise OperationRefused("provider_credential_expired")


@dataclass(frozen=True)
class ProviderCredential:
    """Parent-only value; never serialize into evidence or a canonical digest."""

    harness: str
    mode: str
    value: str = field(repr=False)
    expires_at: int | None = field(default=None, repr=False)


def credential_mode(profile: dict, harness: str) -> str:
    if harness not in ("claude", "codex") or harness not in profile["adapters"]:
        raise OperationRefused("adapter_separability_unqualified")
    adapter = profile["adapters"][harness]
    keys = {"version", "models", "files", "executable", "provider_env"}
    if not isinstance(adapter, dict) or set(adapter) not in (keys, keys | {"credential_mode"}):
        raise OperationRefused("adapter_model_unqualified")
    # The old exact provider_env profile explicitly qualifies API-key transport.
    # Only a reviewed profile with an explicit mode can qualify subscriptions.
    mode = adapter.get("credential_mode", "api_key")
    expected = {
        ("claude", "api_key"): "ANTHROPIC_API_KEY",
        ("codex", "api_key"): "OPENAI_API_KEY",
        ("claude", "subscription"): "CLAUDE_CODE_OAUTH_TOKEN",
        ("codex", "subscription"): None,
    }
    if (
        not isinstance(mode, str)
        or (harness, mode) not in expected
        or adapter["provider_env"] != expected[harness, mode]
    ):
        raise OperationRefused("provider_credential_scope")
    return mode


def _codex_auth(raw: str) -> dict:
    try:
        auth = _credential_json(raw.encode("utf-8"))
        if (
            not {"auth_mode", "tokens"} <= set(auth)
            or not set(auth) <= {"auth_mode", "OPENAI_API_KEY", "tokens", "last_refresh"}
            or auth["auth_mode"] != "chatgpt"
            or auth.get("OPENAI_API_KEY") is not None
            or not isinstance(auth["tokens"], dict)
            or set(auth["tokens"]) != {"id_token", "access_token", "refresh_token", "account_id"}
        ):
            raise ValueError
        for token in auth["tokens"].values():
            _token(token)
        for name in ("access_token", "id_token"):
            parts = auth["tokens"][name].split(".")
            if len(parts) != 3 or any(not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in parts):
                raise ValueError
            decoded = [base64.b64decode(part + "=" * (-len(part) % 4), altchars=b"-_", validate=True) for part in parts]
            header = _credential_json(decoded[0])
            if header.get("alg") != "RS256" or header.get("typ", "JWT") != "JWT" or not decoded[2]:
                raise ValueError
            expiry = _credential_json(decoded[1]).get("exp")
            if type(expiry) is not int or not 0 < expiry < 253402300800:
                raise ValueError
            # The access token authenticates native API calls. Cached ID tokens
            # can outlive their identity-token expiry while access stays fresh.
            # Neither check is signature/provider verification.
            if name == "access_token":
                _fresh(expiry)
        if "last_refresh" in auth:
            refreshed = datetime.fromisoformat(auth["last_refresh"].replace("Z", "+00:00"))
            if refreshed.tzinfo is None or not 0 < refreshed.timestamp() <= time.time():
                raise ValueError
        return auth
    except (ValueError, TypeError, AttributeError, UnicodeError, OverflowError):
        raise OperationRefused("provider_credential_auth_json") from None


def _validate_credential(credential: ProviderCredential, harness: str, mode: str) -> tuple[bytes, ...]:
    if not isinstance(credential, ProviderCredential) or (credential.harness, credential.mode) != (harness, mode):
        raise OperationRefused("provider_credential_mismatch")
    if mode == "subscription":
        _fresh(credential.expires_at)
        if harness == "codex":
            auth = _codex_auth(credential.value)
            return (credential.value.encode(), *(value.encode() for value in auth["tokens"].values()))
    elif credential.expires_at is not None:
        raise OperationRefused("provider_credential_schema")
    _token(credential.value)
    return (credential.value.encode(),)


def parse_provider_credential(raw: bytes, *, harness: str, mode: str) -> ProviderCredential:
    if harness not in ("codex", "claude") or mode not in ("api_key", "subscription"):
        raise OperationRefused("provider_credential_mismatch")
    payload = _credential_json(raw)
    if mode == "api_key" and set(payload) == {"credential"}:
        credential = ProviderCredential(harness, mode, payload["credential"])
    else:
        value_key = (
            "auth_json"
            if (harness, mode) == ("codex", "subscription")
            else ("access_token" if mode == "subscription" else "credential")
        )
        keys = {"schema", "harness", "mode", value_key}
        if mode == "subscription":
            keys.add("expires_at")
        if (
            set(payload) != keys
            or payload.get("schema") != CREDENTIAL_SCHEMA
            or payload.get("harness") != harness
            or payload.get("mode") != mode
        ):
            raise OperationRefused("provider_credential_schema")
        credential = ProviderCredential(harness, mode, payload[value_key], payload.get("expires_at"))
    _validate_credential(credential, harness, mode)
    return credential


def _sealed_auth_fd(raw: bytes) -> int:
    try:
        create = ctypes.CDLL(None, use_errno=True).memfd_create
    except AttributeError:
        raise OperationRefused("credential_memfd_unavailable") from None
    create.argtypes = (ctypes.c_char_p, ctypes.c_uint)
    create.restype = ctypes.c_int
    # MFD_CLOEXEC | MFD_ALLOW_SEALING; never a named-file fallback.
    fd = create(b"v4-provider-auth", 0x0001 | 0x0002)
    if fd < 0:
        raise OperationRefused("credential_memfd_unavailable")
    try:
        pending = memoryview(raw)
        while pending:
            sent = os.write(fd, pending)
            if sent <= 0:
                raise OSError("credential write failed")
            pending = pending[sent:]
        os.lseek(fd, 0, os.SEEK_SET)
        os.fchmod(fd, 0o400)
        fcntl.fcntl(fd, _F_ADD_SEALS, _AUTH_SEALS)
        return fd
    except BaseException:
        os.close(fd)
        raise


def profile_path() -> Path:
    return resource_root() / "data/projects/open_model_data/trust/v4_child_profile_v3.json"


def load_profile() -> dict:
    raw = profile_path().read_bytes()
    if digest(raw) != PRODUCTION_CHILD_PROFILE_SHA256:
        raise OperationRefused("runtime_profile_digest")
    profile = json.loads(raw)
    if (
        set(profile) != {"schema", "bwrap", "bwrap_sha256", "sources_url", "adapters"}
        or profile["schema"] != "hramatka-v4-child-profile.v1"
    ):
        raise OperationRefused("runtime_profile")
    return profile


def _verified_file(path: str, expected: str) -> Path:
    file = Path(path)
    if not file.is_absolute() or not file.is_file() or file.is_symlink() or digest(file.read_bytes()) != expected:
        raise OperationRefused("runtime_closure_digest")
    if file.stat().st_mode & 0o022:
        raise OperationRefused("runtime_closure_writable")
    return file


@dataclass(frozen=True)
class CapturedChild:
    request_id: str
    attempt_id: str
    argv_sha256: str
    prompt_sha256: str
    stdout: bytes
    stderr: bytes
    returncode: int
    harness: str


_CODEX_TOOLS = frozenset({"verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form"})


def _codex_requests(binding: dict, prompt: str = "<canonical-prompt>", thread_id: str = "<thread-id>") -> list[dict]:
    """Fixed stdin protocol, also committed by the transport digest."""
    return [
        {"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "v4-execution", "version": "1"},
            "capabilities": {"experimentalApi": False},
        }},
        {"method": "initialized", "params": {}},
        {"id": 2, "method": "thread/start", "params": {
            "model": binding["expected_seat_or_model"], "modelProvider": "openai",
            "approvalPolicy": "never", "sandbox": "read-only", "cwd": "/work", "ephemeral": True,
        }},
        {"id": 3, "method": "mcpServerStatus/list", "params": {"threadId": thread_id, "limit": 32}},
        {"id": 4, "method": "turn/start", "params": {
            "threadId": thread_id, "input": [{"type": "text", "text": prompt}],
        }},
    ]


class _CodexProtocol:
    """Correlate unmodified server evidence; never synthesize a model event."""

    def __init__(self, binding: dict, prompt: str = "<canonical-prompt>"):
        self.binding = binding
        self.prompt = prompt
        self.thread_id = None
        self.model = None
        self.turn_id = None
        self.threads: set[str] = set()
        self.turns: set[str] = set()
        self.response_id = 0
        self.remote_disabled = False
        self.completed = False
        self.finished = False
        self.refused = False
        self.messages: list[str] = []
        self.message_ids: set[str] = set()
        self.buffer = bytearray()

    @staticmethod
    def _frames(messages: list[dict]) -> bytes:
        return b"".join(canonical_bytes(message) + b"\n" for message in messages)

    def initial(self) -> bytes:
        return self._frames(_codex_requests(self.binding)[:1])

    @staticmethod
    def _identifier(value) -> str:
        if not isinstance(value, str) or not value or len(value) > 256:
            raise OperationRefused("child_identity_or_terminal_unproved")
        return value

    def _same_ids(self) -> None:
        if (len(self.threads) > 1 or len(self.turns) > 1
                or (self.thread_id is not None and self.threads != {self.thread_id})
                or (self.turn_id is not None and self.turns != {self.turn_id})):
            raise OperationRefused("child_identity_or_terminal_unproved")

    def event(self, event: dict) -> bytes:
        if not isinstance(event, dict):
            raise OperationRefused("child_event_invalid")
        if "id" in event and "method" in event:
            # No approval, user-input, dynamic tool or credential request may
            # broaden the child. Send only a protocol rejection, then close.
            request_id = event["id"]
            if not (type(request_id) is int or
                    (isinstance(request_id, str) and 0 < len(request_id) <= 256)):
                raise OperationRefused("child_event_invalid")
            self.refused = self.finished = True
            return self._frames([{"id": request_id, "error": {
                "code": -32601, "message": "Client requests are disabled",
            }}])
        if "id" in event:
            identifier = event["id"]
            if (type(identifier) is not int or identifier != self.response_id + 1
                    or identifier not in (1, 2, 3, 4) or not isinstance(event.get("result"), dict)
                    or "error" in event or self.finished):
                raise OperationRefused("child_identity_or_terminal_unproved")
            self.response_id = identifier
            result = event["result"]
            if identifier == 1:
                return self._frames(_codex_requests(self.binding)[1:3])
            if identifier == 2:
                if (result.get("model") != self.binding["expected_seat_or_model"]
                        or result.get("modelProvider") != "openai"
                        or result.get("approvalPolicy") != "never" or result.get("cwd") != "/work"
                        or not isinstance(result.get("sandbox"), dict)
                        or result["sandbox"].get("type") != "readOnly"
                        or not isinstance(result.get("thread"), dict)):
                    raise OperationRefused("child_identity_or_terminal_unproved")
                self.model = result["model"]
                self.thread_id = self._identifier(result["thread"].get("id"))
                self.threads.add(self.thread_id)
                self._same_ids()
                return self._frames(_codex_requests(self.binding, thread_id=self.thread_id)[3:4])
            if identifier == 3:
                servers = result.get("data")
                if (not isinstance(servers, list) or len(servers) != 1
                        or not isinstance(servers[0], dict) or servers[0].get("name") != "sources"
                        or not isinstance(servers[0].get("tools"), dict)
                        or set(servers[0]["tools"]) != _CODEX_TOOLS or result.get("nextCursor") is not None):
                    raise OperationRefused("child_sources_tools_unavailable")
                if not self.remote_disabled:
                    raise OperationRefused("child_identity_or_terminal_unproved")
                return self._frames(_codex_requests(self.binding, self.prompt, self.thread_id)[4:])
            turn = result.get("turn")
            if not isinstance(turn, dict):
                raise OperationRefused("child_identity_or_terminal_unproved")
            self.turn_id = self._identifier(turn.get("id"))
            self.turns.add(self.turn_id)
            self._same_ids()
            return b""
        method, params = event.get("method"), event.get("params")
        if not isinstance(method, str) or not isinstance(params, dict):
            raise OperationRefused("child_event_invalid")
        if method == "warning" and str(params.get("message", "")).startswith("Code Mode is unavailable"):
            raise OperationRefused("child_sources_tools_unavailable")
        if method in ("error", "model/rerouted"):
            raise OperationRefused("child_identity_or_terminal_unproved")
        if method == "remoteControl/status/changed":
            if params.get("status") != "disabled":
                raise OperationRefused("child_identity_or_terminal_unproved")
            self.remote_disabled = True
        if "threadId" in params:
            self.threads.add(self._identifier(params["threadId"]))
        if "turnId" in params:
            self.turns.add(self._identifier(params["turnId"]))
        if method == "thread/started":
            thread = params.get("thread")
            if not isinstance(thread, dict):
                raise OperationRefused("child_identity_or_terminal_unproved")
            self.threads.add(self._identifier(thread.get("id")))
        if method in ("turn/started", "turn/completed"):
            turn = params.get("turn")
            if not isinstance(turn, dict) or "threadId" not in params or self.response_id < 3:
                raise OperationRefused("child_identity_or_terminal_unproved")
            self.turns.add(self._identifier(turn.get("id")))
            if method == "turn/completed":
                if (self.completed or self.response_id != 4 or turn.get("status") != "completed"
                        or turn.get("error") is not None):
                    raise OperationRefused("child_identity_or_terminal_unproved")
                self.completed = self.finished = True
        self._same_ids()
        if method == "item/completed":
            item = params.get("item")
            if (self.completed or self.response_id < 3 or not isinstance(item, dict)
                    or "threadId" not in params or "turnId" not in params):
                raise OperationRefused("child_identity_or_terminal_unproved")
            if item.get("type") == "agentMessage":
                identifier = self._identifier(item.get("id"))
                if identifier in self.message_ids or not isinstance(item.get("text"), str):
                    raise OperationRefused("child_identity_or_terminal_unproved")
                self.message_ids.add(identifier)
                self.messages.append(item["text"])
        # ModelVerification in this pinned protocol concerns trusted cyber
        # access, not model identity. It is neither required nor an attestation.
        return b""

    def feed(self, chunk: bytes) -> bytes:
        self.buffer.extend(chunk)
        outgoing = bytearray()
        while b"\n" in self.buffer:
            line, _, rest = self.buffer.partition(b"\n")
            self.buffer = bytearray(rest)
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except (UnicodeError, ValueError):
                raise OperationRefused("child_capture_invalid") from None
            outgoing.extend(self.event(event))
        return bytes(outgoing)

    def result(self) -> dict:
        if (self.buffer.strip() or self.refused or not self.completed or self.response_id != 4
                or not self.remote_disabled or not self.messages):
            raise OperationRefused("child_identity_or_terminal_unproved")
        self._same_ids()
        return {"model": self.model,
                "session_id": self.thread_id, "response": "\n".join(self.messages)}


def _plan(
    profile: dict, claim: dict, provider_credential: ProviderCredential | str
) -> tuple[list[str], dict[str, str]]:
    binding = claim["binding"]
    harness = binding["expected_harness"]
    mode = credential_mode(profile, harness)
    adapter = profile["adapters"][harness]
    if binding["expected_seat_or_model"] not in adapter["models"]:
        raise OperationRefused("adapter_model_unqualified")
    if isinstance(provider_credential, str) and mode == "api_key":
        provider_credential = ProviderCredential(harness, mode, provider_credential)
    _validate_credential(provider_credential, harness, mode)
    binary = _verified_file(profile["bwrap"], profile["bwrap_sha256"])
    cmd = [
        str(binary),
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup",
        "--new-session",
        "--die-with-parent",
        "--tmpfs",
        "/",
        "--dir",
        "/runtime",
        "--dir",
        "/home",
        "--tmpfs",
        "/home/v4",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/work",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
    ]
    destinations = set()
    for entry in adapter["files"]:
        if set(entry) != {"source", "destination", "sha256"}:
            raise OperationRefused("runtime_closure_keys")
        path = _verified_file(entry["source"], entry["sha256"])
        target = Path(entry["destination"])
        if (
            not target.is_absolute()
            or ".." in target.parts
            or str(target) in destinations
            or (target.parts[1] not in ("runtime", "lib", "lib64", "usr") and str(target) not in _NETWORK_DATA_TARGETS)
            or target.name in ("sh", "bash", "dash", "zsh", "psql", "sudo", "env", "bwrap")
        ):
            raise OperationRefused("runtime_closure_mount")
        destinations.add(str(target))
        for parent in reversed(target.parents):
            if parent != Path("/"):
                cmd.extend(["--dir", str(parent)])
        cmd.extend(["--ro-bind", str(path), str(target)])
    if adapter["executable"] not in destinations:
        raise OperationRefused("adapter_executable_unpinned")
    if harness == "codex" and "/runtime/codex-code-mode-host" not in destinations:
        raise OperationRefused("adapter_tool_runner_unpinned")
    env = {
        "HOME": "/home/v4",
        "TMPDIR": "/tmp",
        "PATH": "/runtime",
        "LANG": "C.UTF-8",
        "V4_SOURCES_ATTEMPT_CAPABILITY": claim["capability_token"],
    }
    if adapter["provider_env"] is not None:
        env[adapter["provider_env"]] = provider_credential.value
    try:
        effort = {"author": "medium", "reviewer": "high"}[binding["role"]]
    except KeyError as exc:
        raise OperationRefused("operation_role") from exc
    model = binding["expected_seat_or_model"]
    url = profile["sources_url"]
    if harness == "claude":
        mcp = canonical_bytes(
            {
                "mcpServers": {
                    "sources": {
                        "type": "http",
                        "url": url,
                        "headers": {"Authorization": "Bearer ${V4_SOURCES_ATTEMPT_CAPABILITY}"},
                    }
                }
            }
        ).decode()
        argv = [
            adapter["executable"],
            "--print",
            "--verbose",
            "--output-format",
            "stream-json",
            "--model",
            model,
            "--effort",
            effort,
            "--setting-sources",
            "",
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            mcp,
            "--allowedTools",
            "mcp__sources__verify_word,mcp__sources__verify_words,mcp__sources__verify_lemma,mcp__sources__verify_stress,mcp__sources__check_modern_form",
        ]
    else:
        env["CODEX_HOME"] = "/home/v4/.codex"
        cmd.extend(["--dir", env["CODEX_HOME"]])
        argv = [
            adapter["executable"],
            "app-server",
            "--listen",
            "stdio://",
            "-c",
            "model_reasoning_effort=" + json.dumps(effort),
            "-c",
            "features.shell_tool=false",
            "-c",
            "features.multi_agent=false",
            "-c",
            "features.apps=false",
            "-c",
            'cli_auth_credentials_store="file"',
            "-c",
            "mcp_servers.sources.url=" + json.dumps(url),
            "-c",
            'mcp_servers.sources.bearer_token_env_var="V4_SOURCES_ATTEMPT_CAPABILITY"',
            "-c",
            'mcp_servers.sources.enabled_tools=["verify_word","verify_words","verify_lemma","verify_stress","check_modern_form"]',
        ]
        # The fixed, read-only Sources operations are already authorized.
        # Unknown tools/servers and every server-to-client request still refuse.
        for tool in sorted(_CODEX_TOOLS):
            argv.extend(["-c", f'mcp_servers.sources.tools.{tool}.approval_mode="approve"'])
    cmd.extend(["--chdir", "/work", "--", *argv])
    return cmd, env


def run_child(claim: dict, *, provider_credential: ProviderCredential) -> CapturedChild:
    profile = load_profile()
    harness = claim["binding"]["expected_harness"]
    mode = credential_mode(profile, harness)
    secrets = (*_validate_credential(provider_credential, harness, mode), claim["capability_token"].encode())
    cmd, env = _plan(profile, claim, provider_credential)
    prompt = claim["prompt"].encode()
    if not prompt or len(prompt) > 65536:
        raise OperationRefused("semantic_input_size")
    if any(secret in prompt or secret in canonical_bytes(cmd) for secret in secrets):
        raise OperationRefused("child_credential_disclosure")
    # Describe the actual transport with an opaque FD placeholder, never the
    # descriptor number or any credential-derived hash.
    if (harness, mode) == ("codex", "subscription"):
        offset = cmd.index("--chdir")
        cmd[offset:offset] = ["--perms", "0400", "--ro-bind-data", "<parent-auth-fd>", CODEX_AUTH_DESTINATION]
    protocol = _CodexProtocol(claim["binding"], claim["prompt"]) if harness == "codex" else None
    transport = {"argv": cmd, "stdin_protocol": _codex_requests(claim["binding"])} if protocol else cmd
    argv_sha256 = digest(canonical_bytes(transport))
    remaining = claim["deadline_at"].timestamp() - time.time()
    if remaining <= 0:
        raise OperationRefused("execution_expired")
    deadline = time.monotonic() + min(1800, remaining)
    auth_fd = None
    try:
        if (harness, mode) == ("codex", "subscription"):
            auth_fd = _sealed_auth_fd(provider_credential.value.encode())
            cmd[cmd.index("<parent-auth-fd>")] = str(auth_fd)
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            close_fds=True,
            pass_fds=() if auth_fd is None else (auth_fd,),
            start_new_session=True,
        )
    except (OSError, ValueError):
        raise OperationRefused("child_launch_failed") from None
    finally:
        if auth_fd is not None:
            os.close(auth_fd)
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        with selectors.DefaultSelector() as selector:
            for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
            pending = memoryview(protocol.initial() if protocol else prompt)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise OperationRefused("execution_timeout")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    if key.data == "stdin":
                        try:
                            sent = os.write(key.fd, pending)
                            pending = pending[sent:]
                        except BrokenPipeError:
                            pending = memoryview(b"")
                        if not pending:
                            selector.unregister(key.fileobj)
                            if protocol is None or protocol.finished:
                                key.fileobj.close()
                    else:
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        else:
                            streams[key.data].extend(chunk)
                            if sum(map(len, streams.values())) > MAX_CAPTURE_BYTES:
                                raise OperationRefused("capture_limit")
                            if any(secret in output for secret in secrets for output in streams.values()):
                                raise OperationRefused("child_credential_disclosure")
                            if protocol is not None and key.data == "stdout":
                                outgoing = protocol.feed(chunk)
                                if outgoing:
                                    if process.stdin.closed:
                                        raise OperationRefused("child_identity_or_terminal_unproved")
                                    pending = memoryview(bytes(pending) + outgoing)
                                    if process.stdin not in selector.get_map():
                                        selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
                                elif protocol.finished and not pending and not process.stdin.closed:
                                    process.stdin.close()
            rc = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if any(secret in output for secret in secrets for output in streams.values()):
            raise OperationRefused("child_credential_disclosure")
        return CapturedChild(
            claim["request_id"],
            claim["attempt_id"],
            argv_sha256,
            digest(prompt),
            bytes(streams["stdout"]),
            bytes(streams["stderr"]),
            rc,
            claim["binding"]["expected_harness"],
        )
    except subprocess.TimeoutExpired:
        raise OperationRefused("execution_timeout") from None
    finally:
        if process.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream and not stream.closed:
                stream.close()


def parse_child(capture: CapturedChild, binding: dict) -> dict:
    """Derive semantic output and identity from the same owned capture."""
    if (
        capture.request_id != binding["request_id"]
        or capture.returncode != 0
        or capture.prompt_sha256 != binding["prompt_sha256"]
    ):
        raise OperationRefused("child_unsuccessful")
    if capture.harness != binding["expected_harness"]:
        raise OperationRefused("child_identity_or_terminal_unproved")
    if capture.harness == "codex":
        protocol = _CodexProtocol(binding)
        protocol.feed(capture.stdout)
        result = protocol.result()
        response = result["response"]
    else:
        try:
            events = [json.loads(line) for line in capture.stdout.decode().splitlines() if line.strip()]
        except (UnicodeError, ValueError):
            raise OperationRefused("child_capture_invalid") from None
        models = set()
        sessions = set()
        text = []
        terminal = False
        for event in events:
            if not isinstance(event, dict):
                raise OperationRefused("child_event_invalid")
            model = event.get("model") or (event.get("message") or {}).get("model")
            if model:
                models.add(model)
            session = event.get("session_id") or event.get("thread_id")
            if session:
                sessions.add(session)
            if event.get("type") == "assistant":
                text.extend(
                    item["text"] for item in event.get("message", {}).get("content", []) if item.get("type") == "text"
                )
            if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
                text.append(event["item"]["text"])
            if event.get("type") == "result":
                terminal = event.get("subtype") == "success" and event.get("is_error") is False
            if event.get("type") == "turn.completed":
                terminal = True
        if models != {binding["expected_seat_or_model"]} or len(sessions) != 1 or not terminal:
            raise OperationRefused("child_identity_or_terminal_unproved")
        response = "\n".join(text)
        result = {"model": models.pop(), "session_id": sessions.pop(), "response": response}
    if binding["role"] == "author":
        if response.count("V4-AUTHOR-ROW:") != 1:
            raise OperationRefused("author_row_marker")
        try:
            row = json.loads(response.split("V4-AUTHOR-ROW:", 1)[1].strip())
        except ValueError as exc:
            raise OperationRefused("author_row_json") from exc
        if not isinstance(row, dict) or not isinstance(row.get("row_text"), str) or not row["row_text"].strip():
            raise OperationRefused("author_row_absent")
        if not set(row) <= {"row_text", "explanation", "answer", "instruction"} or any(
            not isinstance(value, str) for value in row.values()
        ):
            raise OperationRefused("author_row_shape")
        result["row"] = row
    else:
        verdicts = [
            line.removeprefix("V4-REVIEW-VERDICT: ").strip()
            for line in response.splitlines()
            if line.startswith("V4-REVIEW-VERDICT: ")
        ]
        if len(verdicts) != 1 or verdicts[0] not in ("PASS", "FAIL"):
            raise OperationRefused("review_verdict_absent")
        result["verdict"] = verdicts[0]
    return result
