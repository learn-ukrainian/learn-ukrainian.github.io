"""Shared Gemini fallback ladder for direct CLI and runtime callers."""
from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

PRIMARY_GEMINI_MODEL = "gemini-3.1-pro-preview"
FLASH_GEMINI_MODEL = "gemini-3-flash-preview"
FINAL_GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_MODEL_LADDER = (
    PRIMARY_GEMINI_MODEL,
    FLASH_GEMINI_MODEL,
    FINAL_GEMINI_MODEL,
)
GEMINI_AUTH_ENV_VARS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
)
#: Stderr/stdout markers that mean "this rung is not going to answer —
#: advance to the next rung instead of retrying the same one 3x". Lowercase;
#: matched via case-insensitive ``in`` on the haystack.
#:
#: ``no capacity available`` is emitted by Gemini when the backend queue for
#: the chosen model is full. Treating it as a retryable error (as happened
#: before 2026-04-21 PM, #1384) produced the exact failure mode the user hit:
#: 3 retries on rung 1 API, every one seeing "No capacity", never advancing
#: to OAuth or to the flash model. Now classified as rate-limited so the
#: ladder advances immediately.
#:
#: ``resource_exhausted`` is the GRPC status name for 429; Gemini sometimes
#: prints it instead of a numeric 429 code.
_RATE_LIMIT_MARKERS = (
    # HTTP / GRPC status codes (numeric + name forms)
    "429",
    "resource_exhausted",
    # Explicit quota / rate-limit phrases from Gemini CLI stderr
    "quota",
    "rate_limited",
    "rate limit exceeded",          # CLI free-tier 429 phrasing (#2596)
    "free tier limits",             # CLI auth-fallback quota exhaustion phrasing
    # Backend unavailability = "advance rung", not "retry same rung"
    "no capacity available",        # backend queue full (observed 14:30 today)
    "model is overloaded",          # CLI 503 phrasing (#7227)
    "unavailable",                  # GRPC status name for 503, covers JSON +
                                    # text forms regardless of whitespace.
                                    # Safe because the classifier is only
                                    # called on failure-path stderr (never
                                    # on article content stdout).
)

AuthMode = Literal["api", "oauth"]
AttemptStatus = Literal["success", "rate_limited", "retryable_error", "timeout", "fatal"]


@dataclass(frozen=True)
class GeminiRung:
    index: int
    total: int
    model: str
    auth_mode: AuthMode


@dataclass(frozen=True)
class AttemptOutcome:
    status: AttemptStatus
    elapsed_s: float
    response_text: str | None = None
    stderr_excerpt: str | None = None
    returncode: int | None = None
    note: str | None = None


@dataclass(frozen=True)
class AttemptRecord:
    rung_index: int
    rung_total: int
    model: str
    auth_mode: AuthMode
    attempt_index: int
    max_retries: int
    status: AttemptStatus
    elapsed_s: float
    returncode: int | None = None
    stderr_excerpt: str | None = None
    note: str | None = None
    response_chars: int = 0


@dataclass(frozen=True)
class CallResult:
    response_text: str | None
    model_used: str | None
    auth_mode_used: AuthMode | None
    elapsed_s: float
    attempts: list[AttemptRecord] = field(default_factory=list)
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.response_text is not None


def build_gemini_ladder(
    preferred_model: str = PRIMARY_GEMINI_MODEL,
    *,
    allowed_auth_modes: tuple[AuthMode, ...] = ("api", "oauth"),
) -> list[GeminiRung]:
    """Build the ordered `(model, auth)` ladder for one fresh Gemini call.

    ``allowed_auth_modes`` filters which auth modes appear in the ladder.
    Used by callers that know one mode is exhausted (e.g. API cooldown
    active ⇒ pass ``("oauth",)`` to skip all API rungs and avoid burning
    retries on a key that's guaranteed to 429). The rung indices in the
    result are renumbered to the filtered total so log lines like
    ``Rung 1/3`` stay accurate.
    """
    if not allowed_auth_modes:
        raise ValueError("allowed_auth_modes must not be empty")
    if preferred_model in GEMINI_MODEL_LADDER:
        model_order = list(GEMINI_MODEL_LADDER[GEMINI_MODEL_LADDER.index(preferred_model):])
    else:
        model_order = [preferred_model, FLASH_GEMINI_MODEL, FINAL_GEMINI_MODEL]

    rungs: list[GeminiRung] = []
    total = len(model_order) * len(allowed_auth_modes)
    for model in model_order:
        for auth_mode in ("api", "oauth"):
            if auth_mode not in allowed_auth_modes:
                continue
            rungs.append(
                GeminiRung(
                    index=len(rungs) + 1,
                    total=total,
                    model=model,
                    auth_mode=auth_mode,
                )
            )
    return rungs


