"""Conservative, execution-free Python import impact analysis.

Inventory, parse and resource failures force FULL globally. Runtime uncertainty
is scoped to the affected dependency closure; unrelated command runners do not
disable selection. Shell intermediaries participate without being executed.
This module does not enable selection in the full-suite workflow.
"""

from __future__ import annotations

import ast
import gc
import os
import re
import subprocess
import time
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import get_context
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
BUILD_BUDGET_SECONDS = 10.0
_REFERENCE = re.compile(r"(?:scripts|tests|agents_extensions)(?:[/.][A-Za-z_]\w*)+(?:\.py)?")
_BARE_REFERENCE = re.compile(r"[A-Za-z_]\w*(?:[/.][A-Za-z_]\w*)*(?:\.(?:py|sh))?")
_SHELL_REFERENCE = re.compile(r"(?:[A-Za-z_][\w-]*/)*[A-Za-z_][\w-]*\.sh\b")
_PYTHON_PATH = re.compile(r"(?:[A-Za-z_]\w*/)*[A-Za-z_]\w*\.py\b")
_MODULE_COMMAND = re.compile(r"(?:^|\s)[\"']?-m[\"']?\s+[\"']?([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)")
_LOADERS = {
    "__import__": (0, "name", False),
    "import_module": (0, "name", False),
    "run_module": (0, "mod_name", False),
    "run_path": (0, "path_name", True),
    "spec_from_file_location": (1, "location", True),
    "SourceFileLoader": (1, "path", True),
}


def is_test_file(path: str) -> bool:
    name = PurePosixPath(path).name
    return path.startswith("tests/") and name.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py")
    )


def read_sources(root: Path = ROOT) -> dict[str, bytes]:
    """Batch-read indexed blobs, including sparse files, with worktree overlays.

    Staged and unstaged source changes and untracked new modules participate.
    Missing non-sparse tracked sources fail closed rather than reusing old blobs.
    """
    index = subprocess.run(
        ["git", "ls-files", "--stage", "-z"], cwd=root, check=True,
        capture_output=True, timeout=BUILD_BUDGET_SECONDS,
    ).stdout
    entries: dict[str, str] = {}
    for entry in index.decode("utf-8", errors="surrogateescape").split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, sha, stage = meta.split()
        if stage != "0":
            raise ValueError("unmerged index")
        if path.endswith((".py", ".sh")):
            if mode not in {"100644", "100755"}:
                raise ValueError(f"non-regular source: {path}")
            entries[path] = sha
    sparse = subprocess.run(
        ["git", "ls-files", "-t", "-z"], cwd=root, check=True,
        capture_output=True, timeout=BUILD_BUDGET_SECONDS,
    ).stdout.decode("utf-8", errors="surrogateescape")
    skipped = {entry[2:] for entry in sparse.split("\0") if entry.startswith("S ")}
    sources = {}
    missing = {}
    for path, sha in entries.items():
        current = root / path
        if current.is_symlink():
            raise ValueError(f"non-regular source: {path}")
        if current.is_file():
            sources[path] = current.read_bytes()
        elif path not in skipped:
            raise ValueError(f"missing or non-regular source: {path}")
        else:
            missing[path] = sha
    # Present files are already authoritative overlays. Only sparse files need
    # blob reads, avoiding a second full copy of the repository's source bytes.
    if missing:
        batch = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=root, check=True,
            input="".join(sha + "\n" for sha in missing.values()).encode(),
            capture_output=True, timeout=BUILD_BUDGET_SECONDS,
        ).stdout
        offset = 0
        for path, sha in missing.items():
            end = batch.index(b"\n", offset)
            actual, kind, size = batch[offset:end].split()
            if actual.decode() != sha or kind != b"blob":
                raise ValueError("invalid source blob")
            offset = end + 1
            sources[path] = batch[offset:offset + int(size)]
            offset += int(size) + 1
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root,
        check=True, capture_output=True, timeout=BUILD_BUDGET_SECONDS,
    ).stdout.decode("utf-8", errors="surrogateescape")
    for path in untracked.split("\0"):
        if path.endswith((".py", ".sh")):
            current = root / path
            if current.is_symlink() or not current.is_file():
                raise ValueError(f"non-regular source: {path}")
            sources[path] = current.read_bytes()
    return sources


def _module(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".").removesuffix(".__init__")


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _name(node.value)
        return f"{base}.{node.attr}" if base else ""
    return ""


