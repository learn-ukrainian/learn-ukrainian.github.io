"""Tests for the import-graph dependency index (#8750 phase B0a).

Every risk class is a small synthetic git repository with an exact expected
outcome (selected set or reason code). Two real-repo checks at the running
HEAD compare the index against an independent regex fixpoint and against
tests that clearly do not depend on ``scripts/delegate.py``.
"""

from __future__ import annotations

import re
import subprocess
import textwrap
from collections import defaultdict
from pathlib import Path

import pytest

from scripts.ci import import_graph
from scripts.ci.import_graph import (
    Reason,
    build_index,
    extract_facts,
    select_tests,
)

GIT_TIMEOUT = 60


class Repo:
    """A throwaway git repository built from ``{path: source}`` maps."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        env_args = [
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
        ]
        done = subprocess.run(
            ["git", *env_args, *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=True,
        )
        return done.stdout.strip()

    def commit(self, files: dict[str, str | None]) -> str:
        """Write (or delete, for ``None``) files and commit; returns the sha."""
        for rel, text in files.items():
            target = self.root / rel
            if text is None:
                target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        return self.git("rev-parse", "HEAD")


def make(tmp_path: Path, files: dict[str, str | None]) -> Repo:
    repo = Repo(tmp_path / "repo")
    repo.commit(files)
    return repo


def picked(repo: Repo, changed: list[str], **kwargs: object) -> tuple[str, ...]:
    result = select_tests(repo.root, "HEAD", changed, **kwargs)
    assert not result.full, f"unexpected FULL: {result.reason} {result.detail}"
    return result.tests


def full_reason(repo: Repo, changed: list[str], **kwargs: object) -> Reason:
    result = select_tests(repo.root, "HEAD", changed, **kwargs)
    assert result.full, f"expected FULL, got {result.tests}"
    assert result.reason is not None
    return result.reason


# A change to scripts/tool.py must select exactly the tests that use it.
BASE = {
    "scripts/__init__.py": "",
    "scripts/tool.py": "def run():\n    return 1\n",
    "scripts/other.py": "def go():\n    return 2\n",
    "tests/__init__.py": "",
    "tests/test_unrelated.py": "def test_x():\n    assert 1\n",
    "tests/test_other.py": "from scripts.other import go\n\n\ndef test_x():\n    assert go()\n",
}


# --------------------------------------------------------------------------
# edge kinds
# --------------------------------------------------------------------------


def test_direct_import_selects_only_importers(tmp_path: Path) -> None:
    repo = make(
        tmp_path, {**BASE, "tests/test_tool.py": "from scripts.tool import run\n\n\ndef test_x():\n    assert run()\n"}
    )
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_tool.py",)


def test_transitive_import_chain_through_non_test_helpers(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/mid.py": "import scripts.tool as tool\n",
            "scripts/top.py": "from scripts import mid\n",
            "tests/test_top.py": "import scripts.top\n\n\ndef test_x():\n    assert scripts.top\n",
        },
    )
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_top.py",)


def test_from_package_import_submodule_and_ancestor_initializer(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/pkg/__init__.py": "VERSION = 1\n",
            "scripts/pkg/mod.py": "X = 1\n",
            "scripts/pkg/sibling.py": "Y = 1\n",
            "tests/test_submodule.py": "from scripts.pkg import mod\n\n\ndef test_x():\n    assert mod.X\n",
            "tests/test_dotted.py": "import scripts.pkg.sibling\n\n\ndef test_x():\n    assert scripts.pkg.sibling\n",
        },
    )
    assert picked(repo, ["scripts/pkg/mod.py"]) == ("tests/test_submodule.py",)
    # Importing any submodule runs the package initializer first.
    assert picked(repo, ["scripts/pkg/__init__.py"]) == ("tests/test_dotted.py", "tests/test_submodule.py")


def test_relative_and_star_imports(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/pkg/__init__.py": "",
            "scripts/pkg/a.py": "from . import b\nfrom .c import *\n",
            "scripts/pkg/b.py": "B = 1\n",
            "scripts/pkg/c.py": "C = 1\n",
            "scripts/pkg/d.py": "D = 1\n",
            "tests/test_a.py": "from scripts.pkg.a import B\n\n\ndef test_x():\n    assert B\n",
        },
    )
    assert picked(repo, ["scripts/pkg/b.py"]) == ("tests/test_a.py",)
    assert picked(repo, ["scripts/pkg/c.py"]) == ("tests/test_a.py",)
    assert picked(repo, ["scripts/pkg/d.py"]) == ()


def test_flat_and_dotted_identities_map_to_the_same_file(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/test_flat.py": """
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
            import tool


            def test_x():
                assert tool.run()
        """,
            "tests/test_dotted.py": "import scripts.tool\n\n\ndef test_x():\n    assert scripts.tool.run()\n",
            "tests/test_from_flat.py": "from tool import run\n\n\ndef test_x():\n    assert run()\n",
        },
    )
    assert picked(repo, ["scripts/tool.py"]) == (
        "tests/test_dotted.py",
        "tests/test_flat.py",
        "tests/test_from_flat.py",
    )


def test_sys_path_insertion_of_a_non_default_root(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            "tools/helper.py": "def h():\n    return 1\n",
            "tests/test_helper.py": """
            import sys

            sys.path.insert(0, "tools")
            import helper


            def test_x():
                assert helper.h()
        """,
            "tests/test_unrelated.py": "def test_x():\n    assert 1\n",
        },
    )
    assert picked(repo, ["tools/helper.py"]) == ("tests/test_helper.py",)


def test_literal_dynamic_imports(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/test_import_module.py": """
            import importlib


            def test_x():
                assert importlib.import_module("scripts.tool").run()
        """,
            "tests/test_dunder.py": """
            def test_x():
                assert __import__("scripts.tool", fromlist=["run"]).run()
        """,
        },
    )
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_dunder.py", "tests/test_import_module.py")


def test_literal_prefix_dynamic_import_reaches_the_whole_package(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/plugins/__init__.py": "",
            "scripts/plugins/p1.py": "P = 1\n",
            "tests/test_plugins.py": """
            import importlib


            def test_x():
                for name in ("p1",):
                    assert importlib.import_module(f"scripts.plugins.{name}")
        """,
        },
    )
    assert picked(repo, ["scripts/plugins/p1.py"]) == ("tests/test_plugins.py",)
    assert picked(repo, ["scripts/tool.py"]) == ()


@pytest.mark.parametrize(
    "snippet",
    [
        'subprocess.run(["python", "scripts/tool.py", "--flag"], timeout=5)',
        'TOOL = ROOT / "scripts" / "tool.py"',
        'TOOL = os.path.join("scripts", "tool.py")',
        'TOOL = SCRIPTS / "tool.py"',
        'monkeypatch.setattr("scripts.tool.run", lambda: 2)',
        'subprocess.run("python -m scripts.tool", shell=True, timeout=5)',
        'runpy.run_module("scripts.tool", run_name="__main__")',
        'CMD = "python $ROOT/scripts/tool.py"',
    ],
)
def test_string_literal_references_to_first_party_files(tmp_path: Path, snippet: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/test_uses_tool.py": f"def test_x():\n    {snippet}\n",
        },
    )
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_uses_tool.py",)
    assert picked(repo, ["scripts/other.py"]) == ("tests/test_other.py",)


def test_comments_and_prose_do_not_create_edges(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/test_comment.py": """
            # import scripts.tool  (kept for reference, see scripts/tool.py)
            # subprocess.run(["python", "scripts/tool.py"])


            def test_x():
                assert 1  # scripts.tool is not used here
        """,
        },
    )
    assert picked(repo, ["scripts/tool.py"]) == ()


def test_every_first_party_python_file_is_a_node(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            "tools/helper.py": "H = 1\n",
            "packages/kit/kit.py": "K = 1\n",
            "tests/test_root_level.py": "from tools.helper import H\n\n\ndef test_x():\n    assert H\n",
            "tests/test_package.py": "from packages.kit.kit import K\n\n\ndef test_x():\n    assert K\n",
        },
    )
    assert picked(repo, ["tools/helper.py"]) == ("tests/test_root_level.py",)
    assert picked(repo, ["packages/kit/kit.py"]) == ("tests/test_package.py",)


def test_test_helpers_under_tests_are_triggers_and_a_changed_test_selects_itself(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/helpers/__init__.py": "",
            "tests/helpers/util.py": "def u():\n    return 1\n",
            "tests/helpers/lonely.py": "def l():\n    return 1\n",
            "tests/test_uses_helper.py": "from tests.helpers.util import u\n\n\ndef test_x():\n    assert u()\n",
        },
    )
    assert picked(repo, ["tests/helpers/util.py"]) == ("tests/test_uses_helper.py",)
    assert picked(repo, ["tests/test_unrelated.py"]) == ("tests/test_unrelated.py",)
    result = select_tests(repo.root, "HEAD", ["tests/helpers/lonely.py"])
    assert (result.full, result.tests, result.unreached) == (False, (), ("tests/helpers/lonely.py",))


# --------------------------------------------------------------------------
# FULL reasons
# --------------------------------------------------------------------------


def test_empty_non_python_and_unparsable_inputs(tmp_path: Path) -> None:
    repo = make(tmp_path, {**BASE, "scripts/broken.py": "def (:\n", "README.md": "hi\n"})
    assert full_reason(repo, []) is Reason.NO_CHANGED_PATHS
    assert full_reason(repo, ["scripts/tool.py", "README.md"]) is Reason.NON_PYTHON_CHANGE
    assert full_reason(repo, ["scripts/broken.py"]) is Reason.UNPARSABLE_BLOB
    result = select_tests(repo.root, "no-such-ref", ["scripts/tool.py"])
    assert (result.full, result.reason) == (True, Reason.GIT_ERROR)


CONFTEST = {
    **BASE,
    "scripts/shared.py": "S = 1\n",
    "scripts/deep.py": "D = 1\n",
    "scripts/via_shared.py": "import scripts.deep\n",
    "tests/conftest.py": """
        import pytest

        from scripts.shared import S


        @pytest.fixture(autouse=True)
        def _autouse():
            from scripts import via_shared
            return S, via_shared
    """,
    "tests/test_uses_tool.py": "from scripts.tool import run\n\n\ndef test_x():\n    assert run()\n",
}


def test_root_conftest_and_everything_it_reaches_is_full(tmp_path: Path) -> None:
    repo = make(tmp_path, CONFTEST)
    assert full_reason(repo, ["tests/conftest.py"]) is Reason.CONFTEST_REACHABLE
    assert full_reason(repo, ["scripts/shared.py"]) is Reason.CONFTEST_REACHABLE
    # A function-local import inside an autouse fixture still reaches every test.
    assert full_reason(repo, ["scripts/deep.py"]) is Reason.CONFTEST_REACHABLE
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_uses_tool.py",)


def test_nested_conftest_scopes_to_its_directory_and_foreign_conftest_is_full(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/sub_helper.py": "H = 1\n",
            "scripts/foreign_helper.py": "F = 1\n",
            "tests/sub/__init__.py": "",
            "tests/sub/conftest.py": "from scripts.sub_helper import H\n",
            "tests/sub/test_in_scope.py": "def test_x():\n    assert 1\n",
            "tests/sub/deeper/test_deeper.py": "def test_x():\n    assert 1\n",
            "scripts/pkg/conftest.py": "from scripts.foreign_helper import F\n",
        },
    )
    assert picked(repo, ["scripts/sub_helper.py"]) == ("tests/sub/deeper/test_deeper.py", "tests/sub/test_in_scope.py")
    assert full_reason(repo, ["scripts/foreign_helper.py"]) is Reason.CONFTEST_SCOPE_UNKNOWN


@pytest.mark.parametrize(
    ("conftest", "pyproject"),
    [
        ('pytest_plugins = ("scripts.plug",)\n', ""),
        ("", '[tool.pytest.ini_options]\naddopts = "-v -p scripts.plug"\n'),
        ("", '[tool.pytest.ini_options]\naddopts = "-v -pscripts.plug"\n'),
        ("", '[project.entry-points.pytest11]\nmyplug = "scripts.plug"\n'),
        ("", '[project.entry-points."pytest11"]\nmyplug = "scripts.plug:register"\n'),
    ],
)
def test_pytest_plugins_addopts_and_entry_points_are_full(tmp_path: Path, conftest: str, pyproject: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/plug.py": "import scripts.plug_dep\n",
            "scripts/plug_dep.py": "D = 1\n",
            "tests/sub/conftest.py": conftest,
            "pyproject.toml": pyproject or "[project]\nname = 'x'\n",
            "tests/test_uses_tool.py": "from scripts.tool import run\n\n\ndef test_x():\n    assert run()\n",
        },
    )
    assert full_reason(repo, ["scripts/plug.py"]) is Reason.PYTEST_PLUGIN
    assert full_reason(repo, ["scripts/plug_dep.py"]) is Reason.PYTEST_PLUGIN
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_uses_tool.py",)


def test_unbounded_dynamic_import_is_full_and_dependents_always_selects_its_tests(tmp_path: Path) -> None:
    unbounded = make(
        tmp_path / "a",
        {
            **BASE,
            "scripts/loader.py": "import importlib\nimport sys\n\n\ndef load():\n    return importlib.import_module(sys.argv[1])\n",
            "tests/test_loader.py": "from scripts.loader import load\n\n\ndef test_x():\n    assert load\n",
        },
    )
    assert full_reason(unbounded, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    # Opt-in: only the tests that can reach the loader are at risk from its unknown target.
    assert picked(unbounded, ["scripts/tool.py"], dynamic="dependents") == ("tests/test_loader.py",)
    assert picked(unbounded, ["scripts/other.py"], dynamic="dependents") == (
        "tests/test_loader.py",
        "tests/test_other.py",
    )


@pytest.mark.parametrize(
    "loader",
    [
        # A literal registry elsewhere does not bound the computed name.
        """
        import importlib

        from scripts.registry import ADAPTERS


        def load(name):
            module, _, attr = ADAPTERS[name].partition(":")
            return getattr(importlib.import_module(module), attr)
        """,
        # Nor does a literal dynamic import next to it (#8750 B0a review, finding 1).
        """
        import importlib


        def load(name):
            importlib.import_module("json")
            return importlib.import_module(name)
        """,
        # Nor a literal in a module the loader imports.
        """
        import runpy

        import scripts.registry


        def load(name):
            return runpy.run_module(name)
        """,
    ],
)
def test_a_computed_module_name_is_bounded_only_by_its_own_call(tmp_path: Path, loader: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/registry.py": 'ADAPTERS = {"tool": "scripts.tool:run"}\n',
            "scripts/loader.py": loader,
            "tests/test_loader.py": "from scripts.loader import load\n\n\ndef test_x():\n    assert load\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    assert full_reason(repo, ["scripts/tool.py"], dynamic="strict") is Reason.UNBOUNDED_DYNAMIC_IMPORT
    assert picked(repo, ["scripts/tool.py"], dynamic="dependents") == ("tests/test_loader.py",)
    assert picked(repo, ["scripts/other.py"], dynamic="dependents") == ("tests/test_loader.py", "tests/test_other.py")


def test_a_literal_prefix_bounds_the_call_and_must_name_a_first_party_module(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/stages/__init__.py": "",
            "scripts/stages/v4_a1.py": "A = 1\n",
            "scripts/stages/v5_b1.py": "B = 1\n",
            "tests/test_stage.py": """
            import importlib


            def test_x(stage="a1"):
                assert importlib.import_module("scripts.stages.v4_" + stage)
        """,
        },
    )
    assert picked(repo, ["scripts/stages/v4_a1.py"]) == ("tests/test_stage.py",)
    assert picked(repo, ["scripts/stages/v5_b1.py"]) == ()
    assert picked(repo, ["scripts/stages/__init__.py"]) == ("tests/test_stage.py",)
    # ``strict`` counts a literal prefix as unbounded too.
    assert full_reason(repo, ["scripts/stages/v5_b1.py"], dynamic="strict") is Reason.UNBOUNDED_DYNAMIC_IMPORT
    # A prefix naming no first-party module (an installed package) bounds nothing.
    foreign = make(
        tmp_path / "foreign",
        {
            **BASE,
            "tests/test_stage.py": "import importlib\n\n\ndef test_x(s='a'):\n    assert importlib.import_module(f'vendor_pkg.v4_{s}')\n",
        },
    )
    assert full_reason(foreign, ["scripts/other.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT


def test_an_unbounded_import_in_a_conftest_or_plugin_is_seen(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/sub/conftest.py": "import importlib\nimport os\n\nimportlib.import_module(os.environ['PLUGIN'])\n",
            "tests/sub/test_in_scope.py": "def test_x():\n    assert 1\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    assert picked(repo, ["scripts/tool.py"], dynamic="dependents") == ("tests/sub/test_in_scope.py",)
    # Every test reaches a root conftest, so ``dependents`` cannot narrow it.
    root = make(
        tmp_path / "root",
        {
            **BASE,
            "tests/conftest.py": "import importlib\nimport os\n\nimportlib.import_module(os.environ['PLUGIN'])\n",
        },
    )
    assert full_reason(root, ["scripts/tool.py"], dynamic="dependents") is Reason.UNBOUNDED_DYNAMIC_IMPORT


def test_unreachable_unbounded_dynamic_import_does_not_force_full(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/orphan_loader.py": "import importlib\n\n\ndef load(n):\n    return importlib.import_module(n)\n",
        },
    )
    assert picked(repo, ["scripts/other.py"]) == ("tests/test_other.py",)


def test_computed_module_name_without_any_literal_evidence_is_full_even_via_run_module(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/runner.py": "import runpy\nimport sys\n\n\ndef go():\n    return runpy.run_module(sys.argv[1])\n",
            "tests/test_runner.py": "from scripts.runner import go\n\n\ndef test_x():\n    assert go\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT


@pytest.mark.parametrize(
    "call",
    [
        'importlib.util.spec_from_file_location("m", sys.argv[1])',
        "runpy.run_path(sys.argv[1])",
        'importlib.machinery.SourceFileLoader("m", sys.argv[1]).load_module()',
        "runpy.run_path(path)",
    ],
)
def test_runtime_supplied_file_paths_are_unbounded(tmp_path: Path, call: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/runner.py": f"""
            import importlib.machinery
            import importlib.util
            import runpy
            import sys


            def go(path=None):
                return {call}
        """,
            "tests/test_runner.py": "from scripts.runner import go\n\n\ndef test_x():\n    assert go\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    assert picked(repo, ["scripts/tool.py"], dynamic="dependents") == ("tests/test_runner.py",)


@pytest.mark.parametrize(
    "source",
    [
        "import importlib\n\nload = importlib.import_module\n\n\ndef go(n):\n    return load(n)\n",
        "from importlib import import_module as im\n\n\ndef go(n):\n    return im(n)\n",
        "import builtins\n\nreal_import = builtins.__import__\n",
        "import runpy\n\nRUN = runpy.run_path\n",
    ],
)
def test_an_aliased_loader_is_unbounded(tmp_path: Path, source: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/runner.py": source,
            "tests/test_runner.py": "import scripts.runner\n\n\ndef test_x():\n    assert scripts.runner\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT


def test_statically_evaluated_file_loads_are_edges(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/plugins/__init__.py": "",
            "scripts/plugins/p1.py": "P = 1\n",
            "scripts/stub.py": """
            import importlib.util as _ilu
            from pathlib import Path as _P

            _f = _P(__file__).parent / "plugins" / "p1.py"
            _s = _ilu.spec_from_file_location("p1", _f)
        """,
            "scripts/sibling_loader.py": """
            import importlib.util
            from pathlib import Path


            def load(filename):
                here = Path(__file__).resolve().parent
                return importlib.util.spec_from_file_location(filename, here / "plugins" / filename)
        """,
            "tests/test_stub.py": "import scripts.stub\n\n\ndef test_x():\n    assert scripts.stub\n",
            "tests/test_sibling.py": "import scripts.sibling_loader\n\n\ndef test_x():\n    assert scripts.sibling_loader\n",
        },
    )
    # A path under a known directory is bounded by that directory.
    assert picked(repo, ["scripts/plugins/p1.py"]) == ("tests/test_sibling.py", "tests/test_stub.py")
    # p1.py itself links its package initializer (every file does).
    assert picked(repo, ["scripts/plugins/__init__.py"]) == ("tests/test_sibling.py", "tests/test_stub.py")
    assert picked(repo, ["scripts/tool.py"]) == ()


# The open_model_data layout from the #8750 B0a review: a fixture module and
# its consumer in a directory without ``__init__.py`` (pytest inserts it on
# ``sys.path``), plus a test elsewhere that reaches it through a computed
# ``sys.path`` entry.
PLUGIN_TESTS = {
    **BASE,
    "tests/projects/omd/test_v4_packaged_operation_boundary.py": """
        import pytest


        @pytest.fixture
        def pg_cluster():
            return 1


        def test_boundary(pg_cluster):
            assert pg_cluster
    """,
    "tests/projects/omd/test_v4_operation_lifecycle.py": """
        pytest_plugins = ("test_v4_packaged_operation_boundary",)


        def test_lifecycle(pg_cluster):
            assert pg_cluster
    """,
    "tests/projects/omd/test_v4_runner_origin_mechanism.py": """
        pytest_plugins = ["test_v4_operation_lifecycle"]


        def test_origin(pg_cluster):
            assert pg_cluster
    """,
    "tests/test_mcp_sources_v4_invocation_recording.py": """
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent / "projects/omd"))
        import test_v4_operation_lifecycle
        from test_v4_operation_lifecycle import test_lifecycle

        pytest_plugins = ("test_v4_operation_lifecycle",)


        def test_mcp(pg_cluster):
            assert test_v4_operation_lifecycle and test_lifecycle
    """,
}


def test_pytest_plugins_in_a_test_module_is_an_edge(tmp_path: Path) -> None:
    repo = make(tmp_path, PLUGIN_TESTS)
    assert picked(repo, ["tests/projects/omd/test_v4_packaged_operation_boundary.py"]) == (
        "tests/projects/omd/test_v4_operation_lifecycle.py",
        "tests/projects/omd/test_v4_packaged_operation_boundary.py",
        "tests/projects/omd/test_v4_runner_origin_mechanism.py",
        "tests/test_mcp_sources_v4_invocation_recording.py",
    )


def test_a_file_relative_sys_path_entry_resolves_exactly(tmp_path: Path) -> None:
    repo = make(tmp_path, PLUGIN_TESTS)
    assert picked(repo, ["tests/projects/omd/test_v4_operation_lifecycle.py"]) == (
        "tests/projects/omd/test_v4_operation_lifecycle.py",
        "tests/projects/omd/test_v4_runner_origin_mechanism.py",
        "tests/test_mcp_sources_v4_invocation_recording.py",
    )


@pytest.mark.parametrize(
    "plugins",
    [
        "pytest_plugins = [os.environ['PLUGIN']]",
        "pytest_plugins = PLUGINS",
    ],
)
def test_a_computed_module_level_pytest_plugins_is_unbounded(tmp_path: Path, plugins: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tests/test_plugged.py": f"import os\n\nPLUGINS = os.environ\n{plugins}\n\n\ndef test_x():\n    assert 1\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    # A local variable of that name registers nothing.
    local = make(
        tmp_path / "local",
        {
            **BASE,
            "scripts/env.py": "def plugins(raw):\n    pytest_plugins = raw.get('P')\n    return pytest_plugins\n",
            "tests/test_env.py": "import scripts.env\n\n\ndef test_x():\n    assert scripts.env\n",
        },
    )
    assert picked(local, ["scripts/tool.py"]) == ()


@pytest.mark.parametrize(
    "insertion",
    [
        'sys.path.insert(0, os.environ["EXTRA"])',
        "sys.path.append(extra_dir())",
        "sys.path.extend(extra_dirs())",
        "sys.path += extra_dirs()",
        "sys.path[:0] = [extra_dir()]",
        "monkeypatch_syspath = None; sys.path.insert(0, str(ROOT / sub))",
        "site.addsitedir(extra_dir())",
    ],
)
def test_a_computed_sys_path_entry_is_unbounded(tmp_path: Path, insertion: str) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/boot.py": f"""
            import os
            import site
            import sys
            from pathlib import Path

            ROOT = Path(__file__).resolve().parents[1]
            sub = os.environ.get("SUB", "tools")


            def extra_dir():
                return os.environ["EXTRA"]


            def extra_dirs():
                return [extra_dir()]


            {insertion}
        """,
            "tests/test_boot.py": "import scripts.boot\n\n\ndef test_x():\n    assert scripts.boot\n",
        },
    )
    assert full_reason(repo, ["scripts/tool.py"]) is Reason.UNBOUNDED_DYNAMIC_IMPORT
    assert picked(repo, ["scripts/tool.py"], dynamic="dependents") == ("tests/test_boot.py",)


def test_statically_evaluated_sys_path_forms_resolve(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "tools/__init__.py": "",
            "tools/paths.py": "from pathlib import Path\n\nTOOLS = Path(__file__).resolve().parent\n",
            "tools/helper.py": "H = 1\n",
            "tools/other_helper.py": "O = 1\n",
            "tests/test_constant.py": """
            import os
            import sys
            from pathlib import Path

            ROOT = Path(__file__).resolve().parents[1]
            saved = list(sys.path)
            for extra in (ROOT / "tools",):
                sys.path.insert(0, str(extra))
            sys.path += [os.path.join(os.path.dirname(__file__), "..", "tools")]
            import helper

            sys.path[:] = saved


            def test_x():
                assert helper.H
        """,
            "tests/test_imported_constant.py": """
            import sys

            from tools.paths import TOOLS as _TOOLS

            if str(_TOOLS) not in sys.path:
                sys.path.insert(0, f"{_TOOLS}")
            import other_helper


            def test_x():
                assert other_helper.O
        """,
        },
    )
    assert picked(repo, ["tools/helper.py"]) == ("tests/test_constant.py",)
    assert picked(repo, ["tools/other_helper.py"]) == ("tests/test_imported_constant.py",)


def test_an_installed_in_tree_package_is_an_import_root(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "packages/runtime/pyproject.toml": '[project]\nname = "rt"\n\n[tool.setuptools.packages.find]\nwhere = ["src"]\n',
            "packages/runtime/src/rt_pkg/__init__.py": "",
            "packages/runtime/src/rt_pkg/core.py": "C = 1\n",
            "tests/test_runtime.py": "from rt_pkg.core import C\n\n\ndef test_x():\n    assert C\n",
        },
    )
    assert picked(repo, ["packages/runtime/src/rt_pkg/core.py"]) == ("tests/test_runtime.py",)


def test_ambiguous_import_involving_a_changed_file_is_full(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/config.py": "A = 1\n",
            "scripts/audit/__init__.py": "",
            "scripts/audit/config.py": "B = 1\n",
            "scripts/audit/run.py": "import config\n",
            "tests/test_run.py": "import scripts.audit.run\n\n\ndef test_x():\n    assert scripts.audit.run\n",
        },
    )
    assert full_reason(repo, ["scripts/config.py"]) is Reason.AMBIGUOUS_RESOLUTION
    assert full_reason(repo, ["scripts/audit/config.py"]) is Reason.AMBIGUOUS_RESOLUTION
    assert picked(repo, ["scripts/tool.py"]) == ()


def test_package_directory_shadows_a_same_named_module(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/thing.py": "OLD = 1\n",
            "scripts/thing/__init__.py": "NEW = 1\n",
            "tests/test_thing.py": "import scripts.thing\n\n\ndef test_x():\n    assert scripts.thing.NEW\n",
        },
    )
    assert picked(repo, ["scripts/thing/__init__.py"]) == ("tests/test_thing.py",)


# --------------------------------------------------------------------------
# base tree: deletions, renames, changed-list completeness
# --------------------------------------------------------------------------


def test_deletion_without_a_base_tree_is_full(tmp_path: Path) -> None:
    repo = make(tmp_path, BASE)
    assert full_reason(repo, ["scripts/gone.py"]) is Reason.DELETION_UNRECOVERABLE


def test_deleted_file_selects_the_tests_that_imported_it_at_base(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/gone.py": "G = 1\n",
            "tests/test_gone.py": "import scripts.gone\n\n\ndef test_x():\n    assert scripts.gone\n",
        },
    )
    base = repo.git("rev-parse", "HEAD")
    repo.commit({"scripts/gone.py": None})
    assert picked(repo, ["scripts/gone.py"], base=base) == ("tests/test_gone.py",)


def test_rename_selects_importers_of_both_names(tmp_path: Path) -> None:
    repo = make(
        tmp_path,
        {
            **BASE,
            "scripts/old_name.py": "V = 1\n",
            "tests/test_old.py": "import scripts.old_name\n\n\ndef test_x():\n    assert scripts.old_name\n",
        },
    )
    base = repo.git("rev-parse", "HEAD")
    repo.commit(
        {
            "scripts/old_name.py": None,
            "scripts/new_name.py": "V = 1\n",
            "tests/test_new.py": "import scripts.new_name\n\n\ndef test_x():\n    assert scripts.new_name\n",
        }
    )
    changed = ["scripts/old_name.py", "scripts/new_name.py", "tests/test_new.py"]
    assert picked(repo, changed, base=base) == ("tests/test_new.py", "tests/test_old.py")
    # One side of the rename dropped from the list: the trees still differ there.
    assert full_reason(repo, ["scripts/new_name.py", "tests/test_new.py"], base=base) is Reason.CHANGED_SET_INCOMPLETE


def test_deleted_file_that_conftest_reached_at_base_is_full(tmp_path: Path) -> None:
    repo = make(tmp_path, CONFTEST)
    base = repo.git("rev-parse", "HEAD")
    repo.commit({"scripts/shared.py": None, "tests/conftest.py": "import pytest\n"})
    assert full_reason(repo, ["scripts/shared.py", "tests/conftest.py"], base=base) is Reason.CONFTEST_REACHABLE


def test_unreadable_base_ref_is_git_error(tmp_path: Path) -> None:
    repo = make(tmp_path, BASE)
    repo.commit({"scripts/other.py": None})
    result = select_tests(repo.root, "HEAD", ["scripts/other.py"], base="no-such-ref")
    assert (result.full, result.reason) == (True, Reason.GIT_ERROR)


# --------------------------------------------------------------------------
# git access
# --------------------------------------------------------------------------


def test_one_ls_tree_and_one_cat_file_per_tree_and_no_worktree_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make(
        tmp_path, {**BASE, "tests/test_tool.py": "from scripts.tool import run\n\n\ndef test_x():\n    assert run()\n"}
    )
    calls: list[list[str]] = []
    real_run = subprocess.run

    def spy(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(list(cmd))
        return real_run(cmd, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(import_graph.subprocess, "run", spy)
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_tool.py",)
    assert [c[1] for c in calls] == ["ls-tree", "cat-file"]


def test_sparse_checkout_without_the_scripts_tree(tmp_path: Path) -> None:
    repo = make(
        tmp_path, {**BASE, "tests/test_tool.py": "from scripts.tool import run\n\n\ndef test_x():\n    assert run()\n"}
    )
    repo.git("sparse-checkout", "set", "--no-cone", "/tests/")
    assert not (repo.root / "scripts").exists()
    assert picked(repo, ["scripts/tool.py"]) == ("tests/test_tool.py",)


# --------------------------------------------------------------------------
# extraction details
# --------------------------------------------------------------------------


def test_extract_import_statement_shapes() -> None:
    source = textwrap.dedent("""
        import os, sys as s
        from scripts.foo import (
            bar,  # comment
            baz as q,
        )
        from . import sibling
        from ..up import thing
        try: import yaml
        except ImportError: from a.b import c
        code = "import delegate; import other.thing"
        text = "prose: from the docs we import nothing"
        # import commented.out
        if TYPE_CHECKING:
            from typing import Any
    """).encode()
    facts = extract_facts(source)
    assert facts.imports == [
        (0, "os", ()),
        (0, "sys", ()),
        (0, "scripts.foo", ("bar", "baz")),
        (1, "", ("sibling",)),
        (2, "up", ("thing",)),
        (0, "yaml", ()),
        (0, "a.b", ("c",)),
        (0, "delegate", ()),
        (0, "other.thing", ()),
        (0, "typing", ("Any",)),
    ]


def test_extract_dynamic_import_classification() -> None:
    facts = extract_facts(
        textwrap.dedent("""
        importlib.import_module("scripts.a")
        __import__("scripts.b", fromlist=["x"])
        importlib.import_module(f"scripts.plugins.{name}")
        importlib.import_module("scripts.p." + name)
        importlib.import_module(name)
        __import__(module_name, fromlist=[cls])
        from importlib import import_module
    """).encode()
    )
    assert facts.dyn_literals == ["scripts.a", "scripts.b"]
    assert facts.dyn_prefixes == ["scripts.plugins.", "scripts.p."]
    assert len(facts.unbounded) == 2


def test_extract_path_and_dotted_mentions() -> None:
    facts = extract_facts(
        textwrap.dedent("""
        A = ROOT / "scripts" / "delegate.py"
        B = os.path.join("scripts", "ci", "x.py")
        C = ["python", "scripts/build/v7.py", "-m", "scripts.z.k"]
        D = SCRIPTS / "bare.py"
        E = "python -m scripts.q.r --x"
        F = "config.yaml"
        G = "notes.md"
    """).encode()
    )
    assert {"scripts/delegate.py", "scripts/ci/x.py", "ci/x.py", "scripts/build/v7.py"} <= facts.path_tokens
    assert facts.bare_path_tokens == {"bare.py"}
    assert {"scripts.z.k", "scripts.q.r"} <= facts.dotted_tokens
    assert not {t for t in facts.dotted_tokens if t.endswith(("yaml", "md"))}


# --------------------------------------------------------------------------
# real repository at HEAD
# --------------------------------------------------------------------------


def _real_repo_root() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    try:
        tracked = subprocess.run(
            ["git", "ls-tree", "--name-only", "HEAD", "scripts/delegate.py"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return root if tracked.strip() == "scripts/delegate.py" else None


REAL_ROOT = _real_repo_root()
real_repo = pytest.mark.skipif(REAL_ROOT is None, reason="needs the full repository tree at HEAD")

_IMPORT_LINE = re.compile(r"^\s*(?:(?:try|else|if [^:]*)\s*:\s*)?import\s+(.+)$")
_FROM_LINE = re.compile(r"^\s*(?:(?:try|else|if [^:]*)\s*:\s*)?from\s+(\.*)([\w.]*)\s+import\s+(.+)$")
_QUOTED = re.compile(r"""["']([A-Za-z_]\w*(?:\.\w+)+)""")
_TEST_PATH = re.compile(r"^tests/(?:.*/)?(?:test_[^/]*|[^/]*_test)\.py$")


