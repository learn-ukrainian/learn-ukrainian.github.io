"""Keep the actionlint workflow-structure gate load-bearing.

``.github/workflows/actionlint.yml`` is the root-cause fix for the #3739/#3742
break, where a de-indented ``setup-node`` ``with:`` block was valid YAML but
invalid Actions, passed yamllint + zizmor, and broke the Pages deploy. The gate
runs ``scripts/audit/check_workflows.sh`` (a checksum-pinned actionlint).

These tests assert the wiring statically — no actionlint binary or network is
required — so the gate cannot be silently removed or gutted: the workflow must
trigger on PRs and invoke the shared script, and the shared script must keep its
pinned version + per-platform checksums + checksum verification.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "actionlint.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "actionlint workflow did not parse to a mapping"
    return data


def test_workflow_uses_minimal_permissions() -> None:
    workflow = _load_workflow()
    assert workflow.get("permissions") == {"contents": "read"}, (
        "actionlint job needs only contents:read"
    )


def test_workflow_checkout_does_not_persist_credentials() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "persist-credentials: false" in text, (
        "checkout must set persist-credentials: false (zizmor baseline)"
    )
