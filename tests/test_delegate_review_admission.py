"""#9272: review routes retain an eligible identity and bare head pins refuse before effects."""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.agent_runtime import target_admission
from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit
from scripts.review import reviewer_resolver


@pytest.mark.parametrize("outcome", ["published", "refused", "crashed", "spawn-failed"])
@pytest.mark.parametrize("access", ["full", "isolated"])
def test_review_dispatch_protects_preparation_then_publishes_or_releases(tmp_path, monkeypatch, outcome, access):
    from scripts.orchestration import worktree_claims
    from tests.test_delegate import (
        _init_repo_with_worktree,
        _patch_worker_popen,
        _rendered_attempt_prompt,
        _review_code,
        _sanitize_git_env_for_test,
        _write_args,
    )

    main, reviewer = _init_repo_with_worktree(tmp_path)
    _sanitize_git_env_for_test(monkeypatch)
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    monkeypatch.setattr(delegate, "_local_repo_root", reviewer)
    tasks = main / "batch_state/tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    _patch_worker_popen(monkeypatch)
    if outcome == "spawn-failed":
        popen = delegate.subprocess.Popen

        def fail_worker(argv, *args, **kwargs):
            if "_worker" in argv:
                raise OSError("fixture spawn failure")
            return popen(argv, *args, **kwargs)

        monkeypatch.setattr(delegate.subprocess, "Popen", fail_worker)
    inputs = main / ".worktrees/dispatch/codex/render-inputs"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(inputs), "main"],
        cwd=main,
        check=True,
        capture_output=True,
        timeout=30,
    )
    (inputs / "inputs").mkdir()
    input_root = inputs / "inputs"
    _review_code(main)
    monkeypatch.setattr("scripts.agent_runtime.review_mcp.review_server_checkout", lambda: main)
    monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.verify_full_review_tree", lambda *_args: None)
    prompt_file = _rendered_attempt_prompt(main, tmp_path / "prompt.md", input_root=input_root)
    manifest = input_root / "review.yaml"
    manifest.write_text("review: test\n")
    removals = []

    def remove():
        return worktree_claims.remove_unclaimed_worktree(
            inputs,
            repo_root=main,
            tasks_dir=tasks,
            lock_dir=delegate._worktree_lock_dir(),
            lock_timeout_s=0.1,
            owner_task_id=None,
            reason="race probe",
        )

    def prepare(**_kwargs):
        # Another thread reaches the real shared removal guard at the first
        # input read, before any review task record has been published.
        with ThreadPoolExecutor(max_workers=1) as executor:
            removals.append(executor.submit(remove).result(timeout=5))
        assert removals[-1].reason == worktree_claims.LOCK_BUSY
        assert manifest.read_text() == "review: test\n"
        if outcome == "refused":
            raise ValueError("fixture refusal")
        if outcome == "crashed":
            raise RuntimeError("fixture crash")
        return SimpleNamespace(config_path=tmp_path / "config.json", manifest_sha256="a" * 64)

    monkeypatch.setattr("scripts.agent_runtime.review_mcp.prepare_review_attempt", prepare)
    args = _write_args(
        agent="claude",
        model="claude-opus-5-5",
        task_id="review-race",
        mode="read-only",
        prompt=None,
        prompt_file=str(prompt_file),
        cwd=str(reviewer),
        full_checkout=True,
        review_access=access,
        review_attempt=str(manifest),
        review_id="rev-test",
        attempt_id="att-test",
    )
    if outcome == "crashed":
        with pytest.raises(RuntimeError, match="fixture crash"):
            delegate.cmd_dispatch(args)
    else:
        assert delegate.cmd_dispatch(args) == {"published": 0, "refused": 2, "spawn-failed": 1}[outcome]
    assert len(removals) == 1
    # Every exit releases the transient lock; publication hands protection
    # over to the existing contract, not a new persistent lock field.
    with worktree_claims.worktree_lock(inputs, lock_dir=delegate._worktree_lock_dir(), timeout_s=0):
        pass
    if outcome == "published":
        state_path = delegate._state_path("review-race")
        record = json.loads(state_path.read_bytes())
        assert record["review_contract"]["input_root"] == str(input_root)
        assert remove().reason == "review input root claimed by active task review-race"
        record["status"] = "done"
        state_path.write_text(json.dumps(record))
    elif outcome == "spawn-failed":
        record = json.loads(delegate._state_path("review-race").read_bytes())
        assert record["status"] == "failed"
    else:
        assert not delegate._state_path("review-race").exists()
    # The nested untracked manifest intentionally uses git's cleanliness guard;
    # deletion is now attempted and refused by git, not a leaked input claim.
    assert remove().action == "error"


