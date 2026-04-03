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
import time
from datetime import datetime
from pathlib import Path

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
        agent: Writer/reviewer mode — "gemini", "gemini-tools", "claude", "claude-tools".
        phase: Pipeline phase name — "skeleton", "write", "vocab", "review".
        orch_dir: Path to orchestration/{slug}/ for saving logs.
        timeout: Subprocess timeout in seconds.
        mcp_tools: Whether MCP tools are enabled for this dispatch.
        allowed_tools: Comma-separated Claude --allowedTools string (Claude only).
        model: Model override. If None, resolved from batch_gemini_config.

    Returns:
        (success, stdout_text)
    """
    is_gemini = agent.startswith("gemini")
    is_claude = agent.startswith("claude")

    if not is_gemini and not is_claude:
        _log(f"  ❌ Unknown agent: {agent}")
        return False, ""

    # Resolve model
    if model is None:
        if is_gemini:
            from batch_gemini_config import PRO_MODEL
            model = PRO_MODEL
        else:
            from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT
            model = CLAUDE_MODEL_CORE_CONTENT

    agent_label = f"{agent} ({model})"
    _log(f"  Dispatching to {agent_label}...")

    # Build command
    if is_gemini:
        cmd = ["gemini", "-m", model, "-y"]
        if mcp_tools:
            cmd.extend(["--allowed-mcp-server-names", "rag"])
    else:
        mcp_config = str(PROJECT_ROOT / ".mcp.json")
        cmd = [
            "npx", "@anthropic-ai/claude-code@latest", "-p",
            "--model", model,
            "--output-format", "text",
        ]
        if mcp_tools and allowed_tools:
            cmd.extend(["--mcp-config", mcp_config, "--allowedTools", allowed_tools])

    # Execute with timing + Gemini fallback
    # Set LEARN_UKRAINIAN_PIPELINE to skip SessionStart/UserPromptSubmit hooks
    env = {**os.environ, "LEARN_UKRAINIAN_PIPELINE": "1"}

    def _run_cmd(run_cmd, run_label, run_timeout):
        t0 = time.monotonic()
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

    # Pace Gemini calls to avoid burst-induced rate limits
    if is_gemini:
        _pace_gemini_calls()

    ok, raw = _run_cmd(cmd, agent_label, timeout)

    # Gemini fallback: if Pro failed, retry with -m auto
    # BUT skip fallback if rate-limited — same quota, different model won't help
    if not ok and is_gemini:
        # Check if this was a rate limit error
        log_dir = orch_dir / "dispatch"
        latest_stderr = ""
        if log_dir.exists():
            stderr_files = sorted(log_dir.glob(f"*-{phase}-*.stderr.log"), reverse=True)
            if stderr_files:
                latest_stderr = stderr_files[0].read_text()

        if _is_rate_limited(latest_stderr):
            _log("  ⏳ Rate limited — skipping fallback model (same quota)")
            # Signal rate limit to caller via empty string with special marker
            return False, "__RATE_LIMITED__"

        from batch_gemini_config import FALLBACK_MODEL
        if model != FALLBACK_MODEL:
            _pace_gemini_calls()
            fallback_cmd = [c if c != model else FALLBACK_MODEL for c in cmd]
            fallback_label = f"{agent} ({FALLBACK_MODEL})"
            _log(f"  🔄 Retrying with fallback model: {fallback_label}")
            ok, raw = _run_cmd(fallback_cmd, fallback_label, timeout)

    return ok, raw
