"""Dependency-selection regressions and conservative failure boundaries."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci import test_impact as impact
from scripts.ci.classify_changes import SAFETY_NET, build_selected_candidates


def graph(sources):
    return impact.build_graph(sources=sources)


def test_sol_inbox_watch_case():
    root = Path(__file__).resolve().parents[1]
    paths = ["scripts/ai_agent_bridge/_inbox_watch.py", "tests/test_remote_supervisor.py"]
    result = graph({path: (root / path).read_bytes() for path in paths})
    assert "tests/test_remote_supervisor.py" in result.test_dependents([paths[0]])


@pytest.mark.parametrize("source", [
    "import scripts.pkg.target",
    "from scripts.pkg import target",
    "from scripts.pkg.target import VALUE",
    "import target",
    "from target import VALUE",
    "import pkg.target",
    "from pkg import target",
    "import sys\nsys.path.insert(0, 'scripts/pkg')\nimport target",
    "from pathlib import Path\nimport sys\nsys.path.append(Path(__file__).parent / 'scripts' / 'pkg')\nimport target",
    "from importlib import import_module as load\nload('scripts.pkg.target')",
    "import importlib as il\nil.import_module(name='scripts.pkg.target')",
    "__import__('scripts.pkg.target')",
    "import runpy as rp\nrp.run_module(mod_name='scripts.pkg.target')",
    "import runpy\nrunpy.run_path('scripts/pkg/target.py')",
    "from importlib.util import spec_from_file_location as spec\nspec('target', 'scripts/pkg/target.py')",
    "import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'scripts.pkg.target'])",
    "import subprocess, sys\nsubprocess.run([sys.executable, 'scripts/pkg/target.py'])",
    "COMMAND = 'python -m scripts.pkg.target --help'",
    "TARGET = 'scripts.pkg.target.VALUE'",
    "from pathlib import Path\nTARGET = Path('scripts') / 'pkg' / 'target.py'",
    "import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'pkg.target'])",
])
def test_imports_and_string_references(source):
    result = graph({"scripts/pkg/target.py": "VALUE = 1", "tests/test_consumer.py": source})
    selection = result.impacted_tests(["scripts/pkg/target.py"])
    assert selection == {"full_suite": False, "tests": ["tests/test_consumer.py"], "reasons": []}


def test_transitive_cycles_and_test_helpers():
    result = graph({
        "scripts/a.py": "import scripts.b",
        "scripts/b.py": "import scripts.a",
        "tests/helpers.py": "from scripts import a",
        "tests/test_use.py": "from tests.helpers import a",
        "tests/test_unrelated.py": "",
    })
    assert result.impacted_tests(["scripts/b.py"])["tests"] == ["tests/test_use.py"]


def test_relative_imports_and_package_initializers():
    result = graph({
        "scripts/__init__.py": "",
        "scripts/pkg/__init__.py": "from . import target",
        "scripts/pkg/target.py": "",
        "scripts/pkg/consumer.py": "from . import target",
        "tests/test_use.py": "from scripts.pkg import consumer",
    })
    for changed in ("scripts/__init__.py", "scripts/pkg/__init__.py", "scripts/pkg/target.py"):
        assert result.impacted_tests([changed])["tests"] == ["tests/test_use.py"]


def test_bare_name_collisions_select_all_possible_targets():
    result = graph({
        "scripts/one/target.py": "", "scripts/two/target.py": "",
        "tests/test_use.py": "import target",
    })
    for path in ("scripts/one/target.py", "scripts/two/target.py"):
        assert result.impacted_tests([path])["tests"] == ["tests/test_use.py"]


def test_transitive_import_through_local_src_layout_package():
    result = graph({
        "scripts/target.py": "",
        "packages/tool/src/tool/bridge.py": "import scripts.target",
        "tests/test_use.py": "from tool import bridge",
    })
    assert result.impacted_tests(["scripts/target.py"])["tests"] == ["tests/test_use.py"]


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module(target)",
    "import importlib as il\nil.import_module(name=target)",
    "from importlib import import_module as load\nload(target)",
    "__import__(target)",
    "from builtins import __import__ as load\nload(target)",
    "import runpy as rp\nrp.run_module(target)",
    "from runpy import run_path as load\nload(target)",
    "import pkgutil as pu\npu.walk_packages(paths)",
    "from pkgutil import resolve_name as load\nload(target)",
    "import importlib.util as util\nutil.spec_from_file_location('target', path)",
    "import importlib\nloader = importlib.import_module\nloader(target)",
    "loader = __import__\nloader(target)",
    "import subprocess\nsubprocess.run(command)",
    "import subprocess, sys\nsubprocess.run([sys.executable, '-m', target])",
    "import importlib\nimportlib.import_module('.target', package='scripts')",
    "import importlib as il\ngetattr(il, method)(target)",
    "getattr(obj, 'import_module')(target)",
    "exec(source)",
    "from importlib.machinery import SourceFileLoader\nSourceFileLoader('name', path)",
    "__import__('scripts', fromlist=names)",
    "from importlib import import_module as load\nload(target)\nfrom unrelated import function as load",
])
def test_nonliteral_import_anywhere_forces_full(source):
    result = graph({
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "scripts/unrelated.py": source,
    })
    selection = result.impacted_tests(["scripts/target.py"])
    assert selection["full_suite"]
    assert selection["reasons"]
    assert selection["tests"] == ["tests/test_use.py"]


def test_parse_error_anywhere_forces_full():
    result = graph({
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "tests/test_broken.py": "def broken(",
    })
    assert result.impacted_tests(["scripts/target.py"])["reasons"] == ["parse-error:tests/test_broken.py"]


def test_missing_changed_module_and_each_module_without_tests():
    result = graph({
        "scripts/target.py": "", "scripts/uncovered.py": "import scripts.target",
        "tests/test_use.py": "import scripts.target",
    })
    assert result.impacted_tests(["scripts/missing.py"])["full_suite"]
    assert result.impacted_tests(["scripts/target.py", "scripts/uncovered.py"])["full_suite"]
    assert result.impacted_tests([])["full_suite"]


def test_no_test_dependents_despite_script_importer():
    result = graph({"scripts/target.py": "", "scripts/consumer.py": "import scripts.target"})
    assert result.impacted_tests(["scripts/target.py"])["reasons"] == ["no-test-dependents:scripts/target.py"]


def test_scoped_conftest_and_literal_plugins():
    result = graph({
        "scripts/target.py": "", "tests/helpers/plugin.py": "import scripts.target",
        "tests/nested/conftest.py": "pytest_plugins = ['tests.helpers.plugin']",
        "tests/nested/test_use.py": "", "tests/test_outside.py": "",
    })
    assert result.impacted_tests(["scripts/target.py"])["tests"] == ["tests/nested/test_use.py"]


def test_root_conftest_reaches_every_test():
    result = graph({
        "scripts/target.py": "", "conftest.py": "from scripts import target",
        "tests/test_one.py": "", "tests/nested/test_two.py": "",
    })
    assert result.impacted_tests(["scripts/target.py"])["tests"] == [
        "tests/nested/test_two.py", "tests/test_one.py",
    ]


@pytest.mark.parametrize("source", [
    "pytest_plugins = plugins", "import scripts.missing",
    "import runpy\nrunpy.run_path('missing.py')", "from ... import target",
])
def test_unresolved_local_dependency_forces_full(source):
    result = graph({"scripts/target.py": "", "tests/test_use.py": source})
    assert result.impacted_tests(["scripts/target.py"])["full_suite"]


def test_public_query_and_repo_wide_safety_test():
    result = graph({
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "tests/test_invariant.py": "import pytest\npytestmark = pytest.mark.repo_wide",
    })
    assert result.safety_tests == {"tests/test_invariant.py"}
    assert impact.get_impacted_tests(["scripts/target.py"], graph=result)["tests"] == ["tests/test_use.py"]


def test_candidate_union_and_full_fallback_in_ci_suite():
    sources = {
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "tests/test_target_by_name.py": "", SAFETY_NET: "",
    }
    result = graph(sources)
    assert build_selected_candidates(["scripts/target.py"], sources, impact_graph=result) == [
        SAFETY_NET, "tests/test_target_by_name.py", "tests/test_use.py",
    ]
    sources["tests/test_dynamic.py"] = "__import__(module)"
    assert build_selected_candidates(["scripts/target.py"], sources, impact_graph=graph(sources)) is None


def test_build_budget_fails_closed(monkeypatch):
    clock = iter([0.0, 11.0, 11.0])
    monkeypatch.setattr(impact.time, "monotonic", lambda: next(clock))
    result = graph({"scripts/target.py": ""})
    assert "graph-build-budget-exceeded" in result.reasons


def test_parser_worker_failure_fails_closed(monkeypatch):
    def fail(item):
        raise RuntimeError("worker unavailable")

    monkeypatch.setattr(impact, "_scan_source", fail)
    assert graph({"scripts/target.py": ""}).reasons == ("parser-worker-error",)


def test_inventory_failure_fails_closed(monkeypatch):
    def fail(root):
        raise OSError("unavailable index")

    monkeypatch.setattr(impact, "read_sources", fail)
    assert impact.get_impacted_tests(["scripts/target.py"])["full_suite"]


def test_sources_include_sparse_blobs_unstaged_changes_and_new_modules(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, timeout=30)

    git("init", "-q")
    for path in ("scripts/target.py", "tests/test_use.py", "agents_extensions/helper.py"):
        current = tmp_path / path
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_text("VALUE = 1\n")
    git("add", ".")
    git("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    git("update-index", "--skip-worktree", "agents_extensions/helper.py")
    (tmp_path / "agents_extensions/helper.py").unlink()
    (tmp_path / "tests/test_use.py").write_text("import scripts.target\n")
    (tmp_path / "scripts/new.py").write_text("import scripts.target\n")
    sources = impact.read_sources(tmp_path)
    assert sources["agents_extensions/helper.py"] == b"VALUE = 1\n"
    assert sources["tests/test_use.py"] == b"import scripts.target\n"
    assert sources["scripts/new.py"] == b"import scripts.target\n"
    (tmp_path / "scripts/target.py").unlink()
    assert impact.build_graph(tmp_path).reasons == ("source-inventory-error",)


def test_full_repository_build_budget_and_sol_dependency():
    # Measure the production invocation separately from pytest tracing/coverage.
    # The subprocess is awaited, uses this test interpreter, and never runs tests.
    code = """
from scripts.ci.test_impact import BUILD_BUDGET_SECONDS, build_graph
result = build_graph()
assert result.build_seconds < BUILD_BUDGET_SECONDS, result.build_seconds
assert 'tests/test_remote_supervisor.py' in result.test_dependents(['scripts/ai_agent_bridge/_inbox_watch.py'])
print(f'graph_seconds={result.build_seconds:.3f}')
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_local_parser_pool_matches_in_process_graph():
    sources = {"scripts/target.py": "", "tests/test_use.py": "import scripts.target"}
    small = graph(sources)
    sources.update({f"scripts/filler_{index}.py": "" for index in range(40)})
    large = graph(sources)
    assert large.impacted_tests(["scripts/target.py"]) == small.impacted_tests(["scripts/target.py"])
