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
            self.current_function = None
            self.bindings = {}

        def resolve_expr(self, expr) -> str | None:
            if isinstance(expr, ast.Name):
                if expr.id in self.bindings:
                    return self.bindings[expr.id]
                if expr.id in ("import_module", "spec_from_file_location"):
                    return expr.id
            elif isinstance(expr, ast.Attribute):
                base_ref = self.resolve_expr(expr.value)
                if base_ref == "importlib" and expr.attr == "import_module":
                    return "import_module"
                if base_ref == "importlib" and expr.attr == "util":
                    return "importlib.util"
                if base_ref == "importlib.util" and expr.attr == "spec_from_file_location":
                    return "spec_from_file_location"

                # Fallback to literal matching
                if isinstance(expr.value, ast.Name):
                    if expr.value.id == "importlib" and expr.attr == "import_module":
                        return "import_module"
                    if expr.value.id == "importlib" and expr.attr == "util":
                        return "importlib.util"
                elif isinstance(expr.value, ast.Attribute) and isinstance(expr.value.value, ast.Name):
                    if expr.value.value.id == "importlib" and expr.value.attr == "util" and expr.attr == "spec_from_file_location":
                        return "spec_from_file_location"
            return None

        def visit_FunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.in_function += 1
            self.generic_visit(node)
            self.in_function -= 1
            self.current_function = old_func

        def visit_AsyncFunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.in_function += 1
            self.generic_visit(node)
            self.in_function -= 1
            self.current_function = old_func

        def visit_Import(self, node):
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name
                if name == "importlib":
                    self.bindings[asname] = "importlib"
                elif name == "importlib.util":
                    self.bindings[asname] = "importlib.util"
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
            module = node.module
            if module == "importlib":
                for alias in node.names:
                    name = alias.name
                    asname = alias.asname or name
                    if name == "import_module":
                        self.bindings[asname] = "import_module"
                    elif name == "util":
                        self.bindings[asname] = "importlib.util"
            elif module == "importlib.util":
                for alias in node.names:
                    name = alias.name
                    asname = alias.asname or name
                    if name == "spec_from_file_location":
                        self.bindings[asname] = "spec_from_file_location"
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

        def visit_Assign(self, node):
            value_ref = self.resolve_expr(node.value)
            if value_ref:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.bindings[target.id] = value_ref
            self.generic_visit(node)

        def visit_Call(self, node):
            func_name = self.resolve_expr(node.func)
            if func_name in ("import_module", "spec_from_file_location"):
                mod_name = path_to_module_name(file_path)
                loader_cfg = DYNAMIC_LOADERS.get(mod_name)
                if not loader_cfg:
                    failures.append(
                        f"Unregistered dynamic loader call '{func_name}' in module '{mod_name}' at {file_path}:{node.lineno}. "
                        "Register this module and its strategy in DYNAMIC_LOADERS."
                    )
                else:
                    matched = False
                    for call_spec in loader_cfg.get("calls", []):
                        if call_spec.get("func") == func_name and call_spec.get("caller") == self.current_function:
                            matched = True
                            break
                    if not matched:
                        failures.append(
                            f"Unregistered dynamic loader call '{func_name}' under function '{self.current_function}' "
                            f"in module '{mod_name}' at {file_path}:{node.lineno}. "
                            "Every call site must be explicitly registered under the module in DYNAMIC_LOADERS."
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


def test_main_import_with_optional_modules_absent():
    """Verify that scripts.api.main can be imported even when all optional modules are absent."""
    # Use a separate subprocess to ensure a clean import state
    harness_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})

# Mock all optional modules as absent
for mod in {OPTIONAL_MODULES!r}:
    sys.modules[mod] = None
    # Also block base package if there is a dot, except if it is "scripts"
    base = mod.split(".")[0]
    if base != "scripts":
        sys.modules[base] = None

try:
    import scripts.api.main
    sys.exit(0)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    result = subprocess.run(
        [sys.executable, "-c", harness_code],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Failed to import scripts.api.main with optional modules blocked:\\nStdout: {result.stdout}\\nStderr: {result.stderr}"


def test_meta_guard_catches_aliased_loader(tmp_path):
    """Verify that an aliased dynamic loader call in a synthetic module is detected and flagged."""
    synthetic_file = tmp_path / "synthetic_loader.py"
    synthetic_file.write_text(
        "from importlib import import_module as im\n"
        "def dynamic_func():\n"
        "    im('some_module')\n",
        encoding="utf-8"
    )

    harness_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})
from tests.api.test_import_pinning import check_file_imports
failures = check_file_imports(Path({str(synthetic_file)!r}))
if failures and any("Unregistered dynamic loader call" in f for f in failures):
    print("Detected unregistered call:", failures[0])
    sys.exit(0)
print("Failures detected:", failures)
sys.exit(1)
"""
    result = subprocess.run(
        [sys.executable, "-c", harness_code],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Alias check failed to flag unregistered loader call!\nStdout: {result.stdout}\nStderr: {result.stderr}"