def resolve_allowed_auth_modes(
    env: Mapping[str, str] | None = None,
    *,
    cooldown_active: bool | None = None,
) -> tuple[AuthMode, ...]:
    """Choose which ladder rungs to include for this call.

    Honors (in order of precedence):

    1. ``GEMINI_AUTH_MODE=api``  — API rungs only
    2. ``GEMINI_AUTH_MODE=subscription`` / ``oauth``  — OAuth rungs only
    3. ``GEMINI_AUTH_MODE=auto`` / unset  — cooldown-aware:
         - cooldown active ⇒ OAuth only (API key is near-budget, don't burn retries)
         - cooldown inactive ⇒ both modes (API first, OAuth as fallback)

    Invalid values degrade to the ``auto`` behavior.

    ``cooldown_active`` is injectable for tests.
    """
    source = os.environ if env is None else env
    raw = (source.get("GEMINI_AUTH_MODE") or "").strip().lower()
    if raw == "api" or raw == "api-key":
        return ("api",)
    if raw in ("subscription", "oauth"):
        return ("oauth",)
    # auto / unset / invalid
    if cooldown_active is None:
        from ai_llm.cooldown import is_api_cooldown_active
        cooldown_active = is_api_cooldown_active()
    if cooldown_active:
        return ("oauth",)
    return ("api", "oauth")


def is_gemini_rate_limited(stderr_text: str | None) -> bool:
    """Return True when stderr matches the Gemini quota/rate-limit policy."""
    haystack = (stderr_text or "").lower()
    return any(marker in haystack for marker in _RATE_LIMIT_MARKERS)


