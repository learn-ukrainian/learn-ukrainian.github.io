"""Grok through the Cursor harness as an attested formal code/infra reviewer (#9488).

Operator decision 2026-10-02 (recorded on #9488): the latest Grok that Cursor
offers, pinned at high effort and attested by the runtime, is a formal code and
infra reviewer. Sol stays the first seat; the Cursor seat is the Sol-spared
alternative. Native Grok still never judges, a Grok-authored change is never
reviewed by Grok, Composer and Kimi stay one family, and critical risk follows
the catalogue's own role suitability (Grok has no ``critical_review`` role).
"""

from __future__ import annotations

import copy
import json

import pytest

from scripts.review import closeout_cli
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, validate_catalog
from scripts.review.reviewer_resolver import (
    REVIEW_CANDIDATES,
    REVIEW_LADDERS,
    ResolverInputs,
    evaluate_candidate,
    resolve_reviewer,
)

GROK_SEAT = "grok-4.7-cursor-fallback"
GROK_PIN = "grok-4.7-high"
SOL_UNAVAILABLE = {"codex": "unhealthy"}
AUTHORS = ("claude-opus-5-5", "claude-sonnet-5-5", "gpt-6.1-sol", "cursor:grok-4.7")
RISKS = ("critical", "high", "medium", "low")
SOL_STATES = {"healthy": None, "unavailable": SOL_UNAVAILABLE}


def _expected(author: str, risk: str, sol: str) -> str | None:
    """The denominator: one stated outcome per author x risk x Sol row."""
    if author.startswith("claude-"):
        if sol == "healthy":
            return "openai_frontier"
        # Sol unavailable: every Anthropic seat is same family. Grok has no
        # critical_review role, so critical stays Sol/Opus-only and waits.
        return None if risk == "critical" else GROK_SEAT
    if author == "gpt-6.1-sol":
        # Sol is advisory-only for an OpenAI author; the Anthropic primaries
        # keep the seat and the Cursor Grok seat stays a last resort.
        return "claude-opus-5-5" if risk == "critical" else "claude-sonnet-5-5"
    return "grok-author"


@pytest.mark.parametrize("sol", sorted(SOL_STATES))
@pytest.mark.parametrize("risk", RISKS)
@pytest.mark.parametrize("author", AUTHORS)
def test_denominator_selects_an_attested_seat_or_states_the_policy_reason(author, risk, sol):
    resolution = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, routing_snapshot=SOL_STATES[sol]))
    expected = _expected(author, risk, sol)
    selected = resolution.selected
    trace = {entry.name: entry for entry in resolution.trace}
    if expected == "grok-author":
        # A Grok-authored change is never reviewed by Grok, through any harness.
        assert selected is not None
        assert selected.family in {"openai", "anthropic"}
        assert selected.transport in {"native_codex", "native_claude"}
        assert trace[GROK_SEAT].status == "excluded"
        assert (
            trace[GROK_SEAT].reason == "same family as author (xai) — cross-family review requires a different family"
        )
        return
    if expected is None:
        assert selected is None
        assert trace[GROK_SEAT].status == "excluded"
        assert trace[GROK_SEAT].reason == "missing required review role suitability: code/critical catalog suitability"
        assert trace["openai_frontier"].reason == "lane health is unhealthy — route is operationally unavailable"
        return
    assert selected is not None and selected.name == expected
    if expected == GROK_SEAT:
        assert selected.concrete_model == "grok-4.7"
        assert selected.family == "xai"
        assert selected.route == "cursor"
        assert selected.transport == "cursor"
        assert selected.invocation.endswith(f"--agent cursor --model {GROK_PIN}")
        assert selected.health is None
        assert trace["openai_frontier"].reason == "lane health is unhealthy — route is operationally unavailable"
        assert "last resort selected grok-4.7-cursor-fallback" in (resolution.substitution_note or "")
    else:
        assert trace[GROK_SEAT].status != "selected"


def test_sol_healthy_stays_first_even_where_grok_has_the_closer_role_fit():
    """At high risk Grok's strong_review outranks Sol's standard_review on fit alone."""
    resolution = resolve_reviewer(ResolverInputs(author_model="claude-opus-5-5", risk="high"))
    trace = {entry.name: entry for entry in resolution.trace}
    assert trace[GROK_SEAT].status == "eligible"
    assert trace[GROK_SEAT].suitability_rank < trace["openai_frontier"].suitability_rank
    assert resolution.selected.name == "openai_frontier"


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("risk", ["high", "medium", "low"])
def test_cursor_grok_seat_reviews_code_and_infra_for_an_anthropic_author(profile, risk):
    inputs = ResolverInputs(author_model="claude-opus-5-5", review_profile=profile, domain=profile, risk=risk)
    result = evaluate_candidate(REVIEW_CANDIDATES[GROK_SEAT], inputs)
    assert result.status == "eligible"
    assert result.family == "xai"


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_cursor_grok_seat_is_not_qualified_at_critical(profile):
    inputs = ResolverInputs(author_model="claude-opus-5-5", review_profile=profile, domain=profile, risk="critical")
    result = evaluate_candidate(REVIEW_CANDIDATES[GROK_SEAT], inputs)
    assert result.status == "excluded"
    assert result.reason == f"missing required review role suitability: {profile}/critical catalog suitability"


