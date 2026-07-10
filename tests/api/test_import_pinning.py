"""Guard tests for API import pinning and dynamic loading correctness."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.preload import DYNAMIC_LOADERS, OPTIONAL_MODULES, PRELOAD_MODULES


def resolve_import_names(node: ast.Import | ast.ImportFrom, file_path: Path) -> list[str]:
    """Resolve the imported module names, handling relative imports."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if node.level > 0:
        # Relative import resolution
        parts = file_path.resolve().parts
        try:
            scripts_idx = parts.index("scripts")
            rel_parts = parts[scripts_idx:]
        except ValueError:
            rel_parts = ("scripts", "api", file_path.name)

        mod_parts = list(rel_parts[:-1])
        for _ in range(node.level - 1):
            if mod_parts:
                mod_parts.pop()

        base_mod = ".".join(mod_parts)
        if node.module:
            return [f"{base_mod}.{node.module}"]
        return [base_mod]

    return [node.module] if node.module else []

def path_to_module_name(file_path: Path) -> str:
    """Convert file path to module path relative to scripts/."""
    parts = file_path.resolve().parts
    try:
        idx = parts.index("scripts")
        mod_parts = parts[idx:]
    except ValueError:
        return f"scripts.api.{file_path.stem}"

    # Remove .py from the last part
    stem = file_path.stem
    mod_parts = [*list(mod_parts[:-1]), stem]
    return ".".join(mod_parts)

def is_dynamic_import_call(node: ast.Call) -> str | None:
    """Detect if a call is an importlib.import_module or spec_from_file_location call."""
    func = node.func
    if isinstance(func, ast.Name):
        if func.id in ("import_module", "spec_from_file_location"):
            return func.id
    elif isinstance(func, ast.Attribute) and func.attr in ("import_module", "spec_from_file_location"):
        return func.attr
    return None

def check_file_imports(file_path: Path) -> list[str]:
    """Scan a file for function-level imports and unregistered dynamic loader calls.

    Returns a list of error messages.
    """
    failures = []
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        return [f"Syntax error in {file_path}: {e}"]

    lines = content.splitlines()

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.in_function = 0

        def visit_FunctionDef(self, node):
            self.in_function += 1
            self.generic_visit(node)
            self.in_function -= 1

        def visit_AsyncFunctionDef(self, node):
            self.in_function += 1
            self.generic_visit(node)
            self.in_function -= 1

        def visit_Import(self, node):
            if self.in_function > 0:
                line_text = lines[node.lineno - 1]
                if "# lazy-ok:" not in line_text:
                    modules = resolve_import_names(node, file_path)
                    for mod in modules:
                        if mod not in PRELOAD_MODULES and mod not in OPTIONAL_MODULES:
                            failures.append(
                                f"Uncovered nested import '{mod}' in {file_path}:{node.lineno}. "
                                "Add it to PRELOAD_MODULES/OPTIONAL_MODULES or exempt it with '# lazy-ok: <reason>'."
                            )
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if self.in_function > 0:
                line_text = lines[node.lineno - 1]
                if "# lazy-ok:" not in line_text:
                    modules = resolve_import_names(node, file_path)
                    for mod in modules:
                        # Allow matching either the parent module or the full module path
                        if mod not in PRELOAD_MODULES and mod not in OPTIONAL_MODULES:
                            failures.append(
                                f"Uncovered nested import '{mod}' in {file_path}:{node.lineno}. "
                                "Add it to PRELOAD_MODULES/OPTIONAL_MODULES or exempt it with '# lazy-ok: <reason>'."
                            )
            self.generic_visit(node)

        def visit_Call(self, node):
            func_name = is_dynamic_import_call(node)
            if func_name:
                mod_name = path_to_module_name(file_path)
                if mod_name not in DYNAMIC_LOADERS:
                    failures.append(
                        f"Unregistered dynamic loader call '{func_name}' in module '{mod_name}' at {file_path}:{node.lineno}. "
                        "Register this module and its strategy in DYNAMIC_LOADERS."
                    )
            self.generic_visit(node)

    Visitor().visit(tree)
    return failures

def test_ast_imports_and_loaders():
    """Scan all scripts/api/**/*.py files for uncovered nested static/dynamic imports."""
    api_dir = Path(__file__).resolve().parents[2] / "scripts" / "api"
    assert api_dir.exists(), f"API directory does not exist: {api_dir}"

    all_failures = []
    for root, _, files in os.walk(api_dir):
        for file in files:
            if file.endswith(".py") and file != "preload.py":
                path = Path(root) / file
                all_failures.extend(check_file_imports(path))

    if all_failures:
        print("\nAST Import Check Failures:", file=sys.stderr)
        for fail in all_failures:
            print(f"  - {fail}", file=sys.stderr)
        raise AssertionError(f"Found {len(all_failures)} import pinning violation(s).")

def test_lifespan_preload():
    """Boot the FastAPI app and verify that preloaded modules exist in sys.modules."""
    with TestClient(app) as _:
        # Assert registry modules are in sys.modules
        for mod in PRELOAD_MODULES:
            assert mod in sys.modules, f"Preloaded module '{mod}' is missing from sys.modules!"

        # Verify that optional modules that exist are also loaded
        for mod in OPTIONAL_MODULES:
            try:
                # If it's importable in the env, it must be loaded in sys.modules
                __import__(mod)
                # Check base module or submodules
                assert mod in sys.modules, f"Optional module '{mod}' is importable but not in sys.modules!"
            except ImportError:
                pass

def test_meta_guard_fails(tmp_path):
    """Verify that a synthetic module with an uncovered lazy import fails the AST check."""
    synthetic_file = tmp_path / "synthetic_module.py"
    synthetic_file.write_text(
        "def test_func():\n"
        "    import some_uncovered_lazy_module_xyz\n",
        encoding="utf-8"
    )

    # We invoke check_file_imports in a separate process to verify it fails
    harness_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})
from tests.api.test_import_pinning import check_file_imports
failures = check_file_imports(Path({str(synthetic_file)!r}))
if failures:
    print("Detected failure:", failures[0])
    sys.exit(1)
sys.exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", harness_code],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "AST check did not fail for synthetic uncovered import!"
    assert "some_uncovered_lazy_module_xyz" in result.stdout or "some_uncovered_lazy_module_xyz" in result.stderr
