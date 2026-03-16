"""Unified dispatch for Gemini and Claude LLM calls.

All LLM dispatch routing lives here — adding a new backend means changing one file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

# Late imports to avoid circular dependencies
_pipeline_lib = None


def _get_pipeline_lib():
    global _pipeline_lib
    if _pipeline_lib is None:
        import pipeline_lib as _pl
        _pipeline_lib = _pl
    return _pipeline_lib


def _log(msg: str) -> None:
    _get_pipeline_lib().log(msg)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent


def _venv_python() -> str:
    from batch_gemini_config import VENV_PYTHON
    return VENV_PYTHON


def _pro_model() -> str:
    from batch_gemini_config import PRO_MODEL
    return PRO_MODEL


def _flash_model() -> str:
    from batch_gemini_config import FLASH_MODEL
    return FLASH_MODEL


# ---------------------------------------------------------------------------
# Heartbeat subprocess runner
# ---------------------------------------------------------------------------

def run_with_heartbeat(
    cmd: list[str], label: str, timeout: int = 1800,
    heartbeat_interval: int = 30, **kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess with periodic heartbeat logging."""
    stop_event = threading.Event()
    t0 = time.time()

    def _heartbeat():
        while not stop_event.wait(heartbeat_interval):
            elapsed = int(time.time() - t0)
            m, s = divmod(elapsed, 60)
            print(f"    ⏳ {label} — {m}m {s:02d}s elapsed...", flush=True)

    thread = threading.Thread(target=_heartbeat, daemon=True)
    thread.start()
    try:
        result = subprocess.run(cmd, timeout=timeout, **kwargs)
        return result
    finally:
        stop_event.set()
        thread.join(timeout=2)


# ---------------------------------------------------------------------------
# Gemini dispatch
# ---------------------------------------------------------------------------

# Rate limit / auth failure signatures in Gemini CLI output
_RATE_LIMIT_PATTERNS = [
    "Error authenticating",
    "FatalAuthenti",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "quota exceeded",
    "429",
]

# Transient network error signatures (TLS drops, socket resets)
_TRANSIENT_PATTERNS = [
    "premature close",
    "econnreset",
    "socket hang up",
    "fetch failed",
    "network error",
    "etimedout",
    "enotfound",
    "epipe",
    "connection reset",
]


def _is_rate_limited(output: str) -> bool:
    """Check if dispatch failed due to rate limiting or auth exhaustion."""
    lower = output.lower()
    return any(p.lower() in lower for p in _RATE_LIMIT_PATTERNS)


def _is_transient_error(output: str) -> bool:
    """Check if dispatch failed due to a transient network error."""
    lower = output.lower()
    return any(p in lower for p in _TRANSIENT_PATTERNS)


