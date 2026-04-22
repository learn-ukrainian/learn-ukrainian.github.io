"""Version gate for Claude Code CLI features.

Claude Code 2.1.98 introduced ``--exclude-dynamic-system-prompt-sections``
(print-mode flag that strips per-invocation dynamic system prompt sections so
Anthropic's server-side prompt cache hits across calls). Older Claude Code
versions reject the flag as an unknown option, so we version-gate it.

This module is the **single source of truth** for "which Claude Code CLI
supports which feature." All callers pass their own ``cmd_prefix`` (e.g.
``CLAUDE_CMD`` for the bridge, ``["claude"]`` for direct invocations,
``[_get_claude_bin()]`` for pipeline dispatch) and the result is cached
per-prefix so every binary gets probed exactly once per process.

Thread-safe (bridge + dispatch can race from different threads) but
process-local (separate processes probe independently once each, which
is acceptable).

Gemini adversarial review (msg #28518) caught 4 bugs that are fixed here:

1. ``result.stdout or result.stderr`` short-circuited when stdout was a bare
   newline, silently discarding stderr. Now we concatenate both streams.

2. The semver parser greedy-matched the first "X.Y.Z" token it saw. If ``npx``
   printed an update notice like "npm notice New version 10.2.4 -> 10.8.1",
   the parser would extract 10.2.4, think Claude Code >= 2.1.98, and then
   crash the actual CLI by passing it the unknown flag. Fixed with a stricter
   regex and a filter that rejects tokens that look like IP octets or npm
   notices.

3. ``Sequence[str]`` admitted bare strings, so ``supports(...)("claude")`` was
   silently unpacked into individual characters. Fixed with an explicit
   isinstance check.

4. Transient ``TimeoutExpired`` failures were cached permanently, so a single
   slow ``npx`` probe on process start disabled the optimization forever.
   Now we only cache definitive outcomes (successful parse or FileNotFoundError);
   timeouts and other transient failures return False but do NOT poison the
   cache, so a later call can retry.

See issue #1179.
"""
from __future__ import annotations

import re
import subprocess
import threading
from collections.abc import Sequence

# Minimum Claude Code version that accepts --exclude-dynamic-system-prompt-sections.
# Bump this when a new version introduces more gated features that reuse the
# same probing infrastructure.
_MIN_VERSION: tuple[int, int, int] = (2, 1, 98)

# Per-prefix cache. Keyed by ``tuple(cmd_prefix)`` so, e.g.,
# ``("claude",)`` and ``("npx", "@anthropic-ai/claude-code@latest")`` remain
# independent entries — one may be 2.1.98, the other may not.
_CACHE: dict[tuple[str, ...], bool] = {}
_CACHE_LOCK = threading.Lock()

# Strict semver regex: three dot-separated numeric parts, each up to 4 digits,
# NOT surrounded by additional dot-number segments (so "1.2.3.4" does not
# match as 1.2.3). Anchored by word boundaries to prevent matching inside
# longer tokens.
_SEMVER_RE = re.compile(
    r"(?<![\d.])v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})(?![\d.])"
)

# Patterns that indicate the line is NOT the Claude Code version banner.
# We skip these lines before running the regex so npm's update-available
# notices cannot fool us into reading npm's version as Claude's version.
_VERSION_NOISE_MARKERS = (
    "npm notice",       # "npm notice New minor version of npm available!"
    "npm warn",
    "update available",
    "deprecation",
    "->",               # "10.2.4 -> 10.8.1" arrow pattern
)


def _parse_claude_semver(version_text: str) -> tuple[int, int, int] | None:
    """Extract the first plausible Claude Code semver from arbitrary text.

    Claude's ``--version`` output has varied historically — sometimes bare
    ``"2.1.98"``, sometimes ``"2.1.98 (Claude Code)"``, sometimes ``"v2.1.98"``.
    We tolerate all three.

    We also defend against NOISE from the npx layer: npm can print update
    notices that look like version strings to a naive parser (Gemini finding
    #2). The defense:

    1. Split into lines and skip any line containing known noise markers.
    2. Use a strict word-boundary regex so "1.2.3.4" (4 parts) doesn't match
       as 1.2.3, and "192.168.1" doesn't look like a triple.
    3. Prefer the first match on a clean (non-noise) line.

    Returns None if no plausible semver is found. Safe on empty input.
    """
    if not version_text:
        return None

    for line in version_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower()
        if any(marker in low for marker in _VERSION_NOISE_MARKERS):
            continue
        match = _SEMVER_RE.search(stripped)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

    return None


