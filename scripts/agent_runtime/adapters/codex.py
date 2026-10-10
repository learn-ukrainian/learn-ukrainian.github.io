"""CodexAdapter — wraps ``codex exec`` for the agent runtime.

First real adapter. Proves the protocol shape works against a real CLI.
Lifted from the prior art in ``scripts/ai_agent_bridge/_codex.py`` and
``scripts/build/dispatch.py`` (Codex branch) — same flag semantics, now
routed through the unified runtime.

Key design points:

- **Bridge-only warm resume.** CodexAdapter has ``resume_policy="bridge_only"``
  in the registry: dispatch/delegate invocations stay fresh-session via the
  runner policy gate, while an exact bridge task/thread may resume its prior
  Codex CLI session and retain native reasoning/compaction state (#1894).
- **All three modes supported:** read-only, workspace-write, danger.
  Mode → flag mapping matches ``_codex.py::_codex_bridge_flags`` and
  ``dispatch.py::_codex_dispatch_flags``.
- **Identity remains request-side.** The model flag selects a configured
  request. A successful final response or rollout context does not establish
  provider-observed model/version identity; this adapter does not claim it.
- **Output file always used.** ``codex exec -o <tmpfile>`` writes the final
  agent message to a file; we read it in ``parse_response``. The file path
  goes into ``liveness_signal_paths`` so the runner's mtime poller catches
  Codex writing progress even when stdout is quiet.
- **Outcome from the typed event stream.** ``codex exec --json`` prints its
  typed events on stdout, already filtered to this invocation's thread and
  turn. That stream alone decides completion, failure class, session id,
  tool telemetry and usage; human-formatted stderr and the shared session
  rollout never do (#9532). See ``codex_events``.

Issue: #1184
"""

from __future__ import annotations

import hashlib
import json as _json
import logging
import os
import re
import selectors
import shlex
import shutil
import subprocess
import tempfile
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scripts.agent_runtime.attempt_safe_read import AttemptReadError, safe_read_attempt_file
from scripts.review.receipts.ledger import review_tools
from scripts.secret_redactor import redact_text

from ..read_only_tmp import validate_read_only_tmp_root
from ..result import ParseResult
from ..sources_read_only import sources_tool_sets
from ._output_schema import json_value, load_output_schema, plan_output_schema, schema_metadata, structured_result
from .base import InvocationPlan
from .codex_events import (
    INCOMPLETE_FAILURE_CODE,
    codex_outcome,
    fresh_invocation_tokens,
    parse_exec_stream,
    tool_calls_from_items,
)

if TYPE_CHECKING:
    from scripts.review.isolation import SandboxCapability

_logger = logging.getLogger(__name__)

_DISCUSS_READONLY_TOOL_CONFIG_KEY = "discussion_readonly"
_EXCERPT_CHARS = 500


class CodexReviewConfigError(ValueError):
    """A review's config provenance cannot establish its MCP boundary."""


_HOOK_SOURCE_ENV = "LU_CODEX_HOOK_SOURCE"
# Execute the very bytes checked, avoiding a second, raceable read of the entry.
# -I prevents the session cwd/PYTHONPATH from supplying bootstrap imports.
_HOOK_BOOTSTRAP = """import hashlib, os, stat, sys
from pathlib import Path
try:
    root = Path(sys.argv[1]).resolve(strict=True)
    if root != Path(os.environ['LU_CODEX_HOOK_SOURCE']).resolve(strict=True):
        raise ValueError('source mismatch')
    candidate = root / sys.argv[2]
    entry = candidate.resolve(strict=True)
    if not entry.is_relative_to(root) or entry != candidate:
        raise ValueError('entry escape')
    fd = os.open(entry, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1048576:
            raise ValueError('entry is not a bounded regular file')
        content = handle.read(1048577)
    if hashlib.sha256(content).hexdigest() != sys.argv[3]:
        raise ValueError('entry changed')
except (OSError, ValueError, KeyError, RuntimeError):
    print('Codex worker PreToolUse entry verification failed', file=sys.stderr)
    sys.exit(2)
args = sys.argv[4:]
if entry.suffix == '.sh':
    os.execv('/bin/bash', ['bash', '-c', content.decode(), str(entry), *args])
sys.argv = [str(entry), *args]
exec(compile(content, str(entry), 'exec'), {'__name__': '__main__', '__file__': str(entry)})
"""