def dispatch_gemini_raw(
    prompt: str, task_id: str, model: str | None = None,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
    max_retries: int = 3,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini via ai_agent_bridge (no rate-limit fallback).

    Retries up to max_retries times on transient network errors
    (TLS drops, socket resets, etc.) with exponential backoff.

    Returns (success, raw_output_text).
    """
    if model is None:
        model = _pro_model()
    args = [
        str(_SCRIPTS_DIR / "ai_agent_bridge/__main__.py"), "ask-gemini",
        "-",  # read prompt from stdin
        "--task-id", task_id,
        "--model", model,
    ]
    if stdout_only:
        args.append("--stdout-only")
    if allow_write:
        args.append("--allow-write")

    last_output = ""
    for attempt in range(1, max_retries + 1):
        try:
            result = run_with_heartbeat(
                [_venv_python(), *args],
                label=f"Gemini {task_id}",
                timeout=timeout,
                cwd=str(_PROJECT_ROOT), capture_output=True, text=True,
                input=prompt,
            )
            output_text = result.stdout or ""
            last_output = output_text
            if result.returncode == 0:
                if output_file:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(output_text, encoding="utf-8")
                return True, output_text
            # Check if failure is a transient network error
            combined = f"{output_text}\n{result.stderr or ''}"
            if attempt < max_retries and _is_transient_error(combined):
                delay = 5 * (2 ** (attempt - 1))  # 5s, 10s
                _log(f"  [retry] Transient network error on attempt {attempt}/{max_retries}, "
                     f"waiting {delay}s...")
                time.sleep(delay)
                continue
            # Non-transient failure or final attempt
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(output_text, encoding="utf-8")
            return False, output_text
        except subprocess.TimeoutExpired:
            _log(f"  TIMEOUT: Gemini dispatch {task_id} exceeded {timeout}s")
            return False, ""

    # Exhausted retries
    return False, last_output


def dispatch_gemini(
    prompt: str, task_id: str, model: str | None = None,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini with stdout_only=True and flash→pro fallback.

    This is the default dispatch used by the pipeline. Always forces stdout_only=True.
    If the specified model is Flash and it fails due to rate limiting, retries with Pro.
    """
    if model is None:
        model = _pro_model()
    ok, output = dispatch_gemini_raw(
        prompt, task_id, model=model,
        stdout_only=True,  # Always stdout-only in pipeline
        allow_write=allow_write, output_file=output_file, timeout=timeout,
    )
    # Fallback: if rate limited OR timed out (empty output = silent hang), try the other model
    should_fallback = not ok and (_is_rate_limited(output) or output.strip() == "")
    if should_fallback:
        flash = _flash_model()
        pro = _pro_model()
        fallback = pro if model == flash else flash
        reason = "rate-limited" if _is_rate_limited(output) else "timeout/hang"
        _log(f"  [fallback] {model} {reason}, retrying with {fallback}...")
        ok, output = dispatch_gemini_raw(
            prompt, task_id, model=fallback,
            stdout_only=True, allow_write=allow_write,
            output_file=output_file, timeout=timeout,
        )
        if ok:
            _log(f"  [fallback] {fallback} succeeded")
    return ok, output


# ---------------------------------------------------------------------------
# Gemini session capture
# ---------------------------------------------------------------------------
_GEMINI_SESSION_DIR = Path.home() / ".gemini" / "tmp" / "learn-ukrainian" / "chats"


def save_gemini_session(dest: Path, label: str = "session") -> bool:
    """Copy the most recent gemini-cli session JSON to dest directory.

    Returns True if a session was found and copied.
    """
    if not _GEMINI_SESSION_DIR.exists():
        return False
    try:
        session_files = list(_GEMINI_SESSION_DIR.glob("session-*.json"))
        if not session_files:
            return False
        latest = max(session_files, key=lambda p: p.stat().st_mtime)
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / f"{label}-gemini-session.json"
        shutil.copy2(latest, target)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Claude dispatch
# ---------------------------------------------------------------------------

# Phase label → (start_delimiter, end_delimiter) — checked in priority order
_PHASE_DELIMITERS: dict[str, tuple[str, str]] = {
    "D.1":     ("===REVIEW_START===", "===REVIEW_END==="),
    "D.2":     ("===SECTION_FIX_START===", "===SECTION_FIX_END==="),
    "C vocab": ("===VOCABULARY_START===", "===VOCABULARY_END==="),
    "C":       ("===ACTIVITIES_START===", "===ACTIVITIES_END==="),
    "B":       ("===CONTENT_START===", "===CONTENT_END==="),
    "A":       ("===RESEARCH_START===", "===RESEARCH_END==="),
}

_claude_bin_cache: str | None = None


def _get_claude_bin() -> str:
    global _claude_bin_cache
    if _claude_bin_cache is None:
        _claude_bin_cache = shutil.which("claude") or "claude"
    return _claude_bin_cache


def dispatch_claude_phase(
    prompt_file: Path,
    phase_label: str,
    model: str = "claude-opus-4-6",
    timeout: int = 600,
    allow_tools: list[str] | None = None,
) -> tuple[bool, str]:
    """Call Claude CLI headlessly for a phase prompt file."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    prompt = prompt_file.read_text("utf-8")
    prompt = prompt.replace("You are Gemini", "You are Claude")

    cmd = [_get_claude_bin(), "--model", model, "-p", "--output-format", "text"]
    if allow_tools:
        cmd.extend(["--allowedTools", ",".join(allow_tools)])

    expected_start, expected_end = "===REVIEW_START===", "===REVIEW_END==="
    for key in ("D.2", "D.1", "C vocab", "C", "B", "A"):
        if key in phase_label:
            expected_start, expected_end = _PHASE_DELIMITERS[key]
            break

    if "D.1" in phase_label:
        cmd.extend(["--append-system-prompt",
                     f"CRITICAL: Your output MUST contain {expected_start} and {expected_end} "
                     "delimiters wrapping the review, AND ===SECTION_FIX_START=== / ===SECTION_FIX_END=== "
                     "delimiters wrapping FIND/REPLACE fix pairs for every issue found. "
                     "Both blocks are required. Output without these delimiters is automatically discarded. "
                     "FIND/REPLACE FORMAT: The FIND text must be RAW file content copy-pasted from Read output. "
                     "Do NOT add Section/Line metadata headers, do NOT wrap in triple backticks, "
                     "do NOT add any framing text. Just the raw text that exists in the file."])
    elif "D.2" in phase_label and allow_tools:
        cmd.extend(["--append-system-prompt",
                     "You have Edit and Grep tools. Fix each issue by editing files directly. "
                     "Use Grep to verify text exists before editing. "
                     "Do NOT output FIND/REPLACE blocks — use the Edit tool instead. "
                     "After all fixes, output a ===FRICTION_START=== / ===FRICTION_END=== block "
                     "documenting any issues encountered."])
    else:
        cmd.extend(["--append-system-prompt",
                     f"CRITICAL: Your output MUST contain {expected_start} and {expected_end} "
                     "delimiters wrapping the full structured output. Output without these delimiters "
                     "is automatically discarded. Do NOT summarize — produce the FULL output requested."])

    try:
        result = run_with_heartbeat(
            cmd,
            label=f"Claude {phase_label}",
            timeout=timeout,
            capture_output=True, text=True,
            input=prompt,
            cwd=str(_PROJECT_ROOT), env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            _log(f"  Claude CLI error (rc={result.returncode}): {err[:300]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        _log("  Claude CLI not found — ensure 'claude' is on PATH")
        return False, ""
    except subprocess.TimeoutExpired:
        _log(f"  Claude CLI TIMEOUT ({timeout}s)")
        return False, ""
    except Exception as e:
        _log(f"  Claude CLI exception: {e}")
        return False, ""
