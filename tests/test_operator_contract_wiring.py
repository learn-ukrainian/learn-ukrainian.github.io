"""Wiring guard for the operator-expectations contract (PR #4412 follow-up).

The contract is only useful if every agent boot path actually reaches it.
These tests pin the wiring so a refactor can't silently orphan the file:

- Full API reference      -> contract first at /api/rules?scope=full
- Unscoped API cold-start -> binding core, with boot-file contract digests
- Codex / cursor / opencode / hermes slot-5 -> AGENTS.md digest section
- Deploy targets           -> excluded from .claude autoload, present in
                              .codex/.agent/.gemini rules (lock-step lists)
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_skills

REPO = Path(__file__).resolve().parents[1]
def test_deploy_lock_step_lists_include_contract() -> None:
    """deploy excludes x drift-checker x idempotency fixtures must move
    together (learned the hard way in #4412 round 3).

    Since #4610 the lock-step lists live in ONE sourceable file
    (scripts/deploy_orphan_paths.sh) that BOTH consumers source — the
    contract entry must be in the shared file, and both scripts must
    actually source it (a copy that drifts is the #4412 bug reborn).
    """
    shared = (REPO / "scripts/deploy_orphan_paths.sh").read_text(encoding="utf-8")
    deploy = (REPO / "scripts/deploy_prompts.sh").read_text(encoding="utf-8")
    checker = (REPO / "scripts/check_rules_deployment.sh").read_text(encoding="utf-8")
    session_setup = (REPO / "agents_extensions/shared/hooks/session-setup.sh").read_text(encoding="utf-8")
    assert "rules/operator-expectations.md" in shared, "shared autoload-exclude missing"
    assert "deploy_orphan_paths.sh" in deploy, "deploy does not source the shared lists"
    assert "deploy_orphan_paths.sh" in checker, "drift-checker does not source the shared lists"
    assert "deploy_orphan_paths.sh" in session_setup, "session-setup hook does not source the shared lists"


def _offline_fallback_list(body: str) -> list[str]:
    marker = "`RULE_SOURCES`:"
    start = body.index(marker) + len(marker)
    paths: list[str] = []
    for line in body[start:].splitlines():
        stripped = line.strip()
        if not stripped:
            if paths:
                break
            continue
        if stripped.startswith("These files"):
            break
        if stripped.endswith(".md"):
            paths.append(stripped)
        elif paths:
            break
    return paths


def test_offline_fallback_list_equals_rule_sources() -> None:
    """#7011: a down API must not be a different ruleset than RULE_SOURCES."""
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from api.rules_router import RULE_SOURCES

    body = (REPO / "agents_extensions/shared/rules/_load-via-api.md").read_text(encoding="utf-8")
    assert tuple(_offline_fallback_list(body)) == RULE_SOURCES
