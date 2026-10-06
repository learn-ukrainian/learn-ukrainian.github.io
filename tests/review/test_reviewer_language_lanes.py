"""Ukrainian-content reviewer routing and closeout entry-point coverage."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.common.git_context import sanitized_git_env
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
    assert all(
        item["family"] in {"openai", "anthropic", "google"} or item["status"] == "excluded" for item in payload["trace"]
    )
    # #9769: both Grok transports stay excluded from Ukrainian content.
    xai = [item for item in payload["trace"] if item["family"] == "xai"]
    assert [item["name"] for item in xai] == ["grok-4.7", "grok-4.7-cursor-fallback"]
    assert xai[0]["status"] == "excluded"
    assert "Ukrainian-content language-lanes exclusion" in xai[0]["reason"]
    composer = next(item for item in payload["trace"] if item["name"] == "composer-2.5")
    assert composer["status"] == "excluded"
    assert composer["reason"] == (
        "Ukrainian-content language-lanes exclusion: reviewer model family must be Claude, GPT or Gemini"
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
    # DeepSeek is excluded from every review, not just language review.
    assert "deepseek-v4.1-flash" not in REVIEW_CANDIDATES
    for candidate in (
        GROK_4_7,
        GLM,
        REVIEW_CANDIDATES["composer-2.5"],
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
    deepseek_pin = resolve_reviewer(
        ResolverInputs(
            author_model="codex", pinned_candidate="deepseek-v4.1-flash", pressure_override_reason="test pin"
        )
    )
    assert deepseek_pin.selected is None
    assert "unknown explicit reviewer pin" in deepseek_pin.fail_closed_reason


def test_pure_infra_change_falls_to_grok_when_primary_lanes_are_unhealthy():
    """#9769: both admitted transports cover non-language infra review."""
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
    assert resolution.selected.concrete_model == "grok-4.7"
    assert resolution.selected.transport in {"native_grok", "cursor"}
    assert [item.name for item in resolution.trace if item.family == "xai"] == ["grok-4.7", "grok-4.7-cursor-fallback"]
    dark = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            review_profile="infra",
            domain="infra",
            changed_paths=("scripts/orchestration/worker.py",),
            routing_snapshot={"claude": "unhealthy", "codex": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"},
        ),
    )
    assert dark.selected is None


def test_closeout_uses_target_changed_paths_and_language_flag(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True, env=sanitized_git_env(), timeout=30).strip()

    git("init", "-q", "-b", "trunk")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    source = repo / "scripts/lexicon/word_store.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "base")
    base_sha = git("rev-parse", "HEAD")
    source.write_text("value = 2\n", encoding="utf-8")
    git("add", ".")
    # A committed target is attributed by its X-Agent trailer (#9739): a Codex author, as --author-model says.
    git("commit", "-qm", "change word store\n\nX-Agent: codex/gpt-6.1-sol")
    head_sha = git("rev-parse", "HEAD")
    state_file = tmp_path / "review.json"
    assert (
        main(
            [
                "--state-file",
                str(state_file),
                "target",
                "--mode",
                "commit",
                "--commit",
                head_sha,
                "--repo-root",
                str(repo),
            ]
        )
        == 0
    )
    capsys.readouterr()
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["target"]["base_sha"] == base_sha
    assert state["target"]["head_sha"] == head_sha
    assert state["target"]["changed_paths"] == ["scripts/lexicon/word_store.py"]
    assert state["target_args"]["repo_root"] == str(repo.resolve())
    # The fixture repository has no GitHub origin, so name the repository its task records would carry.
    repository = ["--repository", "learn-ukrainian/learn-ukrainian.github.io"]
    assert main(["--state-file", str(state_file), "resolve-reviewer", "--author-model", "codex", *repository]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"]["family"] == "anthropic"
    assert any("Ukrainian-content language-lanes exclusion" in (item["reason"] or "") for item in payload["trace"])

    state["target_args"].pop("repo_root")
    state_file.write_text(json.dumps(state), encoding="utf-8")
    assert main(["--state-file", str(state_file), "resolve-reviewer", "--author-model", "codex"]) == 1
    assert json.loads(capsys.readouterr().err) == {"error": "target_repo_root_missing"}

    state_file.write_text("{}", encoding="utf-8")
    assert (
        main(
            [
                "--state-file",
                str(state_file),
                "resolve-reviewer",
                "--author-model",
                "codex",
                "--language-lane",
                "--owned-path",
                "curriculum/A1/lesson.mdx",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"]["family"] == "anthropic"


def test_ukrainian_semantic_profile_still_fails_closed():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", review_profile="ukrainian"))
    assert resolution.selected is None
    assert resolution.trace == ()
    assert "unsupported local-code-review profile" in resolution.fail_closed_reason


@pytest.mark.parametrize("author,expected", [("gpt-6.1-sol", "claude-opus-5-5"), ("claude-opus-5-5", "gpt-6.1-sol")])
def test_critical_ukrainian_code_review_prefers_opus_and_sol(author, expected):
    resolution = resolve_reviewer(ResolverInputs(author_model=author, risk="critical", language_lane=True))
    assert resolution.selected.concrete_model == expected
    assert resolution.selected.family in {"anthropic", "openai"}
