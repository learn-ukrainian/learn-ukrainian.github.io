"""Ukrainian-content reviewer routing and closeout entry-point coverage."""

from __future__ import annotations

import json

import pytest

from scripts.review.closeout_cli import main
from scripts.review.reviewer_resolver import (
    GLM,
    GROK_4_7,
    REVIEW_CANDIDATES,
    ResolverInputs,
    evaluate_candidate,
    is_ukrainian_content_change,
    resolve_reviewer,
)


@pytest.mark.parametrize(
    "path",
    [
        "curriculum/a.mdx",
        "scripts/curriculum/build.py",
        "scripts/data/stress_overrides.yaml",
        "scripts/verification/stress_check.py",
        "scripts/pipeline/stress_annotator.py",
        "scripts/lexicon/store.py",
        "site/src/lib/lexicon/entry.ts",
        "scripts/review/prompts/lesson.md",
        "scripts/build/phases/lesson.py",
        "scripts/build/fresh/prompt_writer.py",
        "docs/epics/fresh-build-plan.md",
        "schemas/activities-v1.json",
    ],
)
def test_each_ukrainian_content_path_is_classified(path):
    assert is_ukrainian_content_change(ResolverInputs(author_model="codex", changed_paths=(path,)))


def test_unrelated_paths_do_not_match_content_patterns():
    assert not is_ukrainian_content_change(
        ResolverInputs(author_model="codex", changed_paths=("scripts/review/reviewer_resolver.py", "docs/infra.md"))
    )


def test_owned_path_classifies_ukrainian_content_without_changed_paths(tmp_path, capsys):
    inputs = ResolverInputs(author_model="codex", owned_paths=("curriculum/a.mdx",))
    assert is_ukrainian_content_change(inputs)
    result = evaluate_candidate(GROK_4_7, inputs)
    assert result.status == "excluded"
    assert "Ukrainian-content language-lanes exclusion" in result.reason

    state_file = tmp_path / "review.json"
    assert (
        main(
            [
                "--state-file",
                str(state_file),
                "resolve-reviewer",
                "--author-model",
                "codex",
                "--owned-path",
                "curriculum/a.mdx",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert any(
        item["name"] == GROK_4_7.name and "Ukrainian-content language-lanes exclusion" in item["reason"]
        for item in payload["trace"]
    )


@pytest.mark.parametrize(
    "inputs",
    [
        ResolverInputs(author_model="codex", language_lane=True),
        ResolverInputs(author_model="codex", review_profile="ukrainian"),
    ],
)
def test_explicit_ukrainian_signals_are_classified(inputs):
    assert is_ukrainian_content_change(inputs)


@pytest.mark.parametrize("author,expected_family", [("codex", "anthropic"), ("claude", "openai")])
def test_content_code_review_uses_only_cross_family_claude_or_gpt(author, expected_family):
    resolution = resolve_reviewer(ResolverInputs(author_model=author, changed_paths=("scripts/lexicon/word_store.py",)))
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family == expected_family
    assert all(item.family in {"anthropic", "openai"} for item in resolution.advisory)
    for item in resolution.trace:
        if item.family not in {"anthropic", "openai", "google"}:
            assert item.status == "excluded"
            assert "Ukrainian-content language-lanes exclusion" in item.reason


def test_non_language_candidates_and_explicit_pin_are_excluded():
    inputs = ResolverInputs(author_model="codex", changed_paths=("curriculum/A1/lesson.mdx",))
    # Kimi is no longer a review candidate at all (web, UI and backend coding only).
    assert "kimi-k3" not in REVIEW_CANDIDATES
    for candidate in (
        GROK_4_7,
        GLM,
        REVIEW_CANDIDATES["composer-2.5"],
        REVIEW_CANDIDATES["deepseek-v4.1-flash"],
    ):
        result = evaluate_candidate(candidate, inputs)
        assert result.status == "excluded", candidate.name
        assert "Ukrainian-content language-lanes exclusion" in result.reason
    pinned = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            changed_paths=("curriculum/A1/lesson.mdx",),
            pinned_candidate="grok-4.7",
            pressure_override_reason="test pin",
        )
    )
    assert pinned.selected is None
    assert pinned.fail_closed_reason


def test_pure_infra_change_can_still_select_grok():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            review_profile="infra",
            domain="infra",
            changed_paths=("scripts/orchestration/worker.py",),
            routing_snapshot={"claude": "unhealthy", "codex": "unhealthy"},
        ),
    )
    assert resolution.selected is not None
    assert resolution.selected.name == "grok-4.7"


def test_closeout_uses_target_changed_paths_and_language_flag(tmp_path, capsys):
    state_file = tmp_path / "review.json"
    state_file.write_text(
        json.dumps(
            {
                "target": {
                    "mode": "commit",
                    "base_sha": "a" * 40,
                    "head_sha": "b" * 40,
                    "changed_paths": ["scripts/lexicon/word_store.py"],
                    "non_test_loc": 5,
                    "clean_tree": True,
                    "description": "test commit",
                }
            }
        ),
        encoding="utf-8",
    )
    assert main(["--state-file", str(state_file), "resolve-reviewer", "--author-model", "codex"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"]["family"] == "anthropic"
    assert any("Ukrainian-content language-lanes exclusion" in (item["reason"] or "") for item in payload["trace"])

    state_file.write_text("{}", encoding="utf-8")
    assert (
        main(["--state-file", str(state_file), "resolve-reviewer", "--author-model", "codex", "--language-lane"]) == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"]["family"] == "anthropic"


def test_ukrainian_semantic_profile_still_fails_closed():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", review_profile="ukrainian"))
    assert resolution.selected is None
    assert resolution.trace == ()
    assert "unsupported local-code-review profile" in resolution.fail_closed_reason
