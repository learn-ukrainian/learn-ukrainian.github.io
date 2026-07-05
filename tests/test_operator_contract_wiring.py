"""Wiring guard for the operator-expectations contract (PR #4412 follow-up).

The contract is only useful if every agent boot path actually reaches it.
These tests pin the wiring so a refactor can't silently orphan the file:

- Claude / API cold-start  -> RULE_SOURCES[0] (served first at /api/rules)
- Codex / cursor / opencode / hermes slot-5 -> AGENTS.md digest section
- Deploy targets           -> excluded from .claude autoload, present in
                              .codex/.agent/.gemini rules (lock-step lists)
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "agents_extensions/shared/rules/operator-expectations.md"
CONTRACT_REL = "agents_extensions/shared/rules/operator-expectations.md"


def test_contract_file_exists_with_all_eleven_items() -> None:
    body = CONTRACT.read_text(encoding="utf-8")
    for n in range(1, 12):
        assert re.search(rf"^{n}\. \*\*", body, re.MULTILINE), f"contract item {n} missing"
    assert "tie-breakers" in body
    assert "A1 is the deliberate exception" in body, "A1 immersion exception clause missing"
    assert "OUTSIDE your own model family" in body, "cross-family review clause missing"


def test_contract_served_first_by_rules_api() -> None:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from api.rules_router import RULE_SOURCES

    assert RULE_SOURCES[0] == CONTRACT_REL, (
        "operator-expectations must be the FIRST file served by /api/rules "
        f"(got {RULE_SOURCES[0]!r})"
    )


def test_agents_md_carries_binding_digest() -> None:
    """Codex, cursor, opencode-hosted models, and hermes (slot 5) boot from
    AGENTS.md — the contract must be referenced AND digested there, because a
    bare pointer is skippable while an inline digest is not."""
    body = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "operator-expectations.md" in body, "AGENTS.md lost the contract pointer"
    assert "Operator Contract" in body, "AGENTS.md lost the contract digest section"
    # Spot-check the two most operator-sensitive digest items survived edits.
    assert "cross-family" in body, "digest lost the cross-family review clause"
    assert "EXCEPT A1" in body, "digest lost the A1 immersion exception"


def test_deploy_lock_step_lists_include_contract() -> None:
    """deploy excludes x drift-checker x idempotency fixtures must move
    together (learned the hard way in #4412 round 3)."""
    deploy = (REPO / "scripts/deploy_prompts.sh").read_text(encoding="utf-8")
    checker = (REPO / "scripts/check_rules_deployment.sh").read_text(encoding="utf-8")
    assert 'rules/operator-expectations.md' in deploy, "deploy autoload-exclude missing"
    assert 'rules/operator-expectations.md' in checker, "drift-checker exclude missing"


def test_offline_fallback_lists_contract() -> None:
    body = (REPO / "agents_extensions/shared/rules/_load-via-api.md").read_text(
        encoding="utf-8"
    )
    assert CONTRACT_REL in body, "offline fallback list lost the contract"
