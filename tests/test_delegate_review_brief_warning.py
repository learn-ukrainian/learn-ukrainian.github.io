"""#10665: a review brief without a disposition section is dispatched with a typed warning."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate

CODE = delegate.REVIEW_BRIEF_NO_DISPOSITIONS
WITH_DISPOSITIONS = """Review PR #42 at the pinned head for #1.

## Dispositions

- in_scope_blocker: violates the frozen contract on a changed path, or regresses main.
- follow_up: pre-existing off-path defects, wording, P2/P3.
- stop_and_escalate: material contract ambiguity.
"""
WITHOUT_DISPOSITIONS = "Review PR #42 at the pinned head for #1. Is anything wrong?\n"


def _parse(*extra: str) -> object:
    return delegate.build_parser().parse_args(
        ["dispatch", "--agent", "codex", "--task-id", "t", "--prompt", "x", *extra]
    )


def _review_args(*extra: str) -> object:
    return _parse("--require-review-verdict", *extra)


@pytest.mark.parametrize(
    "brief",
    [
        WITH_DISPOSITIONS,
        "# Dispositions\nin_scope_blocker only.\n",
        "Intro.\n\n   ### Disposition rules (frozen in round 1)\n- follow_up: wording.\n",
        "Context.\n\n## Outcome, threat model and dispositions\n",
    ],
    ids=["template", "h1", "indented-h3-singular", "combined-heading"],
)
def test_a_disposition_heading_satisfies_the_check(brief):
    assert delegate._review_brief_warnings(_review_args(), brief) == []


@pytest.mark.parametrize(
    "brief",
    [
        WITHOUT_DISPOSITIONS,
        "Dispositions: in_scope_blocker, follow_up, stop_and_escalate.\n",
        "Review the brief quoted below.\n\n```markdown\n## Dispositions\n- follow_up: all\n```\n",
        "Review the brief quoted below.\n\n> ## Dispositions\n> - follow_up: all\n",
        "Context.\n\n    ## Dispositions\n",
        "## Dispositionsless heading\n",
    ],
    ids=["none", "prose-only", "fenced-quote", "blockquote", "indented-code", "not-a-word-boundary"],
)
def test_a_brief_without_a_disposition_heading_is_warned(brief):
    assert delegate._review_brief_warnings(_review_args(), brief) == [CODE]


def test_only_review_typed_dispatches_are_checked():
    assert delegate._review_brief_warnings(_parse(), WITHOUT_DISPOSITIONS) == []
    for typing in (("--review-profile", "code"), ("--review-risk", "medium"), ("--pr", "42")):
        assert delegate._review_brief_warnings(_parse(*typing), WITHOUT_DISPOSITIONS) == [CODE]


def test_a_formal_review_attempt_is_exempt():
    # Its rendered template fixes the severities and the validator computes the verdict.
    args = _review_args("--review-attempt", "manifest.yaml")
    assert delegate._review_brief_warnings(args, WITHOUT_DISPOSITIONS) == []


def test_the_warning_line_names_the_code_and_never_refuses():
    line = delegate._review_brief_warning_line(CODE)
    assert line.startswith(f"⚠ {CODE}: ")
    assert "Dispatch continues." in line


def _section(relative: str, start: str, end: str) -> str:
    text = (Path(__file__).resolve().parents[1] / relative).read_text(encoding="utf-8")
    return text[text.index(start) : text.index(end)]


def _shared_review_texts() -> dict[str, str]:
    from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers

    references = "agents_extensions/shared/skills/drive-epic/references"
    return {
        "review brief template": _section(
            f"{references}/review-merge-cleanup.md", "### Review brief template (#10665)", "## §7."
        ),
        "security brief": _section(
            f"{references}/routing-and-dispatch.md",
            "**Security-code briefs (#10665).**",
            "Write every brief so pytest basetemp",
        ),
        "ask verdict preamble": wrappers._REVIEW_VERDICT_OUTPUT,
        "review-deep instructions": wrappers.REVIEW_DEEP_INSTRUCTIONS,
    }


@pytest.mark.parametrize(
    "name", ["review brief template", "security brief", "ask verdict preamble", "review-deep instructions"]
)
def test_shared_review_texts_pass_read_only_admission_and_carry_no_verdict(name):
    """Copied into a read-only review brief, these texts neither refuse it (#8703) nor supply a verdict."""
    from scripts.review.verdict_parser import recognized_verdicts

    text = _shared_review_texts()[name]
    assert delegate._read_only_write_intent_error(mode="read-only", prompt=text) is None
    assert recognized_verdicts(text) == []
    assert delegate.parse_review_verdict(text) is None


def test_shared_review_texts_state_the_rules():
    texts = _shared_review_texts()
    for disposition in ("in_scope_blocker", "follow_up", "stop_and_escalate"):
        assert disposition in texts["review brief template"]
        assert disposition in texts["review-deep instructions"]
    assert "inconclusive: give the BLOCKED token" in texts["ask verdict preamble"]
    assert "approval may carry tracked non-blocking follow-ups" in texts["ask verdict preamble"]
    assert "fail-closed" in texts["security brief"] and "second rejected review round" in texts["security brief"]


@pytest.fixture
def pr_review(tmp_path, monkeypatch):
    """A same-repository PR review whose target resolves without the network (#9272 fixture)."""
    from scripts.orchestration.fleet_repos import load_fleet_repos
    from scripts.review import target_resolution
    from tests.test_ask_review_admission_floor import _git
    from tests.test_delegate import _sanitize_git_env_for_test

    repo = tmp_path / "ordinary-review"
    repo.mkdir()
    for command in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "Test"),
        ("config", "user.email", "test@example.com"),
        ("config", "core.hooksPath", "/dev/null"),
    ):
        _git(repo, *command)
    (repo / "ordinary.py").write_text("value = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    # Same-repository PR admission reads this origin; no authored commits past the base.
    _git(repo, "remote", "add", "origin", f"https://github.com/{load_fleet_repos()['public'].github}.git")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/ordinary-review", "HEAD")
    _sanitize_git_env_for_test(monkeypatch)
    monkeypatch.setattr(delegate, "_local_repo_root", repo)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: {"agents": {}, "diagnostics": {"stale": False}})
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: {})
    head = _git(repo, "rev-parse", "HEAD")
    payload = json.dumps(
        {
            "number": 42,
            "baseRefName": "main",
            "baseRefOid": head,
            "headRefName": "ordinary-review",
            "headRefOid": head,
            "isCrossRepository": False,
        }
    )
    completed = subprocess.CompletedProcess([], 0, payload, "")
    monkeypatch.setattr(target_resolution, "_run_gh", lambda *_args, **_kwargs: completed)
    monkeypatch.setattr("scripts.common.github_client.run", lambda *_args, **_kwargs: completed)
    return tmp_path