def _portable_hook_command(command: str, root: Path) -> str:
    """Bind a tracked entry to the source checkout, never the session's Git root.

    Checkout locations live only in the private launch environment. The public
    command contains a relative entry and its tracked content digest.
    """
    try:
        root = root.resolve(strict=True)
        words = shlex.split(command)
        if words and words[0] in {"bash", "/bin/bash"}:
            words.pop(0)
        candidate = Path(words.pop(0))
        entry = candidate.resolve(strict=True)
        if not entry.is_relative_to(root):
            raise ValueError("entry escape")
        if entry != candidate or not entry.is_file():
            raise ValueError("entry is not a regular source path")
        relative = candidate.relative_to(root).as_posix()
        tracked = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "show", f"HEAD:{relative}"],
            env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
            capture_output=True, check=True, timeout=2,
        ).stdout
        if entry.read_bytes() != tracked:
            raise ValueError("entry differs from tracked content")
    except (OSError, ValueError, IndexError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Codex worker PreToolUse guard has an unportable or untracked path") from exc
    git = '/usr/bin/env -i /usr/bin/git -C "${LU_CODEX_HOOK_SOURCE:?}"'
    return (
        f'root="$({git} rev-parse --show-toplevel)" && '
        f'common="$({git} rev-parse --path-format=absolute --git-common-dir)" && '
        '"${common%/*}/.venv/bin/python" -I -c '
        + shlex.quote(_HOOK_BOOTSTRAP)
        + ' "$root" '
        + " ".join(shlex.quote(word) for word in [relative, hashlib.sha256(tracked).hexdigest(), *words])
        + " || exit 2"
    )


def _worker_hook_flags() -> list[str]:
    """Bind tracked pre-tool policy, independent of deployed project discovery.

    Codex supports inline hooks through TOML CLI overrides. Non-managed hooks
    require trust even for session flags; this harness vets its tracked sources
    and uses the documented automation trust flag (learn.chatgpt.com/docs/hooks).
    """
    from scripts.agent_runtime.codex_hook_policy import LOCAL_BASH_GUARDS, MERGE_GUARDS, PRIMARY_WRITE_GUARD

    from .claude import _worker_guard_settings

    root = Path(__file__).resolve().parents[3]
    manifest = _json.loads((root / "agents_extensions/codex/hooks.json").read_text(encoding="utf-8"))
    groups = manifest["hooks"]["PreToolUse"]
    entry = root / "scripts/agent_runtime/codex_hook_entry.sh"
    if not entry.is_file() or not groups:
        raise RuntimeError("Codex worker PreToolUse guards unavailable")
    for group in groups:
        for hook in group["hooks"]:
            expected = 'bash "$(git rev-parse --show-toplevel)/scripts/agent_runtime/codex_hook_entry.sh" pre-tool-use'
            if hook["command"] != expected:
                raise RuntimeError("Codex worker PreToolUse runner has an unsupported form")
            hook["command"] = _portable_hook_command(f"bash {shlex.quote(str(entry))} pre-tool-use", root)

    # Reuse the tracked shared-settings reader. Keep the deterministic Codex
    # runner, adding shared guards it does not already execute (#10305).
    covered = {name for name, _ in (*LOCAL_BASH_GUARDS, PRIMARY_WRITE_GUARD, *MERGE_GUARDS)} | {"enforce-venv.sh"}
    for group in _json.loads(_worker_guard_settings())["hooks"]["PreToolUse"]:
        missing = [hook for hook in group["hooks"] if Path(shlex.split(hook["command"])[-1]).name not in covered]
        if missing:
            portable = [{**hook, "command": _portable_hook_command(hook["command"], root)} for hook in missing]
            groups.append({**group, "hooks": portable})
    return [
        "--enable", "hooks", "--dangerously-bypass-hook-trust",
        "-c", "hooks.PreToolUse=" + CodexAdapter._encode_config_value(groups),
    ]


def _codex_config_layers(
    binary: str, cwd: Path, home: str, *, env: dict[str, str] | None = None, sandbox: SandboxCapability | None = None
) -> list[dict]:
    """Read native layer provenance without starting a model turn.

    Installed ``codex exec --help``: ``--ignore-user-config`` means
    "Do not load `$CODEX_HOME/config.toml`; auth still uses `CODEX_HOME`".
    Official precedence: CLI > project > profile > user > cloud > system.
    https://learn.chatgpt.com/docs/config-file/config-basic
    ``config/read`` with ``includeLayers`` also exposes shadowed definitions;
    checking only ``mcp list`` would lose their provenance.

    Sealed reviews supply the final allowlisted launch environment and sandbox
    after auth staging, so signed-in cloud layers and auth refreshes are shared
    with launch. Other callers use the same environment allowlist.
    """
    from scripts.review.isolation import build_reviewer_env, wrap_argv_with_sandbox

    probe_env = dict(env) if env is not None else build_reviewer_env(engine="codex", reject_root=cwd)
    probe_env["CODEX_HOME"] = home
    argv = [binary, "app-server"]
    if sandbox is not None:
        argv = wrap_argv_with_sandbox(argv, sandbox)
    messages = [
        {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "review-config-gate", "version": "1"}}},
        {"method": "initialized"},
        {"id": 2, "method": "config/read", "params": {"cwd": str(cwd), "includeLayers": True}},
    ]
    try:
        with subprocess.Popen(
            # app-server has no ignore-user-config flag. Read original layers
            # without CLI MCP overrides: an ignored user URL must not merge
            # into the launch's stdio command during this provenance probe.
            argv,
            cwd=cwd,
            env=probe_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ) as proc:
            try:
                assert proc.stdin is not None and proc.stdout is not None
                proc.stdin.write(("\n".join(_json.dumps(msg) for msg in messages) + "\n").encode())
                proc.stdin.flush()
                deadline = time.monotonic() + 10
                pending = b""
                size = 0
                with selectors.DefaultSelector() as selector:
                    selector.register(proc.stdout, selectors.EVENT_READ)
                    while time.monotonic() < deadline:
                        if not selector.select(max(0, deadline - time.monotonic())):
                            break
                        chunk = os.read(proc.stdout.fileno(), 65536)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > 4 * 1024 * 1024:
                            break
                        pending += chunk
                        while b"\n" in pending:
                            line, pending = pending.split(b"\n", 1)
                            reply = _json.loads(line)
                            if reply.get("id") == 2:
                                layers = reply.get("result", {}).get("layers")
                                if not isinstance(layers, list) or not layers:
                                    raise CodexReviewConfigError("review_mcp_config_layers_unavailable")
                                return layers
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError) as exc:
        raise CodexReviewConfigError("review_mcp_config_layers_unavailable") from exc
    raise CodexReviewConfigError("review_mcp_config_layers_unavailable")


def _validate_review_mcp_layers(layers: list[dict], expected: dict, home: str) -> None:
    """Only adapter-authored CLI definitions may supply a review's MCP set."""
    if not isinstance(layers, list) or not layers:
        raise CodexReviewConfigError("review_mcp_config_layers_unavailable")
    for layer in layers:
        if (
            not isinstance(layer, dict)
            or not isinstance(layer.get("name"), dict)
            or not isinstance(layer["name"].get("type"), str)
        ):
            raise CodexReviewConfigError("review_mcp_config_layers_unavailable")
        source = layer["name"]
        config = layer.get("config")
        if not isinstance(config, dict):
            raise CodexReviewConfigError("review_mcp_config_layers_unavailable")
        # exec ignores exactly the base user file, not profile or other layers.
        if (
            source.get("type") == "user"
            and source.get("profile") is None
            and isinstance(source.get("file"), str)
            and Path(source["file"]).resolve() == Path(home, "config.toml").resolve()
        ):
            continue
        servers = config.get("mcp_servers", {})
        if not isinstance(servers, dict):
            raise CodexReviewConfigError("review_mcp_config_layers_unavailable")
        # The provenance probe supplies no MCP CLI overrides. Any definition
        # it reports (including a session layer) was not written by this adapter.
        if servers:
            raise CodexReviewConfigError("review_mcp_foreign_config_layer")
    # An ignored base-user definition cannot serve as the launch's only source.
    # The adapter must emit an explicit transport, not just tool policy keys.
    if expected and not all(
        isinstance(server, dict) and (server.get("command") or server.get("url")) for server in expected.values()
    ):
        raise CodexReviewConfigError("review_mcp_sources_definition_mismatch")