@pytest.mark.parametrize("inner_first", [False, True])
def test_review_input_lock_selects_deepest_registered_tree(tmp_path, monkeypatch, inner_first):
    from scripts.orchestration import worktree_claims

    outer = tmp_path / "outer"
    inner = outer / "inner"
    inputs = inner / "inputs"
    inputs.mkdir(parents=True)
    wc = delegate._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    trees = [tmp_path, *([inner, outer] if inner_first else [outer, inner])]
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: trees)
    monkeypatch.setattr(delegate, "_worktree_lock_dir", lambda: tmp_path / "locks")
    with contextlib.ExitStack() as locks:
        delegate._lock_review_input_root({"input_root": str(inputs)}, locks)
        with pytest.raises(worktree_claims.WorktreeLockReentry):
            with delegate.worktree_lock(inner):
                pass
        with delegate.worktree_lock(outer):
            pass
    with delegate.worktree_lock(inner):
        pass


def test_review_input_lock_refuses_tree_removed_while_waiting(tmp_path, monkeypatch):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    lookups = iter([[tmp_path, inputs], [tmp_path]])
    wc = delegate._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: next(lookups))
    monkeypatch.setattr(delegate, "_worktree_lock_dir", lambda: tmp_path / "locks")
    with contextlib.ExitStack() as locks, pytest.raises(ValueError, match="disappeared while dispatch waited"):
        delegate._lock_review_input_root({"input_root": str(inputs)}, locks)


def test_review_input_lock_reuses_own_dispatch_lock_and_releases_on_refusal(tmp_path, monkeypatch):
    from scripts.orchestration import worktree_claims

    inputs = tmp_path / "inputs"
    inputs.mkdir()
    wc = delegate._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: [tmp_path, inputs])
    monkeypatch.setattr(delegate, "_worktree_lock_dir", lambda: tmp_path / "locks")
    with contextlib.ExitStack() as locks:
        locks.enter_context(delegate.worktree_lock(inputs))
        delegate._lock_review_input_root({"input_root": str(inputs)}, locks, locked_worktree=inputs)
    with worktree_claims.worktree_lock(inputs, lock_dir=tmp_path / "locks", timeout_s=0):
        pass


def test_review_input_lock_allows_non_worktree_and_refuses_missing_root(tmp_path, monkeypatch):
    wc = delegate._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: [tmp_path])
    with contextlib.ExitStack() as locks:
        delegate._lock_review_input_root({"input_root": str(tmp_path)}, locks)
        with pytest.raises(ValueError, match="disappeared before preparation"):
            delegate._lock_review_input_root({"input_root": str(tmp_path / "gone")}, locks)


def test_review_input_lock_fails_closed_on_unavailable_registration(tmp_path, monkeypatch):
    wc = delegate._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: [])
    with contextlib.ExitStack() as locks, pytest.raises(ValueError, match="registration unavailable"):
        delegate._lock_review_input_root({"input_root": str(tmp_path)}, locks)


def test_review_input_lock_allows_inputs_outside_git(tmp_path, monkeypatch):
    wc = delegate._load_worktree_containment()

    def outside_git(_path):
        raise wc.NotAGitRepositoryError("fixture outside git")

    monkeypatch.setattr(wc, "resolve_main_root", outside_git)
    with contextlib.ExitStack() as locks:
        delegate._lock_review_input_root({"input_root": str(tmp_path)}, locks)


def test_review_input_lock_includes_acp_runtime_without_allowing_reuse(tmp_path, monkeypatch):
    from scripts.orchestration import worktree_claims
    from tests.test_delegate import _init_repo_with_worktree, _sanitize_git_env_for_test

    main, _reviewer = _init_repo_with_worktree(tmp_path)
    _sanitize_git_env_for_test(monkeypatch)
    monkeypatch.setattr(delegate, "_REPO_ROOT", main)
    runtime = main / ".worktrees/dispatch/acp/input-runtime"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(runtime), "main"],
        cwd=main,
        check=True,
        capture_output=True,
        timeout=30,
    )
    assert delegate._resolve_verified_worktree_path(runtime) is None
    with contextlib.ExitStack() as locks:
        delegate._lock_review_input_root({"input_root": str(runtime)}, locks)
        with pytest.raises(worktree_claims.WorktreeLockReentry):
            with delegate.worktree_lock(runtime):
                pass


def _args(*extra, verdict=True):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--model",
            "gpt-6.1-sol",
            "--task-id",
            "review-9272",
            "--mode",
            "read-only",
            *(("--require-review-verdict",) if verdict else ()),
            "--prompt",
            "Review the branch.",
            *extra,
        ]
    )


def _budget(*, claude="cool", codex="near_cap", cursor="cool"):
    return {
        "agents": {"claude": {"status": claude}, "codex": {"status": codex}, "cursor": {"status": cursor}},
        "diagnostics": {"records_loaded": 5, "stale": False},
    }


def _admit(args, monkeypatch, budget=None):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget or _budget())
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    routing = delegate._DispatchRouting()
    result = delegate._admit_dispatch_target(
        args,
        agent=args.agent,
        trees=None,
        route=delegate._dispatch_route(
            args, routing, language_lane=delegate._dispatch_is_language_lane(args), review_attempt=args.review_attempt
        ),
    )
    return result, routing


