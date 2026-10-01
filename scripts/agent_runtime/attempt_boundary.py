"""Review access: full matching checkout or isolated copied manifest evidence.

Full attempts use a verified host read-only mount and the attempt-scoped sources ledger.
For explicit isolated mode, the runner owns the boundary until response parsing
finishes: sources runs outside the sandbox, connected by a byte-stream socket,
and the original repository, Git objects, receipt store and home are unmounted.
This is separate from code-review isolation (#9251).
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
import stat
import subprocess
import tempfile
import threading
import time
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


def linux_claude_auth() -> dict[str, str]:
    """Select only a fresh access token; --bare ignores file-backed login.

    The existing auth staging supports keychain selection on Darwin. Linux
    needs equivalent selection from its credential file, never a home grant,
    refresh token, login mutation or copied credential store.
    """
    from scripts.review.isolation import ReviewIsolationError

    if platform.system() != "Linux" or any(
        os.environ.get(k)
        for k in (
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
        )
    ):
        return {}
    path = Path.home() / ".claude" / ".credentials.json"
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return {}
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
        return {"CLAUDE_CODE_OAUTH_TOKEN": token}
    except (ValueError, KeyError, TypeError) as exc:
        raise ReviewIsolationError("attempt_claude_auth_invalid") from exc
    finally:
        os.close(fd)


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
                self.env.update(linux_claude_auth())
            self.env.update(HOME=str(home), TMPDIR=str(self.write_root / "tmp"))
            self.env.pop("GIT_DIR", None)
            self.env.pop("GIT_WORK_TREE", None)
            proxy = self.write_root / "stdio.py"
            proxy.write_bytes(Path(__file__).with_name("attempt_proxy.py").read_bytes())
            endpoint = self.write_root / "sources.sock"
            self.endpoint = endpoint
            self.connection = SourcesConnection(endpoint, server)
            self.egress_endpoint = self.write_root / "egress.sock"
            if not self.full:
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
                if not self.full:
                    self.tool_config["allowed_tools"] = "Read,Glob,Grep," + str(tool_config.get("allowed_tools", ""))
        except BaseException:
            self.cleanup()
            raise

    def wrap(self, cmd: list[str], env_overrides: dict[str, str]) -> tuple[list[str], dict[str, str]]:
        from scripts.review.isolation import ReviewIsolationError, prepare_host_sandbox, wrap_argv_with_sandbox

        binary = Path(shutil.which(cmd[0]) or cmd[0]).resolve(strict=True)
        if self.full:
            from scripts.review.isolation import prepare_full_host_sandbox

            if not hasattr(self, "sandbox"):
                self.sandbox = prepare_full_host_sandbox(write_root=self.write_root, cwd=self.workspace)
            env = {**self.env, **env_overrides}
            env.update(HOME=self.env["HOME"], TMPDIR=self.env["TMPDIR"])
            return wrap_argv_with_sandbox([str(binary), *cmd[1:]], self.sandbox), env
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
            wrapped[-len(argv) : -len(argv)] = ["--proc", "/proc", "--chdir", str(self.workspace)]
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


def prepare_attempt_boundary(agent: str, mode: str, session_id: str | None, tool_config: dict | None):
    """Keep isolated boundaries and enforce a host read-only boundary for full attempts."""
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
