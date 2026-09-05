"""Fixed bwrap child plan, bounded capture and parsing owned by the API parent.

The profile is an immutable reviewed release resource. No invocation accepts
argv, executable, model, MCP configuration, environment or parser overrides.
Only installed adapters whose complete runtime closure is pinned are eligible.
"""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, canonical_bytes, digest
from learn_ukrainian_v4_runtime.resources import resource_root

MAX_CAPTURE_BYTES = 1048576


def profile_path() -> Path:
    return resource_root() / "data/projects/open_model_data/trust/v4_child_profile_v1.json"


def load_profile() -> dict:
    profile = json.loads(profile_path().read_bytes())
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


def _plan(profile: dict, claim: dict, provider_credential: str) -> tuple[list[str], dict[str, str]]:
    binding = claim["binding"]
    harness = binding["expected_harness"]
    if harness not in ("claude", "codex") or harness not in profile["adapters"]:
        raise OperationRefused("adapter_separability_unqualified")
    adapter = profile["adapters"][harness]
    if (
        set(adapter) != {"version", "models", "files", "executable", "provider_env"}
        or binding["expected_seat_or_model"] not in adapter["models"]
    ):
        raise OperationRefused("adapter_model_unqualified")
    if adapter["provider_env"] != {"claude": "ANTHROPIC_API_KEY", "codex": "OPENAI_API_KEY"}[harness]:
        raise OperationRefused("provider_credential_scope")
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
            or target.parts[1] not in ("runtime", "lib", "lib64", "usr")
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
    env = {
        "HOME": "/home/v4",
        "TMPDIR": "/tmp",
        "PATH": "/runtime",
        "LANG": "C.UTF-8",
        adapter["provider_env"]: provider_credential,
        "V4_SOURCES_ATTEMPT_CAPABILITY": claim["capability_token"],
    }
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
        argv = [
            adapter["executable"],
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--model",
            model,
            "-c",
            "model_reasoning_effort=" + json.dumps(effort),
            "-c",
            "features.shell_tool=false",
            "-c",
            "features.multi_agent=false",
            "-c",
            "mcp_servers.sources.url=" + json.dumps(url),
            "-c",
            'mcp_servers.sources.bearer_token_env_var="V4_SOURCES_ATTEMPT_CAPABILITY"',
            "-c",
            'mcp_servers.sources.enabled_tools=["verify_word","verify_words","verify_lemma","verify_stress","check_modern_form"]',
            "-",
        ]
    cmd.extend(["--chdir", "/work", "--", *argv])
    return cmd, env


def run_child(claim: dict, *, provider_credential: str) -> CapturedChild:
    profile = load_profile()
    cmd, env = _plan(profile, claim, provider_credential)
    prompt = claim["prompt"].encode()
    if not prompt or len(prompt) > 65536:
        raise OperationRefused("semantic_input_size")
    remaining = claim["deadline_at"].timestamp() - time.time()
    if remaining <= 0:
        raise OperationRefused("execution_expired")
    deadline = time.monotonic() + min(1800, remaining)
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        close_fds=True,
        start_new_session=True,
    )
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        with selectors.DefaultSelector() as selector:
            for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
            pending = memoryview(prompt)
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
            rc = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        return CapturedChild(
            claim["request_id"],
            claim["attempt_id"],
            digest(canonical_bytes(cmd)),
            digest(prompt),
            bytes(streams["stdout"]),
            bytes(streams["stderr"]),
            rc,
            claim["binding"]["expected_harness"],
        )
    finally:
        if process.poll() is None:
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
    try:
        events = [json.loads(line) for line in capture.stdout.decode().splitlines() if line.strip()]
    except (UnicodeError, ValueError) as exc:
        raise OperationRefused("child_capture_invalid") from exc
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