def test_9312_alias_explicit_model_uses_alias_resolved_identity(monkeypatch):
    args = _args("--agent", "gemini", "--model", "gemini-3.1-pro-high", "--review-profile", "ukrainian")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("agy", "gemini-3.8-flash-high")
    assert routing.substitution["source"] == "retired-cli"


def test_review_alias_model_is_resolved_once_before_selection(monkeypatch):
    calls = []
    real = delegate._resolve_substitution_model

    def capture(seat, model):
        calls.append((seat, model))
        return real(seat, model)

    monkeypatch.setattr(delegate, "_resolve_substitution_model", capture)
    args = _args("--agent", "gemini", "--model", "gemini-3.1-pro-high", "--review-profile", "ukrainian")
    (refusal, target), _ = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "agy"
    assert calls == [("agy", "gemini-3.1-pro-high")]


def test_9312_budget_substitute_is_checked_for_its_own_deficit(monkeypatch, capsys):
    budget = _budget(claude="near_cap", codex="cool")
    budget["agents"]["codex"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-opus-5-5",
        "--check-budget",
        "--review-author-model",
        "composer-2.5",
        "--review-risk",
        "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch, budget)
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal and "deficit" in refusal
    assert target is None and routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err


@pytest.mark.parametrize(
    "subject",
    [
        ("--owned-path", "scripts/agent_runtime/adapters/codex.py"),
        ("--subject-seat", "codex"),
        ("--subject-family", "openai"),
    ],
)
def test_9312_budget_substitute_excludes_governed_seat(monkeypatch, subject):
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-opus-5-5",
        "--check-budget",
        "--review-author-model",
        "composer-2.5",
        "--review-risk",
        "critical",
        *subject,
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap", codex="cool"))
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal
    assert target is None and routing.substitution is None


def test_requested_reviewer_is_also_subject_excluded_before_budget(monkeypatch):
    args = _args(
        "--owned-path",
        "scripts/agent_runtime/adapters/codex.py",
        "--review-author-model",
        "composer-2.5",
        "--review-risk",
        "critical",
    )
    (refusal, target), _ = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"


@pytest.mark.parametrize(
    "subject",
    [
        ("--owned-path", "scripts/agent_runtime/adapters/base.py"),
        ("--subject-seat", "unknown-seat"),
        ("--subject-family", "unknown-family"),
    ],
)
def test_review_subject_ambiguity_or_invalid_identity_refuses_before_budget(monkeypatch, subject):
    def fail():
        pytest.fail("invalid subject must refuse before budget probe")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    args = _args("--check-budget", *subject)
    refusal, target = delegate._admit_dispatch_target(
        args,
        agent=args.agent,
        trees=None,
        route=delegate._dispatch_route(args, delegate._DispatchRouting(), language_lane=False, review_attempt=None),
    )
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal and target is None


def test_9312_alias_without_model_records_only_the_alias(monkeypatch, capsys):
    args = _args("--agent", "gemini", "--review-profile", "ukrainian")
    args.model = None
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "agy"
    assert "REVIEW_IDENTITY_SUBSTITUTED" not in capsys.readouterr().err
    assert routing.substitution["source"] == "retired-cli"
    assert routing.substitution["requested_model"] is None


def test_9312_ineligible_ukrainian_reviewer_has_no_code_substitution_hint():
    with pytest.raises(ReviewAdmissionRefused) as refused:
        resolve_and_admit(
            ("grok",), model="grok-4.7", mode="read-only", review_dispatch=True, review_profile="ukrainian"
        )
    assert "--review-profile ukrainian" in str(refused.value)
    assert "--review-author-model" not in str(refused.value)


def test_9312_merge_heading_is_followed_by_landing_policy():
    workflow = Path("agents_extensions/shared/rules/workflow.md").read_text(encoding="utf-8")
    merge = workflow.split("## Merge policy — ready PRs must not sit", 1)[1]
    assert merge.split("\n\n", 1)[1].startswith("The binding landing order")


@pytest.mark.parametrize(
    "inputs",
    [
        (),
        ("--review-author-model", "claude-opus-5-5"),
        ("--review-risk", "critical"),
        ("--review-profile", "ukrainian"),
    ],
)
def test_review_budget_without_both_trusted_inputs_keeps_requested_reviewer(monkeypatch, capsys, inputs):
    (refusal, target), routing = _admit(_args("--check-budget", *inputs), monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("codex", "gpt-6.1-sol")
    assert routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_review_budget_uses_exact_resolver_choice_and_author_identity(monkeypatch, risk):
    calls = []
    real = reviewer_resolver.resolve_reviewer

    def capture(inputs, **kwargs):
        result = real(inputs, **kwargs)
        calls.append((inputs, result))
        return result

    monkeypatch.setattr(reviewer_resolver, "resolve_reviewer", capture)
    args = _args("--check-budget", "--review-author-model", "claude-opus-5-5", "--review-risk", risk)
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap"))
    assert calls and all(inputs.author_model == "claude-opus-5-5" and inputs.risk == risk for inputs, _ in calls)
    if risk in {"critical", "high"}:
        # Author family is excluded and both native seats are exhausted. The
        # Cursor Grok seat has no critical_review role (#9488) and is off the
        # high ladder (#9538), so nothing may substitute.
        assert refusal and target is None
        assert routing.substitution is None
        assert calls[-1][1].selected is None
        return
    # #9488: the Sol-spared substitute is the attested Cursor Grok seat, sent its exact slug.
    assert refusal is None
    assert (target.recipient, target.model) == ("cursor", "grok-4.7-high")
    assert routing.substitution["source"] == "reviewer-resolver"
    assert calls[-1][1].selected.name == "grok-4.7-cursor-fallback"


def _admit_cursor_review(model, author, risk):
    args = _args("--agent", "cursor", "--model", model, "--review-author-model", author, "--review-risk", risk)
    routing = delegate._DispatchRouting()
    refusal, target = delegate._admit_dispatch_target(
        args,
        agent="cursor",
        trees=None,
        route=delegate._dispatch_route(args, routing, language_lane=False, review_attempt=None),
    )
    return refusal, target, routing


def test_review_dispatch_keeps_the_cursor_grok_seat_at_its_attested_slug(monkeypatch):
    """#9488: the eligible requested Cursor Grok seat keeps its identity and exact slug below high risk."""

    def fail():
        pytest.fail("an eligible requested reviewer must not probe budget without --check-budget")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    refusal, target, routing = _admit_cursor_review("grok-4.7-high", "claude-opus-5-5", "medium")
    assert refusal is None and (target.recipient, target.model) == ("cursor", "grok-4.7-high")
    assert routing.substitution is None


@pytest.mark.parametrize(
    "model,author,risk",
    [
        ("grok-4.7", "claude-opus-5-5", "medium"),  # bare slug runs the unattested Fast variant
        ("grok-4.7-high-fast", "claude-opus-5-5", "medium"),
        # A bracket suffix reaches the adapter's --model unchanged, so only the exact slug is kept.
        ("grok-4.7-high[fast]", "claude-opus-5-5", "medium"),
        ("grok-4.7-high[1m]", "claude-opus-5-5", "medium"),
        ("grok-4.7-high ", "claude-opus-5-5", "medium"),
        ("GROK-4.7-HIGH", "claude-opus-5-5", "medium"),
        ("grok-4.7-high", "cursor:grok-4.7", "medium"),  # Grok never reviews Grok
        ("grok-4.7-high", "claude-opus-5-5", "high"),  # high is Sol or Opus only (#9538)
        ("grok-4.7-high", "claude-opus-5-5", "critical"),  # no critical_review role
    ],
)
def test_review_dispatch_replaces_a_cursor_grok_request_outside_policy(model, author, risk):
    """An ineligible requested reviewer is replaced by the resolver's choice (#9272), never kept."""
    refusal, target, routing = _admit_cursor_review(model, author, risk)
    assert refusal is None
    assert target.recipient in {"codex", "claude"}
    assert reviewer_resolver.resolve_family(target.model) != reviewer_resolver.resolve_author_family(author)
    assert routing.substitution["source"] == "reviewer-resolver"
    assert routing.substitution["requested_model"] == model


def _review_target(model, *, attempt=False, seat="cursor", author="claude-opus-5-5", risk="medium"):
    return target_admission._resolve_review_target(
        seat,
        model,
        author_model=author,
        risk=risk,
        profile="code",
        attempt=attempt,
        snapshot=None,
        budget_seat=seat,
    )


@pytest.mark.parametrize("model", ["grok-4.7-high[fast]", "grok-4.7-high[1m]", "grok-4.7-high[]"])
def test_a_suffixed_cursor_grok_slug_is_never_an_attempt_identity(model):
    """#9488: eligibility is decided on the exact string the adapter would send as --model."""
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED"):
        _review_target(model, attempt=True)


def test_the_exact_cursor_grok_slug_is_kept_as_requested():
    assert _review_target("grok-4.7-high", attempt=True) == ("cursor", "grok-4.7-high")


def test_a_native_seat_keeps_its_context_suffix():
    """Bracket suffixes on native seats (context windows) keep their pre-#9488 admission."""
    assert _review_target("claude-opus-5-5[1m]", seat="claude", author="gpt-6.1-sol") == (
        "claude",
        "claude-opus-5-5[1m]",
    )


def test_same_family_requested_reviewer_takes_resolvers_eligible_seat(monkeypatch):
    args = _args("--check-budget", "--review-author-model", "gpt-6.1-sol", "--review-risk", "critical")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert target.recipient == "claude"
    assert reviewer_resolver.resolve_family(target.model) == "anthropic"
    assert routing.substitution["actual_model"] == target.model
    assert routing.substitution["source"] == "reviewer-resolver"


@pytest.mark.parametrize("risk,model", [("medium", "claude-fable-5-1")])
@pytest.mark.parametrize("flags", [(), ("--check-budget",), ("--check-budget", "--force-agent")])
def test_trusted_eligible_off_ladder_reviewer_is_kept(monkeypatch, capsys, risk, model, flags):
    # Fable stays off every routine ladder; an explicit eligible pin is still admitted.
    args = _args(
        "--agent",
        "claude",
        "--model",
        model,
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        risk,
        *flags,
    )
    assert all(
        candidate.concrete_model != args.model for rung in reviewer_resolver.REVIEW_LADDERS[risk] for candidate in rung
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", model)
    assert routing.substitution is None
    assert "SUBSTITUT" not in capsys.readouterr().err


HIGH_RISK_RULE = "a formal review at high risk is performed only by gpt-6.1-sol, claude-opus-5-5"


@pytest.mark.parametrize(
    "seat,model,author,expected",
    [
        ("claude", "claude-sonnet-5-5", "gpt-6.1-sol", ("claude", "claude-opus-5-5")),
        ("claude", "claude-fable-5-1", "gpt-6.1-sol", ("claude", "claude-opus-5-5")),
        ("cursor", "grok-4.7-high", "claude-opus-5-5", ("codex", "gpt-6.1-sol")),
    ],
)
@pytest.mark.parametrize("flags", [(), ("--check-budget",), ("--force-agent",), ("--check-budget", "--force-agent")])
@pytest.mark.parametrize(
    "typing",
    [
        pytest.param(("--require-review-verdict",), id="verdict"),
        pytest.param(("--review-profile", "code"), id="profile-only"),
        pytest.param((), id="author-and-risk-only"),
    ],
)
def test_high_risk_review_never_admits_a_seat_outside_sol_and_opus(
    monkeypatch, capsys, seat, model, author, expected, flags, typing
):
    """#9538: every review-typed dispatch, not only a verdict-gated one, applies the high-risk reviewer rule."""
    args = _args(
        "--agent",
        seat,
        "--model",
        model,
        "--review-author-model",
        author,
        "--review-risk",
        "high",
        *typing,
        *flags,
        verdict=False,
    )
    assert delegate._dispatch_is_review_typed(args)
    (refusal, target), routing = _admit(args, monkeypatch, _budget(codex="cool"))
    assert refusal is None
    assert (target.recipient, target.model) == expected
    assert routing.substitution["source"] == "reviewer-resolver"
    assert routing.substitution["requested_model"] == model
    assert "REVIEW_IDENTITY_SUBSTITUTED:" in capsys.readouterr().err


@pytest.mark.parametrize("flags", [(), ("--check-budget",), ("--check-budget", "--force-agent")])
def test_medium_risk_review_keeps_the_requested_sonnet_seat(monkeypatch, capsys, flags):
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-sonnet-5-5",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "medium",
        *flags,
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(codex="cool"))
    assert refusal is None and (target.recipient, target.model) == ("claude", "claude-sonnet-5-5")
    assert routing.substitution is None


@pytest.mark.parametrize("verdict", [True, False])
def test_high_risk_review_without_an_author_refuses_with_the_rule(monkeypatch, verdict):
    args = _args(
        "--agent", "claude", "--model", "claude-sonnet-5-5", "--review-risk", "high", "--force-agent", verdict=verdict
    )
    (refusal, target), _ = _admit(args, monkeypatch)
    assert target is None
    assert refusal and "REVIEW_ROUTE_REFUSED: requested reviewer is ineligible" in refusal
    assert HIGH_RISK_RULE in refusal


@pytest.mark.parametrize("seat,model", [("claude", "claude-sonnet-5-5"), ("cursor", "grok-4.7-high")])
def test_high_risk_review_attempt_refuses_with_the_rule(seat, model):
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED") as refused:
        _review_target(
            model, attempt=True, seat=seat, author="gpt-6.1-sol" if seat == "claude" else "claude-opus-5-5", risk="high"
        )
    assert HIGH_RISK_RULE in str(refused.value)


def test_pace_only_retention_at_high_keeps_opus_never_the_requested_sonnet(monkeypatch, capsys):
    """#9538: with no permitted substitute, pace-only retention keeps an Opus seat, not Sonnet."""
    budget = _budget()
    budget["agents"]["claude"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-sonnet-5-5",
        "--check-budget",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "high",
        "--dry-run",
    )
    (refusal, target), _ = _admit(args, monkeypatch, budget)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    assert "NOTE: REVIEW_BUDGET_RETAINED" in capsys.readouterr().err


def test_off_ladder_reviewer_is_substituted_when_budget_requires_it(monkeypatch, capsys):
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-fable-5-1",
        "--check-budget",
        "--review-author-model",
        "composer-2.5",
        "--review-risk",
        "medium",
    )
    assert all(
        candidate.concrete_model != args.model
        for rung in reviewer_resolver.REVIEW_LADDERS[args.review_risk]
        for candidate in rung
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap", codex="cool"))
    assert refusal is None and (target.recipient, target.model) == ("codex", "gpt-6.1-sol")
    assert routing.substitution["actual_agent"] == "codex"
    assert "HARD AUTO-SUBSTITUTE: REVIEW_IDENTITY_SUBSTITUTED:" in capsys.readouterr().err


@pytest.mark.parametrize("flags", [(), ("--force-agent",)])
@pytest.mark.parametrize("seat,model", [("codex", "gpt-6.1-sol"), ("grok", "grok-4.7")])
def test_admission_identity_swap_always_prints_typed_note(monkeypatch, capsys, flags, seat, model):
    args = _args(
        "--agent",
        seat,
        "--model",
        model,
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "critical",
        *flags,
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"
    assert routing.substitution["actual_model"] == target.model
    assert "REVIEW_IDENTITY_SUBSTITUTED:" in capsys.readouterr().err


def test_gemini_alias_keeps_ukrainian_review_admission(monkeypatch, capsys):
    args = _args("--agent", "gemini", "--review-profile", "ukrainian")
    args.model = None
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("agy", "gemini-3.8-flash-high")
    assert routing.substitution["actual_agent"] == "agy"
    assert "RETIRED CLI ALIAS:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "flags",
    [
        ("--review-author-model", "gpt-6.1-sol"),
        ("--review-risk", "medium"),
        ("--review-author-model", "gpt-6.1-sol", "--review-risk", "critical"),
    ],
)
def test_ukrainian_review_resolver_flags_refuse_with_code_only_guidance(monkeypatch, flags):
    (refusal, target), _ = _admit(_args("--review-profile", "ukrainian", *flags), monkeypatch)
    assert target is None
    assert "REVIEW_ROUTE_REFUSED:" in refusal and "code profile only" in refusal


def test_review_resolver_help_and_budget_notice_state_code_profile_only(monkeypatch, capsys):
    parser = delegate.build_parser()
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(["dispatch", "--help"])
    assert exit_info.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert help_text.count("Code profile only") >= 2
    (refusal, target), _ = _admit(_args("--review-profile", "ukrainian", "--check-budget"), monkeypatch)
    assert refusal is None and target.recipient == "codex"
    assert "code profile only" in capsys.readouterr().err


def test_review_budget_success_matches_exact_in_process_resolver_result(monkeypatch, capsys):
    resolutions = []
    real = reviewer_resolver.resolve_reviewer

    def capture(inputs, **kwargs):
        result = real(inputs, **kwargs)
        resolutions.append(result)
        return result

    monkeypatch.setattr(reviewer_resolver, "resolve_reviewer", capture)
    args = _args("--check-budget", "--review-author-model", "composer-2.5", "--review-risk", "critical")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    selected = resolutions[-1].selected
    assert (target.recipient, target.model) == (selected.route, selected.concrete_model)
    assert target.recipient == "claude" and selected.quality_tier == "frontier_authority"
    assert routing.substitution["actual_model"] == selected.concrete_model
    output = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in output and "grok" not in output


def test_review_budget_substitute_pins_resolver_model(monkeypatch):
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-sonnet-5-5",
        "--check-budget",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"
    assert target.model != "claude-sonnet-5-5"  # Critical reviews require the authority seat.
    assert routing.substitution["actual_model"] == target.model


def test_review_admits_sole_cross_family_seat_in_pace_deficit(monkeypatch, capsys):
    budget = _budget()
    budget["agents"]["claude"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args("--check-budget", "--review-author-model", "gpt-6.1-sol", "--review-risk", "critical", "--dry-run")
    (refusal, target), _ = _admit(args, monkeypatch, budget)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    assert "NOTE: REVIEW_BUDGET_RETAINED" in capsys.readouterr().err


@pytest.mark.parametrize(
    "inputs",
    [
        (),
        ("--review-author-model", "gpt-6.1-sol"),
        ("--review-risk", "critical"),
        ("--review-author-model", "gpt-6.1-sol", "--review-risk", "critical"),
    ],
)
def test_retained_reviewer_only_hints_about_missing_trusted_inputs(monkeypatch, capsys, inputs):
    budget = _budget()
    budget["agents"]["claude"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args("--agent", "claude", "--model", "claude-opus-5-5", "--check-budget", *inputs)
    (refusal, target), routing = _admit(args, monkeypatch, budget)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    assert routing.substitution is None
    output = capsys.readouterr().err
    assert "NOTE: REVIEW_BUDGET_RETAINED" in output
    missing_inputs = not (args.review_author_model and args.review_risk)
    assert ("Legacy calls without trusted author/risk inputs" in output) == missing_inputs
    assert ("budget substitution requires --review-author-model and --review-risk (code profile only)" in output) == (
        missing_inputs
    )


def test_explicit_reviewer_context_window_keeps_its_model(monkeypatch):
    args = _args("--agent", "claude", "--model", "claude-opus-5-5[1m]")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.model == "claude-opus-5-5[1m]"
    assert routing.substitution is None


@pytest.mark.parametrize(
    "seat,model",
    [("grok", "grok-4.7"), ("cursor", "grok-4.7"), ("agy", "gemini-3.8-flash-high"), ("kimi", "kimi-code/k3")],
)
def test_ineligible_review_refuses_before_budget_probe(monkeypatch, seat, model):
    def fail():
        pytest.fail("ineligible review must not probe budget")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    args = _args("--agent", seat, "--model", model, "--check-budget")
    routing = delegate._DispatchRouting()
    refusal, target = delegate._admit_dispatch_target(
        args,
        agent=seat,
        trees=None,
        route=delegate._dispatch_route(args, routing, language_lane=False, review_attempt=None),
    )
    assert refusal and target is None


@pytest.mark.parametrize("inputs", [(), ("--review-author-model", "claude-opus-5-5", "--review-risk", "critical")])
def test_review_attempt_refuses_budget_substitution_separately(monkeypatch, capsys, inputs):
    (refusal, target), routing = _admit(
        _args("--check-budget", "--review-attempt", "attempt.yaml", *inputs), monkeypatch
    )
    assert "REVIEW_ATTEMPT_IDENTITY_REFUSED" in refusal and target is None
    assert routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err


@pytest.mark.parametrize("fallbacks", [{}, {"codex": "codex"}])
def test_review_attempt_budget_refusal_without_substitute_names_seat_and_cause(monkeypatch, fallbacks):
    monkeypatch.setattr("scripts.common.fallback_substitutions.load_dispatch_fallbacks", lambda _path: fallbacks)
    (refusal, target), routing = _admit(_args("--check-budget", "--review-attempt", "attempt.yaml"), monkeypatch)
    assert target is None and routing.substitution is None
    assert refusal == (
        "REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused for codex: "
        "budget guard requires substitution; attempt identity is immutable (#8517)"
    )


def test_retired_review_attempt_refuses_before_route_and_budget_probe(monkeypatch):
    def fail(*_args, **_kwargs):
        pytest.fail("retired review attempt must refuse before routing or probing")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    with pytest.raises(ReviewAdmissionRefused) as refused:
        resolve_and_admit(("gemini",), mode="read-only", review_dispatch=True, review_attempt=True, route=fail)
    assert str(refused.value) == (
        "REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused: "
        "agent substitution from gemini to agy (retired CLI) is not allowed (#8517)"
    )


def test_review_attempt_with_headroom_keeps_identity(monkeypatch):
    (refusal, target), _ = _admit(
        _args("--check-budget", "--review-attempt", "attempt.yaml"), monkeypatch, _budget(codex="cool")
    )
    assert refusal is None and (target.recipient, target.model) == ("codex", "gpt-6.1-sol")


def test_review_admission_refuses_a_route_ignoring_the_reviewer_selector():
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ROUTE_REFUSED"):
        resolve_and_admit(
            ("codex",),
            mode="read-only",
            model="gpt-6.1-sol",
            review_dispatch=True,
            route=lambda request: ("cursor", "grok-4.7", "budget"),
        )


@pytest.mark.parametrize("flags", [(), ("--worktree",), ("--worktree", "--dry-run"), ("--check-budget",)])
def test_bare_pinned_head_refuses_before_probes_worktree_or_task_record(monkeypatch, tmp_path, capsys, flags):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))

    def fail(*_a, **_k):
        pytest.fail("bare pin reached a probe, task record, or worktree effect")

    for name in ("_fetch_routing_budget", "_ensure_worktree", "_write_state_atomic", "tasks_dir"):
        monkeypatch.setattr(delegate, name, fail)
    monkeypatch.setattr(delegate.subprocess, "run", fail)
    monkeypatch.setattr(delegate.subprocess, "Popen", fail)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail)
    assert delegate.cmd_dispatch(_args("--pinned-head", "a" * 40, *flags)) == 2
    assert "PINNED_HEAD_TARGET_REQUIRED" in capsys.readouterr().err
    assert not tasks.exists()


@pytest.mark.parametrize("reused,local_head", [(False, "a" * 40), (True, "a" * 40), (True, "b" * 40)])
def test_branch_pin_is_exact_for_new_and_reused_worktrees(monkeypatch, tmp_path, reused, local_head):
    worktree = tmp_path / "worktree"
    if reused:
        worktree.mkdir()
    monkeypatch.setattr(delegate, "_validate_existing_worktree", lambda **_k: None)
    monkeypatch.setattr(delegate, "_fetch_existing_branch", lambda _b: None)
    monkeypatch.setattr(delegate, "_require_local_branch_is_ancestor_of_origin", lambda _b: "a" * 40)
    monkeypatch.setattr(delegate, "_resolve_sha", lambda _p: local_head)
    kwargs = dict(
        agent="codex",
        task_id="review-9272",
        validated_path=worktree,
        base="main",
        branch="codex/subject",
        pinned_head_sha="a" * 40,
    )
    if reused and local_head != "a" * 40:
        with pytest.raises(RuntimeError, match="differs from the pinned head SHA"):
            delegate._resolve_worktree_base_sha(**kwargs)
    else:
        assert delegate._resolve_worktree_base_sha(**kwargs) == "a" * 40


@pytest.mark.parametrize(
    "lane",
    [
        {"status": "near_cap"},
        {"status": "hot"},
        {"status": "cool", "health": {"healthy": False}},
        {"status": "cool", "runtime": {"headroom_blocked": True}},
        {"status": "cool", "scheduler": {"circuit_open": True}},
    ],
)
def test_pace_exception_never_overrides_hard_capacity_or_health(monkeypatch, lane):
    budget = _budget(codex="cool")
    budget["agents"]["claude"] = dict(
        lane,
        codexbar={
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 12.0,
            "weekly_expected_pct": 40.0,
        },
    )
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-opus-5-5",
        "--check-budget",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "critical",
        "--dry-run",
    )
    (refusal, target), _ = _admit(args, monkeypatch, budget)
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal
    assert target is None


