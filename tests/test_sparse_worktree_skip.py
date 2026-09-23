"""Sparse worktrees skip tests that need an absent tree; CI does not."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


def _conftest() -> ModuleType:
    for module in sys.modules.values():
        file = getattr(module, "__file__", None)
        if isinstance(file, str) and file.endswith("tests/conftest.py"):
            return module
    raise AssertionError("tests/conftest.py was not loaded")


def test_sparse_off_never_skips_even_when_tree_is_absent() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/projects/open_model_data/test_mine.py",
        sparse_enabled=False,
        missing_trees=frozenset({"data/projects", "data/lexicon"}),
        item_name="test_mine",
    )
    assert reason is None
    lexicon_reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_ohoiko_source_inventory_scope.py",
        sparse_enabled=False,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_ohoiko_abetka_inventory_covers_all_committed_key_words",
    )
    assert lexicon_reason is None


def test_sparse_on_skips_open_model_data_when_projects_absent() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/projects/open_model_data/test_mine.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/projects"}),
        item_name="test_mine",
    )
    assert reason is not None
    assert "--sparse-include data/projects" in reason


def test_sparse_on_skips_lexicon_readers_when_lexicon_absent() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/lexicon/test_manifest.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_manifest",
    )
    assert reason is not None
    assert "--sparse-include data/lexicon" in reason

    live = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_generate_practice_deck.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_live_paronym_pairs_yaml_is_valid_and_has_promoted_candidates",
    )
    assert live is not None
    assert "--sparse-include data/lexicon" in live

    unrelated = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_generate_practice_deck.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_paronym_empty_file_emits_empty_fail_closed",
    )
    assert unrelated is None


def test_sparse_on_skips_top_level_open_model_readers() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_open_model_foundry_cli.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/projects"}),
        item_name="test_example_runs_end_to_end_without_model_or_private_database",
    )
    assert reason is not None
    assert "--sparse-include data/projects" in reason

    untouched = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_open_model_data_timeouts.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/projects"}),
        item_name="test_gemma_hardware_probe_require_hf_auth_timeout",
    )
    assert untouched is None


def test_sparse_on_skips_source_inventory_readers() -> None:
    conftest = _conftest()
    decisions = conftest.sparse_missing_tree_skip_reason(
        "tests/test_source_inventory_review_decisions.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_committed_first_source_inventory_review_batch_validates",
    )
    assert decisions is not None
    assert "--sparse-include data/lexicon" in decisions

    sample = conftest.sparse_missing_tree_skip_reason(
        "tests/test_source_inventory_intake.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_pos_balanced_sample_has_required_pos_buckets_and_source_fields",
    )
    assert sample is not None

    candidates = conftest.sparse_missing_tree_skip_reason(
        "tests/test_source_inventory_review_candidates.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_review_candidates_use_committed_inventories_and_keep_provenance",
    )
    assert candidates is not None

    defaults = conftest.sparse_missing_tree_skip_reason(
        "tests/test_source_inventory_review_candidates.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_review_workflow_defaults_outside_repo",
    )
    assert defaults is not None


def test_sparse_marker_skips_only_the_marked_test() -> None:
    conftest = _conftest()
    marked = conftest.sparse_missing_tree_skip_reason(
        "tests/test_sparse_worktree_skip.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_sparse_marker_example",
    )
    assert marked is not None
    unmarked = conftest.sparse_missing_tree_skip_reason(
        "tests/test_sparse_worktree_skip.py",
        sparse_enabled=True,
        missing_trees=frozenset({"data/lexicon"}),
        item_name="test_sparse_marker_skips_only_the_marked_test",
    )
    assert unmarked is None


@pytest.mark.needs_sparse_tree("data/lexicon")
def test_sparse_marker_example() -> None:
    """Declared reader; collection skips it when data/lexicon is absent."""


def test_sparse_on_does_not_skip_when_tree_is_present() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/projects/open_model_data/test_mine.py",
        sparse_enabled=True,
        missing_trees=frozenset(),
        item_name="test_mine",
    )
    assert reason is None
