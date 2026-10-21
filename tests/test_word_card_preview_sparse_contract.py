"""The two committed preview-pointer readers follow the shared sparse contract."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.conftest import sparse_missing_tree_skip_reason

READERS = (
    ("tests/test_deploy_pages_workflow.py", "test_preview_pin_changes_keep_manual_deployment_semantics"),
    (
        "tests/test_prepare_word_card_preview.py",
        "test_committed_pin_matches_the_published_release_runbook_and_site_selector",
    ),
)


@pytest.mark.parametrize(("module", "reader"), READERS)
@pytest.mark.parametrize(
    ("sparse_enabled", "missing_trees", "expected"),
    [
        (
            True,
            {"site/src/data"},
            "site/src/data is absent from this sparse worktree; re-include it with --sparse-include site/src/data",
        ),
        (True, set(), None),
        (False, set(), None),
        (False, {"site/src/data"}, None),
    ],
    ids=("sparse-absent", "sparse-included", "full-present", "full-absent"),
)
def test_pointer_reader_skip_requires_sparse_absence(module, reader, sparse_enabled, missing_trees, expected) -> None:
    assert (
        sparse_missing_tree_skip_reason(
            module, item_name=reader, sparse_enabled=sparse_enabled, missing_trees=missing_trees
        )
        == expected
    )


@pytest.mark.parametrize(("module", "reader"), READERS)
def test_other_cases_in_the_pointer_modules_still_run_when_sparse(module: str, reader: str) -> None:
    source = Path(__file__).resolve().parents[1] / module
    functions = {
        node.name for node in ast.parse(source.read_text(encoding="utf-8")).body if isinstance(node, ast.FunctionDef)
    }
    assert reader in functions
    unaffected = {name for name in functions if name.startswith("test_")} - {reader}
    assert unaffected
    for name in unaffected:
        assert (
            sparse_missing_tree_skip_reason(
                module, item_name=name, sparse_enabled=True, missing_trees={"site/src/data"}
            )
            is None
        ), name
