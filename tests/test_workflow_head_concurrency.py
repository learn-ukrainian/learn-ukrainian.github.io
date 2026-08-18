"""Guard workflow concurrency against ref-keyed TOCTOU cancellation.

Two-tier cutover (#6943 stage 2): dual-event / advisory workflows prefix the
group with ``github.event_name`` so a PR push cannot share a bucket with a
queued ``merge_group`` run. PR-only workflows keep the original head-SHA
group. ``merge_group`` must never set ``cancel-in-progress: true``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PR_HEAD_GROUP = "${{ github.workflow }}-${{ github.event.pull_request.head.sha || github.ref }}"
_EVENT_PR_HEAD_GROUP = (
    "${{ github.workflow }}-${{ github.event_name }}-"
    "${{ github.event.pull_request.head.sha || github.ref }}"
)
_EVENT_SHA_GROUP = "${{ github.workflow }}-${{ github.event_name }}-${{ github.sha }}"
_WORKFLOW_EXPECTATIONS = {
    ".github/workflows/ci.yml": {
        "group": _EVENT_PR_HEAD_GROUP,
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    },
    ".github/workflows/content-ci.yml": {
        "group": _PR_HEAD_GROUP,
        "cancel-in-progress": True,
    },
    ".github/workflows/hygiene.yml": {
        "group": _EVENT_SHA_GROUP,
        "cancel-in-progress": "${{ github.event_name != 'merge_group' }}",
    },
    ".github/workflows/security-audit.yml": {
        "group": _EVENT_SHA_GROUP,
        "cancel-in-progress": True,
    },
    ".github/workflows/zizmor.yml": {
        "group": _PR_HEAD_GROUP,
        "cancel-in-progress": True,
    },
}


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    _WORKFLOW_EXPECTATIONS.items(),
)
def test_workflow_concurrency_is_head_sha_keyed_and_preserves_cancellation(
    relative_path: str,
    expected: dict[str, str | bool],
) -> None:
    """Each scoped workflow isolates runs by immutable identity and keeps its policy."""
    workflow_path = _REPO_ROOT / relative_path
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    assert workflow["concurrency"] == expected


def test_merge_group_workflows_do_not_unconditionally_cancel() -> None:
    """A queued merge_group run must not be cancelled by a later run in the same workflow."""
    workflows_dir = _REPO_ROOT / ".github" / "workflows"
    for path in sorted(workflows_dir.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        triggers = workflow.get("on", workflow.get(True))
        if not isinstance(triggers, dict) or "merge_group" not in triggers:
            continue
        cancel = workflow.get("concurrency", {}).get("cancel-in-progress")
        assert cancel is not True, (
            f"{path.name} fires on merge_group but cancel-in-progress is unconditionally true"
        )
        assert "github.event_name" in str(cancel), (
            f"{path.name} must gate cancel-in-progress on event_name so merge_group is kept"
        )
