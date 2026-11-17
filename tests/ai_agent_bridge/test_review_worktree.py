"""Release bridge review-target admission that the deleted product review-worktree suite also covered.

The product ``scripts/ai_agent_bridge/_review_worktree.py`` and its seat modules
were removed as dead forks; these cases exercise the installed ``lu_machinery``
bridge, so they stay.
"""

from __future__ import annotations

import json

import pytest
from lu_machinery.ai_agent_bridge import _agy, _cli


def _review_message(*, to: str) -> dict[str, object]:
    return {
        "id": 91,
        "task_id": "null-checkout-review",
        "from": "orchestrator",
        "to": to,
        "type": "query",
        "content": "Review the branch.",
        "data": json.dumps({"review_target": {"branch": "feature/review"}}),
    }


def test_agy_review_bridge_refuses_null_sealed_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    """AGY sealed CF refuses before checkout provision (#5553)."""
    monkeypatch.setattr(_agy, "_fetch_agy_message", lambda _id: _review_message(to="agy"))
    monkeypatch.setattr(
        _agy.agent_runner,
        "invoke",
        lambda *_args, **_kwargs: pytest.fail("runtime must not launch without a sealed checkout"),
    )

    with pytest.raises(ValueError, match="agy_isolated_review_unsupported"):
        _agy.process_for_agy(91, review=True)


def test_review_cli_accepts_explicit_branch_only_with_review() -> None:
    parser = _cli._build_parser()
    args = parser.parse_args(
        [
            "ask-agy",
            "Review the branch.",
            "--task-id",
            "review-5150",
            "--review",
            "--branch",
            "feature/review",
        ]
    )

    assert _cli._review_target_kwargs(args) == {
        "review_branch": "feature/review",
        "review_pr_number": None,
    }

    args.review = False
    with pytest.raises(SystemExit, match="require --review"):
        _cli._review_target_kwargs(args)
