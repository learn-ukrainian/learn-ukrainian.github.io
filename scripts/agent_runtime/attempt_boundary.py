"""Formal attempts: copied manifest evidence, fresh homes, external receipt runtime.

The runner owns this boundary before adapter planning and until response parsing
finishes. Sources runs outside the seat sandbox; only a byte-stream socket is
exposed inside. The original repository, Git objects, receipt store and home
are never mounted. This is separate from code-review isolation (#9251).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

import yaml

from scripts.common.repo_root import project_interpreter
from scripts.review.isolation import (
    ReviewIsolationError,
    prepare_host_sandbox,
    stage_engine_auth,
    wrap_argv_with_sandbox,
)

from .env_sanitize import build_agent_env


def authorized_closure(manifest: dict[str, Any], root: Path) -> dict[str, bytes]:
    """All eligible manifest pins, and only those pins, verified before copying.

    `module_digest` and `upstream_lessons` are lesson inputs under the existing
    schema. A re-review additionally admits exactly previous review, previous
    ledger and diff. No file referred to by an input's contents is opened.
    """
    from scripts.build.fresh.manifest import pinned_entries
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
        destination = (
            "authorized/previous-ledger.jsonl" if location == "previous_attempt.ledger" else entry["path"]
        )
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
        from .review_mcp import SUPPORTED_HARNESSES, verify_review_attempt_paths

        if agent not in SUPPORTED_HARNESSES:
            raise ReviewIsolationError("attempt_harness_unsupported")
        config = Path(tool_config["mcp_config_path"])
        verify_review_attempt_paths(config)
        server = json.loads(config.read_bytes())["mcpServers"]["sources"]
        manifest_path = Path(tool_config["review_manifest"])
        data = manifest_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != server["env"]["LU_REVIEW_MANIFEST_SHA256"]:
            raise ReviewIsolationError("attempt_manifest_hash_mismatch")
        if server["env"]["LU_REVIEW_ATTEMPT_ID"] != tool_config["attempt_id"]:
            raise ReviewIsolationError("attempt_identity_mismatch")
        root = Path(tool_config["review_input_root"]).resolve(strict=True)
        closure = authorized_closure(yaml.safe_load(data), root)
        temporary_parent = tool_config.get("read_only_tmp_root")
        self.temp = tempfile.TemporaryDirectory(prefix="attempt-", dir=temporary_parent)
        self.connection = None
        self.socket_temp = None
        self.agent = agent
        try:
            base = Path(self.temp.name).resolve()
            self.workspace = base / "inputs"
            self.write_root = base / "runtime"
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
            self.env.update(HOME=str(home), TMPDIR=str(self.write_root / "tmp"))
            self.env.pop("GIT_DIR", None)
            self.env.pop("GIT_WORK_TREE", None)
            proxy = self.write_root / "stdio.py"
            proxy.write_bytes(Path(__file__).with_name("attempt_proxy.py").read_bytes())
            endpoint = self.write_root / "sources.sock"
            if platform.system() == "Darwin":
                # UNIX socket addresses have a short fixed limit. The socket
                # alone is allowed, never the surrounding shared temp tree.
                self.socket_temp = tempfile.TemporaryDirectory(prefix="attempt-mcp-", dir="/tmp")
                endpoint = Path(self.socket_temp.name).resolve() / "sources.sock"
            self.endpoint = endpoint
            self.connection = SourcesConnection(endpoint, server)
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
                    _render_codex_review_config(Path(proxy_server["command"]), proxy, {})
                    .replace(f'args = ["{proxy}"]', f'args = ["{proxy}", "{endpoint}"]')
                )
                self.tool_config["codex_home_override"] = str(codex_home)
                self.tool_config["attempt_os_sandbox"] = True
            elif agent == "agy":
                from .review_mcp import _real_agy_token, agy_review_mcp_config_path

                target = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(_real_agy_token(), target)
                target.chmod(0o600)
                mcp = agy_review_mcp_config_path(home)
                mcp.parent.mkdir(parents=True, exist_ok=True)
                mcp.write_bytes(proxy_config.read_bytes())
                self.tool_config["agy_home_override"] = str(home)
                self.env["AGY_APP_DATA_DIR"] = str(target.parent)
            else:
                self.tool_config["allowed_tools"] = "Read,Glob,Grep," + str(tool_config.get("allowed_tools", ""))
        except BaseException:
            self.cleanup()
            raise

    def wrap(self, cmd: list[str], env_overrides: dict[str, str]) -> tuple[list[str], dict[str, str]]:
        binary = Path(shutil.which(cmd[0]) or cmd[0]).resolve(strict=True)
        runtime = runtime_files(binary)
        reject = Path(self.tool_config["review_input_root"]).resolve()
        if any(p.is_relative_to(reject) or reject.is_relative_to(p) for p in runtime):
            raise ReviewIsolationError("attempt_runtime_overlaps_repository")
        self.sandbox = prepare_host_sandbox(
            engine=self.agent,
            snapshot_root=self.workspace,
            write_root=self.write_root,
            reject_root=Path(self.tool_config["review_input_root"]),
            runtime_reads=[*runtime, self.endpoint],
        )
        argv = [str(binary), *cmd[1:]]
        env = {**self.env, **env_overrides}
        env["HOME"] = self.env["HOME"]
        env["TMPDIR"] = self.env["TMPDIR"]
        env["PATH"] = "/usr/bin:/bin:" + str(binary.parent)
        wrapped = wrap_argv_with_sandbox(argv, self.sandbox)
        if self.sandbox.mechanism == "linux-bwrap":
            # A private procfs supports native executable discovery without
            # exposing host processes, descriptors, cwd or environment.
            wrapped[-len(argv):-len(argv)] = ["--proc", "/proc", "--chdir", str(self.workspace)]
        return wrapped, env

    def cleanup(self) -> None:
        if self.connection is not None:
            self.connection.cleanup()
        if self.socket_temp is not None:
            self.socket_temp.cleanup()
        self.temp.cleanup()


def prepare_attempt_boundary(agent: str, mode: str, session_id: str | None, tool_config: dict | None):
    """Every formal-attempt identity requires the parent-owned launch boundary."""
    tc = tool_config or {}
    if not (tc.get("review_id") or tc.get("attempt_id")):
        return None
    required = ("review_id", "attempt_id", "review_manifest", "review_input_root", "mcp_config_path")
    if mode != "read-only" or session_id is not None or not tc.get("strict_mcp_config"):
        raise ReviewIsolationError("attempt_requires_fresh_read_only_sources")
    if any(not tc.get(key) for key in required):
        raise ReviewIsolationError("attempt_boundary_inputs_missing")
    return AttemptBoundary(agent=agent, tool_config=tc)
