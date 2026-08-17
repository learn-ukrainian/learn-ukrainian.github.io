"""Make `import ai_agent_bridge` deterministic for this test package.

These tests import the bridge as a top-level package (`from ai_agent_bridge
import …`), which requires `scripts/` on sys.path. In full runs that happened
only by import-order luck (an earlier module primed the path); Pytest fastlane
runs changed files alone and failed collection (#6800). Prime it here so any
subset of this package collects standalone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

# review-pr CLI suites call evaluate_formal_cf_thrash, which live-queries
# githubstatus unless pinned. Keep those suites hermetic (#6962). Do not apply
# package-wide: test_review_pr_thrash.py exercises the real probe parser.
_REVIEW_PR_CLI_THRASH_PIN_MODULES = frozenset(
    {
        "test_review_pr.py",
        "test_review_pr_lifecycle.py",
    }
)


@pytest.fixture(autouse=True)
def _pin_review_pr_thrash_probe_healthy(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Pin githubstatus Actions probe to healthy for review-pr CLI suites."""
    path = getattr(request.node, "path", None)
    if path is None or Path(path).name not in _REVIEW_PR_CLI_THRASH_PIN_MODULES:
        return
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
        lambda **_kwargs: False,
    )