def test_pace_deficit_prefers_available_cross_family_alternative(monkeypatch):
    budget = _budget(codex="cool")
    budget["agents"]["claude"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-opus-5-5",
        "--check-budget",
        "--review-author-model",
        "composer-2.5",
        "--review-risk",
        "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch, budget)
    assert refusal is None
    assert (target.recipient, target.model) == ("codex", "gpt-6.1-sol")
    assert routing.substitution["actual_agent"] == "codex"


@pytest.mark.parametrize(
    "status,review_trusted_inputs,expected_exact,expected_prefix,expected_suffix",
    [
        (
            "cool",
            False,
            None,
            "NOTE: REVIEW_BUDGET_RETAINED: no eligible substitute; retaining admitted reviewer on pace-only deficit.",
            "budget substitution requires --review-author-model and --review-risk (code profile only)",
        ),
        (
            "cool",
            True,
            "NOTE: REVIEW_BUDGET_RETAINED: no eligible substitute; retaining admitted reviewer on pace-only deficit.",
            None,
            None,
        ),
        (
            "near_cap",
            False,
            None,
            "REVIEW_SUBSTITUTION_DISABLED: retaining eligible requested reviewer;",
            "budget substitution requires --review-author-model and --review-risk (code profile only)",
        ),
        (
            "near_cap",
            True,
            "REVIEW_SUBSTITUTION_DISABLED: retaining eligible requested reviewer.",
            None,
            None,
        ),
    ],
)
def test_review_substitution_disabled_notice_no_dangling_separator(
    monkeypatch, capsys, status, review_trusted_inputs, expected_exact, expected_prefix, expected_suffix
):
    budget = _budget(claude=status)
    if status == "cool":
        budget["agents"]["claude"]["codexbar"] = {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 12.0,
            "weekly_expected_pct": 40.0,
        }
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    res = delegate._resolve_agent_with_budget_guard(
        "claude",
        requested_model="claude-opus-5-5",
        fallbacks={},
        review_select=lambda _p, _r: ("claude", "claude-opus-5-5"),
        review_trusted_inputs=review_trusted_inputs,
    )
    assert res == "claude"
    err = capsys.readouterr().err.strip()
    if expected_exact:
        assert err == expected_exact
    else:
        assert err.startswith(expected_prefix)
        assert err.endswith(expected_suffix)
    assert not err.endswith(";")
    assert not err.endswith(":")


def test_review_substitution_disabled_with_trusted_inputs_via_admit(monkeypatch, capsys):
    from scripts.agent_runtime import target_admission

    monkeypatch.setattr(
        target_admission,
        "_resolve_review_target",
        lambda *args, **kwargs: ("claude", "claude-opus-5-5"),
    )
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-opus-5-5",
        "--check-budget",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap"))
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    assert routing.substitution is None
    err = capsys.readouterr().err.strip()
    assert err == "REVIEW_SUBSTITUTION_DISABLED: retaining eligible requested reviewer."


@pytest.mark.parametrize(
    "extra",
    [
        pytest.param(("--review-profile", "code"), id="profile"),
        pytest.param(("--review-author-model", "gpt-6.1-sol"), id="author"),
        pytest.param(("--review-risk", "medium"), id="risk"),
    ],
)
def test_review_flags_type_a_dispatch_without_the_verdict_flag(extra):
    """#9538: review typing never depends on --require-review-verdict."""
    assert not delegate._dispatch_is_review_typed(_args(verdict=False))
    assert delegate._dispatch_is_review_typed(_args(*extra, verdict=False))


@pytest.mark.parametrize("seat,model", [("kimi", None), ("agy", "gemini-3.8-flash-high")])
def test_code_review_without_the_verdict_flag_refuses_a_seat_that_never_reviews_code(monkeypatch, seat, model):
    """#9538: a code-review dispatch without trusted inputs still passes reviewer admission."""
    pin = ("--model", model) if model else ()
    args = _args("--agent", seat, *pin, "--review-profile", "code", "--force-agent", verdict=False)
    (refusal, target), _ = _admit(args, monkeypatch)
    assert target is None
    assert refusal


def test_medium_risk_review_without_the_verdict_flag_keeps_the_requested_sonnet_seat(monkeypatch):
    """Medium risk is unchanged: the practical ladder still admits Sonnet without the verdict flag."""
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-sonnet-5-5",
        "--review-profile",
        "code",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "medium",
        "--force-agent",
        verdict=False,
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(codex="cool"))
    assert refusal is None and (target.recipient, target.model) == ("claude", "claude-sonnet-5-5")
    assert routing.substitution is None