def _nodes(tree: ast.AST) -> Iterable[ast.AST]:
    """Visit dependencies and literals, avoiding millions of terminal AST leaves."""
    relevant = (ast.Import, ast.ImportFrom, ast.Constant, ast.Attribute, ast.Name, ast.Assign, ast.AnnAssign, ast.Call)
    pending = [tree]
    while pending:
        node = pending.pop()
        # Documentation can cite another executable without loading it. Skip
        # inert string expressions (including docstrings), not runtime values.
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                yield node
            continue
        if isinstance(node, ast.Name):
            yield node
            continue
        if isinstance(node, relevant) and (
            not isinstance(node, ast.Attribute) or node.attr in _LOADERS or node.attr == "repo_wide"
        ):
            yield node
        for child_field in node._fields:
            value = getattr(node, child_field)
            if isinstance(value, list):
                pending.extend(child for child in value if isinstance(child, ast.AST) and child._fields and not isinstance(child, ast.alias))
            elif isinstance(value, ast.AST) and value._fields:
                pending.append(value)


def _scan_source(item: tuple[str, bytes | str]) -> tuple:
    """Extract one file in a bounded local parser pool; return no AST objects."""
    path, source = item
    imports: set[tuple[str, bool]] = set()
    load_paths: set[str] = set()
    reasons: set[str] = set()
    safety = False
    test_source = is_test_file(path)

    if path.endswith(".sh"):
        text = source.decode("utf-8") if isinstance(source, bytes) else source
        text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#")).replace("\\\n", " ")
        # Retain references even in shell variable-prefixed paths. Resolution
        # checks the repository inventory, never the host filesystem or shell.
        for match in _PYTHON_PATH.finditer(text):
            reference = match.group()
            # $ROOT/scripts/... is a variable-prefixed repository path, not
            # a Python module named ROOT.scripts....
            local = _REFERENCE.search(reference)
            imports.add((local.group() if local else reference, False))
        imports.update((match.group(1), True) for match in _MODULE_COMMAND.finditer(text))
        load_paths.update(match.group() for match in _SHELL_REFERENCE.finditer(text))
        return path, imports, load_paths, reasons, safety

    def add(importer, name, *, required=False):
        imports.add((name, required))

    try:
        tree = ast.parse(source, filename=path)
    except (SyntaxError, ValueError, UnicodeError, RecursionError):
        reasons.add(f"parse-error:{path}")
        return path, imports, load_paths, reasons, safety
    groups: dict[type, list[ast.AST]] = defaultdict(list)
    for node in _nodes(tree):
        groups[type(node)].append(node)
    aliases: dict[str, str] = {}

    def bind(alias: str, name: str) -> None:
        previous = aliases.get(alias, name)
        if previous != name and any(
            target.split(".")[0] in {"importlib", "runpy", "pkgutil", "builtins"}
            or target.split(".")[-1] in _LOADERS for target in (previous, name)
        ):
            # Imports in separate scopes cannot overwrite a loader's identity
            # and thereby make an opaque call appear safe.
            reasons.add(f"ambiguous-loader-alias:{path}:{alias}")
        aliases[alias] = name

    for node in groups[ast.Import] + groups[ast.ImportFrom]:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bind(alias.asname or alias.name.split(".")[0], alias.name if alias.asname else alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bind(alias.asname or alias.name, f"{node.module}.{alias.name}")

    callees = {id(node.func) for node in groups[ast.Call]}
    # Most Name nodes are variables with no loading role. Filter them once,
    # after imports have bound loader aliases, instead of repeatedly examining
    # every variable through the full dependency decision tree.
    loader_names = set(_LOADERS) | {
        alias for alias, name in aliases.items() if name.split(".")[-1] in _LOADERS
    }
    groups[ast.Name] = [node for node in groups[ast.Name] if node.id in loader_names]
    assignments: dict[str, list[ast.AST]] = defaultdict(list)
    for node in groups[ast.Assign] + groups[ast.AnnAssign]:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and node.value is not None:
                assignments[target.id].append(node.value)

    def command_shell_paths(command: ast.AST | None) -> set[str]:
        """Follow argv constants and assigned Path components without executing."""
        refs: set[str] = set()
        pending = [command] if command is not None else []
        visited: set[int] = set()
        while pending:
            current = pending.pop()
            if id(current) in visited:
                continue
            visited.add(id(current))
            if isinstance(current, ast.Name):
                pending.extend(assignments.get(current.id, ()))
            elif isinstance(current, ast.Constant) and isinstance(current.value, str):
                if ".sh" in current.value:
                    refs.update(match.group() for match in _SHELL_REFERENCE.finditer(current.value))
                matches = _PYTHON_PATH.finditer(current.value) if ".py" in current.value else ()
                for match in matches:
                    reference = match.group()
                    local = _REFERENCE.search(reference)
                    imports.add((local.group() if local else reference, False))
            else:
                pending.extend(ast.iter_child_nodes(current))
        return refs

    nodes = (node for group in groups.values() for node in group)

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(path, alias.name, required=True)
        elif isinstance(node, ast.ImportFrom):
            package = _module(path).split(".")
            if not path.endswith("/__init__.py"):
                package.pop()
            if node.level > len(package):
                reasons.add(f"invalid-relative-import:{path}")
                continue
            base = package[:len(package) - node.level + 1] if node.level else []
            if node.module:
                base.extend(node.module.split("."))
            name = ".".join(base)
            add(path, name, required=True)
            for alias in node.names:
                add(path, f"{name}.{alias.name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # String candidates resolve only to actual repository modules in
            # build_graph, with stricter rules than genuine import statements.
            # Production file-path data (e.g. a scope allowlist) does not load
            # that module. Path-based execution is captured at loader/command
            # calls; tests additionally use paths to copy/load source fixtures.
            path_reference = test_source or "/" not in node.value
            if path_reference and len(node.value) <= 256 and ("." in node.value or "/" in node.value) and _BARE_REFERENCE.fullmatch(node.value):
                add(path, node.value)
            if path_reference and len(node.value) <= 256 and node.value.endswith(".py"):
                add(path, PurePosixPath(node.value).name)
            # Tests also copy/read shell fixtures before executing them. In
            # production code, executable shell references come from command
            # expressions below, not arbitrary help text or lint registries.
            if test_source and ".sh" in node.value and _SHELL_REFERENCE.fullmatch(node.value):
                load_paths.add(node.value)
            matches = _REFERENCE.finditer(node.value) if any(
                prefix in node.value for prefix in ("scripts", "tests", "agents_extensions")
            ) else ()
            for match in matches:
                reference = match.group()
                if "/" in reference and not test_source:
                    continue
                add(path, reference)
                # String monkeypatch targets can append a symbol to a module.
                while "." in reference and not reference.endswith(".py"):
                    reference = reference.rsplit(".", 1)[0]
                    add(path, reference)
        elif isinstance(node, (ast.Attribute, ast.Name)):
            if isinstance(node, ast.Attribute) and node.attr == "repo_wide" and test_source:
                safety = True
            if isinstance(node, ast.Attribute) and node.attr not in _LOADERS:
                continue
            if isinstance(node, ast.Name) and aliases.get(node.id, node.id).split(".")[-1] not in _LOADERS:
                continue
            name = _name(node)
            first, _, rest = name.partition(".")
            name = aliases.get(first, first) + ("." + rest if rest else "")
            if name.split(".")[-1] in _LOADERS and id(node) not in callees:
                reasons.add(f"indirect-import-loader:{path}:{node.lineno}")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in targets):
                value = node.value
                values = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
                if not all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in values):
                    reasons.add(f"nonliteral-pytest-plugins:{path}")
                else:
                    for item in values:
                        add(path, item.value, required=True)
        elif isinstance(node, ast.Call):
            name = _name(node.func)
            first, _, rest = name.partition(".")
            name = aliases.get(first, first) + ("." + rest if rest else "")
            leaf = name.split(".")[-1]
            if leaf in {"eval", "exec"} or (leaf == "getattr" and node.args and (
                _name(node.args[0]).split(".")[0] in {
                    key for key, value in aliases.items()
                    if value.split(".")[0] in {"importlib", "runpy", "pkgutil", "builtins"}
                }
                or (len(node.args) > 1 and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in _LOADERS)
            )):
                reasons.add(f"dynamic-import:{path}:{node.lineno}")
            if name.startswith("pkgutil."):
                reasons.add(f"dynamic-import:{path}:{node.lineno}")
            if name in {
                "subprocess.run", "subprocess.Popen", "subprocess.call",
                "subprocess.check_call", "subprocess.check_output",
                "subprocess.getoutput", "subprocess.getstatusoutput", "os.system", "os.popen",
                "asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell",
            }:
                argv = node.args[0] if node.args else next((kw.value for kw in node.keywords if kw.arg == "args"), None)
                load_paths.update(command_shell_paths(argv))
                # Arguments to git and other known non-Python executables do
                # not become opaque Python loads merely by using variables.
                # Literal module/script targets remain resolvable even when
                # later command arguments are dynamic.
                args = argv.elts if isinstance(argv, (ast.List, ast.Tuple)) else []
                executable = args[0] if args else None
                literal = executable.value if isinstance(executable, ast.Constant) else None
                python = _name(executable) in {"sys.executable", "sys._base_executable"} or (
                    isinstance(literal, str) and PurePosixPath(literal).name.startswith("python")
                )
                if python:
                    target = args[2] if len(args) > 2 and isinstance(args[1], ast.Constant) and args[1].value == "-m" else (
                        args[1] if len(args) > 1 else None
                    )
                    if not isinstance(target, ast.Constant) or not isinstance(target.value, str):
                        reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
                elif not isinstance(literal, str):
                    reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
            if leaf not in _LOADERS:
                continue
            index, keyword, is_path = _LOADERS[leaf]
            target = node.args[index] if len(node.args) > index else next(
                (kw.value for kw in node.keywords if kw.arg == keyword), None,
            )
            if not isinstance(target, ast.Constant) or not isinstance(target.value, str):
                reasons.add(f"dynamic-import:{path}:{node.lineno}")
            elif target.value.startswith("."):
                # A runtime package parameter cannot be inferred from the caller.
                reasons.add(f"relative-runtime-import:{path}:{node.lineno}")
            elif is_path:
                load_paths.add(target.value)
            else:
                add(path, target.value, required=True)
            if leaf == "__import__":
                fromlist = node.args[3] if len(node.args) > 3 else next(
                    (kw.value for kw in node.keywords if kw.arg == "fromlist"), None,
                )
                if fromlist is not None and not (
                    isinstance(fromlist, (ast.List, ast.Tuple))
                    and all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in fromlist.elts)
                ):
                    reasons.add(f"dynamic-import:{path}:{node.lineno}")

    return path, imports, load_paths, reasons, safety


