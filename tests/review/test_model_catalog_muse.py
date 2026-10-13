"""A held Muse candidate changes no automatic route (#10511)."""

import argparse
import json
from pathlib import Path

import pytest

from scripts import delegate
from scripts.agent_runtime.registry import AGENTS
from scripts.review.model_catalog import load_model_catalog, resolve_role
from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

MODEL = "muse-wonder-1.0"
ROOT = Path(__file__).resolve().parents[2]


def test_candidate_is_metadata_only():
    catalog = load_model_catalog()
    entry = catalog["models"][MODEL]
    assert entry["family"] == "meta"
    assert entry["lifecycle"] == "hold"
    assert entry["roles"] == ["candidate_author", "candidate_reviewer"]
    assert entry["context_window"] == 1000000
    assert "https://dev.meta.ai/models/muse-wonder" in entry["sources"]
    assert AGENTS["muse"]["default_model"] is None
    assert not AGENTS["muse"]["capabilities"]
    assert all(row["default_model"] != MODEL for row in AGENTS.values())
    for key, value in catalog.items():
        if key != "models":
            assert MODEL not in json.dumps(value), key
    assert "muse" not in (ROOT / "scripts/config/agent_fallback_substitutions.yaml").read_text()


def test_full_frozen_reviewer_matrix_never_selects_muse():
    matrix = json.loads((ROOT / "tests/fixtures/routing_baseline/inputs.json").read_text())["reviewer"]
    assert len(matrix) == 1504
    for row in matrix:
        typed = dict(row)
        for key in ("required_capabilities", "subject_seats", "subject_families", "author_families"):
            if key in typed:
                typed[key] = frozenset(typed[key])
        if "owned_paths" in typed:
            typed["owned_paths"] = tuple(typed["owned_paths"])
        result = resolve_reviewer(ResolverInputs(**typed))
        if result.selected is not None:
            assert result.selected.concrete_model != MODEL, row
            assert result.selected.route != "muse", row
        for candidate in (*result.trace, *result.advisory, *result.quorum):
            assert candidate.concrete_model != MODEL, row
            assert candidate.route != "muse", row


def test_every_generated_role_case_excludes_muse():
    matrix = json.loads((ROOT / "tests/fixtures/routing_baseline/inputs.json").read_text())["roles"]
    assert len(matrix) == 870
    for row in matrix:
        if row["health"] and "stale" in row["health"].values():
            with pytest.raises(ValueError, match="unsupported health status 'stale'"):
                resolve_role(**row)
            continue
        result = resolve_role(**row)
        for candidate in result.candidates:
            assert candidate.model_id != MODEL, row
            assert candidate.transport != "muse", row


@pytest.mark.parametrize(
    "repo,language,seat,model,reason",
    [
        ("public-monorepo", True, "muse", MODEL, "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "muse", "gpt-6.1-sol", "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "muse", "claude-opus-5-5", "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "muse", None, "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "muse", "", "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "muse", " \t", "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "codex", MODEL, "UKRAINIAN_MODEL_REFUSED"),
        ("public-monorepo", True, "claude", "meta/muse-wonder-1.0", "UKRAINIAN_MODEL_REFUSED"),
        ("private-infra", False, "muse", MODEL, "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"),
        ("private-product", False, "muse", MODEL, "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"),
        ("public-monorepo", False, "muse", MODEL, "MUSE_GUARD_PARITY_UNPROVEN"),
    ],
)
def test_candidate_exclusion_at_dispatch(repo, language, seat, model, reason):
    args = argparse.Namespace(agent=seat, model=model, mode="read-only", language_lane=language, task_id="muse-test")
    refusal, target = delegate._admit_dispatch_target(args, agent=seat, trees=(), repo_role=repo)
    assert target is None and reason in refusal


@pytest.mark.parametrize("model", [None, "", " ", "\t\n"])
def test_candidate_requires_nonblank_model(model):
    args = argparse.Namespace(agent="muse", model=model, mode="read-only", task_id="muse-test")
    refusal, target = delegate._admit_dispatch_target(args, agent="muse", trees=(), repo_role="public-monorepo")
    assert target is None and "MUSE_MODEL_REFUSED" in refusal


@pytest.mark.parametrize("status", ["cool", "warm"])
def test_budget_hint_excludes_held_seat(status):
    assert delegate._budget_cooler_lanes(
        {"codex": {"status": "hot"}, "muse": {"status": status}, "claude": {"status": status}}, exclude="codex"
    ) == ["claude"]


@pytest.mark.parametrize("language,reason", [(False, "MUSE_GUARD_PARITY_UNPROVEN"), (True, "UKRAINIAN_MODEL_REFUSED")])
def test_resolved_muse_dispatch_remains_held(language, reason):
    args = argparse.Namespace(
        agent="codex", model="gpt-6.1-sol", language_lane=language, mode="read-only", task_id="muse-test"
    )
    refusal, target = delegate._admit_dispatch_target(
        args,
        agent="codex",
        trees=(),
        repo_role="public-monorepo",
        route=lambda _request: ("muse", "gpt-6.1-sol", "synthetic held target"),
    )
    assert target is None and reason in refusal