@pytest.mark.parametrize("risk", RISKS)
def test_native_grok_still_never_judges(risk):
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk=risk)
    result = evaluate_candidate(REVIEW_CANDIDATES["grok-4.7"], inputs)
    assert result.status == "excluded"
    assert "native Grok never judges" in result.reason


@pytest.mark.parametrize("author", ["composer-2.5", "cursor:auto", "kimi-code/k3"])
def test_cursor_grok_seat_refuses_xai_and_moonshot_union_authors(author):
    result = evaluate_candidate(REVIEW_CANDIDATES[GROK_SEAT], ResolverInputs(author_model=author, risk="medium"))
    assert result.status == "excluded"


def test_composer_and_cursor_routed_claude_stay_unattested_formal_identities():
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="high")
    for name in ("composer-2.5", "claude-opus-5-5-cursor-fallback"):
        result = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        assert result.status == "excluded"
        assert "is not pinned for model" in result.reason


def test_grok_seat_never_reviews_its_own_adapter():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            risk="high",
            routing_snapshot=SOL_UNAVAILABLE,
            owned_paths=("scripts/agent_runtime/adapters/grok_build.py",),
        )
    )
    assert resolution.selected is None
    grok = next(entry for entry in resolution.trace if entry.name == GROK_SEAT)
    assert grok.status == "excluded" and "subject seat grok" in grok.reason


def test_closeout_cli_selects_the_attested_cursor_grok_seat_when_sol_is_unavailable(tmp_path, capsys):
    snapshot = tmp_path / "routing.json"
    snapshot.write_text(json.dumps(SOL_UNAVAILABLE), encoding="utf-8")
    state = tmp_path / "state.json"
    code = closeout_cli.main(
        [
            "--state-file",
            str(state),
            "resolve-reviewer",
            "--author-model",
            "claude-sonnet-5-5",
            "--review-profile",
            "code",
            "--risk",
            "high",
            "--routing-snapshot-file",
            str(snapshot),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["selected"]["name"] == GROK_SEAT
    assert payload["selected"]["family"] == "xai"
    assert payload["selected"]["invocation"].endswith(f"--model {GROK_PIN}")
    assert json.loads(state.read_text())["resolved_reviewer"]["selected"]["name"] == GROK_SEAT


# --- catalogue lints ---------------------------------------------------------


def _catalog() -> dict:
    return copy.deepcopy(load_model_catalog())


def test_catalog_pins_the_cursor_review_endpoint_to_grok_only():
    endpoint = load_model_catalog()["review_scheduler"]["endpoints"]["cursor"]
    assert endpoint["formal_review_eligible"] is True
    assert endpoint["models"] == ["grok-4.7"]


@pytest.mark.parametrize("model", ["composer-2.5", "kimi-code/k3", "gemini-3.8-flash-high"])
def test_catalog_refuses_a_cursor_review_pin_outside_policy(model):
    catalog = _catalog()
    catalog["review_scheduler"]["endpoints"]["cursor"]["models"].append(model)
    with pytest.raises(ModelCatalogError, match=r"review_scheduler\.endpoints\.cursor"):
        validate_catalog(catalog)


def test_catalog_refuses_a_formal_cursor_endpoint_without_a_pin():
    catalog = _catalog()
    catalog["review_scheduler"]["endpoints"]["cursor"]["models"] = []
    with pytest.raises(ModelCatalogError, match="needs an explicit models pin"):
        validate_catalog(catalog)


@pytest.mark.parametrize("risk", RISKS)
def test_catalog_still_refuses_native_grok_in_any_ladder(risk):
    catalog = _catalog()
    catalog["review_ladders"][risk].append(["grok-4.7"])
    with pytest.raises(ModelCatalogError, match="native Grok never judges"):
        validate_catalog(catalog)


def test_catalog_requires_the_cursor_grok_seat_to_stay_a_sol_spared_last_resort():
    catalog = _catalog()
    catalog["review_candidates"][GROK_SEAT]["last_resort"] = False
    with pytest.raises(ModelCatalogError, match="last_resort"):
        validate_catalog(catalog)


def test_catalog_requires_the_cursor_grok_seat_to_pin_a_high_effort_cursor_slug():
    catalog = _catalog()
    catalog["review_candidates"][GROK_SEAT]["invocation"] = (
        ".venv/bin/python scripts/delegate.py dispatch --agent cursor --model grok-4.7"
    )
    with pytest.raises(ModelCatalogError, match="runtime-attestable Cursor slug"):
        validate_catalog(catalog)


def test_every_ladder_lists_the_cursor_grok_seat_last():
    for risk in RISKS:
        assert REVIEW_LADDERS[risk][-1] == (REVIEW_CANDIDATES[GROK_SEAT],)


# --- runtime attestation on the verdict receipt ------------------------------


@pytest.fixture
def _publishing(synthetic_opsec, publisher_transport, monkeypatch):
    monkeypatch.setenv("GH_REPO", "unit/public")


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
    monkeypatch.setattr(recorder, "author_families", lambda repository, number, task_root: set(families))
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
