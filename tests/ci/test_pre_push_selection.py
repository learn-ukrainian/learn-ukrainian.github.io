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
    assert sorted(answer["selected_tests"]) == sorted(TESTS)


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


def test_a_deleted_path_selects_its_importers_through_the_base_graph() -> None:
    base = graph(("tests/test_user.py", "scripts/user.py"), ("scripts/user.py", "scripts/gone.py"))

    answer = selector.select([], CHAIN, TESTS, deleted=["scripts/gone.py"], base_graph=base)

    assert answer["selected_tests"] == ["tests/test_user.py"] and answer["deleted_paths"] == 1
    with pytest.raises(ValueError, match="base import graph"):
        selector.select([], CHAIN, TESTS, deleted=["scripts/gone.py"])


@pytest.mark.parametrize("path", ["tests/conftest.py", "tests/api/conftest.py"])
def test_a_deleted_conftest_or_configuration_still_widens_the_selection(path: str) -> None:
    answer = selector.select([], CHAIN, TESTS, deleted=[path], base_graph=graph())

    assert "tests/api/test_route.py" in answer["selected_tests"]


def test_selection_reads_the_import_graph_of_the_base_commit_for_deleted_files(tmp_path: Path) -> None:
    files = {
        "scripts/__init__.py": "",
        "scripts/lib.py": "VALUE = 1\n",
        "scripts/app.py": "from scripts import lib\n",
        "tests/test_lib.py": "from scripts.lib import VALUE\n",
        "tests/test_app.py": "import scripts.app\n",
        "tests/test_unrelated.py": "def test_ok():\n    pass\n",
    }
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "base")
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    _git(tmp_path, "rm", "-q", "scripts/lib.py")

    answer = selector.selection([], tmp_path, deleted=["scripts/lib.py"], base=base)

    assert answer["selected_tests"] == ["tests/test_lib.py", "tests/test_app.py"]
    with pytest.raises(ValueError, match="base"):
        selector.selection([], tmp_path, deleted=["scripts/lib.py"])
    # The CLI takes the same inputs; an unknown base commit is an error the gate falls back on.
    with pytest.raises(subprocess.CalledProcessError):
        selector.main(["--base", "0" * 40, "--deleted", "scripts/lib.py", "--paths"])


@pytest.mark.parametrize(
    ("path", "source", "deleted", "kept"),
    [
        ("scripts/app.py", b"from scripts.lib import VALUE\n", "scripts/lib.py", True),
        ("scripts/app.py", b"from . import lib\n", "scripts/lib.py", True),
        ("scripts/app.py", b"DATA = Path(__file__).parent / 'table.json'\n", "scripts/table.json", True),
        ("scripts/app.py", b"import os\n", "scripts/lib.py", False),
        # A relative import reaches its package's __init__.py without naming it: the package is kept whole.
        ("scripts/pkg/mod.py", b"from . import sibling\n", "scripts/pkg/__init__.py", True),
        ("scripts/other.py", b"import scripts.pkg.mod\n", "scripts/pkg/__init__.py", True),
        ("scripts/other.py", b"import os\n", "scripts/pkg/__init__.py", False),
        ("scripts/lib.py", b"", "scripts/lib.py", True),
    ],
)
def test_only_base_files_that_can_reach_a_deleted_path_are_parsed(
    path: str, source: bytes, deleted: str, kept: bool
) -> None:
    assert selector.may_reach(path, source, [deleted]) is kept


def test_a_relative_importer_of_a_deleted_package_is_selected(tmp_path: Path) -> None:
    # Nothing below names the package: the test reaches its __init__.py only through relative imports.
    files = {
        "tests/pkg/__init__.py": "VALUE = 1\n",
        "tests/pkg/helper.py": "from . import VALUE\n",
        "tests/pkg/test_inner.py": "from .helper import VALUE\n",
        "tests/test_unrelated.py": "import os\n",
    }
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "base")
    _git(tmp_path, "rm", "-q", "tests/pkg/__init__.py")

    answer = selector.selection([], tmp_path, deleted=["tests/pkg/__init__.py"], base="HEAD")

    assert answer["selected_tests"] == ["tests/pkg/test_inner.py"]
