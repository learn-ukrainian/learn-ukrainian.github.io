"""Review metadata loss and subject self-review must fail before a paid launch."""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.review import record_cf_verdict as cf
from scripts.review.subject_seat import classify_owned_path

BRANCH_AUTHOR_FAMILIES = checks.check_branch_author_families


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/review", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    # The synthetic head has no Git history; branch authorship is exercised against a real repository below.
    monkeypatch.setattr(checks, "check_branch_author_families", lambda *a: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(
        {**record, "pid": os.getpid(), "process_start": worker._identity(os.getpid())}, prompt,
    ))
    monkeypatch.setattr(worker, "start", start)

    def invoke(*flags, agent="sol", model="gpt-6.1-sol", expected=0):
        assert cli.main(["dispatch", "--agent", agent, "--model", model, "--task-id", "review",
                         "--prompt", "Review this change", *flags]) == expected
        if expected:
            start.assert_not_called()
            git.create_worktree.assert_not_called()
            assert not (tmp_path / "tasks").exists()
            return None
        return store.read("review")

    return invoke


def test_review_metadata_loss_round_trip_enforces_risk_and_subjects(dispatch, monkeypatch):
    record = dispatch("--risk", "high", "--review-profile", "code", "--review-mode", "cross_family",
                      "--review-author-model", "claude-opus-5-5", "--language-lane", "", "--pr", "42",
                      "--subject-seat", "GROK_build", "--subject-seat", "claude-infra",
                      "--subject-seat", "grok", "--subject-family", " XAI ", "--require-review-verdict")
    assert record["schema_version"] == 2
    assert {key: record[key] for key in ("review_risk", "review_profile", "review_mode", "review_author_model",
                                       "language_lane", "pr", "require_review_verdict")} == dict(
        review_risk="high", review_profile="code", review_mode="cross_family",
        review_author_model="claude-opus-5-5", language_lane="", pr=42, require_review_verdict=True)
    assert record["require_review_verdict"] is True
    assert cf._task_flag_values(record, "review_subject_seats") == ("claude", "grok")
    assert cf._task_flag_values(record, "review_subject_families") == ("xai",)
    assert not cf.is_ukrainian_review(record)
    facts = Mock()
    monkeypatch.setattr(cf, "evaluate_candidate", lambda *a, **kw: SimpleNamespace(status="eligible"))
    cf._require_qualified_reviewer(facts, task=record,
                                   model="gpt-6.1-sol", family="openai")
    assert facts.resolver_inputs.call_args.kwargs["risk"] == "high"


@pytest.mark.parametrize("agent,model,flag,value", [
    ("sol", "gpt-6.1-sol", "--subject-seat", "codex-desktop"),
    ("sol", "gpt-6.1-sol", "--subject-family", " OPENAI "),
    ("claude", "claude-opus-5-5", "--subject-seat", "claude-infra"),
    ("cursor", "grok-4.7-high", "--subject-seat", "grok-build"),
    ("cursor", "grok-4.7-high", "--subject-seat", "cursor"),
    ("cursor", "grok-4.7-high", "--subject-family", "xai"),
    ("cursor", "gpt-6.1-sol", "--subject-seat", "codex"),
    ("cursor", "gpt-6.1-sol", "--subject-seat", "grok"),
    ("cursor", "gpt-6.1-sol", "--subject-family", "xai"),
    ("sol", "grok-4.7-high", "--subject-seat", "cursor"),
    ("sol", "grok-4.7-high", "--owned-path", "scripts/dispatcher/providers/cursor.py"),
    ("sol", "gpt-6.1-sol", "--subject-seat", "unknown-seat"),
    ("sol", "gpt-6.1-sol", "--subject-family", "unknown-family"),
    ("cursor", "auto", "--subject-seat", "grok"),
    ("sol", "gpt-6.1-sol", "--owned-path", "scripts/dispatcher/providers/codex.py"),
    ("cursor", "grok-4.7-high", "--owned-path", "scripts/dispatcher/providers/cursor.py"),
])
def test_subject_self_review_effective_identity_or_unknown_refused_before_launch(dispatch, capsys, agent, model, flag, value):
    dispatch(flag, value, agent=agent, model=model, expected=2)
    assert "subject" in capsys.readouterr().err


@pytest.mark.parametrize("model,flags", [
    ("grok-4.7-high", ("--subject-seat", "claude")),
    ("gpt-6.1-sol", ()),
    ("unknown-model", ()),
])
def test_effective_identity_does_not_overexclude_cursor_without_matching_subject(dispatch, model, flags):
    assert dispatch(*flags, agent="cursor", model=model)["model"] == model


def test_unresolvable_cursor_fallback_identity_fails_closed(dispatch, monkeypatch, capsys):
    from scripts.review import model_catalog

    monkeypatch.setattr(model_catalog, "substitution_default_model", lambda _: "unknown-model")
    dispatch("--subject-seat", "claude", agent="cursor", expected=2)
    assert "subject" in capsys.readouterr().err