@dataclass
class ImportGraph:
    dependents: dict[str, set[str]]
    tests: set[str]
    safety_tests: set[str]
    reasons: tuple[str, ...]
    build_seconds: float
    uncertainty: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def reached_files(self, changed: Iterable[str]) -> set[str]:
        """Reverse transitive closure, including shell and test helpers."""
        visited = set(changed)
        pending = deque(visited)
        while pending:
            for importer in self.dependents.get(pending.popleft(), ()):
                if importer not in visited:
                    visited.add(importer)
                    pending.append(importer)
        return visited

    def test_dependents(self, changed: Iterable[str]) -> set[str]:
        """Return tests in the dependency closure."""
        return self.reached_files(changed) & self.tests

    def selection_reasons(self, paths: Iterable[str]) -> list[str]:
        """Scope uncertainty to affected sources, including changed tests.

        Already selected tests and their support files execute opaque loads. Those
        calls cannot introduce additional test importers of the changed source.
        An opaque load in a changed test itself still fails closed.
        """
        changed = set(paths)
        return sorted(set(self.reasons).union(*(
            self.uncertainty.get(path, ()) for path in self.reached_files(changed)
            if not path.startswith("tests/") or path in changed
        )))

    def impacted_tests(self, changed: Iterable[str]) -> dict:
        """FULL on affected uncertainty or a changed module without tests."""
        paths = sorted(set(changed))
        reasons = self.selection_reasons(paths)
        for path in paths:
            if path not in self.dependents:
                reasons.append(f"missing-module:{path}")
            elif not self.test_dependents([path]):
                reasons.append(f"no-test-dependents:{path}")
        if not paths:
            reasons.append("no-changed-modules")
        return {
            "full_suite": bool(reasons),
            "tests": sorted(self.test_dependents(paths)),
            "reasons": sorted(set(reasons)),
        }


