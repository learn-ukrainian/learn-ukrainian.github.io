"""Policy guard for ``v6_build._determine_reviewer``.

Pins the reviewer-default mapping against drift. The function encodes
the current (2026-04-23 PM) REVIEWER POLICY:

  * Codex is the primary pipeline reviewer.
  * Gemini self-review is OFF — Gemini is never the default reviewer.
  * Writer family must never equal reviewer family (no self-review).

Before #1527 this function routed claude writers to gemini-tools,
contradicting the policy that had been in effect since 2026-04-23. The
regression shipped silently because no test pinned the mapping. These
tests exist so that if someone edits ``_determine_reviewer`` in the
future, the drift trips CI instead of quietly corrupting a production
build.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from build import v6_build

# ── Family helpers (keep tests decoupled from literal family names) ─────

_CLAUDE = v6_build.get_family("claude-tools").name
_GEMINI = v6_build.get_family("gemini-tools").name
_CODEX = v6_build.get_family("codex-tools").name


def _resolve(writer: str, override: str | None = None) -> tuple[str, str]:
    """Thin wrapper that also asserts the policy never returns ``None``.

    ``_determine_reviewer`` is typed ``tuple[str, str] | None`` for
    historical reasons — some call sites gate on a ``None`` return — but
    under the current policy every writer family has a legal reviewer.
    The assertion narrows the type for type-checkers AND documents the
    behavioral invariant.
    """
    result = v6_build._determine_reviewer(writer, reviewer_override=override)
    assert result is not None, f"_determine_reviewer returned None for writer={writer!r}"
    return result


# ── 1. Default mapping: codex-tools reviews everything non-codex ────────


@pytest.mark.parametrize(
    "writer",
    [
        "claude",
        "claude-tools",
        "gemini",
        "gemini-tools",
    ],
)
def test_non_codex_writer_defaults_to_codex_tools(writer):
    """Per current policy, codex-tools is the primary reviewer for any
    non-Codex writer family. This is the main behavior #1527 fixed —
    prior logic routed claude writers to gemini-tools.
    """
    family, agent = _resolve(writer)
    assert agent == "codex-tools"
    assert family == _CODEX


# ── 2. Codex writer falls back to claude-tools (Gemini is off) ──────────


@pytest.mark.parametrize("writer", ["codex", "codex-tools"])
def test_codex_writer_defaults_to_claude_tools(writer):
    """When the writer IS Codex, the reviewer must switch to a
    non-Codex family to preserve the no-self-review invariant. Because
    Gemini self-review is disabled by policy, the only remaining family
    is Claude.
    """
    family, agent = _resolve(writer)
    assert agent == "claude-tools"
    assert family == _CLAUDE


# ── 3. No-self-review invariant across every writer choice ─────────────


@pytest.mark.parametrize(
    "writer",
    ["claude", "claude-tools", "gemini", "gemini-tools", "codex", "codex-tools"],
)
def test_writer_family_never_equals_reviewer_family(writer):
    """The strongest invariant: writer family and reviewer family must
    never coincide. Any change that breaks this trips the
    SELF_REVIEW_DETECTED audit gate downstream and silently fails a
    production build.
    """
    writer_family = v6_build.get_family(writer).name
    reviewer_family, _ = _resolve(writer)
    assert writer_family != reviewer_family


# ── 4. Gemini is never the default reviewer (policy: self-review off) ──


@pytest.mark.parametrize(
    "writer",
    ["claude", "claude-tools", "gemini", "gemini-tools", "codex", "codex-tools"],
)
def test_gemini_never_default_reviewer(writer):
    """REVIEWER POLICY: ``Gemini self-review OFF``. For the default
    path (no --reviewer override) Gemini must never be selected for
    *any* writer family.
    """
    family, agent = _resolve(writer)
    assert family != _GEMINI
    assert "gemini" not in agent


# ── 5. Override path stays intact (operator escape hatch) ──────────────


@pytest.mark.parametrize(
    ("writer", "override"),
    [
        # User explicitly asks for Gemini reviewer — allowed via override
        # even though it's off by default.
        ("claude-tools", "gemini-tools"),
        # Force codex on gemini writer (already the default, but the
        # override path should still work idempotently).
        ("gemini-tools", "codex-tools"),
        # Cross-family override.
        ("codex-tools", "claude-tools"),
    ],
)
def test_override_bypasses_default_policy(writer, override):
    family, agent = _resolve(writer, override=override)
    assert agent == override
    assert family == v6_build.get_family(override).name
