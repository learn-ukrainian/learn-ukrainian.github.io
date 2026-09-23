"""Sparse worktrees skip tests that need an absent tree; CI does not."""

from __future__ import annotations

import sys
from types import ModuleType


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


def test_sparse_on_does_not_skip_when_tree_is_present() -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/projects/open_model_data/test_mine.py",
        sparse_enabled=True,
        missing_trees=frozenset(),
        item_name="test_mine",
    )
    assert reason is None
