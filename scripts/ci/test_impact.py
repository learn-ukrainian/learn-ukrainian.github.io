"""Conservative, execution-free Python import impact analysis.

Inventory, parse and resource failures force FULL globally. Opaque runtime
loads conservatively select every test that can reach the loading file.
Shell intermediaries participate without being executed.
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
from contextlib import suppress
from dataclasses import dataclass, field
from multiprocessing import get_context
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
_MAX_PARSER_WORKERS = 8


def _build_budget_seconds(cpu_count: int | None) -> float:
    """Keep the eight-worker 10-second allowance on smaller CI runners.

    Parsing is CPU-bound. Two-core runners receive 40 seconds rather than
    being judged against the throughput of the eight-worker development pool.
    The elapsed-time guard still forces FULL when this bounded limit is hit.
    """
    return 10.0 * _MAX_PARSER_WORKERS / min(_MAX_PARSER_WORKERS, max(1, cpu_count or 1))


def _available_cpu_count() -> int:
    """Respect process affinity and container quotas before the host count."""
    process_count = getattr(os, "process_cpu_count", lambda: None)() or os.cpu_count()
    limits = [max(1, process_count or 1)]
    with suppress(AttributeError, OSError):
        limits.append(max(1, len(os.sched_getaffinity(0))))
    try:
        # Unified cgroups can impose quotas at any ancestor of this process.
        membership = Path("/proc/self/cgroup").read_text()
        relative = next(line[3:] for line in membership.splitlines() if line.startswith("0::"))
        base = Path("/sys/fs/cgroup")
        current = base / relative.lstrip("/")
        if ".." not in current.parts:
            while True:
                try:
                    quota, period = (current / "cpu.max").read_text().split()
                except FileNotFoundError:
                    quota, period = "max", "1"
                if quota != "max":
                    limits.append(max(1, int(quota) // int(period)))
                if current == base:
                    break
                current = current.parent
    except (OSError, ValueError, StopIteration, ZeroDivisionError):
        pass
    return min(limits)


BUILD_BUDGET_SECONDS = _build_budget_seconds(_available_cpu_count())
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


def _nodes(tree: ast.AST) -> Iterable[tuple[ast.AST, tuple[int, ...]]]:
    """Visit dependencies and literals, avoiding millions of terminal AST leaves."""
    relevant = {
        ast.Import, ast.ImportFrom, ast.Attribute, ast.Assign, ast.AnnAssign,
        ast.AugAssign, ast.For, ast.Call, ast.arg, ast.ClassDef,
        ast.FunctionDef, ast.AsyncFunctionDef, ast.Global, ast.Nonlocal,
    }
    pending = [(tree, ())]
    while pending:
        node, scope = pending.pop()
        kind = type(node)
        # Documentation can cite another executable without loading it. Skip
        # inert string expressions (including docstrings), not runtime values.
        if kind is ast.Expr and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if kind is ast.Constant:
            if isinstance(node.value, str):
                yield node, scope
            continue
        if kind is ast.Name:
            yield node, scope
            continue
        if kind in relevant and (
            kind is not ast.Attribute or node.attr in _LOADERS or node.attr == "repo_wide"
        ):
            yield node, scope
        nested_scope = (id(node), *scope) if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ) else scope
        for child_field in node._fields:
            value = getattr(node, child_field)
            child_scope = nested_scope
            if nested_scope != scope and child_field not in {"body", "args"}:
                child_scope = scope
            elif isinstance(node, ast.arguments) and child_field in {"defaults", "kw_defaults"}:
                child_scope = scope[1:]
            if isinstance(value, list):
                # AST sequence fields contain nodes (aliases and terminal
                # operators have no relevant descendants). Filter on pop.
                pending.extend((child, child_scope) for child in value if isinstance(child, ast.AST))
            elif isinstance(value, ast.AST) and value._fields:
                pending.append((value, child_scope))


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
    node_scopes: dict[int, tuple[int, ...]] = {}
    for node, scope in _nodes(tree):
        groups[type(node)].append(node)
        node_scopes[id(node)] = scope
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
    bindings: dict[tuple[int, ...], dict[str, list[ast.AST]]] = defaultdict(lambda: defaultdict(list))
    classes = {id(node) for node in groups[ast.ClassDef]}
    redirected = {(node_scopes[id(node)], name) for node in groups[ast.Global] + groups[ast.Nonlocal] for name in node.names}

    def assign(node: ast.AST, name: str, value: ast.AST) -> None:
        assignments[name].append(value)
        bindings[node_scopes[id(node)]][name].append(value)
        if (node_scopes[id(node)], name) in redirected:
            # Mutations of enclosing state need interprocedural ordering proof.
            # Keep every matching scope uncertain rather than borrowing a literal.
            for scope in (node_scopes[id(node)][index:] for index in range(1, len(node_scopes[id(node)]) + 1)):
                bindings[scope][name].append(ast.Constant(value=None))

    for node in groups[ast.Assign] + groups[ast.AnnAssign]:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and node.value is not None:
                assign(node, target.id, node.value)

    # Retain unknown rebindings in the lexical scope. A local parameter cannot
    # borrow a module-level literal, nor obscure a literal in another function.
    unknown = ast.Constant(value=None)
    for node in groups[ast.FunctionDef] + groups[ast.AsyncFunctionDef] + groups[ast.ClassDef]:
        assign(node, node.name, unknown)
    for node in groups[ast.Import] + groups[ast.ImportFrom]:
        for alias in node.names:
            assign(node, alias.asname or alias.name.split(".")[0], unknown)
    for node in groups[ast.arg]:
        assign(node, node.arg, unknown)
    for node in groups[ast.AugAssign]:
        if isinstance(node.target, ast.Name):
            assign(node, node.target.id, unknown)
    for node in groups[ast.Assign]:
        for target in node.targets:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                assign(node, target.value.id, unknown)
    for node in groups[ast.Call]:
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "append", "extend", "insert", "pop", "remove", "clear", "reverse", "sort",
        } and isinstance(node.func.value, ast.Name):
            assign(node, node.func.value.id, unknown)

    def lookup(name: str, scope: tuple[int, ...]) -> tuple[tuple[int, ...], list[ast.AST]]:
        for index in range(len(scope) + 1):
            current = scope[index:]
            if index and current and current[0] in classes:
                # Methods resolve free names in enclosing functions/modules,
                # never the class attribute namespace.
                continue
            if name in bindings[current]:
                return current, bindings[current][name]
        return (), [unknown]

    def values(node: ast.AST | None, scope: tuple[int, ...], seen: frozenset = frozenset()) -> list[ast.AST]:
        if isinstance(node, ast.Name):
            current, expressions = lookup(node.id, scope)
            key = (current, node.id)
            if key in seen or len(seen) >= 32:
                return [unknown]
            result = []
            for expr in expressions:
                result.extend(values(expr, current, seen | {key}))
                if len(result) > 64:
                    return [unknown]
            return result
        return [node if node is not None else unknown]

    for node in sorted(groups[ast.For], key=lambda item: item.lineno):
        if isinstance(node.target, ast.Name):
            for iterable in values(node.iter, node_scopes[id(node)]):
                for value in iterable.elts if isinstance(iterable, (ast.Tuple, ast.List)) else [unknown]:
                    assign(node, node.target.id, value)

    def prefixes(node: ast.AST | None, scope: tuple[int, ...], seen: frozenset = frozenset()) -> set[tuple[str | None, ...]]:
        """Resolve up to executable/-m/target, retaining every unknown branch."""
        if isinstance(node, ast.Name):
            current, expressions = lookup(node.id, scope)
            key = (current, node.id)
            if key in seen or len(seen) >= 32:
                return {(None,)}
            result = set()
            for expr in expressions:
                result.update(prefixes(expr, current, seen | {key}))
                if len(result) > 64:
                    return {(None,)}
            return result
        if isinstance(node, (ast.Tuple, ast.List)):
            result: set[tuple[str | None, ...]] = {()}
            for item in node.elts:
                parts = prefixes(item.value, scope, seen) if isinstance(item, ast.Starred) else {
                    prefix[:1] for prefix in prefixes(item, scope, seen)
                }
                result = {(left + right)[:3] for left in result for right in parts}
                if len(result) > 64:
                    return {(None,)}
                if all(len(prefix) == 3 for prefix in result):
                    break
            return result
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {(node.value,)}
        name = _name(node)
        first, _, rest = name.partition(".")
        name = aliases.get(first, first) + ("." + rest if rest else "")
        return {(name,)} if name in {"sys.executable", "sys._base_executable"} else {(None,)}

    # All command references feed the same file-level edge sets. Visiting an
    # assigned argv expression once is enough, even if many commands use it.
    # A per-call visited set repeatedly traversed large shared fixture values.
    command_nodes: set[int] = set()

    def command_shell_paths(command: ast.AST | None) -> set[str]:
        """Follow argv constants and assigned Path components without executing."""
        refs: set[str] = set()
        pending = [command] if command is not None else []
        while pending:
            current = pending.pop()
            if id(current) in command_nodes:
                continue
            command_nodes.add(id(current))
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
                plugin_values = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
                if not all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in plugin_values):
                    reasons.add(f"nonliteral-pytest-plugins:{path}")
                else:
                    for item in plugin_values:
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
                # A shell string can contain pipelines, substitutions or a
                # second interpreter; its first token is not an argv proof.
                if any(isinstance(value, ast.Constant) and isinstance(value.value, str)
                       for value in values(argv, node_scopes[id(node)])):
                    reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
                # Arguments to git and other known non-Python executables do
                # not become opaque Python loads merely by using variables.
                # Literal module/script targets remain resolvable even when
                # later command arguments are dynamic.
                for args in prefixes(argv, node_scopes[id(node)]):
                    executable = args[0] if args else None
                    python = executable in {"sys.executable", "sys._base_executable"} or (
                        executable is not None and PurePosixPath(executable).name.startswith("python")
                    )
                    if python:
                        index = 2 if len(args) > 1 and args[1] == "-m" else 1
                        target = args[index] if len(args) > index else None
                        if target is None or target.startswith("-"):
                            reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
                        elif index == 2:
                            add(path, target, required=True)
                        elif target.endswith(".py"):
                            load_paths.add(target)
                        else:
                            reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
                    elif executable is None:
                        reasons.add(f"nonliteral-subprocess:{path}:{node.lineno}")
            if leaf not in _LOADERS:
                continue
            index, keyword, is_path = _LOADERS[leaf]
            target = node.args[index] if len(node.args) > index else next(
                (kw.value for kw in node.keywords if kw.arg == keyword), None,
            )
            for value in values(target, node_scopes[id(node)]):
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    reasons.add(f"dynamic-import:{path}:{node.lineno}")
                elif value.value.startswith("."):
                    # A runtime package parameter cannot be inferred from the caller.
                    reasons.add(f"relative-runtime-import:{path}:{node.lineno}")
                elif is_path:
                    load_paths.add(value.value)
                else:
                    add(path, value.value, required=True)
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

    def uncertain_tests(self) -> set[str]:
        """Opaque loads may reach any change; include their known test consumers.

        An unreachable production loader cannot execute in a statically known
        test. Any opaque test entry point is itself included in this closure.
        Shared conftests/package initializers naturally widen it to their scope.
        """
        return self.test_dependents(self.uncertainty)

    def selection_reasons(self, paths: Iterable[str]) -> list[str]:
        """Global failures stay FULL; unknown loads contaminate their consumers."""
        if self.tests and self.uncertain_tests() == self.tests:
            return sorted(set(self.reasons).union(*self.uncertainty.values()))
        return list(self.reasons)

    def impacted_tests(self, changed: Iterable[str]) -> dict:
        """Include opaque consumers; FULL if uncertainty covers the whole suite."""
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
            "tests": sorted(self.test_dependents(paths) | self.uncertain_tests()),
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
    # Pytest imports a test's regular parent packages during collection, even
    # when the test has no explicit import of its own package initializer.
    for test in tests:
        for parent in package_parents[test]:
            dependents[parent].add(test)

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
    workers = min(_MAX_PARSER_WORKERS, _available_cpu_count())
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
