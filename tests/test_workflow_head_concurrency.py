"""Guard PR workflow concurrency against ref-keyed TOCTOU cancellation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HEAD_SHA_GROUP = "${{ github.workflow }}-${{ github.event.pull_request.head.sha || github.ref }}"
_WORKFLOW_EXPECTATIONS = {
    ".github/workflows/ci.yml": "${{ github.event_name == 'pull_request' }}",
    ".github/workflows/content-ci.yml": True,
    ".github/workflows/hygiene.yml": True,
    ".github/workflows/security-audit.yml": True,
    ".github/workflows/zizmor.yml": True,
}


@pytest.mark.parametrize(
    ("relative_path", "expected_cancellation"),
    _WORKFLOW_EXPECTATIONS.items(),
)
def test_workflow_concurrency_is_head_sha_keyed_and_preserves_cancellation(
    relative_path: str,
    expected_cancellation: bool | str,
) -> None:
    """Each scoped workflow isolates PR runs by immutable head and keeps its policy."""
    workflow_path = _REPO_ROOT / relative_path
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    assert workflow["concurrency"] == {
        "group": _HEAD_SHA_GROUP,
        "cancel-in-progress": expected_cancellation,
    }
