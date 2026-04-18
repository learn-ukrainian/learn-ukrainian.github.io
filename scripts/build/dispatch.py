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
import time
from datetime import datetime
from pathlib import Path

from agent_runtime.tool_config import build_mcp_tool_config

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
_CYRILLIC_RE = re.compile(r"[А-Яа-яЇїІіЄєҐґ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


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


def _token_divisor_for_text(text: str | None) -> float:
    """Estimate chars-per-token based on script mix in the text."""
    if not text:
        return 3.8
    cyrillic = len(_CYRILLIC_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    if cyrillic and not latin:
        return 3.5
    if latin and not cyrillic:
        return 4.0
    return 3.8


def _estimate_tokens(char_count: int, text: str | None = None) -> int:
    """Cheap token estimate for cost tracking; no external tokenizer."""
    if char_count <= 0:
        return 0
    divisor = _token_divisor_for_text(text)
    return round(char_count / divisor)


def _get_gemini_fallback_chain(model: str) -> list[str]:
    """Resolve Gemini fallback order without relying on optional helpers."""
    try:
        from batch_gemini_config import (
            FALLBACK_MODEL,
            FLASH_LITE_MODEL,
            FLASH_MODEL,
            PRO_MODEL,
        )
    except ImportError:
        return ["auto"] if model != "auto" else []

    ordered = [FLASH_LITE_MODEL, FLASH_MODEL, PRO_MODEL, FALLBACK_MODEL]
    if model in ordered:
        start = ordered.index(model) + 1
        return [candidate for candidate in ordered[start:] if candidate != model]
    return [candidate for candidate in (PRO_MODEL, FALLBACK_MODEL) if candidate != model]


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
    "review-style": "05b",
}


def _save_dispatch_log(
    orch_dir: Path,
    phase: str,
    agent: str,
    *,
    model: str | None = None,
    prompt_chars: int = 0,
    response_chars: int = 0,
    stderr: str = "",
    returncode: int | None = None,
    duration_s: float = 0.0,
    ok: bool = False,
    prompt: str | None = None,
    response: str | None = None,
    call_start_time: datetime | None = None,
) -> None:
    """Save dispatch metadata + stderr for debugging agent communications.

    If ``prompt`` and ``response`` are both provided (and the call was
    successful), we also write a ``session-analysis-{phase}.yaml`` next
    to the dispatch log with a prompt-size breakdown and directive
    compliance report. This is best-effort — any failure is swallowed
    so telemetry never breaks a build.
    """
    log_dir = orch_dir / "dispatch"
    log_dir.mkdir(parents=True, exist_ok=True)

    seq = _PHASE_SEQ.get(phase, "99")
    now = datetime.now()
    ts = now.strftime("%Y%m%d-%H%M%S-%f")
    suffix = f"{time.monotonic_ns() % 1_000_000_000:09d}"
    base = f"{seq}-{phase}-{ts}-{suffix}"

    log_entry = {
        "timestamp": now.isoformat(),
        "phase": phase,
        "agent": agent,
        "model": model,
        "ok": ok,
        "returncode": returncode,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "prompt_tokens_est": _estimate_tokens(prompt_chars, prompt),
        "response_tokens_est": _estimate_tokens(response_chars, response),
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

    # Best-effort post-dispatch session analysis (#1174). Only runs when
    # the caller passed the actual prompt + response text, the call was
    # successful, and the agent is Gemini (Codex/Claude session parsers
    # may land later). Any failure is swallowed.
    if ok and prompt and response and ("gemini" in agent.lower()):
        try:
            from build.session_analysis import build_report, write_report_yaml
            report = build_report(
                prompt, response, phase=phase,
                session_path="",  # set below if we can resolve it
            )
            # Best-effort correlation to the on-disk Gemini session file.
            if call_start_time is not None:
                from build.gemini_session import find_session_near_time
                matched = find_session_near_time(call_start_time)
                if matched is not None:
                    report.session_path = str(matched)
            analysis_path = log_dir / f"{base}-session-analysis.yaml"
            write_report_yaml(report, analysis_path)
            if report.large_sections:
                _log(
                    f"  📊 Session analysis: large prompt sections {report.large_sections} "
                    f"({report.directives_covered}/{report.directives_total} directives covered)"
                )
            else:
                _log(
                    f"  📊 Session analysis: "
                    f"{report.directives_covered}/{report.directives_total} directives covered"
                )
        except Exception as exc:  # pragma: no cover — observability only
            _log(f"  ⚠️  Session analysis skipped: {type(exc).__name__}: {exc}")


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
    cascade_per_call_max_s: int | None = None,
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
    is_gemma_local = agent.startswith("gemma-local")
    is_claude = agent.startswith("claude")
    is_codex = agent.startswith("codex")

    if not is_gemini and not is_gemma_local and not is_claude and not is_codex:
        _log(f"  ❌ Unknown agent: {agent}")
        return False, ""

    # Resolve model
    if model is None:
        if is_gemini:
            from batch_gemini_config import PRO_MODEL
            model = PRO_MODEL
        elif is_gemma_local:
            model = "mlx-community/gemma-4-e4b-it-4bit"
        elif is_codex:
            model = "gpt-5.4"
        else:
            from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT
            model = CLAUDE_MODEL_CORE_CONTENT

    agent_label = f"{agent} ({model})"
    _log(f"  Dispatching to {agent_label}...")
    if is_gemini:
        from agent_runtime.adapters.gemini import resolve_gemini_auth_mode

        _log(f"  Gemini auth mode: {resolve_gemini_auth_mode()}")

    # ---------- All three agents now routed through agent_runtime (Phase 3 + 5) ----------
    if is_codex or is_gemini or is_gemma_local:
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
            runtime_agent_name="gemma-local" if is_gemma_local else ("gemini" if is_gemini else "codex"),
            cascade_per_call_max_s=cascade_per_call_max_s,
        )
    if is_claude:
        return _dispatch_claude_via_runtime(
            prompt=prompt,
            agent=agent,
            phase=phase,
            orch_dir=orch_dir,
            timeout=timeout,
            mcp_tools=mcp_tools,
            allowed_tools=allowed_tools,
            model=model,
            agent_label=agent_label,
        )
    return False, ""


def _dispatch_claude_via_runtime(
    *,
    prompt: str,
    agent: str,
    phase: str,
    orch_dir: Path,
    timeout: int,
    mcp_tools: bool,
    allowed_tools: str | None,
    model: str,
    agent_label: str,
) -> tuple[bool, str]:
    """Route Claude dispatch through scripts.agent_runtime.runner.invoke().

    Phase 5: Claude joins Codex + Gemini on the runtime. Preserves
    legacy behavior:
    - MCP tool config via the shared agent_runtime builder
    - No session resume (dispatch uses fresh sessions)
    - --exclude-dynamic-system-prompt-sections is applied inside ClaudeAdapter
      via utils.claude_version gating
    - Writes dispatch log to orchestration/{slug}/dispatch/
    """
    from agent_runtime.errors import (
        AgentStalledError,
        AgentTimeoutError,
        RateLimitedError,
    )
    from agent_runtime.runner import invoke as runtime_invoke

    tool_config = (
        build_mcp_tool_config(
            "claude",
            allowed_tools=allowed_tools,
        )
        if mcp_tools and allowed_tools
        else None
    )

    t0 = time.monotonic()
    call_start = datetime.now().astimezone()
    try:
        result = runtime_invoke(
            "claude",
            prompt,
            mode="read-only",  # dispatch treats Claude as read-only; write
                                # capability for pipeline calls flows through
                                # tool_config allowed_tools, not mode
            cwd=PROJECT_ROOT,
            model=model,
            task_id=f"{phase}-{orch_dir.name}" if orch_dir else phase,
            session_id=None,  # dispatch never uses resume (fresh session)
            tool_config=tool_config,
            entrypoint="dispatch",
            hard_timeout=timeout,
            # Stall budget is generous: Gemini/Claude CAN reasonably go
            # silent for 5+ minutes during long reasoning bursts (especially
            # skeleton + review phases). 600s = 10 min. The liveness-file
            # mtime poller (logs.json, chats/, state_5.sqlite) catches real
            # activity even when stdout is buffered, so this ceiling only
            # applies to *genuinely* dead processes. Bumped from 180s on
            # 2026-04-10 after a successful 319s Gemini skeleton run was
            # killed at 181s.
            stall_timeout=min(600, timeout),
        )
        elapsed = time.monotonic() - t0
        _save_dispatch_log(
            orch_dir, phase, agent_label,
            model=model,
            prompt_chars=len(prompt),
            response_chars=len(result.response),
            stderr=result.stderr_excerpt or "",
            returncode=result.returncode,
            duration_s=elapsed,
            ok=result.ok,
            prompt=prompt,
            response=result.response,
            call_start_time=call_start,
        )
        return result.ok, result.response
    except RateLimitedError as exc:
        elapsed = time.monotonic() - t0
        _log(f"  ⏳ {agent_label} rate limited: {exc}")
        _save_dispatch_log(
            orch_dir, phase, agent_label,
            model=model,
            prompt_chars=len(prompt), response_chars=0,
            stderr=f"RateLimitedError: {exc}", returncode=None,
            duration_s=elapsed, ok=False, prompt=prompt,
        )
        return False, "__RATE_LIMITED__"
    except (AgentStalledError, AgentTimeoutError) as exc:
        elapsed = time.monotonic() - t0
        _log(f"  ❌ {agent_label} {type(exc).__name__}: {exc}")
        _save_dispatch_log(
            orch_dir, phase, agent_label,
            model=model,
            prompt_chars=len(prompt), response_chars=0,
            stderr=f"{type(exc).__name__}: {exc}", returncode=None,
            duration_s=elapsed, ok=False, prompt=prompt,
        )
        return False, ""


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
    runtime_agent_name: str,
    cascade_per_call_max_s: int | None,
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
        tool_config = (
            build_mcp_tool_config("gemini", mcp_servers=["rag"])
            if mcp_tools
            else None
        )
        # Pace Gemini calls (preserved from legacy path)
        _pace_gemini_calls()
    elif runtime_agent_name == "gemma-local":
        runtime_mode = "workspace-write"
        tool_config = None
    else:
        # Codex
        runtime_mode = _codex_runtime_mode(agent)
        tool_config = None  # Codex has no MCP tool restrictions

    def _call_runtime(call_model: str, label: str, call_timeout: int) -> tuple[bool, str, str, float, int | None]:
        """One invocation. Returns (ok, response, stderr_excerpt, duration, returncode)."""
        t0 = time.monotonic()
        call_start = datetime.now().astimezone()
        try:
            result = runtime_invoke(
                runtime_agent_name,
                prompt,
                mode=runtime_mode,
                cwd=PROJECT_ROOT,
                model=call_model,
                task_id=f"{phase}-{orch_dir.name}" if orch_dir else phase,
                session_id=None,  # dispatch never uses resume
                tool_config=tool_config,
                entrypoint="dispatch",
                hard_timeout=call_timeout,
                # See 180→600 rationale in _dispatch_claude_via_runtime
                # above. Same reasoning applies to Gemini (reasoning bursts
                # silence stdout for 3-5 min) and Codex (-o file redirects
                # all stdout, adapter liveness paths cover the gap).
                stall_timeout=min(600, call_timeout),
            )
            elapsed = time.monotonic() - t0
            _save_dispatch_log(
                orch_dir, phase, label,
                model=call_model,
                prompt_chars=len(prompt),
                response_chars=len(result.response),
                stderr=result.stderr_excerpt or "",
                returncode=result.returncode,
                duration_s=elapsed,
                ok=result.ok,
                prompt=prompt,
                response=result.response,
                call_start_time=call_start,
            )
            return result.ok, result.response, result.stderr_excerpt or "", elapsed, result.returncode
        except RateLimitedError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ⏳ {label} rate limited: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                model=call_model,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"RateLimitedError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
                prompt=prompt,
            )
            # Use a special return tuple to signal rate limiting upstream.
            return False, "__RATE_LIMITED__", str(exc), elapsed, None
        except AgentStalledError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ❌ {label} stalled: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                model=call_model,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"AgentStalledError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
                prompt=prompt,
            )
            return False, "", str(exc), elapsed, None
        except AgentTimeoutError as exc:
            elapsed = time.monotonic() - t0
            _log(f"  ❌ {label} hard timeout: {exc}")
            _save_dispatch_log(
                orch_dir, phase, label,
                model=call_model,
                prompt_chars=len(prompt),
                response_chars=0,
                stderr=f"AgentTimeoutError: {exc}",
                returncode=None,
                duration_s=elapsed,
                ok=False,
                prompt=prompt,
            )
            return False, "", str(exc), elapsed, None

    # Cap the first attempt so a single stalled call can't eat the entire
    # budget and leave zero room for the cascade. For Gemini we use the
    # shared cascade budget; Codex + Claude get the full timeout since
    # they don't have a fallback chain to preserve budget for.
    if is_gemini:
        from batch_gemini_config import CASCADE_PER_CALL_MAX_S
        per_call_cap = cascade_per_call_max_s or CASCADE_PER_CALL_MAX_S
        first_call_timeout = min(per_call_cap, timeout)
    else:
        first_call_timeout = timeout

    # First attempt
    ok, raw, _, elapsed1, _ = _call_runtime(model, agent_label, first_call_timeout)
    if ok:
        return True, raw

    # Short-circuit rate-limited: don't fall back, same quota
    if raw == "__RATE_LIMITED__":
        _log("  ⏳ Rate limited — skipping fallback cascade (same quota)")
        return False, "__RATE_LIMITED__"

    # Gemini-only: walk the fallback cascade
    # (e.g. flash → pro → auto, or flash-lite → flash → pro → auto)
    # Each step is capped at CASCADE_PER_CALL_MAX_S so no single call can
    # starve the remaining budget for downstream attempts. We also require
    # at least 30s of headroom before trying — a sub-30s attempt is useless.
    if is_gemini:
        from batch_gemini_config import CASCADE_PER_CALL_MAX_S
        _MIN_ATTEMPT_S = 30
        per_call_cap = cascade_per_call_max_s or CASCADE_PER_CALL_MAX_S
        elapsed_total = elapsed1
        for fallback_model in _get_gemini_fallback_chain(model):
            remaining_total = int(timeout - elapsed_total)
            if remaining_total < _MIN_ATTEMPT_S:
                _log(
                    f"  ⏳ No budget left for {fallback_model} fallback "
                    f"(elapsed: {elapsed_total:.0f}s of {timeout}s)"
                )
                break
            step_timeout = min(per_call_cap, remaining_total)
            _pace_gemini_calls()
            fallback_label = f"{agent} ({fallback_model})"
            _log(
                f"  🔄 Cascade → {fallback_label} "
                f"(step budget: {step_timeout}s, remaining: {remaining_total}s)"
            )
            ok2, raw2, _, elapsed_step, _ = _call_runtime(
                fallback_model, fallback_label, step_timeout
            )
            elapsed_total += elapsed_step
            if ok2:
                return True, raw2
            if raw2 == "__RATE_LIMITED__":
                _log(
                    f"  ⏳ {fallback_label} rate-limited — aborting cascade"
                )
                return False, "__RATE_LIMITED__"
            # else: loop to next fallback

    return ok, raw