def _validate_review_mcp_keys(value: dict) -> None:
    """Refuse dotted/quoted keys that escape the adapter's nested MCP map."""
    for key, nested in value.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise CodexReviewConfigError("review_mcp_foreign_config_override")
        if isinstance(nested, dict):
            _validate_review_mcp_keys(nested)


# Exposure filtering remains effective even under parent-sandboxed bypass.


def _sources_read_only_flags(tool_names: tuple[str, ...] | None = None) -> list[str]:
    """Replace inherited sources grants with the route's readers, then approve each."""
    if tool_names is None:
        tool_names = sources_tool_sets()[0]
    tools = {name: {"approval_mode": "approve"} for name in tool_names}
    approvals = "{" + ",".join(f'{name}={{approval_mode="approve"}}' for name in tools) + "}"
    return [
        "-c",
        "mcp_servers.sources.enabled_tools=" + _json.dumps(list(tool_names)),
        "-c",
        'mcp_servers.sources.default_tools_approval_mode="prompt"',
        "-c",
        "mcp_servers.sources.tools=" + approvals,
    ]


def _prompt_names_sources_mcp(prompt: str) -> bool:
    return "mcp__sources__" in prompt


def _argv_can_call_sources_mcp(argv: list[str]) -> bool:
    if "--dangerously-bypass-approvals-and-sandbox" in argv:
        return True
    if any(
        all(flag in argv for flag in _sources_read_only_flags(tools))
        for tools in (tuple(sorted(review_tools())), tuple(sorted(review_tools("full"))))
    ):
        return True
    return all(flag in argv for flag in _sources_read_only_flags())


def _read_only_tmp_flags(root: Path) -> list[str]:
    # Replace the entire permissions map so inherited entries cannot add
    # writable paths. The legacy mode is a fail-closed fallback for old CLIs.
    # HOME and the checkout remain read-only; gh authentication is inherited
    # through the existing runtime environment. Only scratch needs writes.
    return [
        "-c",
        'sandbox_mode="read-only"',
        "-c",
        'default_permissions="lu_review"',
        "-c",
        'permissions={lu_review={filesystem={":root"="read",'
        + _json.dumps(str(root), ensure_ascii=False)
        + '="write"},network={enabled=true,domains={"github.com"="allow","api.github.com"="allow"}}}}',
        "-c",
        "features.network_proxy=true",
        "-c",
        'approval_policy="never"',
    ]


def _resumed_session_id(plan: InvocationPlan | None) -> str | None:
    """Return the session a ``codex exec resume`` plan names in its own argv."""
    if plan is None or plan.cmd[1:3] != ["exec", "resume"] or len(plan.cmd) < 5 or plan.cmd[-1] != "-":
        return None
    return plan.cmd[-2]


def _discussion_readonly_requested(tool_config: dict | None) -> bool:
    """Return True when the caller is an ab discuss read-only invocation."""
    return bool(
        os.environ.get("AB_DISCUSS_READONLY") == "1" or (tool_config or {}).get(_DISCUSS_READONLY_TOOL_CONFIG_KEY)
    )


# Operator 2026-09-29 (#9230). GPT-6.1 Sol is the only Sol: it orchestrates and
# holds the former Astra advisory seat. Luna scouts.
CODEX_APPROVED_MODELS = frozenset({"gpt-6-luna", "gpt-6.1-sol"})