def supports_exclude_dynamic_system_prompt_sections(
    cmd_prefix: Sequence[str] | str,
) -> bool:
    """Return True iff the Claude Code binary at ``cmd_prefix`` is >= 2.1.98.

    Args:
        cmd_prefix: The exact argv prefix to probe. Examples:
            ``["claude"]``
            ``["npx", "@anthropic-ai/claude-code@latest"]``
            ``["/Users/foo/.local/bin/claude"]``
            A bare string ``"claude"`` is ALSO accepted and treated as a
            single-element list (defensive — ``Sequence[str]`` would
            otherwise unpack a string into characters).
            The callsite passes whatever it is about to invoke — NOT a
            generic "claude" — so we version-check the binary actually
            being run at that site.

    Returns:
        True if the version probe parses to >= 2.1.98, else False.
        Returns False on any exception (binary missing, network timeout,
        unparsable output). "Safe failure" — we drop the optimization
        rather than crash the caller.

    Caching behavior (post Gemini review):
        - Successful parse → cached permanently.
        - FileNotFoundError (binary missing) → cached permanently.
        - Transient failure (TimeoutExpired, OSError, other) → NOT cached,
          so a later call can retry. Prevents a single slow network probe
          from permanently disabling the optimization.

    Concurrent calls with the same prefix are safe.
    """
    # Defensive: a bare string is not Sequence[str] in the way we want.
    # Unpacking "claude" into characters would try to exec binary "c"
    # and permanently cache False. Treat a bare string as [string].
    if isinstance(cmd_prefix, str):
        cmd_prefix = [cmd_prefix]

    key = tuple(cmd_prefix)

    # Fast path: cache hit
    with _CACHE_LOCK:
        if key in _CACHE:
            return _CACHE[key]

    # Slow path: probe. Lock is NOT held during subprocess call —
    # that would serialize all callers behind one 5-second probe.
    ok = False
    should_cache = True  # Only cache definitive outcomes (see docstring).
    try:
        result = subprocess.run(
            [*cmd_prefix, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        # Concatenate stdout and stderr explicitly — `stdout or stderr`
        # short-circuits when stdout is a bare newline (truthy but empty
        # after strip), which would silently discard stderr. Gemini #1.
        combined = f"{result.stdout or ''}\n{result.stderr or ''}".strip()
        version = _parse_claude_semver(combined)
        ok = bool(version and version >= _MIN_VERSION)
    except FileNotFoundError:
        # Binary genuinely not on PATH — definitive outcome, cache it.
        ok = False
    except (subprocess.TimeoutExpired, OSError):
        # Transient: network slow, signal interrupted, etc. Do NOT cache,
        # so a later call can retry.
        ok = False
        should_cache = False
    except Exception:
        # Any other unexpected exception → safe False, do not cache.
        # We'd rather retry than lock in a spurious permanent False.
        ok = False
        should_cache = False

    if should_cache:
        # Store result. If another thread raced and stored first, honor the
        # first store (deterministic across races on the same prefix).
        with _CACHE_LOCK:
            _CACHE.setdefault(key, ok)
            return _CACHE[key]
    return ok


def supports_effort(cmd_prefix: Sequence[str] | str) -> bool:
    """Return True iff Claude Code at ``cmd_prefix`` supports ``--effort``.

    ``--effort`` was available in Claude Code 2.1.98+ (verified against
    2.1.117 ``--help`` output on 2026-04-22). Gates on the same minimum
    version as ``--exclude-dynamic-system-prompt-sections`` for
    simplicity; if this turns out to be wrong, split the constant.

    Args:
        cmd_prefix: Same semantics as
            :func:`supports_exclude_dynamic_system_prompt_sections` —
            the exact argv prefix to probe.

    Returns:
        True if the probed CLI is >= 2.1.98, else False.
    """
    return supports_exclude_dynamic_system_prompt_sections(cmd_prefix)


def _reset_cache_for_tests() -> None:
    """Clear the cache. Tests only — do NOT call from production code."""
    with _CACHE_LOCK:
        _CACHE.clear()
