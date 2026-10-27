"""Review metadata loss and subject self-review must fail before a paid launch."""

import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.review import record_cf_verdict as cf
from scripts.review.subject_seat import classify_owned_path


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    # The metadata fixture is a sibling repository with a verifiable canonical origin.
    subprocess.run(["git", "init", "-q", "-b", "fixture", str(tmp_path)], check=True, timeout=30)
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin",
                    "https://github.com/example/public.git"], check=True, timeout=30)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/review", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(record, prompt))
    monkeypatch.setattr(worker, "start", start)

    def invoke(*flags, agent="sol", model="gpt-6.1-sol", expected=0):
        if "workspace-write" in flags and "--owned-path" not in flags:
            flags = (*flags, "--owned-path", "docs/review.md")
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
    ("grok", "grok-4.7-high", "--subject-seat", "grok-build"),
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


@pytest.mark.parametrize("flags", [(), ("--review-profile", "code"), ("--subject-seat", "grok"),
                                  ("--subject-family", "xai")])
def test_ambiguous_provider_refused_for_review_only(dispatch, capsys, flags):
    dispatch("--owned-path", "scripts/dispatcher/providers/hermes.py",
             *flags, expected=2 if flags else 0)
    if flags:
        assert "ambiguous review subject path" in capsys.readouterr().err


@pytest.mark.parametrize("provider,seat", [("claude", "claude"), ("opencode", "deepseek")])
def test_inferred_subject_seat_is_persisted_for_publication(dispatch, provider, seat):
    record = dispatch("--owned-path", f"scripts/dispatcher/providers/{provider}.py")
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