def build_graph(root: Path = ROOT, *, sources: Mapping[str, bytes | str] | None = None) -> ImportGraph:
    """Index all local Python modules without importing or executing any source.

    Bare names resolve against every matching local module suffix: ambiguous sys.path
    precedence increases selection rather than discarding possible importers.
    Regular package initializers, scoped conftests and literal pytest plugins
    contribute edges too. Parse and I/O failures are terminal FULL reasons.
    """
    started = time.monotonic()
    reasons: set[str] = set()
    if sources is None:
        try:
            sources = read_sources(root)
        except (OSError, ValueError, subprocess.SubprocessError):
            return ImportGraph({}, set(), set(), ("source-inventory-error",), time.monotonic() - started)
    modules: dict[str, set[str]] = defaultdict(set)
    shell_paths: dict[str, set[str]] = defaultdict(set)
    namespaces: set[str] = set()
    for path in sources:
        if path.endswith(".sh"):
            parts = path.split("/")
            for index in range(len(parts)):
                shell_paths["/".join(parts[index:])].add(path)
            continue
        name = _module(path)
        modules[name].add(path)
        parts = name.split(".")
        for index in range(1, len(parts)):
            namespaces.add(".".join(parts[:index]))
        # Also retain src-layout packages and test helpers exposed by sys.path.
        # Without a proven path precedence, every matching suffix is possible.
        for index in range(1, len(parts)):
            modules[".".join(parts[index:])].add(path)
    dependents: dict[str, set[str]] = {path: set() for path in sources}
    tests = {path for path in sources if is_test_file(path)}
    safety_tests: set[str] = set()
    uncertainty: dict[str, set[str]] = defaultdict(set)
    # Package ancestors depend only on inventory, not on each reference. Many
    # files repeat the same imports; compute these once rather than per edge.
    package_parents: dict[str, set[str]] = {}
    for path in sources:
        parts = _module(path).split(".")
        package_parents[path] = {
            parent for index in range(1, len(parts))
            for parent in modules.get(".".join(parts[:index]), ())
            if parent.endswith("/__init__.py")
        }

    def add(importer: str, name: str, *, required: bool = False) -> None:
        # Bare words such as 'main', 'config' and 'test' are ordinary data,
        # not evidence of an import through an arbitrary sys.path suffix.
        if not required and "." not in name and "/" not in name:
            return
        name = name.removesuffix(".py").replace("/", ".")
        targets = modules.get(name, set())
        if not targets and required and name.startswith(("scripts.", "tests.", "agents_extensions.")) and name not in namespaces:
            uncertainty[importer].add(f"unresolved-import:{importer}:{name}")
        for target in targets:
            dependents[target].add(importer)
            # Importing a submodule executes regular parent packages.
            for parent in package_parents[target]:
                dependents[parent].add(importer)

    # Largest files first avoid a long final parser chunk on this repository's
    # uneven source sizes. Cap workers at available CPUs and eight processes.
    items = sorted(sources.items(), key=lambda item: len(item[1]), reverse=True)
    workers = min(8, os.cpu_count() or 1)
    # Bounded local CPU workers, no provider calls or source execution.
    # Small fixture graphs stay in-process; large graphs return compact records.
    try:
        if len(items) > 32:
            # ASTs have no parent cycles. Refcounting reclaims each file's AST;
            # avoid repeated cyclic-GC traversals in these short-lived workers.
            with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("fork"), initializer=gc.disable) as executor:
                records = list(executor.map(_scan_source, items, chunksize=4))
        else:
            records = [_scan_source(item) for item in items]
    except (OSError, RuntimeError, ValueError):
        return ImportGraph(dependents, tests, set(), ("parser-worker-error",), time.monotonic() - started)
    for path, imports, load_paths, errors, safety in records:
        for error in errors:
            if error.startswith("parse-error:"):
                reasons.add(error)
            else:
                uncertainty[path].add(error)
        if safety:
            safety_tests.add(path)
        for name, required in imports:
            add(path, name, required=required)
        for target in load_paths:
            if target.endswith(".sh"):
                parts = target.split("/")
                targets = next((
                    shell_paths[suffix] for index in range(len(parts))
                    if (suffix := "/".join(parts[index:])) in shell_paths
                ), ())
                for shell in targets:
                    if shell != path:
                        dependents[shell].add(path)
            elif target not in sources:
                uncertainty[path].add(f"unresolved-load-path:{path}:{target}")
            else:
                dependents[target].add(path)

    # Conftests are implicitly imported for all tests in their directory subtree.
    for path in sources:
        if PurePosixPath(path).name == "conftest.py":
            prefix = str(PurePosixPath(path).parent)
            for test in tests:
                if prefix == "." or test.startswith(prefix + "/"):
                    dependents[path].add(test)
    elapsed = time.monotonic() - started
    if elapsed >= BUILD_BUDGET_SECONDS:
        reasons.add("graph-build-budget-exceeded")
    return ImportGraph(
        dependents, tests, safety_tests, tuple(sorted(reasons)), elapsed,
        {path: tuple(sorted(errors)) for path, errors in uncertainty.items()},
    )


def get_impacted_tests(changed_files: Iterable[str], *, root: Path = ROOT, graph: ImportGraph | None = None) -> dict:
    """Public fail-closed query; callers may share a graph within one invocation."""
    return (graph if graph is not None else build_graph(root)).impacted_tests(changed_files)
