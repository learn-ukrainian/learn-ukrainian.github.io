"""Sparse worktrees skip tests that need an absent tree; CI does not."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from tests import sparse_trees


def _conftest() -> ModuleType:
    for module in list(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if isinstance(file, str) and file.endswith("tests/conftest.py"):
            return module
    raise AssertionError("tests/conftest.py was not loaded")


def test_conftest_lookup_survives_sys_modules_mutation_during_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sys.modules entry whose __file__ lookup inserts a new module must not
    crash the conftest lookup; regression for #8919."""

    class _MutatingEntry:
        fired = False

        def __getattr__(self, name: str) -> object:
            if name == "__file__" and not _MutatingEntry.fired:
                _MutatingEntry.fired = True
                sys.modules["_regression_probe_8919_conftest"] = object()
            raise AttributeError(name)

    target = ModuleType("target_conftest_8919")
    target.__file__ = "/scratch/tests/conftest.py"

    fake_modules: dict[str, object] = {"decoy_8919_conftest": _MutatingEntry()}
    fake_modules["target_conftest_8919"] = target
    monkeypatch.setattr(sys, "modules", fake_modules)

    assert _conftest() is target


class _Item:
    def __init__(self, rel: str, name: str) -> None:
        self.path = _conftest()._REPO_ROOT / rel
        self.name = name
        self.nodeid = f"{rel}::{name}"
        self.markers: list[str] = []

    def get_closest_marker(self, name: str) -> None:
        return None

    def add_marker(self, marker: pytest.MarkDecorator) -> None:
        self.markers.append(marker.name)


def test_sparse_skip_is_decided_at_run_time_not_collection(
    monkeypatch: pytest.MonkeyPatch, pytestconfig: pytest.Config
) -> None:
    """Collection analyzes no module; only a test that runs is checked (#10498)."""
    monkeypatch.setenv(sparse_trees.FORCE_MISSING_TREES_ENV, "data/projects")
    conftest = _conftest()
    setup = pytestconfig.pluginmanager.get_plugin("sparse-tree-skip")
    assert isinstance(setup, conftest._SparseTreeSkip)
    reader = _Item("tests/projects/open_model_data/test_mine.py", "test_mine")
    unrelated = _Item("tests/api/test_unrelated.py", "test_unrelated")

    def analyzed(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("collection ran the sparse-tree analysis")

    with monkeypatch.context() as collecting:
        collecting.setattr(conftest, "sparse_missing_tree_skip_reason", analyzed)
        conftest.pytest_collection_modifyitems(None, [reader, unrelated])
    assert "skip" not in reader.markers + unrelated.markers

    with pytest.raises(pytest.skip.Exception, match="--sparse-include data/projects") as skipped:
        setup.pytest_runtest_setup(reader)
    assert skipped.value._use_item_location
    assert setup.pytest_runtest_setup(unrelated) is None
