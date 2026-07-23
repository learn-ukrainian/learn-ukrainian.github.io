"""Run the launcher handoff-identity fixtures under the required pytest gate.

``scripts/audit/test_handoff_identity.sh`` exercises
``scripts/lib/handoff_identity.sh`` — the derivation that ``start-claude.sh``
uses to turn a Claude Code ``--agent`` selection into the right
``SESSION_HANDOFF_AGENT`` cold-start slot (e.g. ``infra-orchestrator`` →
``claude-infra``). This thin wrapper makes that mapping load-bearing in the
required ``Test (pytest)`` job, so the infra/folk cold-start collision cannot
silently regress.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_handoff_identity.sh"
_HANDOFF_IDENTITY = _REPO_ROOT / "scripts" / "lib" / "handoff_identity.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_handoff_identity_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing identity test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"identity fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - handoff identity fixtures passed" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("resolver", "expected"),
    [
        ("handoff_identity_for_epic", "claude-infra"),
        ("handoff_identity_for_gemini_epic", "gemini-infra"),
        ("handoff_identity_for_codex_epic", "codex-infra"),
    ],
)
def test_devops_alias_resolves_to_canonical_infra_slot(resolver: str, expected: str) -> None:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; "$2" devops', "bash", str(_HANDOFF_IDENTITY), resolver],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected
