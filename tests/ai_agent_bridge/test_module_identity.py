"""Guard: the bridge package must load under a single module identity (#6812).

The canonical identity is ``scripts.ai_agent_bridge`` (repo root is on
``sys.path`` via ``tests/conftest.py``). The bare ``ai_agent_bridge`` identity
used to load as a second ``sys.modules`` entry with independent module-level
state, so ``monkeypatch`` on one identity never affected the other.

These tests fail if any test file reintroduces a non-canonical bridge import
or quoted module target, or if the bare identity is loaded at runtime.

``scripts/api/`` is scanned too: the Monitor API boots inside the test process
(FastAPI lifespan preload, comms sweep background thread), and bare-identity
imports there were the runtime loaders that made this guard flaky under
pytest-xdist (#6838 red on an unrelated CSS change).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _TESTS_ROOT.parent
_SELF = Path(__file__).resolve()

# Match the bare identity as a module path segment, not a substring (#M-16):
# ``from ai_agent_bridge`` / ``import ai_agent_bridge._db`` are non-canonical,
# while ``scripts.ai_agent_bridge`` (the canonical form) never matches because
# the segment must directly follow ``from``/``import`` or an opening quote.
_NONCANONICAL_PATTERNS = {
    "import statement": re.compile(r"^\s*(?:from|import)\s+ai_agent_bridge(?:[\s.]|$)", re.M),
    "quoted module target": re.compile(r"""['"]ai_agent_bridge\."""),
}

# Static scan roots: the test suite plus the in-process API package. The rest
# of scripts/ deliberately keeps blessed bare fallbacks for direct-script
# production runs (``__main__`` script mode, agent_runtime adapters), which a
# blanket scan would flag; scripts/api/ never runs that way — it imports
# ``scripts.*`` at module level, so the repo root is always on sys.path.
_SCAN_ROOTS = (_TESTS_ROOT, _REPO_ROOT / "scripts" / "api")


def _iter_scanned_files():
    for root in _SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if path.resolve() != _SELF:
                yield path


def test_no_noncanonical_bridge_imports_in_test_suite() -> None:
    """No scanned file may reference the bare ``ai_agent_bridge`` identity."""
    violations: list[str] = []
    for path in _iter_scanned_files():
        text = path.read_text(encoding="utf-8")
        for kind, pattern in _NONCANONICAL_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{path.relative_to(_REPO_ROOT)}:{line}: {kind}: {match.group()!r}")
    assert not violations, (
        "Non-canonical `ai_agent_bridge` module identity found; use `scripts.ai_agent_bridge` "
        "everywhere (#6812):\n" + "\n".join(violations)
    )


def test_bare_bridge_identity_not_loaded() -> None:
    """The bare identity must never occupy a second ``sys.modules`` entry."""
    bare = sys.modules.get("ai_agent_bridge")
    assert "ai_agent_bridge" not in sys.modules, (
        "The bare `ai_agent_bridge` module identity is loaded alongside "
        "`scripts.ai_agent_bridge`; module-level state would diverge (#6812). "
        f"Loaded from: {getattr(bare, '__file__', '<unknown>')}"
    )
