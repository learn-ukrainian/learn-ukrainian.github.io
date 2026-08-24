"""Formal CF thrash guard unit tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.ai_agent_bridge._review_pr_thrash import (
    ThrashDecision,
    evaluate_formal_cf_thrash,
    github_actions_outaged,
)


def test_already_approved_same_head():
    with (
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._load_approved_heads",
            return_value=[("abc123", "review_1")],
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
            return_value=False,
        ),
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="ABC123",
            git_repo=None,
        )
    assert d.action == "already_approved"
    assert d.exit_code == 0


def test_refuse_empty_tree_after_approved_ancestor():
    with (
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._load_approved_heads",
            return_value=[("aaa111", "review_old")],
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._git_diff_empty",
            return_value=True,
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
            return_value=False,
        ),
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="bbb222",
            git_repo=Path("/tmp/fake"),
        )
    assert d.action == "refuse"
    assert d.exit_code == 2
    assert "no product tree change" in d.message


def test_allow_thrash_override_skips_tree_guard():
    with (
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._load_approved_heads",
            return_value=[("aaa111", "review_old")],
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
            return_value=True,
        ),
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="bbb222",
            git_repo=Path("/tmp/fake"),
            allow_thrash=True,
        )
    assert d.action == "continue"


def test_actions_outage_refuses():
    with patch(
        "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
        return_value=True,
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="bbb222",
            git_repo=None,
        )
    assert d.action == "refuse"
    assert "Actions" in d.message


def test_continue_when_tree_differs():
    with (
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._load_approved_heads",
            return_value=[("aaa111", "review_old")],
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._git_diff_empty",
            return_value=False,
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
            return_value=False,
        ),
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="bbb222",
            git_repo=Path("/tmp/fake"),
        )
    assert d.action == "continue"


def test_github_actions_outaged_parses_status():
    payload = {
        "components": [
            {"name": "API Requests", "status": "operational"},
            {"name": "Actions", "status": "major_outage"},
        ]
    }
    class _Resp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            import json
            return json.dumps(payload).encode()

    with patch(
        "scripts.ai_agent_bridge._review_pr_thrash.urllib.request.urlopen",
        return_value=_Resp(),
    ):
        assert github_actions_outaged() is True


def test_already_approved_wins_over_actions_outage():
    with (
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash._load_approved_heads",
            return_value=[("abc123", "review_1")],
        ),
        patch(
            "scripts.ai_agent_bridge._review_pr_thrash.github_actions_outaged",
            return_value=True,
        ),
    ):
        d = evaluate_formal_cf_thrash(
            repository="org/repo",
            pr_number=1,
            head_sha="ABC123",
            git_repo=None,
        )
    assert d.action == "already_approved"
    assert d.exit_code == 0
