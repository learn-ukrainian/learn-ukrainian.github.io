"""The pre-push gate's affected-test selector: proven importer closure, nearest first (#11207)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.ci import pre_push_shadow as selector

TESTS = ["tests/test_core.py", "tests/test_user.py", "tests/test_other.py", "tests/api/test_route.py"]


def graph(*edges: tuple[str, str], unresolved: int = 0) -> dict:
    return {
        "file_edges": sorted(edges),
        "unresolved_edges": [{"path": "x.py", "line": 1, "reason": "unresolved-subprocess"}] * unresolved,
        "python_files": 9,
    }


CHAIN = graph(
    ("tests/test_core.py", "scripts/core.py"),
    ("scripts/user.py", "scripts/core.py"),
    ("tests/test_user.py", "scripts/user.py"),
    ("tests/conftest.py", "scripts/core.py"),
)


def test_importer_distances_count_hops_from_the_changed_paths() -> None:
    assert selector.importer_distances(["scripts/core.py"], CHAIN["file_edges"]) == {
        "scripts/core.py": 0,
        "tests/test_core.py": 1,
        "scripts/user.py": 1,
        "tests/conftest.py": 1,
        "tests/test_user.py": 2,
    }


def test_only_importers_are_selected_nearest_first() -> None:
    answer = selector.select(["scripts/core.py"], CHAIN, TESTS)

    assert answer["schema"] == selector.SCHEMA and answer["scope"] == "importer_closure"
    # A conftest that merely imports the change does not widen the selection to its directory.
    assert answer["selected_tests"] == ["tests/test_core.py", "tests/test_user.py"]
    assert answer["import_edges"] == 4 and answer["unfollowed_edges"] == 0


def test_a_change_nothing_imports_selects_nothing() -> None:
    answer = selector.select(["docs/guide.md"], CHAIN, TESTS)

    assert answer["selected_tests"] == [] and answer["scope"] == "importer_closure"


def test_a_changed_test_file_selects_itself() -> None:
    assert selector.select(["tests/test_other.py"], CHAIN, TESTS)["selected_tests"] == ["tests/test_other.py"]


def test_a_changed_conftest_selects_every_test_under_its_directory() -> None:
    edges = graph(("tests/api/conftest.py", "scripts/core.py"))
    answer = selector.select(["tests/api/conftest.py"], edges, [*TESTS, "tests/api/deep/test_more.py"])

    assert answer["selected_tests"] == ["tests/api/deep/test_more.py", "tests/api/test_route.py"]


@pytest.mark.parametrize("path", ["pyproject.toml", "pytest.ini", "conftest.py", "tests/conftest.py"])
def test_a_pytest_configuration_change_affects_every_test(path: str) -> None:
    answer = selector.select([path], CHAIN, TESTS)

    assert answer["scope"] == "all_tests" and answer["all_tests_reasons"] == ["pytest_configuration"]
    selected = answer["selected_tests"]
    assert isinstance(selected, list) and sorted(selected) == sorted(TESTS)


def test_a_changed_configured_plugin_affects_every_test_but_its_imports_do_not() -> None:
    edges = graph(("scripts/ci/cap.py", "scripts/core.py"), ("tests/test_core.py", "scripts/core.py"))

    answer = selector.select(["scripts/ci/cap.py"], edges, TESTS, plugins=["scripts/ci/cap.py"])
    assert answer["scope"] == "all_tests" and answer["all_tests_reasons"] == ["pytest_plugin"]

    answer = selector.select(["scripts/core.py"], edges, TESTS, plugins=["scripts/ci/cap.py"])
    assert answer["scope"] == "importer_closure" and answer["selected_tests"] == ["tests/test_core.py"]


def test_plugin_files_resolve_addopts_plugins_on_the_pythonpath() -> None:
    pyproject = b"""
[tool.pytest.ini_options]
pythonpath = ["scripts"]
addopts = "-v -m 'not slow' -p ci.cap -p no:cacheprovider -pother"
"""
    tracked = {"scripts/ci/cap.py", "other/__init__.py", "other.py"}

    # Both the module and the package of a bare name are reported: either can be what pytest imports.
    assert selector.plugin_files(pyproject, tracked) == ["other.py", "other/__init__.py", "scripts/ci/cap.py"]
    assert selector.plugin_files(b"not toml [", tracked) == []
    assert selector.plugin_files(b"[tool.ruff]\n", tracked) == []


def test_the_repository_pytest_plugin_is_resolved() -> None:
    root = Path(__file__).resolve().parents[2]
    tracked = {"scripts/ci/pytest_dispatch_cap.py"}

    assert selector.plugin_files((root / "pyproject.toml").read_bytes(), tracked) == [
        "scripts/ci/pytest_dispatch_cap.py"
    ]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)


def test_selection_scans_the_indexed_tree(tmp_path: Path) -> None:
    files = {
        "scripts/__init__.py": "",
        "scripts/lib.py": "VALUE = 1\n",
        "scripts/app.py": "from scripts import lib\n",
        "tests/test_lib.py": "from scripts.lib import VALUE\n\n\ndef test_value():\n    assert VALUE\n",
        "tests/test_app.py": "import scripts.app\n",
        "tests/test_unrelated.py": "def test_ok():\n    pass\n",
    }
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")

    answer = selector.selection(["scripts/lib.py"], tmp_path)

    assert answer["selected_tests"] == ["tests/test_lib.py", "tests/test_app.py"]
    assert json.loads(json.dumps(answer)) == answer  # the gate reads it as one JSON line
