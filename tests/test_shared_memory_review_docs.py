"""Offline execution of shared memory's branch-before-PR review example (#10065)."""

from __future__ import annotations

import io
import json
import re
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts import delegate
from scripts.ai_agent_bridge import _cli
from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers
from tests.test_authoring_review_feasibility import SOL, mini_repo

MEMORY = Path(__file__).resolve().parents[1] / "agents_extensions/shared/memory/MEMORY.md"


def _review_section():
    body = MEMORY.read_text(encoding="utf-8")
    return body.split("## #0H —", 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize("moved_head", [False, True], ids=["pushed-head", "remote-drift"])
def test_documented_ask_reaches_native_branch_pin_admission(monkeypatch, tmp_path, capsys, moved_head):
    """Real parser/handler/wrapper/admission/checkout; only the native worker is offline."""
    repo = mini_repo(tmp_path, monkeypatch)
    head = repo.commit(SOL)
    repo.publish()
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    recipe = re.search(r"`(printf .*?scripts/ai_agent_bridge/__main__\.py ask-.*?)`", _review_section())
    assert recipe is not None
    tokens = shlex.split(recipe.group(1))
    pipe = tokens.index("|")
    assert tokens[:2] == ["printf", "%s\\n"] and pipe == 3
    replacements = {
        "<branch>": "feature",
        "<SHA>": head,
        "<lane>": "claude",
        "<id>": "fixture",
        "<resolved-model>": "claude-opus-5-5",
    }
    for old, new in replacements.items():
        tokens = [token.replace(old, new) for token in tokens]
    assert tokens[pipe + 1:pipe + 3] == [".venv/bin/python", "scripts/ai_agent_bridge/__main__.py"]
    args = _cli._build_parser().parse_args(tokens[pipe + 3:])
    assert args.review and args.branch == "feature" and args.pr is None
    assert args.to_model == "claude-opus-5-5" and args.effort == "high"
    monkeypatch.setattr(_cli, "require_core_or_exit", lambda _name: None)
    monkeypatch.setattr(_cli.sys, "stdin", io.StringIO(tokens[2] + "\n"))

    @contextmanager
    def prompt_directory():
        yield tmp_path

    monkeypatch.setattr(wrappers, "_prompt_directory", prompt_directory)
    real_run = subprocess.run
    commands = []
    reply = tmp_path / "review.result"
    reply.write_text("VERDICT: APPROVE\n", encoding="utf-8")

    def native_boundary(command, **kwargs):
        if "scripts/delegate.py" not in command:
            assert command[0] == "git", "unexpected external call in offline review fixture"
            return real_run(command, **kwargs)
        commands.append(command)
        launch = delegate.build_parser().parse_args(command[2:])
        if launch.command == "dispatch":
            assert launch.mode == "read-only" and launch.worktree == "auto"
            assert launch.require_review_verdict
            assert launch.branch == "feature" and launch.pr is None
            assert launch.model == "claude-opus-5-5" and launch.effort == "high"
            prompt = Path(launch.prompt_file).read_text(encoding="utf-8")
            assert f"branch feature at head {head}" in prompt
            assert "schemas/code-review-findings.v1.schema.json" in prompt
            assert launch.pinned_head is None  # Admission pins the branch, not reply stdout.
            refusal, target = delegate._admit_dispatch_target(launch, agent=launch.agent, trees=None)
            assert refusal is None and target is not None
            assert launch.pinned_head == launch._review_target.head_sha == head
            if moved_head:
                repo.advance_remote("feature", SOL)
            base = delegate._resolve_worktree_base_sha(
                agent=launch.agent,
                task_id=launch.task_id,
                base="main",
                branch=launch.branch,
                pinned_head_sha=launch.pinned_head,
                validated_path=tmp_path / "checkout",
            )
            assert base == head
            return subprocess.CompletedProcess(command, 0, f"{launch.task_id}\nfixture-nonce\n", "")
        assert launch.command == "wait" and launch.task_id == "review-fixture"
        return subprocess.CompletedProcess(
            command, 0,
            json.dumps({"status": "done", "result_file": str(reply), "worktree_base_sha": head}), "",
        )

    monkeypatch.setattr(wrappers.subprocess, "run", native_boundary)
    if moved_head:
        with pytest.raises(SystemExit, match="differs from the pinned head SHA"):
            _cli._handle_acp_compat(args, "claude")
        assert len(commands) == 1  # Refused before any worker/wait or publication.
        assert "VERDICT: APPROVE" not in capsys.readouterr().out
    else:
        _cli._handle_acp_compat(args, "claude")
        assert len(commands) == 2
        assert capsys.readouterr().out.strip() == "VERDICT: APPROVE"  # Fixture reply, not SHA proof.
