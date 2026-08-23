#!/usr/bin/env python3
"""Build a slim dependency file, constrained by the repository lock, for changed pytest modules.

Use this helper only for CI's advisory changed-test fastlane. It maps
third-party imports reachable from selected tests through an explicit,
reviewed mapping; unknown imports fail closed instead of guessing a
distribution name. The required full pytest tier remains responsible for the
complete dependency set.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# Import roots whose distribution names do not follow a safe one-to-one rule
# are deliberately listed here rather than inferred. Keep this small and add a
# mapping with a regression test when a selected test needs a new dependency.
IMPORT_DISTRIBUTIONS = {
    "aiosqlite": "aiosqlite",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "fastapi": "fastapi",
    "filelock": "filelock",
    "httpx": "httpx",
    "huggingface_hub": "huggingface_hub",
    "jsonschema": "jsonschema",
    "referencing": "referencing",
    "lxml": "lxml",
    "mcp": "mcp",
    "numpy": "numpy",
    "PIL": "pillow",
    "pymorphy3": "pymorphy3",
    "pymorphy3_dicts_uk": "pymorphy3-dicts-uk",
    "pydantic": "pydantic",
    "pypdf": "pypdf",
    "psutil": "psutil",
    "pydantic": "pydantic",
    "pytest": "pytest",
    "rapidfuzz": "RapidFuzz",
    "requests": "requests",
    "ruamel": "ruamel.yaml",
    "starlette": "starlette",
    "tokenizers": "tokenizers",
    "uvicorn": "uvicorn",
    "yaml": "PyYAML",
}

# requirements-lock.txt predates the project's direct pyahocorasick declaration
# in requirements.txt. Keep its reviewed, exact fastlane pin explicit until the
# lock is regenerated as separate dependency maintenance.
EXPLICIT_REQUIREMENTS = {"ahocorasick": "pyahocorasick==2.3.1"}

# These modules must not inflate the normal fastlane profile merely because a
# slow-marked test imports them. The workflow retries only after pytest proves
# that selected, non-deselected work actually needs the live ML stack.
LIVE_MODEL_IMPORTS = frozenset({"stanza", "torch", "ukrainian_word_stress"})
_LOCK_LINE = re.compile(r"^([A-Za-z0-9_.-]+)==")
_NORMALIZE_NAME = re.compile(r"[-_.]+")


class RequirementSelectionError(RuntimeError):
    """Raised when a selected test has no reviewed dependency mapping."""


def canonical_name(name: str) -> str:
    """Return the PEP 503 comparison form without importing packaging."""
    return _NORMALIZE_NAME.sub("-", name).lower()


def import_roots(path: Path) -> set[str]:
    """Return absolute top-level imports from one Python test module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _imported_modules(path: Path, project_root: Path, *, module_level_only: bool = False) -> set[str]:
    """Return absolute module names imported by ``path`` for graph traversal."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    rel_path = path.resolve().relative_to(project_root.resolve())
    module_parts = rel_path.with_suffix("").parts
    package_parts = module_parts[:-1]

    nodes = ast.walk(tree)
    if module_level_only:

        class ModuleImports(ast.NodeVisitor):
            def __init__(self) -> None:
                self.nodes: list[ast.AST] = []

            def visit(self, node: ast.AST) -> None:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    return
                self.nodes.append(node)
                for child in ast.iter_child_nodes(node):
                    self.visit(child)

        visitor = ModuleImports()
        visitor.visit(tree)
        nodes = visitor.nodes

    for node in nodes:
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.level == 0:
            base_parts = tuple(node.module.split(".")) if node.module else ()
        else:
            trim = max(0, node.level - 1)
            base_parts = package_parts[: max(0, len(package_parts) - trim)]
            if node.module:
                base_parts += tuple(node.module.split("."))

        if base_parts:
            modules.add(".".join(base_parts))
        for alias in node.names:
            if alias.name != "*" and base_parts:
                modules.add(".".join((*base_parts, alias.name)))

    return modules


def _resolve_project_module(
    module: str,
    project_root: Path,
    *,
    importing_file: Path | None = None,
) -> Path | None:
    """Resolve a module name to a project Python file, if it is project-local.

    Script entry points can put their own directory on ``sys.path`` and use a
    flat import as the fallback for a package import. Include that directory
    when resolving a module reached from such a file so the fallback remains
    first-party instead of being treated as an unmapped dependency.
    """
    parts = tuple(part for part in module.split(".") if part)
    if not parts:
        return None

    relative = Path(*parts)
    candidates: list[Path] = []
    if importing_file is not None:
        candidates.extend(
            (
                importing_file.parent / relative.with_suffix(".py"),
                importing_file.parent / relative / "__init__.py",
            )
        )
    candidates.extend(
        (
            project_root / relative.with_suffix(".py"),
            project_root / relative / "__init__.py",
            project_root / "scripts" / relative.with_suffix(".py"),
            project_root / "scripts" / relative / "__init__.py",
        )
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _reachable_import_roots(test_paths: Iterable[Path], project_root: Path) -> set[str]:
    """Collect third-party roots from selected tests and reachable project modules."""
    initial_paths = {path.resolve() for path in test_paths}
    pending = [(path, True) for path in initial_paths]
    visited: set[Path] = set()
    roots: set[str] = set()

    while pending:
        path, is_initial_test = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        for module in _imported_modules(path, project_root, module_level_only=not is_initial_test):
            root = module.split(".", 1)[0]
            if root in LIVE_MODEL_IMPORTS or root == "__future__":
                continue
            resolved = _resolve_project_module(module, project_root, importing_file=path)
            if resolved is not None:
                pending.append((resolved, False))
            elif not is_project_import(root, project_root):
                roots.add(root)

    return roots


def read_lock(path: Path) -> dict[str, str]:
    """Read exact version pins from the lock file, keyed canonically."""
    requirements: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _LOCK_LINE.match(line)
        if match:
            requirements.setdefault(canonical_name(match.group(1)), line)
    return requirements


def read_requirements(path: Path) -> list[str]:
    """Read non-comment requirement lines while retaining their source order."""
    return [
        line for line in path.read_text(encoding="utf-8").splitlines() if line and not line.lstrip().startswith("#")
    ]


def is_project_import(root: str, project_root: Path) -> bool:
    """Whether a root can resolve from the repository or its scripts package."""
    candidates = (
        project_root / root,
        project_root / f"{root}.py",
        project_root / "scripts" / root,
        project_root / "scripts" / f"{root}.py",
    )
    return any(candidate.exists() for candidate in candidates)


def select_requirements(
    test_paths: Iterable[Path],
    *,
    base_requirements: Iterable[str],
    lock_requirements: dict[str, str],
    project_root: Path,
) -> list[str]:
    """Return the base profile plus pins for reviewed reachable test imports."""
    roots = _reachable_import_roots(test_paths, project_root)
    unknown: set[str] = set()
    additions: set[str] = set()

    for root in roots:
        if root in LIVE_MODEL_IMPORTS or root == "__future__":
            continue
        if requirement := EXPLICIT_REQUIREMENTS.get(root):
            additions.add(requirement)
            continue
        distribution = IMPORT_DISTRIBUTIONS.get(root)
        if distribution:
            requirement = lock_requirements.get(canonical_name(distribution))
            if requirement is None:
                raise RequirementSelectionError(
                    f"{root!r} maps to {distribution!r}, which is missing from requirements-lock.txt"
                )
            additions.add(requirement)
        elif root in sys.stdlib_module_names or is_project_import(root, project_root):
            continue
        else:
            unknown.add(root)

    if unknown:
        names = ", ".join(sorted(unknown))
        raise RequirementSelectionError(
            f"selected tests import unmapped third-party module(s): {names}; "
            "add a reviewed mapping instead of installing the full lock"
        )

    selected: list[str] = []
    for requirement in [*base_requirements, *sorted(additions, key=str.lower)]:
        if requirement not in selected:
            selected.append(requirement)
    return selected


def read_test_plan(path: Path) -> list[Path]:
    """Read the newline-delimited changed-test plan emitted by changed_tests.py."""
    return [Path(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=Path, required=True, help="newline-delimited selected test-module plan")
    parser.add_argument("--base", type=Path, required=True, help="checked-in slim requirements profile")
    parser.add_argument("--lock", type=Path, required=True, help="repository lock file supplying exact pins")
    parser.add_argument("--output", type=Path, required=True, help="generated requirements file for pip")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="repository root used to recognize local imports (default: current directory)",
    )
    args = parser.parse_args(argv)

    try:
        selected = select_requirements(
            [args.project_root / path for path in read_test_plan(args.tests)],
            base_requirements=read_requirements(args.base),
            lock_requirements=read_lock(args.lock),
            project_root=args.project_root,
        )
    except (OSError, RequirementSelectionError, SyntaxError) as exc:
        print(f"fastlane requirements failed: {exc}", file=sys.stderr)
        return 1

    args.output.write_text("\n".join(selected) + "\n", encoding="utf-8")
    print(f"fastlane slim requirements: {len(selected)} requirement(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