def build_gemini_subprocess_env(
    auth_mode: AuthMode,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Construct a fresh subprocess env for one ladder rung."""
    env = dict(base_env) if base_env is not None else os.environ.copy()
    if auth_mode == "oauth":
        for key in GEMINI_AUTH_ENV_VARS:
            env.pop(key, None)
    return env


def visible_sleep(seconds: int, reason: str, *, logger: Callable[[str], None] | None = None) -> None:
    """Sleep with visible countdown output instead of going silent."""
    if seconds <= 0:
        return
    emit = logger or print
    deadline = time.monotonic() + seconds
    emit(f"  💤 Sleeping {seconds}s ({reason})...")
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        chunk = min(30.0, remaining)
        time.sleep(chunk)
        still_remaining = deadline - time.monotonic()
        if still_remaining > 0:
            emit(f"  … {int(still_remaining)}s remaining")
    emit(f"  ↻ Resuming (slept {seconds}s)")


def run_gemini_fallback_ladder(
    *,
    task_name: str,
    preferred_model: str = PRIMARY_GEMINI_MODEL,
    per_rung_timeout_s: int | None = None,
    overall_timeout_s: int | None = None,
    min_attempt_budget_s: int = 1,
    max_retries: int = 3,
    attempt_runner: Callable[[GeminiRung, int, int | None], AttemptOutcome],
    logger: Callable[[str], None] | None = None,
    sleep_fn: Callable[[int, str], None] | None = None,
    allowed_auth_modes: tuple[AuthMode, ...] | None = None,
) -> CallResult:
    """Run the shared Gemini ladder until success or terminal failure.

    ``allowed_auth_modes`` filters which rungs the ladder attempts. When
    None (default), resolved from ``GEMINI_AUTH_MODE`` env var and the
    API cooldown state — so a ``GEMINI_AUTH_MODE=subscription`` shell or
    an active cooldown automatically skips API rungs. Explicit callers
    (e.g. tests) can still pass a specific tuple.

    Hooks ``set_api_cooldown()`` on any rate-limited outcome whose rung
    was on API mode, so future ladder invocations skip API rungs without
    a probe call (#1384).
    """
    emit = logger or print
    sleeper = sleep_fn or (lambda seconds, reason: visible_sleep(seconds, reason, logger=emit))
    attempts: list[AttemptRecord] = []
    effective_auth_modes = (
        allowed_auth_modes if allowed_auth_modes is not None
        else resolve_allowed_auth_modes()
    )
    ladder = build_gemini_ladder(preferred_model, allowed_auth_modes=effective_auth_modes)
    if effective_auth_modes != ("api", "oauth"):
        emit(
            f"  🎛️  Ladder filtered to auth modes {effective_auth_modes} "
            f"({len(ladder)} rungs)"
        )
    overall_start = time.monotonic()

    for rung in ladder:
        for attempt_index in range(1, max_retries + 1):
            timeout_s = per_rung_timeout_s
            if overall_timeout_s is not None:
                remaining_s = int(overall_timeout_s - (time.monotonic() - overall_start))
                if remaining_s < min_attempt_budget_s:
                    error = (
                        f"{task_name}: no budget left for rung {rung.index}/{rung.total} "
                        f"({rung.model} + {rung.auth_mode})"
                    )
                    emit(f"  ❌ {error}")
                    _emit_attempt_history(emit, attempts)
                    return CallResult(
                        response_text=None,
                        model_used=None,
                        auth_mode_used=None,
                        elapsed_s=time.monotonic() - overall_start,
                        attempts=attempts,
                        error_message=error,
                    )
                timeout_s = min(timeout_s, remaining_s) if timeout_s is not None else remaining_s

            emit(
                f"🎯 Rung {rung.index}/{rung.total}: {rung.model} + "
                f"{rung.auth_mode.upper()} (attempt {attempt_index}/{max_retries})"
            )
            outcome = attempt_runner(rung, attempt_index, timeout_s)
            record = AttemptRecord(
                rung_index=rung.index,
                rung_total=rung.total,
                model=rung.model,
                auth_mode=rung.auth_mode,
                attempt_index=attempt_index,
                max_retries=max_retries,
                status=outcome.status,
                elapsed_s=outcome.elapsed_s,
                returncode=outcome.returncode,
                stderr_excerpt=outcome.stderr_excerpt,
                note=outcome.note,
                response_chars=len(outcome.response_text or ""),
            )
            attempts.append(record)

            if outcome.status == "success":
                response_text = outcome.response_text or ""
                emit(
                    f"  ✓ Responded in {outcome.elapsed_s:.1f}s ({len(response_text):,} chars). "
                    f"Model used: {rung.model}, auth: {rung.auth_mode}."
                )
                emit(
                    f"✓ Gemini via [rung {rung.index}: {_short_model_label(rung.model)} + "
                    f"{rung.auth_mode.upper()}] in {time.monotonic() - overall_start:.1f}s"
                )
                return CallResult(
                    response_text=response_text,
                    model_used=rung.model,
                    auth_mode_used=rung.auth_mode,
                    elapsed_s=time.monotonic() - overall_start,
                    attempts=attempts,
                    error_message=None,
                )

            if outcome.status == "rate_limited":
                excerpt = _clean_excerpt(outcome.stderr_excerpt)
                next_step = (
                    f"Advancing to rung {rung.index + 1}."
                    if rung.index < rung.total
                    else "No more rungs."
                )
                emit(
                    f"  ⚠️  Rate-limited after {outcome.elapsed_s:.1f}s "
                    f"(stderr: {excerpt}). {next_step}"
                )
                # 429 on an API rung = key is near-budget. Set the sticky
                # cooldown so subsequent ladder invocations skip API
                # entirely without a probe call. 429 on OAuth rung is
                # handled as "try next model" only — no cooldown.
                if rung.auth_mode == "api":
                    from ai_llm.cooldown import set_api_cooldown
                    expires_at = set_api_cooldown()
                    emit(
                        f"  🧊 API cooldown armed until {time.strftime('%H:%M:%S', time.localtime(expires_at))} "
                        f"(future calls skip API rungs)"
                    )
                break

            if outcome.status == "timeout":
                emit(f"  ⏱️  Timeout after {outcome.elapsed_s:.1f}s. Retrying same rung.")
            elif outcome.status == "fatal":
                error = (
                    f"{task_name}: fatal Gemini error on rung {rung.index}/{rung.total}: "
                    f"{outcome.stderr_excerpt or outcome.note or 'unknown error'}"
                )
                emit(f"  ❌ {error}")
                _emit_attempt_history(emit, attempts)
                return CallResult(
                    response_text=None,
                    model_used=None,
                    auth_mode_used=None,
                    elapsed_s=time.monotonic() - overall_start,
                    attempts=attempts,
                    error_message=error,
                )
            else:
                emit(
                    f"  ⚠️  Non-rate-limit failure after {outcome.elapsed_s:.1f}s: "
                    f"{_clean_excerpt(outcome.stderr_excerpt)}"
                )

            if attempt_index >= max_retries:
                error = (
                    f"{task_name}: rung {rung.index}/{rung.total} failed after "
                    f"{max_retries} attempts"
                )
                emit(f"  ❌ {error}")
                _emit_attempt_history(emit, attempts)
                return CallResult(
                    response_text=None,
                    model_used=None,
                    auth_mode_used=None,
                    elapsed_s=time.monotonic() - overall_start,
                    attempts=attempts,
                    error_message=error,
                )

            sleeper(10, f"{task_name} retry backoff")
        else:
            continue

    error = f"{task_name}: all {len(ladder)} Gemini fallback rungs rate-limited"
    emit(f"  ❌ {error}")
    _emit_attempt_history(emit, attempts)
    return CallResult(
        response_text=None,
        model_used=None,
        auth_mode_used=None,
        elapsed_s=time.monotonic() - overall_start,
        attempts=attempts,
        error_message=error,
    )


def call_gemini_with_fallback(
    prompt: str,
    *,
    task_name: str,
    preferred_model: str = PRIMARY_GEMINI_MODEL,
    per_rung_timeout_s: int | None = None,
    overall_timeout_s: int | None = None,
    max_retries: int = 3,
    gemini_cli: str = "gemini",
    cwd: Path | None = None,
    base_env: Mapping[str, str] | None = None,
    logger: Callable[[str], None] | None = None,
    sleep_fn: Callable[[int, str], None] | None = None,
    recover_response: Callable[[float, str], str | None] | None = None,
) -> CallResult:
    """Call the Gemini CLI through the shared rung ladder."""
    # Default-timeout changed 2026-04-24 from `min(300 + len//500, 900)` to
    # 1 day. The 900s ceiling was a hidden override on the production 24h
    # hard_timeout policy set in scripts/batch/batch_gemini_config.py —
    # flagged by Codex + Gemini in bridge architecture thread 0f94b8c0.
    # If a caller really wants a shorter budget (e.g. a liveness probe),
    # they pass `per_rung_timeout_s=300` explicitly; no silent clamp here.
    _ONE_DAY = 24 * 60 * 60
    effective_timeout = per_rung_timeout_s or _ONE_DAY
    workdir = cwd or Path.cwd()
    emit = logger or print

    def _attempt_runner(rung: GeminiRung, _attempt_index: int, timeout_s: int | None) -> AttemptOutcome:
        call_start_wall = time.time()
        call_start_mono = time.monotonic()
        env = build_gemini_subprocess_env(rung.auth_mode, base_env=base_env)
        cmd = [gemini_cli, "-m", rung.model, "--approval-mode=yolo"]
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(workdir),
                env=env,
            )
            try:
                stdout, stderr = proc.communicate(input=prompt, timeout=timeout_s or effective_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                recovered = (
                    recover_response(call_start_wall, prompt[:200])
                    if recover_response is not None
                    else None
                )
                if recovered:
                    return AttemptOutcome(
                        status="success",
                        elapsed_s=time.monotonic() - call_start_mono,
                        response_text=recovered,
                        note="recovered from Gemini session after timeout",
                    )
                return AttemptOutcome(
                    status="timeout",
                    elapsed_s=time.monotonic() - call_start_mono,
                    stderr_excerpt=f"Timed out after {timeout_s or effective_timeout}s",
                )

            elapsed_s = time.monotonic() - call_start_mono
            if proc.returncode != 0:
                recovered = (
                    recover_response(call_start_wall, prompt[:200])
                    if recover_response is not None
                    else None
                )
                if recovered:
                    return AttemptOutcome(
                        status="success",
                        elapsed_s=elapsed_s,
                        response_text=recovered,
                        returncode=proc.returncode,
                        note="recovered from Gemini session after subprocess error",
                    )
                stderr_text = stderr or ""
                status: AttemptStatus = "rate_limited" if is_gemini_rate_limited(stderr_text) else "retryable_error"
                return AttemptOutcome(
                    status=status,
                    elapsed_s=elapsed_s,
                    stderr_excerpt=stderr_text or None,
                    returncode=proc.returncode,
                )

            response = stdout.strip()
            if len(response) < 100:
                recovered = (
                    recover_response(call_start_wall, prompt[:200])
                    if recover_response is not None
                    else None
                )
                if recovered:
                    return AttemptOutcome(
                        status="success",
                        elapsed_s=elapsed_s,
                        response_text=recovered,
                        note="recovered from Gemini session after short stdout response",
                    )
                return AttemptOutcome(
                    status="retryable_error",
                    elapsed_s=elapsed_s,
                    stderr_excerpt=f"Very short response ({len(response)} chars)",
                    returncode=proc.returncode,
                )

            return AttemptOutcome(
                status="success",
                elapsed_s=elapsed_s,
                response_text=response,
                returncode=proc.returncode,
            )
        except FileNotFoundError:
            return AttemptOutcome(
                status="fatal",
                elapsed_s=time.monotonic() - call_start_mono,
                stderr_excerpt="gemini CLI not found. Install: https://github.com/google-gemini/gemini-cli",
            )
        except Exception as exc:
            recovered = (
                recover_response(call_start_wall, prompt[:200])
                if recover_response is not None
                else None
            )
            if recovered:
                return AttemptOutcome(
                    status="success",
                    elapsed_s=time.monotonic() - call_start_mono,
                    response_text=recovered,
                    note=f"recovered from Gemini session after {type(exc).__name__}",
                )
            return AttemptOutcome(
                status="retryable_error",
                elapsed_s=time.monotonic() - call_start_mono,
                stderr_excerpt=f"{type(exc).__name__}: {exc}",
            )

    emit(f"  🤖 Gemini ladder call ({len(prompt):,} prompt chars)...")
    return run_gemini_fallback_ladder(
        task_name=task_name,
        preferred_model=preferred_model,
        per_rung_timeout_s=effective_timeout,
        overall_timeout_s=overall_timeout_s,
        max_retries=max_retries,
        attempt_runner=_attempt_runner,
        logger=emit,
        sleep_fn=sleep_fn,
    )


def _clean_excerpt(text: str | None) -> str:
    if not text:
        return "(no stderr)"
    compact = " ".join(text.strip().split())
    return compact[:120]


def _emit_attempt_history(logger: Callable[[str], None], attempts: list[AttemptRecord]) -> None:
    if not attempts:
        return
    logger("  Attempt history:")
    for attempt in attempts:
        detail = _clean_excerpt(attempt.stderr_excerpt)
        logger(
            f"    - rung {attempt.rung_index}/{attempt.rung_total} "
            f"{attempt.model} + {attempt.auth_mode.upper()} "
            f"attempt {attempt.attempt_index}/{attempt.max_retries}: "
            f"{attempt.status} in {attempt.elapsed_s:.1f}s (stderr: {detail})"
        )


def _short_model_label(model: str) -> str:
    if model == PRIMARY_GEMINI_MODEL:
        return "3.1-pro"
    if model == FLASH_GEMINI_MODEL:
        return "3-flash"
    if model == FINAL_GEMINI_MODEL:
        return "2.5-pro"
    return model
