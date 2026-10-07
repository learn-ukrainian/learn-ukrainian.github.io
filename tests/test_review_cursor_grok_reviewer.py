"""Native and Cursor Grok admission, independence and attestation (#9769)."""

from __future__ import annotations

import copy
import json
from dataclasses import replace

import pytest

from scripts.review import closeout_cli
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, validate_catalog
from scripts.review.reviewer_resolver import (
    REVIEW_CANDIDATES,
    ResolverInputs,
    evaluate_candidate,
    resolve_reviewer,
)

GROK_SEAT = "grok-4.7-cursor-fallback"
GROK_PIN = "grok-4.7-high"
GROK_SEATS = ("grok-4.7", GROK_SEAT)
RISKS = ("critical", "high", "medium", "low")
AUTHORS = ("claude-opus-5-5", "gpt-6.1-sol", "grok-4.7", "cursor:auto")
SOL_STATES = {"healthy": None, "unavailable": {"codex": "unhealthy"}}


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("risk", RISKS)
@pytest.mark.parametrize("author", ["claude-opus-5-5", "gpt-6.1-sol", "grok-4.7", "composer-2.5", "cursor:auto"])
@pytest.mark.parametrize("health", ["healthy", "native_dark", "both_dark"])
def test_denominator_admission_and_independence(profile, risk, author, health):
    snapshot = {"grok": "unhealthy"} if health != "healthy" else {}
    if health == "both_dark":
        snapshot["cursor"] = "unhealthy"
    inputs = ResolverInputs(author_model=author, risk=risk, review_profile=profile, routing_snapshot=snapshot)
    resolution = resolve_reviewer(inputs)
    assert resolution.selected is not None
    if author == "grok-4.7":
        assert resolution.selected.family not in {"xai", "moonshot"}
    if author == "cursor:auto":
        assert resolution.selected.family != "cursor"
        assert resolution.selected.route != "cursor"
    if author == "gpt-6.1-sol":
        assert resolution.selected.family != "openai"
    for name in GROK_SEATS:
        result = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        excluded = author == "grok-4.7" or (author in {"composer-2.5", "cursor:auto"} and name == GROK_SEAT) or health == "both_dark" or (
            name == "grok-4.7" and health == "native_dark"
        )
        assert result.status == ("excluded" if excluded else "eligible")
        if author == "grok-4.7":
            assert "same family as author" in result.reason or "union" in result.reason
        elif author == "cursor:auto":
            if health != "healthy":
                assert "unhealthy" in result.reason or "Cursor-as-reviewer" in result.reason
            elif name == GROK_SEAT:
                assert "Cursor-as-reviewer" in result.reason
            else:
                assert result.family == "xai"


@pytest.mark.parametrize("risk", RISKS)
@pytest.mark.parametrize("native_dark", [False, True])
def test_grok_transport_fallback_when_opus_unavailable(risk, native_dark):
    snapshot = {"claude": "unhealthy"}
    if native_dark:
        snapshot["grok"] = "unhealthy"
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk, routing_snapshot=snapshot))
    assert result.selected.name in ({GROK_SEAT} if native_dark else set(GROK_SEATS))
    assert evaluate_candidate(REVIEW_CANDIDATES["grok-4.7"], ResolverInputs(author_model="gpt-6.1-sol", risk=risk, routing_snapshot=snapshot)).status == ("excluded" if native_dark else "eligible")
    assert result.selected.family == "xai"


@pytest.mark.parametrize("risk", RISKS)
@pytest.mark.parametrize("subject", [{"subject_seats": ("grok",)}, {"subject_seats": ("cursor",)}, {"subject_families": ("xai",)}])
def test_both_grok_transports_refuse_subject_seats_and_families(risk, subject):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, **subject)
    result = resolve_reviewer(inputs)
    assert result.selected.family != "xai"
    for name in GROK_SEATS:
        candidate = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        assert candidate.status == "excluded" and "subject exclusion" in candidate.reason


