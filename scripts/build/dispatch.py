"""Unified V6 dispatch — all LLM subprocess calls + logging in one place.

Every call to Gemini or Claude from v6_build.py goes through dispatch_agent().
This centralizes:
- subprocess execution with timing
- stderr capture (tool calls, errors, debug info)
- structured dispatch logs to orchestration/{slug}/dispatch/
- heartbeat logging for long-running calls
- rate limit detection and inter-call pacing

Issue: #1029 (observability)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from utils.claude_version import supports_exclude_dynamic_system_prompt_sections

# Command prefix for invoking Claude Code in print mode from this dispatcher.
# Passed to utils.claude_version so the version probe targets the exact
# binary this dispatcher will execute.
_CLAUDE_CMD_PREFIX: tuple[str, ...] = ("npx", "@anthropic-ai/claude-code@latest")

# ---------------------------------------------------------------------------
# Rate limit detection + pacing
# ---------------------------------------------------------------------------

# Patterns in stderr that indicate rate limiting (not content errors)
_RATE_LIMIT_PATTERNS = (
    "429",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "rate_limit",
    "quota exceeded",
    "No capacity available",
    "capacity",
    "too many requests",
    "Too Many Requests",
)

# Minimum seconds between consecutive Gemini CLI calls (prevents burst-induced 429s)
_GEMINI_INTER_CALL_DELAY = 3.0
_last_gemini_call_time: float = 0.0

_CODEX_MODES = {"safe", "workspace-write", "full-auto", "danger"}


def _is_rate_limited(stderr: str) -> bool:
    """Check if a failure was caused by rate limiting."""
    stderr_lower = stderr.lower()
    return any(pat.lower() in stderr_lower for pat in _RATE_LIMIT_PATTERNS)


def _pace_gemini_calls() -> None:
    """Enforce minimum delay between Gemini CLI calls to avoid bursts."""
    global _last_gemini_call_time
    if _last_gemini_call_time > 0:
        elapsed = time.monotonic() - _last_gemini_call_time
        if elapsed < _GEMINI_INTER_CALL_DELAY:
            wait = _GEMINI_INTER_CALL_DELAY - elapsed
            time.sleep(wait)
    _last_gemini_call_time = time.monotonic()


def _codex_dispatch_mode(agent: str) -> str:
    """Resolve Codex sandbox mode for tool-enabled dispatch calls."""
    requested = (
        os.environ.get("CODEX_DISPATCH_MODE")
        or os.environ.get("CODEX_CLI_MODE")
        or ""
    ).strip().lower()
    if requested:
        if requested in _CODEX_MODES:
            return "workspace-write" if requested == "full-auto" else requested
        _log(f"  ⚠️  Invalid CODEX_DISPATCH_MODE='{requested}' — falling back to default")
    return "workspace-write" if agent.endswith("-tools") else "safe"


def _codex_dispatch_flags(agent: str) -> list[str]:
    """Translate Codex dispatch mode to CLI flags."""
    mode = _codex_dispatch_mode(agent)
    if mode == "danger":
        return ["--dangerously-bypass-approvals-and-sandbox"]
    if mode == "workspace-write":
        return ["--full-auto"]
    return ["-s", "read-only"]


def _codex_runtime_mode(agent: str) -> str:
    """Translate dispatch's Codex mode vocabulary to runtime vocabulary.

    Dispatch uses: safe, workspace-write, full-auto, danger.
    Runtime uses:  read-only, workspace-write, danger.
    This bridges the two during the Phase 3 migration.
    """
    dispatch_mode = _codex_dispatch_mode(agent)
    if dispatch_mode == "danger":
        return "danger"
    if dispatch_mode == "workspace-write":
        return "workspace-write"
    return "read-only"  # "safe" → "read-only"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Allowed MCP tools (single source of truth)
# ---------------------------------------------------------------------------

# Claude writer: all RAG tools + Read (no Edit/Write/Bash)
CLAUDE_WRITER_TOOLS = (
    "mcp__rag__verify_word,"
    "mcp__rag__verify_words,"
    "mcp__rag__verify_lemma,"
    "mcp__rag__search_text,"
    "mcp__rag__search_images,"
    "mcp__rag__search_literary,"
    "mcp__rag__query_pravopys,"
    "mcp__rag__query_wikipedia,"
    "mcp__rag__search_style_guide,"
    "mcp__rag__query_cefr_level,"
    "mcp__rag__search_definitions,"
    "mcp__rag__search_etymology,"
    "mcp__rag__search_idioms,"
    "mcp__rag__search_synonyms,"
    "mcp__rag__translate_en_uk,"
    "mcp__rag__query_grac,"
    "mcp__rag__query_ulif,"
    "mcp__rag__query_r2u,"
    "Read"
)

# Claude reviewer: verification + quality + reference tools
CLAUDE_REVIEWER_TOOLS = (
    "mcp__rag__verify_word,"
    "mcp__rag__verify_words,"
    "mcp__rag__verify_lemma,"
    "mcp__rag__search_style_guide,"
    "mcp__rag__query_r2u,"
    "mcp__rag__query_cefr_level,"
    "mcp__rag__search_definitions,"
    "mcp__rag__search_etymology,"
    "mcp__rag__search_idioms,"
    "mcp__rag__search_synonyms,"
    "mcp__rag__query_grac,"
    "mcp__rag__search_text,"
    "mcp__rag__search_literary,"
    "mcp__rag__query_pravopys,"
    "mcp__rag__query_wikipedia,"
    "Read"
)


# ---------------------------------------------------------------------------
# Dispatch log persistence
# ---------------------------------------------------------------------------

# Phase → sequence number for predictable sort order
_PHASE_SEQ = {
    "pre-verify": "00",
    "skeleton": "01",
    "write": "02",
    "activities": "02b",
    "vocab": "03",
    "enrich": "04",
    "review": "05",
}


def _save_dispatch_log(
    orch_dir: Path,
    phase: str,
    agent: str,
    *,
    prompt_chars: int = 0,
    response_chars: int = 0,
    stderr: str = "",
    returncode: int | None = None,
    duration_s: float = 0.0,
    ok: bool = False,
) -> None:
    """Save dispatch metadata + stderr for debugging agent communications."""
    log_dir = orch_dir / "dispatch"
    log_dir.mkdir(parents=True, exist_ok=True)

    seq = _PHASE_SEQ.get(phase, "99")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{seq}-{phase}-{ts}"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "phase": phase,
        "agent": agent,
        "ok": ok,
        "returncode": returncode,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "duration_s": round(duration_s, 1),
    }

    # Save metadata
    meta_path = log_dir / f"{base}-meta.json"
    meta_path.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))

    # Always save stderr (even if empty — removes ambiguity)
    stderr_path = log_dir / f"{base}.stderr.log"
    stderr_path.write_text(stderr or "")

    stderr_info = f", stderr: {len(stderr)} chars" if stderr and stderr.strip() else ""
    _log(f"  📋 Dispatch log → dispatch/{base}-meta.json ({duration_s:.0f}s{stderr_info})")


# ---------------------------------------------------------------------------
# Unified dispatch
# ---------------------------------------------------------------------------

def dispatch_agent(
    prompt: str,
    *,
    agent: str,
    phase: str,
    orch_dir: Path,
    timeout: int = 600,
    mcp_tools: bool = False,
    allowed_tools: str | None = None,
    model: str | None = None,
) -> tuple[bool, str]:
    """Unified dispatcher for Gemini and Claude subprocess calls.

    Args:
        prompt: The full prompt text to send.
        agent: Writer/reviewer mode — "gemini", "gemini-tools", "claude", "claude-tools",
            "codex", or "codex-tools".
        phase: Pipeline phase name — "skeleton", "write", "vocab", "review".
        orch_dir: Path to orchestration/{slug}/ for saving logs.
        timeout: Subprocess timeout in seconds.
        mcp_tools: Whether MCP tools are enabled for this dispatch.
        allowed_tools: Comma-separated Claude --allowedTools string (Claude only).
        model: Model override. If None, resolved from batch_gemini_config.

    Returns:
        (success, stdout_text)

    Migration note: Codex and Gemini branches are routed through
    ``scripts.agent_runtime.runner.invoke()`` (Phase 3 of #1184).
    Claude branch remains on the legacy subprocess path until Phase 5.
    """
    is_gemini = agent.startswith("gemini")
    is_claude = agent.startswith("claude")
    is_codex = agent.startswith("codex")

    if not is_gemini and not is_claude and not is_codex:
        _log(f"  ❌ Unknown agent: {agent}")
        return False, ""

    # Resolve model
    if model is None:
        if is_gemini:
            from batch_gemini_config import PRO_MODEL
            model = PRO_MODEL
        elif is_codex:
            model = "gpt-5.4"
        else:
            from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT
            model = CLAUDE_MODEL_CORE_CONTENT

    agent_label = f"{agent} ({model})"
    _log(f"  Dispatching to {agent_label}...")

    # ---------- Codex + Gemini routed through agent_runtime (Phase 3) ----------
    if is_codex or is_gemini:
        return _dispatch_via_runtime(
            prompt=prompt,
            agent=agent,
            phase=phase,
            orch_dir=orch_dir,
            timeout=timeout,
            mcp_tools=mcp_tools,
            model=model,
            agent_label=agent_label,
            is_gemini=is_gemini,
        )

    # ---------- Claude still uses the legacy path (Phase 5 will migrate) ----------
    if False:  # pragma: no cover — structural placeholder
        pass
    else:
        mcp_config = str(PROJECT_ROOT / ".mcp.json")
        cmd = [
            *_CLAUDE_CMD_PREFIX, "-p",
            "--model", model,
            "--output-format", "text",
        ]
        if supports_exclude_dynamic_system_prompt_sections(_CLAUDE_CMD_PREFIX):
            cmd.append("--exclude-dynamic-system-prompt-sections")
        if mcp_tools and allowed_tools:
            cmd.extend(["--mcp-config", mcp_config, "--allowedTools", allowed_tools])

    # Execute with timing + Gemini fallback
    # Set LEARN_UKRAINIAN_PIPELINE to skip SessionStart/UserPromptSubmit hooks
    env = {**os.environ, "LEARN_UKRAINIAN_PIPELINE": "1"}

    def _run_cmd(run_cmd, run_label, run_timeout):
        t0 = time.monotonic()
        output_path: str | None = None
        if is_codex:
            with tempfile.NamedTemporaryFile(
                prefix="codex-dispatch-", suffix=".txt", delete=False
            ) as tmp:
                output_path = tmp.name
            if run_cmd and run_cmd[-1] == "-":
                run_cmd = [*run_cmd[:-1], "-o", output_path, "-"]
            else:
                run_cmd = [*run_cmd, "-o", output_path]
        try:
            result = subprocess.run(
                run_cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=run_timeout,
                cwd=str(PROJECT_ROOT),
                env=env,
            )
            elapsed = time.monotonic() - t0
            ok = result.returncode == 0
            raw = result.stdout if ok else ""
            stderr = result.stderr or ""
            if is_codex:
                file_output = Path(output_path).read_text("utf-8") if output_path and Path(output_path).exists() else ""
                raw = file_output if ok else ""
                if not ok and file_output.strip():
                    stderr = "\n".join(part for part in (stderr.strip(), "[codex output file]", file_output.strip()) if part)
                stderr = "\n".join(part for part in ((result.stdout or "").strip(), stderr.strip()) if part)

            if not ok:
                _log(f"  ❌ {run_label} returned error (rc={result.returncode}): {stderr[:200]}")

            _save_dispatch_log(
                orch_dir, phase, run_label,
                prompt_chars=len(prompt),
                response_chars=len(raw),
                stderr=stderr,
                returncode=result.returncode,
                duration_s=elapsed,
                ok=ok,
            )
            return ok, raw

        except subprocess.TimeoutExpired as e:
            elapsed = time.monotonic() - t0
            _log(f"  ❌ {run_label} timed out ({run_timeout}s)")
            partial_stderr = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or "")
            partial_stdout = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or "")
            _save_dispatch_log(
                orch_dir, phase, run_label,
                prompt_chars=len(prompt),
                response_chars=len(partial_stdout),
                stderr=partial_stderr,
                duration_s=elapsed,
                ok=False,
            )
            return False, ""
        finally:
            if output_path:
                Path(output_path).unlink(missing_ok=True)

    ok, raw = _run_cmd(cmd, agent_label, timeout)
    return ok, raw


def _dispatch_via_runtime(
    *,
    prompt: str,
    agent: str,
    phase: str,
    orch_dir: Path,
    timeout: int,
    mcp_tools: bool,
    model: str,
    agent_label: str,
    is_gemini: bool,
) -> tuple[bool, str]:
    """Route Codex + Gemini dispatch through scripts.agent_runtime.runner.invoke().

    Preserves the legacy behavior the pipeline depends on:
    - Pacing between Gemini calls to prevent burst-induced rate limits
    - Model fallback (Pro → Flash) on non-rate-limited failure
    - __RATE_LIMITED__ sentinel in the return value for rate-limited calls
    - Writes to orchestration/{slug}/dispatch/ via _save_dispatch_log
      (this is PIPELINE observability, separate from the runtime's
      batch_state/api_usage/ records — both logs are written)
    """
    from agent_runtime.errors import (
        AgentStalledError,
        AgentTimeoutError,
        RateLimitedError,
    )
    from agent_runtime.runner import invoke as runtime_invoke

    # Determine mode + tool_config based on legacy agent name
    if is_gemini:
        # Gemini in the pipeline is always -y (write-enabled) — existing behavior.
        runtime_mode = "workspace-write"
        tool_config: dict | None = None
        if mcp_tools:
            tool_config = {"mcp_server_names": ["rag"]}
        # Pace Gemini calls (preserved from legacy path)
        _pace_gemini_calls()
    else:
        # Codex
        runtime_mode = _codex_runtime_mode(agent)
        tool_config = None  # Codex has no MCP tool restrictions

    def _call_runtime(call_model: str, label: str) -> tuple[bool, str, str, float, int | None]:
        """One invocation. Returns (ok, response, stderr_excerpt, duration, returncode)."""
        t0 = time.monotonic()
        try:
            result = runtime_invoke(
                "gemini" if is_gemini else "codex",
                prompt,
                mode=runtime_mode,
                cwd=PROJECT_ROOT,
                model=call_model,
                task_id=f"{phase}-{orch_dir.name}" if orch_dir else phase,
                session_id=None,  # dispatch never uses resume
                tool_config=tool_config,
                entrypoint="dispatch",
                hard_timeout=timeout,
                stall_timeout=min(180, timeout),
            )
            elapsed = time.monotonic() - t0
            _save_dispatch_log(
                orch_dir, phase, label,
                prompt_chars=len(prompt),
                response_chars=len(result.response),
                stderr=result.stderr_excerpt or "",
                returncode=result.returncode,
                duration_s=elapsed,
                ok=result.ok,
            )
            return result.ok, result.response, result.stderr_excerpt or "", elapsed, result.returncode
        except RateLimitedError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ⏳ {label} rate limited: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"RateLimitedError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
            )
            # Use a special return tuple to signal rate limiting upstream.
            return False, "__RATE_LIMITED__", str(exc), elapsed, None
        except AgentStalledError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ❌ {label} stalled: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"AgentStalledError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
            )
            return False, "", str(exc), elapsed, None
        except AgentTimeoutError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ❌ {label} hard timeout: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"AgentTimeoutError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
            )
            return False, "", str(exc), elapsed, None

    # First attempt
    ok, raw, _, _, _ = _call_runtime(model, agent_label)
    if ok:
        return True, raw

    # Short-circuit rate-limited: don't fall back, same quota
    if raw == "__RATE_LIMITED__":
        _log("  ⏳ Rate limited — skipping fallback model (same quota)")
        return False, "__RATE_LIMITED__"

    # Gemini-only fallback to secondary model (Pro → Flash)
    if is_gemini:
        from batch_gemini_config import FALLBACK_MODEL
        if model != FALLBACK_MODEL:
            _pace_gemini_calls()
            fallback_label = f"{agent} ({FALLBACK_MODEL})"
            _log(f"  🔄 Retrying with fallback model: {fallback_label}")
            ok2, raw2, _, _, _ = _call_runtime(FALLBACK_MODEL, fallback_label)
            if raw2 == "__RATE_LIMITED__":
                return False, "__RATE_LIMITED__"
            return ok2, raw2

    return ok, raw
