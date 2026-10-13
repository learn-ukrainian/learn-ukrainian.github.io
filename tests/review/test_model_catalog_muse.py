"""A held Muse candidate changes no automatic route (#10511)."""

import argparse
import json
from pathlib import Path

import pytest

from scripts import delegate
from scripts.agent_runtime.registry import AGENTS
from scripts.review.model_catalog import load_model_catalog
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
    assert len(matrix) == 1480
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
        assert all(candidate.concrete_model != MODEL for candidate in result.trace), row


@pytest.mark.parametrize(
    "repo,language,reason",
    [
        ("public-monorepo", True, "UKRAINIAN_MODEL_REFUSED"),
        ("private-infra", False, "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"),
        ("private-product", False, "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"),
    ],
)
def test_candidate_exclusion_at_dispatch(repo, language, reason):
    args = argparse.Namespace(agent="muse", model=MODEL, mode="read-only", language_lane=language, task_id="muse-test")
    refusal, target = delegate._admit_dispatch_target(args, agent="muse", trees=(), repo_role=repo)
    assert target is None and reason in refusal
