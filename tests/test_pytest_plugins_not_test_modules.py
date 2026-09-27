"""Test modules must not load other collected test modules as plugins.

``pytest_plugins = ("test_other",)`` only publishes that module's fixtures when
the named file is imported as a plugin and not also collected on the same xdist
worker. Shard placement decides which files share a worker, so the suite then
passes or fails depending on the duration file. Share fixtures through a
``conftest.py`` or a helper whose name does not match ``test_*.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.repo_wide

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"


def _import_time_nodes(nodes: list[ast.stmt]) -> list[ast.stmt]:
    found: list[ast.stmt] = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        found.append(node)
        body = getattr(node, "body", None)
        if isinstance(body, list):
            found.extend(_import_time_nodes(body))
        orelse = getattr(node, "orelse", None)
        if isinstance(orelse, list):
            found.extend(_import_time_nodes(orelse))
    return found


def _plugin_names(value: ast.expr) -> list[str] | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return [part.strip() for part in value.value.split(",") if part.strip()]
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        names: list[str] = []
        for element in value.elts:
            if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                return None
            names.append(element.value)
        return names
    return None


def _declared_plugins(tree: ast.AST) -> list[str] | None:
    if not isinstance(tree, ast.Module):
        return []
    names: list[str] = []
    for node in _import_time_nodes(tree.body):
        value: ast.expr | None = None
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in targets):
            continue
        parsed = _plugin_names(value)
        if parsed is None:
            return None
        names.extend(parsed)
    return names


def cross_module_pytest_plugin_violations(tests_root: Path) -> list[str]:
    """Return ``path: plugin`` rows for test modules that plugin-load another test module."""
    test_files = sorted(
        path
        for path in tests_root.rglob("test_*.py")
        if path.is_file() and path.name.startswith("test_") and "__pycache__" not in path.parts
    )
    stems = {path.stem for path in test_files}
    relative = {path.relative_to(tests_root).as_posix() for path in test_files}
    violations: list[str] = []
    for path in test_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        plugins = _declared_plugins(tree)
        display = path.relative_to(tests_root).as_posix()
        if plugins is None:
            violations.append(f"{display}: non-literal pytest_plugins")
            continue
        for plugin in plugins:
            dotted = plugin.replace(".", "/") + ".py"
            stem = plugin.rsplit(".", 1)[-1]
            if dotted in relative or (stem.startswith("test_") and stem in stems):
                violations.append(f"{display}: {plugin}")
    return violations


def test_checker_flags_a_pytest_plugins_name_that_is_a_collected_test_module(tmp_path: Path) -> None:
    """Negative case: a sibling ``test_*.py`` named from ``pytest_plugins`` is a violation."""
    (tmp_path / "test_provider.py").write_text("def test_provider() -> None:\n    pass\n", encoding="utf-8")
    (tmp_path / "test_consumer.py").write_text(
        'pytest_plugins = ("test_provider",)\n',
        encoding="utf-8",
    )
    (tmp_path / "test_string_form.py").write_text(
        'pytest_plugins = "test_provider"\n',
        encoding="utf-8",
    )
    (tmp_path / "test_allowed.py").write_text(
        'pytest_plugins = ("pytester", "_v4_shared_runtime_fixtures")\n',
        encoding="utf-8",
    )
    assert cross_module_pytest_plugin_violations(tmp_path) == [
        "test_consumer.py: test_provider",
        "test_string_form.py: test_provider",
    ]


def test_collected_test_modules_do_not_load_other_test_modules_as_plugins() -> None:
    violations = cross_module_pytest_plugin_violations(_TESTS_ROOT)
    assert not violations, (
        "pytest_plugins in a collected test module names another collected test module. "
        "Move the shared fixtures to a conftest.py or a helper that is not test_*.py:\n" + "\n".join(violations)
    )
