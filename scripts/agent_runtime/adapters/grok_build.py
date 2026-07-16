"""GrokBuildAdapter — wraps the native ``grok`` CLI headless.

Registry seat id is canonical ``grok`` (historical alias ``grok-build``).
DISTINCT from the Hermes-backed ``grok-hermes`` agent (``HermesGrokAdapter``,
``grok-4.5`` via the Hermes OAuth API path). This adapter drives
the local ``grok`` CLI binary (``~/.local/bin/grok``) in
single-turn headless mode:

    grok -p "<prompt>" --output-format json [-m MODEL] [--effort LEVEL] \
         --permission-mode <mode> --cwd <dir> --no-alt-screen

Headless JSON output is a single object: ``{text, stopReason, sessionId, ...}``.
The CLI uses its own stored auth under ``~/.grok`` (OAuth), so no API key is
injected — HOME (already allow-listed by env_sanitize) is sufficient.

Mode → ``--permission-mode``:
- ``read-only``       → ``plan``               (analysis only, no mutations)
- ``workspace-write`` → ``acceptEdits``        (auto-accept file edits, headless)
- ``danger``          → ``bypassPermissions``  (full autonomy)

``resume_policy`` is ``never`` in the registry: the CLI's ``--resume`` +
cross-session memory risk worktree contamination — the same footgun as Codex.
The grok CLI is Claude-Code-shaped, so this mirrors ``claude.py`` closely.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|\b429\b",
    re.IGNORECASE,
)

# Runtime mode → grok CLI --permission-mode value.
_MODE_PERMISSION: dict[str, str] = {
    "read-only": "plan",
    "workspace-write": "acceptEdits",
    "danger": "bypassPermissions",
}

# MCP servers that are safe to run under an execution-capable permission mode
# (read-only data lookups, no mutations). ONLY these may trigger the plan→exec
# override below; any other / future write-capable server falls back to the
# normal (safer) mode mapping rather than silently gaining execution rights.
_READ_ONLY_MCP_SERVERS: frozenset[str] = frozenset({"sources"})

# Defense-in-depth for MCP reviews: even though `bypassPermissions` auto-approves
# tool calls so the MCP read tools execute, explicit `--deny` rules still win
# (per grok's permission model: deny > bypass). Denying file-write + shell tools
# means a prompt-injected review article cannot make grok mutate the filesystem
# or run shell — it can only call the read-only MCP tools the review needs.
_MCP_REVIEW_DENY_RULES: tuple[str, ...] = (
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "search_replace",
    "Bash",
)
GROK_ALLOWED_MODELS: frozenset[str] = frozenset({"grok-4.5"})
GROK_BUILD_DEFAULT_MODEL = "grok-4.5"
GROK_BUILD_DEFAULT_EFFORT = os.environ.get("LEARN_UK_GROK_BUILD_EFFORT", "high")


class GrokBuildAdapter:
    """Adapter for the native ``grok`` CLI in single-turn headless mode."""

    name: str = "grok"
    default_model: str = GROK_BUILD_DEFAULT_MODEL
    default_effort: str = GROK_BUILD_DEFAULT_EFFORT
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

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
        if mode not in self.supported_modes:
            raise ValueError(f"GrokBuildAdapter: unsupported mode {mode!r} (supported: {sorted(self.supported_modes)})")
        tc = tool_config or {}
        review_isolation = bool(tc.get("review_isolation"))
        review_write_root: Path | None = None
        if review_isolation:
            from scripts.review.isolation import validated_review_write_root

            review_write_root = validated_review_write_root(tc)
            trusted = tc.get("review_engine_binary")
            if not isinstance(trusted, str) or not Path(trusted).is_absolute():
                raise ValueError("GrokBuildAdapter: trusted review_engine_binary required")
            grok_bin = trusted
        else:
            grok_bin = shutil.which("grok")
        if not grok_bin:
            raise RuntimeError(
                "grok CLI not found on PATH. Install the xAI grok CLI "
                "(provides `grok`) to dispatch the native `grok` seat "
                "(historical alias: `grok-build`)."
            )
        requested_model = model or self.default_model
        if requested_model not in GROK_ALLOWED_MODELS:
            raise ValueError(
                f"GrokBuildAdapter: unsupported Grok model {requested_model!r}; allowed: {sorted(GROK_ALLOWED_MODELS)}"
            )
        if "sources" in (tc.get("mcp_server_names") or []):
            prompt = _adapt_prompt_for_grok_build_mcp(prompt)

        cmd: list[str] = [grok_bin]
        execution_cwd = cwd
        # Prompt: inline via -p for the common case; a hyphen-leading prompt
        # would be misparsed by clap as a flag, so route those through a temp
        # --prompt-file instead (robust for any content).
        if review_isolation and review_write_root is not None:
            write_root = review_write_root
            out_dir = write_root / "tmp"
            execution_cwd = write_root / "exec"
            prompt_file = out_dir / "grok-prompt.txt"
            fd = os.open(
                prompt_file,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            with os.fdopen(fd, "wb") as handle:
                handle.write(prompt.encode("utf-8"))
            prompt_path = str(prompt_file)
            cmd.extend(["--prompt-file", prompt_path])
        elif prompt.startswith("-"):
            if review_isolation:
                raise ValueError("GrokBuildAdapter: isolated review prompt file requires review_write_root")
            else:
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".grok-prompt.txt", delete=False, encoding="utf-8"
                ) as handle:
                    handle.write(prompt)
                    prompt_path = handle.name
            cmd.extend(["--prompt-file", prompt_path])
        else:
            cmd.extend(["-p", prompt])

        cmd.extend(["--output-format", "json", "--no-alt-screen"])
        # read-only maps to grok `plan` mode, which is analysis-only and BLOCKS
        # tool execution. MCP-grounded reviews MUST execute tool calls (e.g.
        # sources__verify_word), so when ONLY known read-only MCP servers are
        # requested we override to an execution-capable mode. Defense-in-depth:
        # the `--deny` rules below block file writes + shell even under bypass
        # (deny wins over bypassPermissions), so a prompt-injected review article
        # cannot make grok mutate the filesystem or run shell. Any non-read-only
        # or non-MCP call keeps its normal (safer) mode mapping.
        mcp_servers_requested = set(tc.get("mcp_server_names") or [])
        mcp_read_only = bool(mcp_servers_requested) and mcp_servers_requested <= _READ_ONLY_MCP_SERVERS
        # Review isolation (#5285): force plan/read-only and explicit deny rules.
        # Keys match review_isolation_tool_config: disallowed_tools, review_deny_tools.
        if review_isolation:
            permission_mode = str(tc.get("permission_mode") or "plan")
        else:
            permission_mode = "bypassPermissions" if mcp_read_only else _MODE_PERMISSION[mode]
        cmd.extend(["--permission-mode", permission_mode])
        cmd.extend(["--cwd", str(execution_cwd)])
        if mcp_read_only and not review_isolation:
            cmd.append("--always-approve")
            cmd.append("--no-plan")
            cmd.append("--disable-web-search")
            for rule in _MCP_REVIEW_DENY_RULES:
                cmd.extend(["--deny", rule])
        if review_isolation:
            cmd.extend(["--no-memory", "--no-subagents", "--disable-web-search", "--verbatim"])
            deny_rules = tc.get("review_deny_tools") or list(_MCP_REVIEW_DENY_RULES)
            if isinstance(deny_rules, (list, tuple)):
                for rule in deny_rules:
                    if rule:
                        cmd.extend(["--deny", str(rule)])

        effective_effort = effort or self.default_effort
        cmd.extend(["-m", requested_model])
        if effective_effort:
            # grok accepts the same levels as the runtime: low|medium|high|xhigh|max
            cmd.extend(["--effort", effective_effort])

        disallowed = tc.get("disallowed_tools")
        if disallowed:
            cmd.extend(["--disallowed-tools", str(disallowed)])
        allowed = tc.get("allowed_tools")
        if allowed and not review_isolation:
            cmd.extend(["--tools", str(allowed)])

        # Resume only if the caller explicitly opts in (delegate dispatch never
        # should — resume_policy=never — to avoid cross-worktree contamination).
        if session_id and tc.get("resume"):
            cmd.extend(["--resume", session_id])

        _logger.debug(
            "grok invocation: task=%s mode=%s permission=%s model=%s effort=%s",
            task_id,
            mode,
            _MODE_PERMISSION[mode],
            requested_model,
            effective_effort,
        )

        return InvocationPlan(
            cmd=cmd,
            cwd=execution_cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={},
            liveness_paths=self._liveness_paths(),
        )

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
        _ = (output_file, plan, call_start_time)  # grok -p flushes to stdout

        obj = _parse_json_object(stdout)
        if obj is not None:
            text = str(obj.get("text") or "").strip()
            sid = obj.get("sessionId") or obj.get("session_id")
            session_id = sid if isinstance(sid, str) and sid else None
        else:
            # Fallback: --output-format plain, or noise before the JSON.
            text = (stdout or "").strip()
            session_id = None

        usable = bool(text)
        failed = returncode != 0 or not usable
        rate_limited = failed and bool(_RATE_LIMIT_RE.search(f"{stderr or ''}\n{stdout or ''}"))
        ok = returncode == 0 and usable and not rate_limited

        stderr_excerpt: str | None = None
        if not ok:
            source = (stderr or "").strip() or (stdout or "").strip() or ""
            stderr_excerpt = source[:500] or None

        return ParseResult(
            ok=ok,
            response=text if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # grok JSON does not report token counts
            tool_calls=[],
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return self._liveness_paths()

    def _liveness_paths(self) -> tuple[Path, ...]:
        # grok keeps session/leader state under ~/.grok; mtime bumps there are
        # a liveness signal when stdout is quiet.
        grok_home = Path.home() / ".grok"
        return (grok_home,) if grok_home.exists() else ()


def _translate_mcp_prefix_for_grok_build(prompt: str) -> str:
    """Rewrite canonical MCP names to native grok-build tool names."""
    return prompt.replace("mcp__sources__", "sources__")


def _adapt_prompt_for_grok_build_mcp(prompt: str) -> str:
    """Adapt canonical MCP review prompts for native grok-build headless."""
    translated = _translate_mcp_prefix_for_grok_build(prompt)
    return (
        translated + "\n\n## Native grok-build headless compatibility\n\n"
        "You are running in native grok-build single-turn headless mode. "
        "Do not call abstract `search_tool` or `use_tool` protocols, do not "
        "call `read_file`, and do not describe a plan. The article text and "
        "instructions above are sufficient for this review. Return the final "
        "JSON object now, starting with `{` and ending with `}`.\n"
    )


def _parse_json_object(stdout: str) -> dict | None:
    """Parse the single JSON object grok emits in --output-format json.

    Tolerant of leading/trailing log noise: tries a strict parse first, then
    extracts the outermost ``{...}`` span.
    """
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except ValueError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else None
        except ValueError:
            return None
    return None
