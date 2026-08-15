"""Guard: the bridge package must load under a single module identity (#6812).

The canonical identity is ``scripts.ai_agent_bridge`` (repo root is on
``sys.path`` via ``tests/conftest.py``). The bare ``ai_agent_bridge`` identity
used to load as a second ``sys.modules`` entry with independent module-level
state, so ``monkeypatch`` on one identity never affected the other.

These tests fail if any test file reintroduces a non-canonical bridge import
or quoted module target, or if the bare identity is loaded at runtime.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[1]
_SELF = Path(__file__).resolve()

# Match the bare identity as a module path segment, not a substring (#M-16):
# ``from ai_agent_bridge`` / ``import ai_agent_bridge._db`` are non-canonical,
# while ``scripts.ai_agent_bridge`` (the canonical form) never matches because
# the segment must directly follow ``from``/``import`` or an opening quote.
_NONCANONICAL_PATTERNS = {
    "import statement": re.compile(r"^\s*(?:from|import)\s+ai_agent_bridge(?:[\s.]|$)", re.M),
    "quoted module target": re.compile(r"""['"]ai_agent_bridge\."""),
}


def _iter_test_files():
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        if path.resolve() != _SELF:
            yield path


def test_no_noncanonical_bridge_imports_in_test_suite() -> None:
    """No test file may reference the bare ``ai_agent_bridge`` identity."""
    violations: list[str] = []
    for path in _iter_test_files():
        text = path.read_text(encoding="utf-8")
        for kind, pattern in _NONCANONICAL_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{path.relative_to(_TESTS_ROOT.parent)}:{line}: {kind}: {match.group()!r}")
    assert not violations, (
        "Non-canonical `ai_agent_bridge` module identity found; use `scripts.ai_agent_bridge` "
        "everywhere (#6812):\n" + "\n".join(violations)
    )


def test_bare_bridge_identity_not_loaded() -> None:
    """The bare identity must never occupy a second ``sys.modules`` entry."""
    assert "ai_agent_bridge" not in sys.modules, (
        "The bare `ai_agent_bridge` module identity is loaded alongside "
        "`scripts.ai_agent_bridge`; module-level state would diverge (#6812)."
    )