def _pr_review_argv(task_id: str, *extra: str) -> list[str]:
    return [
        "dispatch",
        "--agent",
        "codex",
        "--model",
        "gpt-6.1-sol",
        "--mode",
        "read-only",
        "--task-id",
        task_id,
        "--pr",
        "42",
        "--require-review-verdict",
        "--review-profile",
        "code",
        "--review-author-model",
        "claude-opus-5-5",
        "--review-risk",
        "medium",
        *extra,
    ]


class _StopAfterBriefCheck(Exception):
    pass


@pytest.mark.parametrize("source", ["prompt", "prompt-file", "stdin", "force-new"])
@pytest.mark.parametrize("has_dispositions", [False, True], ids=["without", "with"])
def test_dispatch_warns_on_stderr_for_every_prompt_source(pr_review, monkeypatch, capsys, source, has_dispositions):
    brief = WITH_DISPOSITIONS if has_dispositions else WITHOUT_DISPOSITIONS
    task_id = f"review-brief-{source}"
    if source == "prompt-file":
        brief_file = pr_review / "brief.md"
        brief_file.write_text(brief, encoding="utf-8")
        extra = ("--prompt-file", str(brief_file))
    elif source == "stdin":
        extra = ("--prompt", "-")
        monkeypatch.setattr(sys, "stdin", io.StringIO(brief))
    elif source == "force-new":
        # A review re-run under the same task id archives the settled prior record first.
        prior = delegate._state_path(task_id)
        delegate._write_state_atomic(prior, {"task_id": task_id, "status": "done", "pid": None, "initiator": "owner"})
        extra = ("--prompt", brief, "--force-new", "--initiator", "owner")
    else:
        extra = ("--prompt", brief)

    def stop(*_args, **_kwargs):
        raise _StopAfterBriefCheck

    # The lifecycle carrier loads right after the brief check and before any worktree effect.
    monkeypatch.setattr(delegate, "_load_task_lifecycle_carrier", stop)
    args = delegate.build_parser().parse_args(_pr_review_argv(task_id, *extra))
    with pytest.raises(_StopAfterBriefCheck):
        delegate.cmd_dispatch(args)
    err = capsys.readouterr().err
    assert (f"⚠ {CODE}: " in err) is not has_dispositions
    if source == "force-new":
        assert len(list((pr_review / "tasks").glob(f"{task_id}.*.archived.json"))) == 1


@pytest.mark.parametrize("has_dispositions", [False, True], ids=["without", "with"])
def test_dry_run_records_the_typed_warning(pr_review, has_dispositions):
    brief = WITH_DISPOSITIONS if has_dispositions else WITHOUT_DISPOSITIONS
    args = delegate.build_parser().parse_args(_pr_review_argv("review-brief-dry", "--prompt", brief, "--dry-run"))
    assert delegate.cmd_dispatch(args) == 0
    record = json.loads(delegate._state_path("review-brief-dry").read_text(encoding="utf-8"))
    assert record["status"] == "dry_run"
    if has_dispositions:
        assert "review_brief_warnings" not in record
    else:
        assert record["review_brief_warnings"] == [CODE]