def _oracle_closure(root: Path, target: str) -> tuple[set[str], set[str]]:
    """Independent oracle: regex scans over ONE ``git grep`` dump, to a fixpoint.

    Import statements and quoted dotted names only (no package-initializer
    edges, no path literals; a bare quoted word is not a module mention) - it
    never calls ``import_graph``. Returns
    ``(direct importers, transitive dependents)`` restricted to test files.
    """
    dump = subprocess.run(
        ["git", "grep", "-n", "-I", "-E", r"import|-m |[\"']", "HEAD", "--", "*.py"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=True,
    ).stdout
    by_name: dict[str, set[str]] = defaultdict(set)
    for row in dump.splitlines():
        _, _, rest = row.partition(":")
        path, _, rest = rest.partition(":")
        _, _, text = rest.partition(":")
        if text.lstrip().startswith("#"):
            continue
        text = re.sub(r"\s#.*$", "", text)
        pkg = path.rpartition("/")[0].replace("/", ".")
        from_match = _FROM_LINE.match(text)
        if from_match:
            dots, module, names = from_match.groups()
            if dots:
                base = pkg.split(".") if pkg else []
                base = base[: len(base) - (len(dots) - 1)]
                module = ".".join([*base, *([module] if module else [])])
            by_name[module].add(path)
            for name in re.findall(r"[A-Za-z_]\w*", names):
                by_name[f"{module}.{name}" if module else name].add(path)
            continue
        import_match = _IMPORT_LINE.match(text)
        if import_match:
            for item in import_match.group(1).split(","):
                name = item.strip().split(" as ")[0].strip()
                if re.fullmatch(r"[\w.]+", name):
                    by_name[name].add(path)
        for token in _QUOTED.findall(text):
            by_name[token].add(path)

    def spellings(path: str) -> set[str]:
        dotted = path[:-3].removesuffix("/__init__").replace("/", ".")
        return {dotted, dotted.removeprefix("scripts.")} if path.startswith("scripts/") else {dotted}

    def importers(path: str) -> set[str]:
        found: set[str] = set()
        for name in spellings(path):
            found |= by_name.get(name, set())
        found.discard(path)
        return found

    direct = {p for p in importers(target) if _TEST_PATH.match(p)}
    seen = {target}
    frontier = {target}
    while frontier:
        new: set[str] = set()
        for path in frontier:
            new |= importers(path)
        frontier = new - seen
        seen |= frontier
    return direct, {p for p in seen if _TEST_PATH.match(p)}


@pytest.fixture(scope="module")
def real_graph() -> import_graph.ImportGraph:
    assert REAL_ROOT is not None
    return build_index(REAL_ROOT, "HEAD")


@real_repo
def test_delegate_dependents_match_the_independent_oracle(real_graph: import_graph.ImportGraph) -> None:
    assert REAL_ROOT is not None
    target = "scripts/delegate.py"
    graph = real_graph
    reach = graph.reverse_closure([target]) & graph.tests()
    direct, closure = _oracle_closure(REAL_ROOT, target)
    grep = subprocess.run(
        [
            "git",
            "grep",
            "-lE",
            r"(from scripts\.delegate import|import scripts\.delegate|scripts\.delegate|^\s*import delegate\b|from delegate import)",
            "HEAD",
            "--",
            "tests/",
        ],
        cwd=REAL_ROOT,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=True,
    ).stdout
    brief_direct = {row.partition(":")[2] for row in grep.splitlines()}
    # Soundness: nothing the oracle or the plain grep can see is missing.
    assert brief_direct & graph.tests() <= reach
    assert direct <= reach
    assert closure <= reach, sorted(closure - reach)
    # Every extra the index reports is invisible to an import-statement regex:
    # its shortest chain crosses a package initializer, a path literal, a
    # quoted dotted name or a file loaded by path.
    for test in sorted(reach - closure):
        chain = graph.explain(test, target)
        assert chain is not None, test
        assert any(set(kinds) & {"init", "mention", "load"} for _, _, kinds in chain), (test, chain)
    # ``dependents`` never selects fewer tests than the import closure.
    result = select_tests(REAL_ROOT, "HEAD", [target], dynamic="dependents")
    assert result.full or reach & graph.tests() <= set(result.tests)


# The 13 test-reachable modules the #8750 B0a review found hidden by an
# unrelated literal elsewhere in their import closure: each has a computed
# import_module / __import__ call of its own, so each is unbounded now.
REVIEW_UNBOUNDED = (
    "scripts/agent_runtime/lane_probe.py",
    "scripts/agent_runtime/primary_tree_watch.py",
    "scripts/agent_runtime/runner.py",
    "scripts/api/preload.py",
    "scripts/audit/check_venv_integrity.py",
    "scripts/delegate.py",
    "scripts/projects/open_model_data/phase3_textbook_nonhit.py",
    "tests/agent_runtime/test_delegate_tool_config_contract.py",
    "tests/api/test_import_pinning.py",
    "tests/api/test_orient_ctx_isolation.py",
    "tests/test_layerb_label_tools.py",
    "tests/test_stripped_flavor_imports.py",
    "tests/test_v7_writer_dispatch.py",
)


@real_repo
def test_review_modules_with_computed_imports_are_unbounded(real_graph: import_graph.ImportGraph) -> None:
    present = [m for m in REVIEW_UNBOUNDED if m in real_graph.py]
    assert present
    for policy in ("bounded", "dependents"):
        unbounded = set(import_graph._unbounded_importers(real_graph, policy))  # type: ignore[arg-type]
        assert set(present) <= unbounded, sorted(set(present) - unbounded)


@real_repo
def test_open_model_data_plugin_and_sys_path_consumers_are_dependents(real_graph: import_graph.ImportGraph) -> None:
    omd = "tests/projects/open_model_data"
    boundary = real_graph.reverse_closure([f"{omd}/test_v4_packaged_operation_boundary.py"], scoped=True)
    assert {
        f"{omd}/test_v4_operation_lifecycle.py",
        f"{omd}/test_v4_canonical_authority_mechanism.py",
        f"{omd}/test_v4_runner_origin_mechanism.py",
    } <= boundary
    lifecycle = real_graph.reverse_closure([f"{omd}/test_v4_operation_lifecycle.py"], scoped=True)
    assert "tests/test_mcp_sources_v4_invocation_recording.py" in lifecycle


@real_repo
@pytest.mark.parametrize(
    "unrelated",
    [
        "tests/etymology/test_transliterate.py",
        "tests/eval/test_zno_nmt_core.py",
        "tests/ingest/test_esum_noise_filters.py",
        "tests/etymology/test_hallucination_detector.py",
        "tests/ci/test_typesafe_pr_triage.py",
    ],
)
def test_tests_that_do_not_use_delegate_are_not_dependents(
    real_graph: import_graph.ImportGraph, unrelated: str
) -> None:
    assert unrelated in real_graph.py
    assert unrelated not in real_graph.reverse_closure(["scripts/delegate.py"])
