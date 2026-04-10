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

See issue #1179.
"""
from __future__ import annotations

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


def _parse_claude_semver(version_text: str) -> tuple[int, int, int] | None:
    """Extract the first ``X.Y.Z`` (or ``vX.Y.Z``) triple from arbitrary text.

    Claude's ``--version`` output has varied historically — sometimes bare
    ``"2.1.98"``, sometimes ``"2.1.98 (Claude Code)"``, sometimes ``"v2.1.98"``.
    We tolerate all three and return the first parseable triple, or None.
    """
    for token in version_text.split():
        clean = token.strip("()[],:;").lstrip("v")
        parts = clean.split(".")
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            return (int(parts[0]), int(parts[1]), int(parts[2]))
    return None


def supports_exclude_dynamic_system_prompt_sections(
    cmd_prefix: Sequence[str],
) -> bool:
    """Return True iff the Claude Code binary at ``cmd_prefix`` is >= 2.1.98.

    Args:
        cmd_prefix: The exact argv prefix to probe. Examples:
            ``["claude"]``
            ``["npx", "@anthropic-ai/claude-code@latest"]``
            ``["/Users/foo/.local/bin/claude"]``
            The callsite passes whatever it is about to invoke — NOT a
            generic "claude" — so we version-check the binary actually
            being run at that site.

    Returns:
        True if the version probe parses to >= 2.1.98, else False.
        Returns False on any exception (binary missing, network timeout,
        unparsable output). "Safe failure" — we drop the optimization
        rather than crash the caller.

    The result is cached per-prefix for the lifetime of the process.
    Concurrent calls with the same prefix are safe.
    """
    key = tuple(cmd_prefix)

    # Fast path: cache hit
    with _CACHE_LOCK:
        if key in _CACHE:
            return _CACHE[key]

    # Slow path: probe. Lock is NOT held during subprocess call —
    # that would serialize all callers behind one 5-second probe.
    ok = False
    try:
        result = subprocess.run(
            [*cmd_prefix, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        version_text = (result.stdout or result.stderr or "").strip()
        version = _parse_claude_semver(version_text)
        ok = bool(version and version >= _MIN_VERSION)
    except Exception:
        # Probe failure → safe False. Any exception (missing binary, timeout,
        # unparsable output, permission denied) drops us to the no-flag path.
        ok = False

    # Store result. If another thread raced and stored first, honor the
    # first store (deterministic across races on the same prefix).
    with _CACHE_LOCK:
        _CACHE.setdefault(key, ok)
        return _CACHE[key]


def _reset_cache_for_tests() -> None:
    """Clear the cache. Tests only — do NOT call from production code."""
    with _CACHE_LOCK:
        _CACHE.clear()