class CodexAdapter:
    """Adapter for ``codex exec`` (OpenAI ChatGPT Codex CLI)."""

    name: str = "codex"
    default_model: str = "gpt-6.1-sol"
    # Omitted effort is the orchestrator setting. Scouting passes Luna and its
    # own effort. An explicit --effort always wins.
    default_effort: str = "high"
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    # Per-invocation scoped $CODEX_HOME path. Set by ``build_invocation``
    # from ``tool_config["codex_home_override"]`` (V7 writer); read by
    # ``_candidate_rollout_dirs`` so liveness polls the scoped sessions/ dir,
    # not the user's real ``~/.codex/sessions/``.
    _codex_home_scope: str | None = None

    def __init__(self) -> None:
        # Early-reap evidence, keyed by each invocation's unique -o path so
        # concurrent invocations sharing this adapter never mix.
        self._early_reap_checked_at: dict[str, float] = {}
        self._early_reap_candidates: dict[str, str] = {}
        self._early_reaped_outputs: dict[str, str] = {}

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        """Build the codex exec invocation.

        Uses ``codex exec`` for fresh calls and ``codex exec resume`` when a
        bridge caller passes ``session_id``. The runner rejects non-bridge
        session reuse before the adapter is invoked.
        Supports Codex MCP config overrides via ``tool_config``:
            - ``{"mcp_servers": {"sources": {"url": "http://127.0.0.1:8766/sse"}}}``
              → ``-c 'mcp_servers.sources.url="http://127.0.0.1:8766/sse"'``
            - Unknown top-level keys are ignored (forward-compatible).

        ``effort``: appended as ``-c model_reasoning_effort=<level>`` so it
        overrides ``~/.codex/config.toml`` for this invocation only. When
        None, the lane default ``high`` is applied.
        See #1396.
        """
        if model is not None and model not in CODEX_APPROVED_MODELS:
            approved = ", ".join(sorted(CODEX_APPROVED_MODELS))
            raise ValueError(f"CodexAdapter: model={model!r} rejected; approved models are {approved}")

        tc_early = tool_config or {}
        if tc_early.get("attempt_os_sandbox"):
            from ..attempt_boundary import AttemptBoundary

            if not isinstance(tc_early.get("review_attempt_boundary"), AttemptBoundary):
                raise ValueError("CodexAdapter: attempt_os_sandbox requires the parent attempt boundary")
        read_only_tmp_root = validate_read_only_tmp_root(tc_early, cwd, mode, adapter="CodexAdapter")
        review_write_root: Path | None = None
        if tc_early.get("review_isolation"):
            from scripts.review.isolation import validated_review_write_root

            review_write_root = validated_review_write_root(tc_early)

        # Per-invocation scoped $CODEX_HOME (set by V7 writer via
        # ``tool_config["codex_home_override"]``): liveness must poll the
        # sessions/ directory the subprocess actually writes to.
        effective_codex_home = tc_early.get("codex_home_override")
        if not effective_codex_home and review_write_root is not None:
            private_home = review_write_root / "home" / ".codex"
            # Reserve the launch home now. Isolation stages auth once and
            # probes its layers there before permitting the model launch.
            try:
                private_home.mkdir(mode=0o700, exist_ok=True)
            except OSError as exc:
                raise CodexReviewConfigError("review_mcp_config_layers_unavailable") from exc
            if private_home.is_symlink():
                raise CodexReviewConfigError("review_mcp_config_home_unsafe")
            effective_codex_home = str(private_home)
        self._codex_home_scope = str(
            Path(effective_codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
        )

        discussion_readonly = _discussion_readonly_requested(tool_config)
        if discussion_readonly and mode != "read-only":
            raise ValueError("AB_DISCUSS_READONLY requires mode='read-only'")

        max_budget_usd = (tool_config or {}).get("max_budget_usd")
        if max_budget_usd is not None:
            _logger.warning(
                "non-claude adapter %s ignoring max_budget_usd=%s; use hard-timeout/silence-timeout instead",
                self.name,
                max_budget_usd,
            )

        # Resolve binary. shutil.which handles PATH lookup; fall back to
        # bare "codex" if not on PATH so subprocess.Popen can report the
        # error clearly.
        if tc_early.get("review_isolation"):
            trusted = tc_early.get("review_engine_binary")
            if not isinstance(trusted, str) or not Path(trusted).is_absolute():
                raise ValueError("CodexAdapter: trusted review_engine_binary required")
            codex_bin = trusted
        else:
            codex_bin = shutil.which("codex") or "codex"

        # Pick a unique output file inside /tmp.
        # Include task_id for human debuggability, but sanitize it:
        # arbitrary task_id strings (issue slugs, URLs, user input)
        # could contain slashes, nulls, or path separators that would
        # make NamedTemporaryFile create files in unintended locations
        # or fail entirely. Strip everything that isn't alphanumeric
        # or a safe punctuation char. Codex 2026-04-10 audit finding.
        safe_suffix = ""
        if task_id:
            safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in task_id)
            safe_suffix = f"-{safe[:60]}"  # cap length too
        write_root = review_write_root or (
            Path(str(tc_early["review_write_root"])) if tc_early.get("review_write_root") else None
        )
        # Resolve trusted temp ancestors before any seat can rename components.
        output_read_root = write_root or Path(read_only_tmp_root or tempfile.gettempdir()).resolve()
        execution_cwd = cwd
        if tc_early.get("review_isolation") and review_write_root is not None:
            # Codex discovers AGENTS.md from its working root independently of
            # --ignore-rules. Run from the parent-created instruction-free
            # directory; complete changed content remains in the sealed prompt.
            execution_cwd = review_write_root / "exec"
        guard_sources_config = tc_early.get("ignore_user_config") or tc_early.get("review_isolation")
        if guard_sources_config:
            servers = tc_early.get("mcp_servers", {})
            if not isinstance(servers, dict):
                raise CodexReviewConfigError("review_mcp_foreign_config_override")
            _validate_review_mcp_keys(servers)
            if servers and not tc_early.get("review_isolation") and set(servers) != {"sources"}:
                raise CodexReviewConfigError("review_mcp_foreign_config_override")
            for server in servers.values():
                if not isinstance(server, dict) or not (server.get("command") or server.get("url")):
                    raise CodexReviewConfigError("review_mcp_sources_definition_mismatch")
            if not tc_early.get("review_isolation"):
                # Sealed reviews must wait for the final auth staging in
                # prepare_isolated_review_launch to see signed-in cloud layers.
                layers = _codex_config_layers(codex_bin, execution_cwd, self._codex_home_scope)
                _validate_review_mcp_layers(layers, servers, self._codex_home_scope)
        if (tc_early.get("review_isolation") or tc_early.get("attempt_os_sandbox")) and write_root is not None:
            out_dir = write_root / "tmp"
            output_path = out_dir / f"codex-runtime{safe_suffix}-{os.getpid()}.txt"
            fd = os.open(
                output_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            os.close(fd)
        else:
            with tempfile.NamedTemporaryFile(
                prefix=f"codex-runtime{safe_suffix}-",
                suffix=".txt",
                dir=output_read_root,
                delete=False,
            ) as output_fd:
                output_path = Path(output_fd.name)

        has_session_to_resume = session_id is not None

        cmd: list[str] = [codex_bin, "exec"]
        if has_session_to_resume:
            cmd.append("resume")
        effective_effort = effort if effort is not None else self.default_effort
        # Per-invocation override of ~/.codex/config.toml (#1396); the lane
        # default is max when the caller omits effort (operator 2026-08-13).
        cmd.extend(["-c", f"model_reasoning_effort={effective_effort}"])
        cmd.append("--skip-git-repo-check")
        # Typed JSONL events on stdout: the only outcome authority (#9532).
        cmd.append("--json")
        if not has_session_to_resume:
            # ``codex exec resume`` does not accept -C or --color. It resumes
            # the original session boundary and the subprocess itself still
            # runs from execution_cwd.
            cmd.extend(["-C", str(execution_cwd), "--color", "never"])
        cmd.extend(["-o", str(output_path), "-m", model or self.default_model])
        # Review isolation (#5285): ignore user/project config when the bridge
        # marks the invocation as a fail-closed review. Missing flags on an
        # older binary are the caller's responsibility to feature-detect; the
        # bridge refuses engines that cannot prove these capabilities.
        tc = tool_config or {}
        if tc.get("review_isolation") or tc.get("ignore_user_config"):
            cmd.append("--ignore-user-config")
        if tc.get("review_isolation") or tc.get("ignore_rules"):
            cmd.append("--ignore-rules")
        # ``_mode_flags`` emits ``--enable multi_agent`` for non-read-only
        # modes (matches start-codex.sh). ``_tool_config_flags`` emits the
        # writer-isolation ``--disable shell_tool / goals / browser_use /
        # in_app_browser / image_generation / apps / plugins / multi_agent``
        # list. Codex applies disables after enables regardless of argv order;
        # caller isolation disables therefore suppress ``multi_agent``.
        if has_session_to_resume and tc.get("review_isolation"):
            raise ValueError("CodexAdapter: sealed review sessions cannot resume")
        if tc.get("review_isolation"):
            # Codex's internal read-only mode cancels stdio MCP calls even
            # when approval_policy=never. The verified parent OS sandbox is
            # the review boundary, so bypass only the nested Codex sandbox to
            # keep the sole sealed read-only MCP tool usable.
            cmd.append("--dangerously-bypass-approvals-and-sandbox")
        elif tc.get("attempt_os_sandbox"):
            # Parent runner owns the manifest filesystem boundary. Keeping a
            # nested read-only sandbox cancels the authorized stdio sources.
            cmd.append("--dangerously-bypass-approvals-and-sandbox")
        elif read_only_tmp_root is not None:
            cmd.extend(_read_only_tmp_flags(read_only_tmp_root))
        elif has_session_to_resume and mode == "read-only":
            # ``resume`` has no -s/--sandbox flag, but accepts config
            # overrides. Reassert the requested boundary instead of inheriting
            # a broader mode if a caller changes delivery metadata mid-thread.
            cmd.extend(["-c", 'sandbox_mode="read-only"'])
        else:
            cmd.extend(self._mode_flags(mode))
        cmd.extend(self._tool_config_flags(tool_config))
        if not tc.get("review_isolation"):
            # Sealed reviews run in an OS sandbox without tracked hook mounts.
            # Ordinary workers, including scoped homes and resumes, enable
            # tracked hooks. _tool_config_flags filters caller hooks disables:
            # an explicit disable would defeat this enable in either order.
            cmd.extend(_worker_hook_flags())
        # Dispatched workers must have NO write-capable GitHub connector tools
        # (#7181). Disabling the `apps` feature suppresses `codex_apps` MCP
        # connectors (including `github.create_commit`, `github.update_ref`,
        # `github.create_pr`) across all runtime invocations (fresh & resume).
        # Keep the unconditional apps disable after every feature enable.
        cmd.extend(["--disable", "apps"])
        mcp_servers = tc.get("mcp_servers")
        sources = mcp_servers.get("sources") if isinstance(mcp_servers, dict) else None
        sources_defined = isinstance(sources, dict) and bool(sources.get("command") or sources.get("url"))
        if mode == "read-only" and ("--ignore-user-config" not in cmd or sources_defined):
            # Last overrides win: caller/global config cannot re-expose writers.
            # Formal scoped homes use the receipt contract, including when the
            # parent AttemptBoundary replaces their server with a stdio proxy.
            if tc.get("codex_home_override") and tc.get("mcp_config_path"):
                tools = tuple(sorted(review_tools(tc.get("review_access", "isolated"))))
            else:
                tools = sources_tool_sets()[0]
            cmd.extend(_sources_read_only_flags(tools))
        if has_session_to_resume:
            cmd.append(session_id)
        cmd.append("-")  # Read prompt from stdin.

        env_overrides: dict[str, str] = {}
        if not tc.get("review_isolation"):
            env_overrides[_HOOK_SOURCE_ENV] = str(Path(__file__).resolve().parents[3])
        if _prompt_names_sources_mcp(prompt) and not _argv_can_call_sources_mcp(cmd):
            raise ValueError(
                "CodexAdapter: this mode cannot call mcp__sources__* "
                "(a read-only sandbox cancels unapproved stdio MCP). "
                "Language reviews need sources auto-approval or "
                "--mode workspace-write."
            )
        if read_only_tmp_root is not None:
            env_overrides["TMPDIR"] = str(read_only_tmp_root)
        if discussion_readonly:
            env_overrides["AB_DISCUSS_READONLY"] = "1"
        codex_home_override = effective_codex_home
        if codex_home_override:
            # Per-invocation scoping of $CODEX_HOME — see
            # ``_tool_config_flags`` docstring for the rationale. The
            # caller is responsible for ensuring the directory exists,
            # contains a minimal ``config.toml`` registering ONLY the
            # MCP servers the writer is allowed to touch, and a
            # readable ``auth.json`` (typically a symlink to the user's
            # real ``$CODEX_HOME/auth.json``).
            env_overrides["CODEX_HOME"] = str(codex_home_override)

        return InvocationPlan(
            cmd=cmd,
            cwd=execution_cwd,
            stdin_payload=prompt,
            output_file=output_path,
            env_overrides=env_overrides,
            liveness_paths=(output_path,),
            metadata={**schema_metadata(load_output_schema(tool_config)), "parent_read_root": str(output_read_root)},
        )

    @classmethod
    def _tool_config_flags(cls, tool_config: dict | None) -> list[str]:
        """Translate supported tool_config keys into ``codex exec`` flags.

        Supported keys:
        - ``mcp_servers``: ``{"<name>": {"url": "...", ...}}`` →
          ``-c mcp_servers.<name>.<field>=<value>`` overrides.
        - ``disable_features``: ``list[str]`` of Codex feature-flag names
          (per ``codex features list``) → ``--disable <name>`` per item.
          Used by ``linear_pipeline._runtime_tool_config`` to enforce
          writer tool-isolation: V7 writers may only call ``mcp__sources__*``
          tools, so feature flags such as ``shell_tool``, ``goals``,
          ``plugins``, ``browser_use``, ``in_app_browser``,
          ``image_generation``, and ``multi_agent`` must be disabled
          before invocation so the model can't reach for them and trip
          the ``writer_trace_isolation`` gate with ``wrong_tool_family``
          (``apps`` is filtered here because it is emitted unconditionally
          in ``build_invocation``; ``hooks`` is filtered for ordinary workers
          because they bind tracked safety hooks. Sealed reviews do not bind
          those hooks and retain caller disables).
          See ``codex_home_override`` for the companion MCP-scoping fix.
        - ``codex_home_override``: NOT translated to flags here — it's a
          companion ``env_overrides`` key handled in
          ``build_invocation``; documented in this method so callers see
          the full surface in one place. The motivation is the same
          ``writer_trace_isolation`` gate: the user-level
          ``$CODEX_HOME/config.toml`` may register MCP servers
          (e.g. Codex.app's ``node_repl`` and ``openaiDeveloperDocs``)
          that surface tools outside ``mcp__sources__*``. Per-invocation
          ``-c mcp_servers.X.url=...`` overrides MERGE with the global
          config; they don't replace it. Repointing ``CODEX_HOME`` at a
          scoped directory containing only the sources MCP definition
          (plus a symlink of the user's ``auth.json``) is the actual
          per-invocation isolation mechanism in codex-cli 0.133.0,
          confirmed via ``ab ask-codex`` 2026-05-22.
        - ``output_schema_path`` plus ``output_schema_sha256``: absolute path
          to a readable JSON object and its exact SHA-256 → ``--output-schema
          <path>``. The adapter validates both again at invocation time so
          direct runtime callers cannot bypass the dispatch boundary's
          fail-closed schema checks or race different bytes into the provider.
        """
        flags: list[str] = []
        if not tool_config:
            return flags

        mcp_servers = tool_config.get("mcp_servers")
        if isinstance(mcp_servers, dict):
            for key, value in cls._flatten_config_overrides("mcp_servers", mcp_servers):
                flags.extend(["-c", f"{key}={value}"])

        disable_features = tool_config.get("disable_features")
        if isinstance(disable_features, (list, tuple)):
            bound_features = {"apps"}
            if not tool_config.get("review_isolation"):
                bound_features.add("hooks")
            for feature in disable_features:
                if isinstance(feature, str) and feature and feature not in bound_features:
                    flags.extend(["--disable", feature])

        output_schema_path = tool_config.get("output_schema_path")
        if output_schema_path is not None:
            if not isinstance(output_schema_path, str) or not output_schema_path:
                raise ValueError("CodexAdapter: output_schema_path must be a non-empty absolute path")
            schema_path = Path(output_schema_path)
            if not schema_path.is_absolute():
                raise ValueError("CodexAdapter: output_schema_path must be absolute")
            if not schema_path.is_file():
                raise ValueError(f"CodexAdapter: output schema is not a readable file: {schema_path}")
            expected_sha256 = tool_config.get("output_schema_sha256")
            if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
                raise ValueError("CodexAdapter: output_schema_sha256 must be a lowercase SHA-256")
            try:
                payload = safe_read_attempt_file(
                    schema_path
                    if tool_config.get("review_write_root")
                    else schema_path.parent.resolve() / schema_path.name,
                    trusted_root=Path(tool_config["review_write_root"])
                    if tool_config.get("review_write_root")
                    else schema_path.parent.resolve(),
                )
                schema = _json.loads(payload.decode("utf-8"))
            except (OSError, UnicodeDecodeError, _json.JSONDecodeError) as exc:
                raise ValueError(f"CodexAdapter: invalid output schema JSON: {exc}") from exc
            if not isinstance(schema, dict):
                raise ValueError("CodexAdapter: output schema JSON must be an object")
            actual_sha256 = hashlib.sha256(payload).hexdigest()
            if actual_sha256 != expected_sha256:
                raise ValueError("CodexAdapter: output schema SHA-256 changed after dispatch validation")
            flags.extend(["--output-schema", str(schema_path)])

        return flags

    @classmethod
    def _flatten_config_overrides(
        cls,
        prefix: str,
        value: Any,
    ) -> list[tuple[str, str]]:
        """Flatten nested config values into dotted ``key=value`` pairs."""
        if isinstance(value, dict):
            flattened: list[tuple[str, str]] = []
            for key, nested in value.items():
                if nested is None:
                    continue
                flattened.extend(cls._flatten_config_overrides(f"{prefix}.{key}", nested))
            return flattened
        return [(prefix, cls._encode_config_value(value))]

    @staticmethod
    def _encode_config_value(value: Any) -> str:
        """Encode a scalar, array or inline table into a TOML-compatible literal."""
        if isinstance(value, tuple):
            value = list(value)
        if isinstance(value, dict):
            return "{" + ",".join(
                f"{_json.dumps(key)}={CodexAdapter._encode_config_value(nested)}" for key, nested in value.items()
            ) + "}"
        if isinstance(value, list):
            return "[" + ",".join(CodexAdapter._encode_config_value(nested) for nested in value) + "]"
        return _json.dumps(value)

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Parse one ``codex exec --json`` invocation into a ParseResult.

        The stdout event stream is the only outcome authority. A completed
        turn succeeds only after a clean exit, or after an early reap that
        verified the final ``-o`` bytes, and its answer always comes from
        ``-o``. Every failure sets ``provider_error_text`` so the failover
        classifier reads the typed outcome, never the raw streams (#9532).
        """
        _ = call_start_time
        file_bytes: bytes | None = None
        if output_file is not None:
            try:
                file_bytes = safe_read_attempt_file(
                    output_file,
                    trusted_root=Path(plan.metadata.get("parent_read_root", "/")) if plan else Path("/"),
                )
            except AttemptReadError as exc:
                return ParseResult(
                    ok=False, response="", failure_code=str(exc), stderr_excerpt=str(exc), provider_error_text=str(exc)
                )
            except FileNotFoundError:
                pass
        file_output = file_bytes.decode("utf-8", errors="replace").strip() if file_bytes is not None else ""
        reaped_digest = self._early_reaped_outputs.pop(str(output_file), None) if output_file is not None else None

        resumed_session_id = _resumed_session_id(plan)
        stream = parse_exec_stream(stdout)
        outcome = codex_outcome(stream, resumed_session_id=resumed_session_id)
        tool_calls = tool_calls_from_items(stream.completed_items)
        session_id = outcome.thread_id

        if outcome.state == "completed":
            # ``turn.completed`` precedes exec's -o write, so the process must
            # exit cleanly or have been reaped after its -o bytes were seen.
            reaped_intact = (
                reaped_digest is not None
                and file_bytes is not None
                and hashlib.sha256(file_bytes).hexdigest() == reaped_digest
            )
            if returncode == 0 or reaped_intact:
                return self._completed_result(
                    file_output,
                    plan=plan,
                    session_id=session_id,
                    tool_calls=tool_calls,
                    tokens=fresh_invocation_tokens(stream, resumed=resumed_session_id is not None),
                )
            outcome = replace(
                outcome, state="incomplete", failure_code=INCOMPLETE_FAILURE_CODE, detail="exit_after_turn_completed"
            )

        if outcome.state == "failed":
            failure_code = outcome.failure_code or "provider_error"
            message = " ".join((redact_text(outcome.provider_message) or "").split())
            return ParseResult(
                ok=False,
                response="",
                stderr_excerpt=f"{failure_code}: {message}"[:_EXCERPT_CHARS],
                rate_limited=failure_code == "rate_limited",
                session_id=session_id,
                tool_calls=tool_calls,
                failure_code=failure_code,
                provider_error_text=message,
            )

        # Incomplete: the stream proves neither success nor a provider failure.
        # stderr and notices are diagnostics only; they never classify.
        excerpt_parts = [f"{INCOMPLETE_FAILURE_CODE}: {outcome.detail} (rc={returncode})"]
        if stream.notices:
            excerpt_parts.append(f"last notice: {' '.join(stream.notices[-1].split())}")
        if stderr.strip():
            excerpt_parts.append(stderr.strip())
        return ParseResult(
            ok=False,
            response="",
            stderr_excerpt=(redact_text("\n".join(excerpt_parts)) or "")[:_EXCERPT_CHARS],
            session_id=session_id,
            tool_calls=tool_calls,
            failure_code=INCOMPLETE_FAILURE_CODE,
            provider_error_text="",
        )

    @staticmethod
    def _completed_result(
        file_output: str,
        *,
        plan: InvocationPlan | None,
        session_id: str | None,
        tool_calls: list[dict[str, Any]],
        tokens: int | None,
    ) -> ParseResult:
        output_schema = plan_output_schema(plan)
        if output_schema is not None:
            schema_result = structured_result(
                json_value(file_output), output_schema, returncode=0, session_id=session_id, tool_calls=tool_calls
            )
            return schema_result if schema_result.ok else replace(schema_result, provider_error_text="")
        if file_output:
            return ParseResult(
                ok=True, response=file_output, session_id=session_id, tokens=tokens, tool_calls=tool_calls
            )
        return ParseResult(
            ok=False,
            response="",
            stderr_excerpt="codex turn completed but wrote no final message to -o",
            session_id=session_id,
            tool_calls=tool_calls,
            provider_error_text="",
        )

    # ---------------------------------------------------------------------
    # Early reap — break out of a Codex CLI post-completion hang
    # ---------------------------------------------------------------------

    def check_early_reap(
        self,
        plan: InvocationPlan,
        *,
        call_start_time: float | None = None,
        stdout_lines: list[str] | None = None,
    ) -> bool:
        """Return True once the turn completed and its final ``-o`` bytes are stable.

        Codex 0.118 hung after finishing a turn, holding the call until the
        hard timeout. The runner calls this every poll tick with the captured
        stdout; True makes it kill the process and parse what is on disk.

        ``turn.completed`` precedes exec's shutdown and its ``-o`` write
        (``exec/src/lib.rs``), so completion alone never authorizes a reap:
        the same non-empty ``-o`` bytes must be seen on two checks at least
        two seconds apart. ``parse_response`` accepts a reaped call only when
        ``-o`` still holds exactly those bytes. Schema calls never reap: they
        must exit cleanly after writing their constrained result.
        """
        import time as _time

        if plan_output_schema(plan) is not None or stdout_lines is None or plan.output_file is None:
            return False
        now = _time.monotonic()
        if call_start_time is not None and (now - call_start_time) < 5.0:
            return False
        key = str(plan.output_file)
        if now - self._early_reap_checked_at.get(key, 0.0) < 2.0:
            return False
        self._early_reap_checked_at[key] = now

        lines = list(stdout_lines)
        last_line = next((line for line in reversed(lines) if line.strip()), "")
        try:
            last_event = _json.loads(last_line)
        except (ValueError, RecursionError):
            return False
        if not isinstance(last_event, dict) or last_event.get("type") != "turn.completed":
            return False
        stream = parse_exec_stream("".join(lines))
        if codex_outcome(stream, resumed_session_id=_resumed_session_id(plan)).state != "completed":
            return False
        try:
            output = safe_read_attempt_file(
                plan.output_file, trusted_root=Path(plan.metadata.get("parent_read_root", "/"))
            )
        except (AttemptReadError, OSError):
            return False
        if not output.strip():
            return False
        digest = hashlib.sha256(output).hexdigest()
        if self._early_reap_candidates.get(key) != digest:
            self._early_reap_candidates[key] = digest
            return False
        self._early_reap_candidates.pop(key, None)
        self._early_reap_checked_at.pop(key, None)
        self._early_reaped_outputs[key] = digest
        return True

    # ---------------------------------------------------------------------
    # Codex home and session directories (liveness signals only)
    # ---------------------------------------------------------------------

    def _codex_home_path(self) -> Path:
        """Return the Codex home this invocation should observe."""
        scope = getattr(self, "_codex_home_scope", None)
        if scope:
            return Path(scope)
        codex_home_env = os.environ.get("CODEX_HOME")
        if codex_home_env:
            return Path(codex_home_env)
        return Path.home() / ".codex"

    def _rollout_discovery_times(self) -> tuple[datetime, datetime]:
        """Return UTC and local clocks for Codex rollout date-dir discovery."""
        return datetime.now(UTC), datetime.now().astimezone()

    def _candidate_rollout_dirs(self) -> list[Path]:
        """Return plausible Codex rollout session dirs for liveness polling.

        Codex stores rollout files under the local-date session dir
        (``sessions/YYYY/MM/DD``). Include +/- 1 day around both UTC and local
        clocks so midnight-straddling runs are found in either direction. Only
        directory mtimes are polled; rollout contents are never read (#9532).

        Honors the per-invocation scoped ``$CODEX_HOME`` (the V7 writer's
        ``tool_config["codex_home_override"]``) so liveness watches the
        sessions directory the subprocess actually writes to.

        Resolution order:
        1. ``self._codex_home_scope`` — set at ``build_invocation``
           time from ``tool_config["codex_home_override"]``.
        2. ``os.environ["CODEX_HOME"]`` — for the (rare) case where
           the orchestrator itself exports CODEX_HOME.
        3. ``~/.codex/sessions/`` — legacy default.
        """
        base = self._codex_home_path() / "sessions"
        utc_now, local_now = self._rollout_discovery_times()
        dates = []
        seen_dates = set()
        for anchor in (utc_now, local_now):
            for delta in (-1, 0, 1):
                d = (anchor + timedelta(days=delta)).date()
                if d not in seen_dates:
                    seen_dates.add(d)
                    dates.append(d)
        dirs: list[Path] = []
        seen_dirs: set[Path] = set()
        for d in dates:
            candidate = base / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}"
            if candidate.exists() and candidate not in seen_dirs:
                seen_dirs.add(candidate)
                dirs.append(candidate)
        return dirs

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return paths the runner should poll for mtime changes.

        Note 2026-04-10: stall detection is no longer a kill condition
        (see watchdog.py::should_kill). The mtime poller still runs to
        populate WatchdogState.last_activity for observability — so
        getting the paths RIGHT still matters for future diagnostic
        logging and for the async delegate.py work, even though a
        missed signal no longer kills the process.

        Codex CLI 0.118.0 storage layout (verified empirically):
          - ``sessions/YYYY/MM/DD/rollout-*.jsonl`` is the ACTUAL live
            file. It grows throughout the run as reasoning messages
            and tool calls are streamed to disk. Confirmed: a 9-minute
            consultation run had its rollout file at 409KB and still
            growing.
          - ``sessions/YYYY/MM/DD/`` (the directory) only bumps on
            child file *creation*, not on content writes. Useful for
            catching the startup signal but goes silent during the run.
          - ``state_5.sqlite`` bumps intermittently (not reliably on
            every message). Kept as a secondary signal.
          - ``logs_1.sqlite``, ``history.jsonl`` are stale in 0.118+
            but kept as fallbacks for older CLI versions.
          - ``plan.output_file`` is the -o target; empty during the run
            and only written at the very end on success, but kept as
            a signal for the "Codex is writing the final response" moment.

        We include plausible session dirs around the UTC and local dates
        so the mtime poller catches Codex startup even when UTC and local
        dates differ.
        """
        paths: list[Path] = []
        if plan.output_file is not None:
            paths.append(plan.output_file)

        codex_home = self._codex_home_path()

        # Secondary / fallback signals
        for rel in ("state_5.sqlite", "history.jsonl", "logs_1.sqlite"):
            candidate = codex_home / rel
            if candidate.exists():
                paths.append(candidate)

        # Plausible sessions directories catch startup via dir mtime bumps
        # but do NOT track subsequent content writes.
        for sessions_dir in self._candidate_rollout_dirs():
            if sessions_dir not in paths:
                paths.append(sessions_dir)

        # Note: we deliberately do NOT include the newest rollout-*.jsonl
        # file here. Earlier versions tried to track it for
        # last_activity updates, but glob-at-build-time is wrong: the
        # file matching "newest" is the PREVIOUS run's rollout, not
        # this run's (which doesn't exist yet). The wrong file both
        # (a) never updates during our run so provides no liveness
        # signal, and (b) would leak the wrong trace into
        # tail_liveness_file_for_debug() on failure. Removed after
        # Gemini review, 2026-04-10. The directory mtime above still
        # bumps when Codex creates its new rollout file at startup,
        # which is good enough for the dispatch-once-at-start signal
        # the mtime poller actually uses.
        #
        # Proper fix (deferred): pass a glob pattern or a build-time
        # snapshot into the runner and let the poller dynamically
        # resolve "any file matching ROLLOUT_GLOB whose mtime changed
        # after POLL_START". Bigger API change; filed as follow-up.

        return tuple(paths)

    @staticmethod
    def _mode_flags(mode: str) -> list[str]:
        """Map runtime mode → codex exec sandbox flags.

        Mirrors ``start-codex.sh`` (the canonical interactive launcher) for
        any non-read-only mode. The launcher unconditionally passes
        ``--dangerously-bypass-approvals-and-sandbox`` AND
        ``--enable multi_agent`` for every interactive Codex session on
        this project; the same flags are required for headless writers
        because Codex's ``--full-auto`` (the previous workspace-write
        mapping) silently blocks localhost MCP server connections,
        leaving writers unable to call ``verify_words``, ``search_text``,
        and other MCP-backed tools. Empirically verified 2026-05-08:
        codex with ``--full-auto`` returned
        "Tool unavailable: ``mcp__sources__verify_words`` is not
        available in this session"; the same prompt with the bypass
        flag set called the tool successfully.

        The runtime ``mode`` parameter is still retained for gating in
        higher layers; at the codex CLI level workspace-write and danger
        produce the same flag set because Codex has no distinct
        "workspace-write + MCP-allowed" mode. This is the cost of
        Codex's coarser sandbox model; worktree isolation is the actual
        security boundary for headless dispatches.

        Matches the mapping in _codex.py::_codex_bridge_flags and
        dispatch.py::_codex_dispatch_flags for consistency during migration.
        """
        if mode == "read-only":
            return ["-s", "read-only"]
        # workspace-write and danger both need the bypass flag for MCP
        # access. multi_agent is on by default to match start-codex.sh.
        return [
            "--dangerously-bypass-approvals-and-sandbox",
            "--enable",
            "multi_agent",
        ]
