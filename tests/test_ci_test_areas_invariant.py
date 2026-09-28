"""Static, tracked-tree coverage for the full-PR open-model-data area lane."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from scripts.ci.classify_changes import hits_shared_root_denylist
from scripts.ci.test_areas import load_areas, matches_root, matches_test

pytestmark = pytest.mark.repo_wide

_REPO = Path(__file__).resolve().parents[1]
_OMD_MODULES = ("scripts.projects.open_model_data", "learn_ukrainian_v4_runtime")


def _tracked() -> set[str]:
    return set(
        subprocess.check_output(
            ["git", "ls-files", "--", "scripts", "packages", "tests"],
            cwd=_REPO,
            text=True,
            timeout=30,
        ).splitlines()
    )


def _module_paths(name: str) -> tuple[str, str]:
    stem = name.replace(".", "/")
    if name == "learn_ukrainian_v4_runtime" or name.startswith("learn_ukrainian_v4_runtime."):
        stem = "packages/v4-runtime/src/" + stem
    return stem + ".py", stem + "/__init__.py"


def _imports(path: str) -> set[str]:
    tree = ast.parse((_REPO / path).read_text(encoding="utf-8"), filename=path)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def _violations(tests: dict[str, list[str]], tracked: set[str]) -> tuple[list[str], list[str]]:
    modules = {path for path in tracked if path.endswith(".py")}
    missing_tests: list[str] = []
    missing_roots: list[str] = []
    for test in sorted(tracked):
        if not test.startswith("tests/") or not Path(test).name.startswith("test_") or not test.endswith(".py"):
            continue
        imports = _imports(test)
        is_area = matches_test(test, tests["tests"])
        if not is_area and any(
            name == root or name.startswith(root + ".") for name in imports for root in _OMD_MODULES
        ):
            missing_tests.append(test)
        if is_area:
            for name in imports:
                for module in _module_paths(name):
                    if (
                        module in modules
                        and not hits_shared_root_denylist(module)
                        and not matches_root(module, tests["roots"])
                    ):
                        missing_roots.append(f"{test} -> {module}")
    return missing_tests, sorted(set(missing_roots))


def test_open_model_data_area_covers_imports() -> None:
    missing_tests, missing_roots = _violations(load_areas()["open_model_data"], _tracked())
    assert missing_tests == []
    assert missing_roots == []


def test_incomplete_area_is_rejected() -> None:
    area = load_areas()["open_model_data"]
    tracked = _tracked()
    omitted_test = "tests/projects/open_model_data/test_a2_resolved_schema.py"
    omitted_root = "scripts/storage/paths.py"
    assert omitted_test in tracked and omitted_root in tracked
    incomplete = {
        "tests": [pattern for pattern in area["tests"] if not pattern.startswith("tests/projects/")],
        "roots": [root for root in area["roots"] if root != "scripts/storage/"],
    }
    missing_tests, missing_roots = _violations(incomplete, tracked)
    assert omitted_test in missing_tests
    assert any(omitted_root in item for item in missing_roots)