def test_verdict_requirement_in_write_mode_refused_before_launch(dispatch, capsys):
    dispatch("--require-review-verdict", "--mode", "workspace-write", expected=2)
    assert "requires --mode read-only" in capsys.readouterr().err


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_review_metadata_defaults_do_not_leak_into_non_review_records(dispatch, mode):
    record = dispatch("--mode", mode)
    assert not (set(record) & {"review_risk", "review_profile", "review_author_model", "review_mode", "language_lane",
                               "pr", "require_review_verdict", "review_subject_seats", "review_subject_families"})


@pytest.mark.parametrize("lane", [(), ("--language-lane", "uk")])
def test_profile_only_ukrainian_review_cannot_bypass_sources_evidence(dispatch, lane):
    record = dispatch("--review-profile", "ukrainian", *lane)
    assert record["review_profile"] == "ukrainian" and record.get("language_lane") == ("uk" if lane else None)
    assert cf.is_ukrainian_review(record)
    with pytest.raises(cf.RecordError, match="Sources MCP call count unknown"):
        cf._require_sources_mcp_calls(record)


@pytest.mark.parametrize("language", [("--review-profile", " UKRAINIAN "), ("--language-lane", "uk"),
                                      ("--review-profile", "code", "--language-lane", " ")])
@pytest.mark.parametrize("subject", [("--subject-seat", "grok"), ("--subject-family", "xai"),
                                     ("--owned-path", "scripts/dispatcher/providers/claude.py")])
def test_unpublishable_language_subject_review_refused_before_launch(dispatch, capsys, language, subject):
    dispatch(*language, *subject, expected=2)
    assert "protected subject scope needs a code-profile review" in capsys.readouterr().err


@pytest.mark.parametrize("flags", [("--review-profile", "code"), ("--subject-seat", "grok"),
                                  ("--subject-family", "xai")])
def test_ambiguous_provider_refused_for_review_only(dispatch, capsys, flags):
    dispatch("--owned-path", "scripts/dispatcher/providers/hermes.py", *flags, expected=2)
    assert "ambiguous review subject path" in capsys.readouterr().err


@pytest.mark.parametrize("provider,seat", [("claude", "claude"), ("opencode", "deepseek")])
def test_inferred_subject_seat_is_persisted_for_publication(dispatch, provider, seat):
    record = dispatch("--review-profile", "code", "--owned-path", f"scripts/dispatcher/providers/{provider}.py")
    assert cf._task_flag_values(record, "review_subject_seats") == (seat,)


@pytest.mark.parametrize("schema", [1, 2])
def test_missing_review_metadata_legacy_readers_do_not_rewrite_records(tmp_path, monkeypatch, schema):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(dict(task_id="legacy", schema_version=schema, status="done")))
    before = path.read_bytes()
    record = store.read("legacy")
    assert cf._task_flag_values(record, "review_subject_seats") == ()
    cf._require_sources_mcp_calls(record)
    assert not cf.is_ukrainian_review(record)
    assert path.read_bytes() == before


def test_v2_subject_provider_paths_inferred_from_absolute_and_windows_paths():
    for path in ("/checkout/scripts/dispatcher/providers/claude.py", r"scripts\dispatcher\providers\claude.py"):
        assert classify_owned_path(path).seats == frozenset({"claude"})


SOL = ("sol", "gpt-6.1-sol")


