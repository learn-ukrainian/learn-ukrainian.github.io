"""Offline execution of shared memory's branch-before-PR review example (#10065)."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

from scripts.dispatcher import cli as dispatch_cli
from scripts.dispatcher import git as dispatch_git
from scripts.review import record_cf_verdict as recorder
from tests.test_authoring_review_feasibility import SOL, mini_repo

MEMORY = Path(__file__).resolve().parents[1] / "agents_extensions/shared/memory/MEMORY.md"


def _review_section():
    body = MEMORY.read_text(encoding="utf-8")
    return body.split("## #0H —", 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize("moved_head", [False, True], ids=["pushed-head", "remote-drift"])
def test_documented_ask_reaches_native_branch_pin_admission(monkeypatch, tmp_path, moved_head):
    """The documented v2 command pins a local Git object even when its remote moves."""
    repo = mini_repo(tmp_path, monkeypatch)
    head = repo.commit(SOL)
    repo.publish()
    recipe = re.search(r"`(printf .*?scripts/dispatch\.py dispatch.*?)`", _review_section())
    assert recipe is not None
    tokens = shlex.split(recipe.group(1))
    pipe = tokens.index("|")
    assert tokens[:2] == ["printf", "%s\\n"] and pipe == 3
    replacements = {
        "<branch>": "feature", "<SHA>": head, "<lane>": "claude",
        "<id>": "fixture", "<resolved-model>": "claude-opus-5-5",
    }
    for old, new in replacements.items():
        tokens = [token.replace(old, new) for token in tokens]
    assert tokens[pipe + 1:pipe + 3] == [".venv/bin/python", "scripts/dispatch.py"]
    args = dispatch_cli.build_parser().parse_args(tokens[pipe + 3:])
    assert args.command == "dispatch" and args.agent == "claude"
    assert args.branch == "feature" and args.pr is None
    assert args.model == "claude-opus-5-5" and args.effort == "high"
    assert args.mode == "read-only" and args.worktree == ""
    assert args.prompt_file == "-" and args.require_review_verdict
    assert args.pinned_head == head
    if moved_head:
        assert repo.advance_remote("feature", SOL) != head
    worktree, branch, base = dispatch_git.worktree_plan(
        repo.root, args.agent, args.task_id, args.pinned_head
    )
    assert base == head
    assert branch == "claude/review-fixture"
    assert worktree == repo.root / ".worktrees/dispatch/claude/review-fixture"


def test_documented_recorder_uses_completed_review_task_and_pr(monkeypatch, capsys):
    """Parse the publication example at the existing recorder's external boundary."""
    recipe = re.search(r"`([^`]*scripts/review/record_cf_verdict\.py.*?)`", _review_section())
    assert recipe is not None
    argv = shlex.split(recipe.group(1).replace("<id>", "fixture").replace("<N>", "7"))
    calls = []

    def publication_boundary(task_id, **kwargs):
        calls.append((task_id, kwargs))
        return {"status": "posted"}

    monkeypatch.setattr(recorder, "record", publication_boundary)
    assert recorder.main(argv[2:]) == 0
    assert calls == [("review-fixture", {"pr_number": 7, "review_mode": None, "red_team_prompt": None})]
    assert json.loads(capsys.readouterr().out) == {"status": "posted"}
