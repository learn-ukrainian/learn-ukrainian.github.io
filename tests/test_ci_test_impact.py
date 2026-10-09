"""Dependency-selection regressions and conservative failure boundaries."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci import test_impact as impact
from scripts.ci.classify_changes import SAFETY_NET, SELECTED_CANDIDATE_CEILING, build_selected_candidates


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
def test_uncertainty_is_scoped_to_reached_sources(source):
    result = graph({
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "scripts/unrelated.py": source,
    })
    selection = result.impacted_tests(["scripts/target.py"])
    assert not selection["full_suite"]
    assert not selection["reasons"]
    assert selection["tests"] == ["tests/test_use.py"]
    # Once the uncertain source imports the changed module, uncertainty is
    # relevant even if that source has no separately named test of its own.
    result = graph({
        "scripts/target.py": "", "tests/test_use.py": "import scripts.target",
        "scripts/consumer.py": "import scripts.target\n" + source,
    })
    assert result.impacted_tests(["scripts/target.py"])["full_suite"]


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
    assert result.impacted_tests(["tests/test_use.py"])["full_suite"]


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
    sources["scripts/consumer.py"] = "import scripts.target\n__import__(module)"
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
from scripts.ci.classify_changes import SELECTED_CANDIDATE_CEILING, build_selected_candidates
result = build_graph()
assert result.build_seconds < BUILD_BUDGET_SECONDS, result.build_seconds
changed = ['scripts/ai_agent_bridge/_inbox_watch.py']
selection = result.impacted_tests(changed)
assert not selection['full_suite'], (len(selection['reasons']), selection['reasons'][:5])
candidates = build_selected_candidates(changed, result.dependents, impact_graph=result)
assert candidates is not None
assert 'tests/test_remote_supervisor.py' in candidates
assert result.safety_tests <= set(candidates)
assert len(candidates) < SELECTED_CANDIDATE_CEILING
assert len(candidates) < len(result.tests)
assert {'tests/test_git_hooks.py', 'tests/test_assert_primary_on_main.py'} <= result.test_dependents(
    ['scripts/guardrails/assert_primary_on_main.py']
)
print(f'graph_seconds={result.build_seconds:.3f}')
print(f'selected={len(candidates)} total={len(result.tests)} safety={len(result.safety_tests)}')
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout.strip())


def test_safety_baseline_fits_but_ceiling_still_applies():
    sources = {"scripts/target.py": "", "tests/test_use.py": "import scripts.target", SAFETY_NET: ""}
    sources.update({
        f"tests/test_safety_{index}.py": "import pytest\npytestmark = pytest.mark.repo_wide"
        for index in range(87)
    })
    selected = build_selected_candidates(["scripts/target.py"], sources, impact_graph=graph(sources))
    assert selected is not None
    assert len(selected) == 89
    sources.update({
        f"tests/test_consumer_{index}.py": "import scripts.target"
        for index in range(SELECTED_CANDIDATE_CEILING)
    })
    assert build_selected_candidates(["scripts/target.py"], sources, impact_graph=graph(sources)) is None


def test_ordinary_bare_strings_do_not_link_suffix_modules():
    result = graph({
        "scripts/pkg/main.py": "", "scripts/pkg/config.py": "",
        "tests/test_words.py": "WORDS = ['main', 'config', 'missing.module']",
        "tests/test_use.py": "import scripts.pkg.main",
    })
    assert result.test_dependents(["scripts/pkg/main.py"]) == {"tests/test_use.py"}
    assert not result.test_dependents(["scripts/pkg/config.py"])
    assert not result.uncertainty


def test_docstrings_do_not_create_import_or_shell_edges():
    result = graph({
        "scripts/target.py": "", "scripts/hook.sh": '"$PY" scripts/target.py',
        "scripts/consumer.py": '"""Mirrors scripts.target and hook.sh."""',
        "tests/test_use.py": "import scripts.target",
    })
    assert result.test_dependents(["scripts/target.py"]) == {"tests/test_use.py"}
    assert not result.dependents["scripts/hook.sh"]


@pytest.mark.parametrize("source", [
    "import subprocess\nsubprocess.run(['git', *args])",
    "import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'scripts.target', value])",
])
def test_known_commands_with_dynamic_arguments_do_not_force_full(source):
    result = graph({
        "scripts/target.py": "", "scripts/consumer.py": source,
        "tests/test_use.py": "import scripts.target",
    })
    assert not result.impacted_tests(["scripts/target.py"])["full_suite"]


def test_selected_tests_can_execute_their_opaque_loads():
    result = graph({
        "scripts/target.py": "",
        "tests/test_use.py": "import scripts.target\n__import__(name)",
    })
    assert result.impacted_tests(["scripts/target.py"])["tests"] == ["tests/test_use.py"]
    assert not result.impacted_tests(["scripts/target.py"])["full_suite"]
    assert result.impacted_tests(["tests/test_use.py"])["full_suite"]


def test_selected_test_support_can_execute_opaque_loads():
    result = graph({
        "scripts/target.py": "",
        "tests/helpers.py": "import scripts.target\n__import__(name)",
        "tests/test_use.py": "import tests.helpers",
    })
    selection = result.impacted_tests(["scripts/target.py"])
    assert not selection["full_suite"]
    assert selection["tests"] == ["tests/test_use.py"]
    assert result.impacted_tests(["tests/helpers.py"])["full_suite"]


@pytest.mark.parametrize("command", [
    '"$PY" -m scripts.pkg.module',
    '"$PY" "-m" "scripts.pkg.module"',
    '"$PY" -m \\\n scripts.pkg.module',
])
def test_shell_intermediaries_include_python_paths_modules_and_sourced_scripts(command):
    result = graph({
        "scripts/pkg/target.py": "", "scripts/pkg/module.py": "",
        "scripts/hook.sh": '"$PY" "$ROOT/scripts/pkg/target.py"\nsource "$ROOT/scripts/nested.sh"',
        "scripts/nested.sh": command,
        "tests/test_hook.py": "from pathlib import Path\nHOOK = Path('scripts') / 'hook.sh'",
        "tests/test_outside.py": "",
    })
    for changed in ("scripts/pkg/target.py", "scripts/pkg/module.py"):
        assert result.impacted_tests([changed])["tests"] == ["tests/test_hook.py"]


def test_shell_comments_do_not_create_edges():
    result = graph({
        "scripts/target.py": "", "scripts/hook.sh": "# tests/test_use.py covers this hook\nexit 0",
        "tests/test_use.py": "import scripts.target\nHOOK = 'scripts/hook.sh'",
    })
    assert not result.dependents["tests/test_use.py"]


def test_python_shell_commands_follow_assignments_but_not_documentation():
    result = graph({
        "scripts/target.py": "", "scripts/hook.sh": '"$PY" scripts/target.py',
        "scripts/consumer.py": (
            "from pathlib import Path\nimport subprocess\n"
            "hook = Path('scripts') / 'hook.sh'\ncommand = ['bash', str(hook)]\n"
            "subprocess.run(command)"
        ),
        "scripts/documentation.py": "HELP = 'scripts/hook.sh'",
        "tests/test_use.py": "import scripts.consumer",
    })
    assert result.test_dependents(["scripts/target.py"]) == {"tests/test_use.py"}
    assert "scripts/documentation.py" not in result.dependents["scripts/hook.sh"]


def test_production_path_data_is_not_a_load_but_python_argv_is():
    result = graph({
        "scripts/target.py": "",
        "scripts/scope.py": "PATHS = {'scripts/target.py': 'allowed path'}",
        "scripts/consumer.py": (
            "import subprocess, sys\nsubprocess.run([sys.executable, 'scripts/target.py', value])"
        ),
        "tests/test_use.py": "import scripts.consumer",
    })
    assert "scripts/scope.py" not in result.dependents["scripts/target.py"]
    assert result.impacted_tests(["scripts/target.py"])["tests"] == ["tests/test_use.py"]


def test_local_parser_pool_matches_in_process_graph():
    sources = {"scripts/target.py": "", "tests/test_use.py": "import scripts.target"}
    small = graph(sources)
    sources.update({f"scripts/filler_{index}.py": "" for index in range(40)})
    large = graph(sources)
    assert large.impacted_tests(["scripts/target.py"]) == small.impacted_tests(["scripts/target.py"])