@pytest.mark.parametrize(
    "trailers,flags,reviewer,refusal",
    [
        # Sol is outside the declared author's family but authored a commit on the branch.
        (("claude/claude-opus-5-5", "codex/gpt-6.1-sol"), ("--review-author-model", "claude-opus-5-5", "--risk", "high"),
         SOL, "['anthropic', 'openai']"),
        # Any review flag types a read-only review, dry runs included (F2).
        (("codex/gpt-6.1-sol",), ("--review-mode", "cross_family"), SOL, "['openai']"),
        (("codex/gpt-6.1-sol",), ("--review-mode", "cross_family", "--dry-run"), SOL, "['openai']"),
        # An unresolvable trailer excludes no family, so no reviewer is provably outside it (F1).
        (("claude/cto-not-a-model",), ("--risk", "low"), SOL, "AUTHOR_UNRESOLVED"),
        # An empty range is a refusal, not a range with nobody to exclude (F2).
        ((), ("--risk", "low"), SOL, "has no commits"),
        # A task id without a task record is unresolved on a single-family harness too (F5).
        (("kimi/cto-not-a-model",), ("--risk", "low"), SOL, "AUTHOR_UNRESOLVED"),
        # Authorship runs from the default branch: a --base cut after the Claude commit hides nothing (F6).
        (("claude/claude-opus-5-5", "codex/gpt-6.1-sol"), ("--base", "@1", "--risk", "low"),
         ("claude", "claude-opus-5-5"), "['anthropic', 'openai']"),
        # A red team keeps only its seat rule: unresolved authors and an empty range are refused (F9).
        (("claude/cto-not-a-model",), ("--review-mode", "red_team", "--review-author-model", "claude-opus-5-5"),
         SOL, "AUTHOR_UNRESOLVED"),
        ((), ("--review-mode", "red_team"), SOL, "has no commits"),
        # A review subject or a reviewed --branch types a read-only review (F10).
        (("codex/gpt-6.1-sol",), ("--subject-seat", "claude"), SOL, "['openai']"),
        (("codex/gpt-6.1-sol",), ("--branch", "review/target"), SOL, "['openai']"),
    ],
)
def test_reviewer_excludes_every_branch_author_family(dispatch, monkeypatch, tmp_path, capsys, trailers, flags,
                                                      reviewer, refusal):
    repo, origin = tmp_path / "repo", tmp_path / "origin.git"
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid")

    def run(*args):
        command = ["git", "-C", str(repo), *args]
        return subprocess.run(command, check=True, capture_output=True, text=True, env=env, timeout=30).stdout.strip()

    repo.mkdir()
    run("init", "-q")
    run("commit", "-q", "--allow-empty", "-m", "base")
    # Origin's default branch is the base commit; the reviewed commits are the branch's own.
    run("init", "-q", "--bare", str(origin))
    run("--git-dir", str(origin), "symbolic-ref", "HEAD", "refs/heads/main")
    run("remote", "add", "origin", str(origin))
    run("push", "-q", "origin", "HEAD:refs/heads/main")
    commits = [run("rev-parse", "HEAD")]
    for trailer in trailers:
        run("commit", "-q", "--allow-empty", "-m", f"work\n\nX-Agent: {trailer}")
        commits.append(run("rev-parse", "HEAD"))
    head = commits[-1]
    flags = tuple(commits[int(flag[1:])] if flag.startswith("@") else flag for flag in flags)
    # The gate guards a reviewed change: a verdict is recorded only for a task pinned with --branch (see below).
    if "--branch" not in flags:
        flags = ("--branch", "review/target", *flags)
    monkeypatch.setattr(git, "resolve_repo", lambda _: (repo, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "claude/branch", head))
    monkeypatch.setattr(checks, "check_branch_author_families", BRANCH_AUTHOR_FAMILIES)
    review = ("--mode", "read-only", *flags)
    dispatch(*review, agent=reviewer[0], model=reviewer[1], expected=2)
    assert refusal in capsys.readouterr().err
    grok = ("--agent", "cursor", "--model", "grok-4.7-high")
    if trailers and refusal.startswith("["):
        if "--dry-run" in flags:
            assert cli.main(["dispatch", *grok, "--prompt", "Review this change", *review]) == 0
        else:
            assert dispatch(*review, agent="cursor", model="grok-4.7-high")["model"] == "grok-4.7-high"
    else:
        # Unresolvable authorship and an empty range refuse every reviewer family.
        dispatch(*review, agent="cursor", model="grok-4.7-high", expected=2)


@pytest.mark.parametrize("flags", [("--language-lane", "ukrainian"), ("--risk", "low"), ("--review-profile", "ukrainian")])
def test_typed_dispatch_without_a_reviewed_change_checks_no_branch_authorship(dispatch, monkeypatch, flags):
    # The uk-preamble eval runs --language-lane at a pinned head with no branch or PR. The verdict recorder
    # refuses such a task ("review was not branch-pinned"), so no authorship range exists to check.
    def unexpected(*_args):
        raise AssertionError("branch authorship checked for a dispatch that reviews no change")

    monkeypatch.setattr(checks, "check_branch_author_families", unexpected)
    dispatch("--mode", "read-only", *flags, "--pinned-head", "a" * 40, agent="codex", model="gpt-6.1-sol")


def test_fourth_default_tier_review_dispatch_is_refused_without_any_recorded_verdict(dispatch, monkeypatch, capsys):
    """Defect class: unbounded review spend through unrecorded rounds (#12098)."""
    heads = iter(f"{index}" * 40 for index in range(1, 5))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (Path("/nonexistent"), "codex/review", next(heads)))
    review = ("--mode", "read-only", "--branch", "codex/fix", "--pr", "42", "--risk", "medium",
              "--require-review-verdict", "--prompt", "Review this change")
    for round_number in (1, 2, 3):
        assert cli.main(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--task-id", f"round-{round_number}",
                         *review]) == 0
    # GitHub knows the PR at the fourth head, with a default-tier diff and no recorded verdict at all.
    monkeypatch.setattr(cf, "_run_json", lambda args, **_k: dict(headRefOid="4" * 40, headRefName="codex/fix",
                                                                 state="OPEN"))
    monkeypatch.setattr(cf, "_review_repository_root", lambda *_a: Path("/nonexistent"))
    monkeypatch.setattr(cf, "pr_review_facts", lambda *_a, **_k: SimpleNamespace(changed_paths=("docs/readme.md",),
                                                                                 scope_paths=()))
    monkeypatch.setattr(cf.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(cf.GitHubAdapter, "comments", lambda self, repository, number: [])
    assert cli.main(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--task-id", "round-4", *review]) == 2
    assert "review dispatch refused: REVIEW_BUDGET_EXHAUSTED: PR #42 already has verdicts at 3 heads (3 dispatched " \
           "with no recorded verdict" in capsys.readouterr().err
    assert store.read("round-4", missing_ok=True) is None