def test_grok_never_reviews_its_own_adapter():
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="critical", owned_paths=("scripts/agent_runtime/adapters/grok_build.py",)))
    assert result.selected.name == "claude-opus-5-5"
    for name in GROK_SEATS:
        assert next(item for item in result.trace if item.name == name).status == "excluded"


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("risk", RISKS)
@pytest.mark.parametrize("name", GROK_SEATS)
def test_pins_and_custom_ladders_admit_grok(profile, risk, name):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, review_profile=profile)
    pinned = resolve_reviewer(replace(inputs, pinned_candidate=name, pressure_override_reason="admission probe"))
    assert pinned.selected.name == name
    custom = resolve_reviewer(inputs, ladder=((REVIEW_CANDIDATES[name],),))
    assert custom.selected.name == name


@pytest.mark.parametrize("native_dark", [False, True])
def test_closeout_cli_selects_grok_transport_with_a_durable_receipt(tmp_path, capsys, native_dark):
    snapshot = tmp_path / "routing.json"
    snapshot.write_text(json.dumps({"claude": "unhealthy", "grok": "unhealthy" if native_dark else "healthy"}))
    state = tmp_path / "state.json"
    code = closeout_cli.main(["--state-file", str(state), "resolve-reviewer", "--author-model", "gpt-6.1-sol", "--review-profile", "code", "--owned-path", "site/src/app.ts", "--risk", "critical", "--routing-snapshot-file", str(snapshot)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["selected"]["name"] in ({GROK_SEAT} if native_dark else set(GROK_SEATS))
    assert json.loads(state.read_text())["resolved_reviewer"]["selected"] == payload["selected"]


def _catalog():
    return copy.deepcopy(load_model_catalog())


@pytest.mark.parametrize("risk", RISKS)
def test_catalog_admits_both_transports_directly_after_opus(risk):
    catalog = load_model_catalog()
    ladder = [name for rung in catalog["review_ladders"][risk] for name in rung]
    opus = ladder.index("claude-opus-5-5")
    assert ladder[opus + 1:opus + 3] == list(GROK_SEATS)
    for name in GROK_SEATS:
        candidate = catalog["review_candidates"][name]
        assert candidate.get("last_resort", False) is False
        assert "critical_review" in catalog["models"][candidate["model_id"]]["roles"]
    validate_catalog(_catalog())


@pytest.mark.parametrize("model", ["composer-2.5", "kimi-code/k3", "gemini-3.8-flash-high"])
def test_catalog_refuses_a_cursor_review_pin_outside_policy(model):
    catalog = _catalog()
    catalog["review_scheduler"]["endpoints"]["cursor"]["models"].append(model)
    with pytest.raises(ModelCatalogError, match=r"review_scheduler\.endpoints\.cursor"):
        validate_catalog(catalog)


def test_catalog_requires_the_cursor_grok_high_effort_slug():
    catalog = _catalog()
    catalog["review_candidates"][GROK_SEAT]["invocation"] = ".venv/bin/python scripts/delegate.py dispatch --agent cursor --model grok-4.7"
    with pytest.raises(ModelCatalogError, match="runtime-attestable Cursor slug"):
        validate_catalog(catalog)


# --- runtime attestation on the verdict receipt ------------------------------


@pytest.fixture
def _publishing(synthetic_opsec, publisher_transport, monkeypatch):
    monkeypatch.setenv("GH_REPO", "unit/public")
    # Receipt identity tests leave path matching to the recorder's own tests.
    monkeypatch.setattr(recorder, "absolute_path_spans", lambda text: [])


def _pr_review_facts(families):
    """The recorder's complete-authorship entry point (#9739), for a PR these families authored."""

    def facts(repository, pr_number, *, head_sha, **_kwargs):
        return recorder.BranchReviewFacts(
            repository=repository,
            base_tip_sha="b" * 40,
            head_sha=head_sha,
            merge_base_sha="b" * 40,
            commits=tuple(recorder.CommitAttribution(None, family, "trailer-model") for family in sorted(families)),
            existing_families=frozenset(families),
            incoming_writer=None,
            incoming_family=None,
            changed_paths=(),
            owned_paths=(),
            subject_seats=frozenset(),
            subject_families=frozenset(),
            subject_evidence=(),
        )

    return facts


def _record(monkeypatch, tmp_path, *, resolved_model, families=frozenset({"anthropic"}), **extra):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    task = {
        "repository": "owner/repo",
        "worktree_branch": "claude/42",
        "worktree_base_sha": "a" * 40,
        "agent": "cursor",
        "model": resolved_model,
        "resolved_model": resolved_model,
        "resolved_model_known": True,
        "resolved_model_source": "cursor-stream-json",
        "started_at": "2026-10-02T12:00:00.000001+00:00",
        "status": "done",
        **extra,
    }
    (tasks / "review-one.json").write_text(json.dumps(task))
    (tasks / "review-one.result").write_text("VERDICT: APPROVE")
    comments: list[dict] = []

    def fake_json(args, *, input_text=None):
        from scripts.publish.github import Request

        if isinstance(args, Request) and args.verb == "issue-comment-json":
            item = {
                "id": 1,
                "body": args.fields["body"],
                "user": {"login": "fleet"},
                "author_association": "MEMBER",
                "created_at": "2026-10-02T13:00:00Z",
                "updated_at": "2026-10-02T13:00:00Z",
            }
            comments.append(item)
            return item
        if isinstance(args, Request) and args.verb == "read-comment":
            return comments[-1]
        if args[:3] == ["gh", "pr", "view"]:
            return {"number": 42, "headRefOid": "a" * 40, "headRefName": "claude/42", "state": "OPEN"}
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_json", fake_json)
    monkeypatch.setattr(recorder, "pr_review_facts", _pr_review_facts(families))
    monkeypatch.setattr(recorder.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(recorder.GitHubAdapter, "comments", lambda self, repository, number: list(comments))
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: None)
    return recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks"), comments


@pytest.mark.usefixtures("_publishing")
def test_runtime_reported_grok_high_receipt_records_the_concrete_model_and_xai(monkeypatch, tmp_path):
    result, comments = _record(monkeypatch, tmp_path, resolved_model="Grok 4.7 256K High")
    assert result["comment"] == "posted"
    assert "Reviewer model: grok-4.7" in comments[0]["body"]
    assert "model=grok-4.7 family=xai" in comments[0]["body"]


@pytest.mark.usefixtures("_publishing")
@pytest.mark.parametrize(
    "resolved_model",
    ["Grok 4.7 256K High Fast", "Grok 4.7 256K Medium", "Grok 4.7 High", "Grok 4.6", "GroK 4.7 256K High"],
)
def test_a_grok_receipt_that_is_not_the_pinned_high_variant_is_refused(monkeypatch, tmp_path, resolved_model):
    with pytest.raises(recorder.RecordError, match="reviewer model unknown"):
        _record(monkeypatch, tmp_path, resolved_model=resolved_model)


@pytest.mark.usefixtures("_publishing")
def test_a_grok_verdict_on_a_grok_authored_change_is_refused(monkeypatch, tmp_path):
    with pytest.raises(recorder.RecordError, match="reviewer family equals an author family"):
        _record(monkeypatch, tmp_path, resolved_model="Grok 4.7 256K High", families=frozenset({"xai"}))


# --- second review round (#9488): fail closed on every ineligible identity -----


@pytest.mark.usefixtures("_publishing")
@pytest.mark.parametrize(
    "resolved_model",
    [
        "grok-4.7-high-fast",  # the reviewer's reproduction: attested, but not the pinned variant
        "grok-4.6",
        "grok-4.5",
        "xai",
        "grok-4.7",  # a bare slug names no variant; Cursor runs it as High Fast
        "grok-4.7-high",  # the dispatch slug is not the runtime's report
        "composer-2.5",
        "Composer 2.5",
        "claude-opus-5-5",  # Cursor-routed Claude is not a pinned formal seat
    ],
)
def test_a_runtime_attested_cursor_identity_the_resolver_never_selects_is_refused(
    monkeypatch, tmp_path, resolved_model
):
    with pytest.raises(recorder.RecordError, match="reviewer model unknown"):
        _record(monkeypatch, tmp_path, resolved_model=resolved_model)


@pytest.mark.usefixtures("_publishing")
@pytest.mark.parametrize(
    "agent,model,extra",
    [
        # The reviewer's reproduction: main refuses this native display name.
        ("grok", "Grok 4.7 256K High", {"resolved_model_known": False, "resolved_model_source": "unattested-harness"}),
        ("grok", "grok-4.7", {}),
        ("grok", "grok-4.7-high", {}),
        ("claude", "grok-4.7", {}),
        ("kimi", "kimi-code/k3", {}),
        ("kimi", "composer-2.5", {}),
    ],
)
def test_a_grok_or_kimi_verdict_through_any_other_harness_is_refused(monkeypatch, tmp_path, agent, model, extra):
    with pytest.raises(recorder.RecordError, match=r"reviewer model unknown|native Grok reviewer model unattested"):
        _record(monkeypatch, tmp_path, resolved_model=model, agent=agent, **extra)


@pytest.mark.usefixtures("_publishing")
@pytest.mark.parametrize("model,family", [("gpt-6.1-sol", "openai"), ("claude-opus-5-5", "anthropic")])
def test_native_primary_reviewers_are_still_recorded(monkeypatch, tmp_path, model, family):
    agent = "codex" if family == "openai" else "claude"
    result, comments = _record(monkeypatch, tmp_path, resolved_model=model, agent=agent, families=frozenset({"xai"}))
    assert result["comment"] == "posted"
    assert f"model={model} family={family}" in comments[0]["body"]


def _all_catalog_roles() -> list[str]:
    return sorted({role for model in load_model_catalog()["models"].values() for role in model.get("roles", [])})


@pytest.mark.parametrize("role", _all_catalog_roles())
def test_requested_roles_preserve_author_independence_at_critical(role):
    for author in ("grok-4.7", "cursor:auto"):
        for name in GROK_SEATS:
            result = resolve_reviewer(ResolverInputs(author_model=author, risk="critical", requested_role=role, pinned_candidate=name, pressure_override_reason="self-review probe"))
            excluded = author == "grok-4.7" or name == GROK_SEAT or role not in REVIEW_CANDIDATES[name].model_roles
            if excluded:
                assert result.selected is None
                assert next(entry for entry in result.trace if entry.name == name).status == "excluded"
            else:
                assert result.selected.name == "grok-4.7"
                assert result.selected.family == "xai"


@pytest.mark.parametrize("role", _all_catalog_roles())
def test_a_requested_role_only_narrows_the_profile_risk_qualified_set(role):
    """Whatever a role selects must be eligible with no role requested (never widened)."""
    for author in AUTHORS:
        for profile in ("code", "infra"):
            for risk in RISKS:
                for sol in SOL_STATES.values():
                    base = ResolverInputs(
                        author_model=author, review_profile=profile, domain=profile, risk=risk, routing_snapshot=sol
                    )
                    selected = resolve_reviewer(replace(base, requested_role=role)).selected
                    if selected is None:
                        continue
                    assert role in REVIEW_CANDIDATES[selected.name].model_roles
                    unnarrowed = evaluate_candidate(REVIEW_CANDIDATES[selected.name], base)
                    assert unnarrowed.status == "eligible", (author, profile, risk, role, selected.name)


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_grok_review_role_is_admitted_at_critical(profile):
    inputs = ResolverInputs(
        author_model="claude-opus-5-5",
        review_profile=profile,
        domain=profile,
        risk="critical",
        requested_role="strong_review",
    )
    result = evaluate_candidate(REVIEW_CANDIDATES[GROK_SEAT], inputs)
    assert result.status == "eligible"
    assert result.reason is None
