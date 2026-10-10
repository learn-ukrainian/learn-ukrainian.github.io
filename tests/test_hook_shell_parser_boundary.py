"""Freeze direct parser sites in hooks until they move behind the shared API (#9807).

Only the two canonical shared modules are exempt. The fixture is a multiset of
(path, enclosing symbol, normalized AST identity), not a line-number allowlist:
formatting is harmless, duplicate sites and replacements are regressions, and
removals require a corresponding fixture shrink. Never regenerate it to admit
new parser sites. The inventory includes directly imported scripts helpers and
their package initializers. Scope resolution follows Python lexical binding
rules; this is a static architecture check, not an evaluator of arbitrary Python
code or a transitive scan of every dependency of those helpers.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import shlex
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tests/fixtures/hook_shell_parser_baseline.json"
PUBLIC_EXPORTS = {
    "shell_shlex": frozenset(
        {
            "ShellPreprocessLimit",
            "collapse_line_continuations",
            "preprocess_shell_command",
            "skippable_heredoc_delimiters",
            "split_operator_run",
            "split_quote_preserving",
            "strip_shell_comments",
            "strip_skippable_heredoc_bodies",
        }
    ),
    "shell_redirects": frozenset(
        {
            "command_repository_unknown",
            "preprocess_branch_command",
            "scope_events",
            "segments_with_following_operator",
            "unknown_repository_segments",
            "unmodeled_shell_offset",
        }
    ),
}
BOUNDARY = frozenset(f"agents_extensions/shared/hooks/{name}.py" for name in PUBLIC_EXPORTS)
PARSER_LIBRARIES = frozenset(
    {"bashlex", "bashparser", "bashlint", "tree_sitter_bash", "bashparse", "tree_sitter", "tree_sitter_languages"}
)
RUNNERS = frozenset(
    {
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "os.system",
        "os.popen",
        "asyncio.create_subprocess_exec",
        "asyncio.create_subprocess_shell",
    }
)

# Immutable Move 2a ceiling. Fixture edits may remove sites, never admit new ones.
FROZEN_SITE_DIGESTS = frozenset(
    {
        "4878dee8da6749437a3207e8d30f7af67addc5cd54bf255fa77f068d4c45a595",
        "49a09b878736a800cefd6c49c76f14aa5f308132f15e33d871e459f936094873",
        "5e35991ad507ad2f38c4f76868de8e504fd083aebfe57f930b9f767bef837f5f",
        "795098df78ff751a65380c3e7e0ec8569bda16afb19fd74d4b832cb3f3f355cb",
        "a032e59df3cb57341ab8a2680d3d638bc2588e5838fe5a4f315be985dbc157f9",
        "ee65714708174713c72ceb91fdefae03f8993aa1f22d39ebe5560e577dc28022",
    }
)


@dataclass(frozen=True)
class _Reference:
    name: str


@dataclass(frozen=True)
class _StringPrefix:
    """Known text before the first dynamic part of a command string."""

    text: str


@dataclass
class _Scope:
    symbol: str
    parent: _Scope | None = None
    kind: str = "module"
    bindings: dict[str, list[tuple[int, object]]] = field(default_factory=dict)
    globals: set[str] = field(default_factory=set)
    nonlocals: set[str] = field(default_factory=set)

    def bind(self, name: str, line: int, value: object = None) -> None:
        self.bindings.setdefault(name, []).append((line, value))

    def lookup(self, name: str, line: int, seen: frozenset = frozenset()) -> object:
        marker = (id(self), name, line)
        if marker in seen:
            return None
        seen = seen | {marker}
        candidates = [(pos, value) for pos, value in self.bindings.get(name, []) if pos < line]
        if name in self.globals and self.parent and not candidates:
            scope = self.parent
            while scope.parent:
                scope = scope.parent
            return scope.lookup(name, 10**18, seen)
        if name in self.nonlocals and self.parent and not candidates:
            return self.parent.lookup(name, 10**18, seen)
        if name in self.bindings:
            if not candidates:
                return None  # A local binding masks the outer name even before assignment.
            _, value = max(enumerate(candidates), key=lambda item: (item[1][0], item[0]))[1]
            if isinstance(value, ast.AST):
                return _resolve(value, self, seen)
            return value
        if self.parent:
            return self.parent.lookup(name, 10**18, seen)
        return _Reference(name) if name in {"getattr", "vars", "__import__"} else None


def _position(node: ast.AST, *, end: bool = False) -> int:
    return (node.end_lineno * 10**6 + node.end_col_offset) if end else (node.lineno * 10**6 + node.col_offset)


def _resolve(node: ast.AST, scope: _Scope, seen: frozenset = frozenset()) -> object:
    """Resolve aliases and known command prefixes without executing code."""
    if isinstance(node, ast.Name):
        return scope.lookup(node.id, _position(node), seen)
    if isinstance(node, ast.Attribute):
        base = _resolve(node.value, scope, seen)
        if isinstance(base, _Reference):
            return _Reference(f"{base.name}.{node.attr}")
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_resolve(item, scope, seen) for item in node.elts]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _resolve(node.left, scope, seen), _resolve(node.right, scope, seen)
        if isinstance(left, (str, list)) and type(left) is type(right):
            return left + right
        if isinstance(left, list):
            return [*left, None]  # Unknown tail cannot change the known argv prefix.
        if isinstance(left, _StringPrefix):
            return left
        if isinstance(left, str):
            return _StringPrefix(left + right.text if isinstance(right, _StringPrefix) else left)
    if isinstance(node, ast.JoinedStr):
        text = ""
        for part in node.values:
            if not isinstance(part, ast.Constant) or not isinstance(part.value, str):
                return _StringPrefix(text)
            text += part.value
        return text
    if isinstance(node, ast.Call):
        func = _resolve(node.func, scope, seen)
        if func in (_Reference("getattr"), _Reference("builtins.getattr")) and len(node.args) >= 2:
            base, member = _resolve(node.args[0], scope, seen), _resolve(node.args[1], scope, seen)
            if isinstance(base, _Reference) and isinstance(member, str):
                return _Reference(f"{base.name}.{member}")
        if func in (_Reference("__import__"), _Reference("importlib.import_module")) and node.args:
            module = _resolve(node.args[0], scope, seen)
            if isinstance(module, str):
                return _Reference(module.lstrip("."))
    return None


class _Scopes(ast.NodeVisitor):
    """Associate every node with its lexical scope, including implicit scopes."""

    def __init__(self, tree: ast.Module):
        self.scope = _Scope("<module>")
        self.by_node: dict[ast.AST, _Scope] = {}
        self.visit(tree)

    def visit(self, node: ast.AST) -> None:
        self.by_node[node] = self.scope
        super().visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.scope.bind(node.id, _position(node))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.scope.bind(name, _position(node), _Reference(alias.name if alias.asname else name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = ".".join(filter(None, (node.module, alias.name)))
            self.scope.bind(alias.asname or alias.name, _position(node), _Reference(name))

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._assign(target, node.value, _position(node, end=True))

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
        self._assign(node.target, node.value, _position(node, end=True))

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self._assign(node.target, node.value, _position(node, end=True))

    def _assign(self, target: ast.AST, value: ast.AST | None, line: int) -> None:
        self.by_node[target] = self.scope
        if isinstance(target, ast.Name):
            self.scope.bind(target.id, line, value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            expressions = value.elts if isinstance(value, (ast.Tuple, ast.List)) else []
            for index, item in enumerate(target.elts):
                expression = expressions[index] if index < len(expressions) else None
                self._assign(item, expression, line)
        else:
            self.visit(target)

    def visit_Global(self, node: ast.Global) -> None:
        self.scope.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.scope.nonlocals.update(node.names)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.scope.bind(node.name, _position(node))
        self.generic_visit(node)

    def _nested(self, node: ast.AST, name: str, kind: str, body: list[ast.AST]) -> None:
        outer = self.scope
        parent = outer
        # Methods and nested classes do not close over class namespace bindings.
        while parent.kind == "class" and parent.parent:
            parent = parent.parent
        symbol = name if outer.symbol == "<module>" else f"{outer.symbol}.{name}"
        self.scope = _Scope(symbol, parent, kind)
        if hasattr(node, "args"):
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
                if arg:
                    self.scope.bind(arg.arg, 0)
        for statement in body:
            self.visit(statement)
        self.scope = outer

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.bind(node.name, _position(node))
        for expression in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults, node.returns]:
            if expression:
                self.visit(expression)
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs, node.args.vararg, node.args.kwarg]:
            if arg and arg.annotation:
                self.visit(arg.annotation)
        self._nested(node, node.name, "function", node.body)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.bind(node.name, _position(node))
        for expression in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(expression)
        self._nested(node, node.name, "class", node.body)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expression in [*node.args.defaults, *node.args.kw_defaults]:
            if expression:
                self.visit(expression)
        self._nested(node, "<lambda>", "function", [node.body])

    def visit_ListComp(self, node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp) -> None:
        outer = self.scope
        self.visit(node.generators[0].iter)
        parent = outer
        while parent.kind == "class" and parent.parent:
            parent = parent.parent
        self.scope = _Scope(f"{outer.symbol}.<comprehension>", parent, "function")
        for index, generator in enumerate(node.generators):
            if index:
                self.visit(generator.iter)
            self.visit(generator.target)
            for condition in generator.ifs:
                self.visit(condition)
        for expression in [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]:
            self.visit(expression)
        self.scope = outer

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


def _shared_name(name: str) -> tuple[str, str] | None:
    parts = name.split(".")
    for index, part in enumerate(parts):
        if part in PUBLIC_EXPORTS:
            return part, ".".join(parts[index + 1 :])
    return None


def _parser_reference(name: str) -> bool:
    return name in {"shlex.split", "shlex.shlex", "shlex.*"} or name.split(".")[0] in PARSER_LIBRARIES


def _syntax_argv(node: ast.Call, scope: _Scope) -> list[str] | None:
    func = _resolve(node.func, scope)
    if not isinstance(func, _Reference) or func.name not in RUNNERS:
        return None
    expression = (
        node.args[0]
        if node.args
        else next((kw.value for kw in node.keywords if kw.arg in {"args", "command", "cmd"}), None)
    )
    if expression is None:
        return None
    argv = _resolve(expression, scope)
    if func.name == "asyncio.create_subprocess_exec":
        argv = [_resolve(arg, scope) for arg in node.args]
    if isinstance(argv, (str, _StringPrefix)):
        partial = isinstance(argv, _StringPrefix)
        text = argv.text if partial else argv
        if partial:
            # Appending a sentinel models the unknown text touching the final
            # token, including escaped/quoted whitespace. Discard that token.
            lexer = shlex.shlex(text + "__dynamic__", posix=True)
            lexer.whitespace_split = True
            lexer.commenters = ""
            argv = []
            try:
                argv.extend(lexer)
            except ValueError:
                pass  # An open quote in the dynamic tail does not erase complete tokens.
            else:
                argv.pop()
        else:
            try:
                argv = shlex.split(text)
            except ValueError:
                return None
    if not isinstance(argv, list) or not argv or not isinstance(argv[0], str):
        return None
    if Path(argv[0]).name not in {"bash", "sh"}:
        return None
    for index, option in enumerate(argv[1:], 1):
        if not isinstance(option, str) or option in {"--", "-c"} or not option.startswith("-"):
            break
        if option == "--noexec" or (not option.startswith("--") and "n" in option[1:]):
            return argv[: index + 1]
    return None


def _ast_identity(node: ast.AST) -> str:
    """Keep the original frozen spelling on Python 3.12 and newer releases."""
    kwargs = {"show_empty": True} if "show_empty" in inspect.signature(ast.dump).parameters else {}
    return ast.dump(node, include_attributes=False, **kwargs)


class _Normalize(ast.NodeTransformer):
    def __init__(self, scope: _Scope):
        self.scope = scope

    def visit_Name(self, node: ast.Name) -> ast.AST:
        return self._reference(node)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        return self._reference(node)

    def _reference(self, node: ast.AST) -> ast.AST:
        value = _resolve(node, self.scope)
        if isinstance(value, _Reference):
            return ast.Name(id=value.name, ctx=ast.Load())
        return self.generic_visit(node)


def _scan(source: str, path: str) -> tuple[list[dict[str, str]], list[str]]:
    tree = ast.parse(source, filename=path)
    scopes = _Scopes(tree)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    sites: list[dict[str, str]] = []
    violations: list[str] = []
    boundary = path in BOUNDARY

    def record(node: ast.AST, kind: str, identity: str) -> None:
        if not boundary:
            sites.append({"path": path, "symbol": scopes.by_node[node].symbol, "site": f"{kind}:{identity}"})

    def check_api(node: ast.AST, name: str) -> None:
        shared = _shared_name(name)
        if shared and not boundary:
            module, member = shared
            if member and member not in PUBLIC_EXPORTS[module]:
                violations.append(f"{path}:{node.lineno}: non-public shared parser access: {name}")

    for node, scope in scopes.by_node.items():
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.name if isinstance(node, ast.Import) else ".".join(filter(None, (node.module, alias.name)))
                if _parser_reference(name):
                    record(node, "import", name)
                check_api(node, name)
        if isinstance(node, (ast.Name, ast.Attribute, ast.Call)) and not (
            isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load)
        ):
            value = _resolve(node, scope)
            if not isinstance(value, _Reference):
                value = None
            parent = parents.get(node)
            if value:
                check_api(node, value.name)
                # Record only the outermost reference, and include its call's arguments.
                if _parser_reference(value.name) and not (isinstance(parent, ast.Attribute) and parent.value is node):
                    context = parent if isinstance(parent, ast.Call) and parent.func is node else node
                    # Normalize a fresh AST so the lexical-scope map stays intact.
                    normalized = _Normalize(scope).visit(copy.deepcopy(context))
                    identity = _ast_identity(normalized)
                    record(node, "reference", identity)
                shared = _shared_name(value.name)
                if shared and not shared[1] and not boundary:
                    safe_parent = (isinstance(parent, ast.Attribute) and parent.value is node) or (
                        isinstance(parent, (ast.Assign, ast.AnnAssign)) and parent.value is node
                    )
                    if not safe_parent:
                        violations.append(f"{path}:{node.lineno}: dynamic shared parser access: {value.name}")
            if isinstance(node, ast.Call):
                func = _resolve(node.func, scope)
                if (
                    func in tuple(_Reference(name) for name in ("getattr", "vars", "builtins.getattr", "builtins.vars"))
                    and node.args
                ):
                    target = _resolve(node.args[0], scope)
                    if isinstance(target, _Reference) and _shared_name(target.name) and not boundary:
                        violations.append(f"{path}:{node.lineno}: dynamic shared parser access: {target.name}")
                argv = _syntax_argv(node, scope)
                if argv:
                    normalized = _Normalize(scope).visit(copy.deepcopy(node))
                    record(
                        node, "syntax-check", json.dumps(argv) + ":" + _ast_identity(normalized)
                    )
    return sites, sorted(set(violations))


def _hook_files(root: Path) -> list[Path]:
    """Enumerate hook files and scripts modules they import, without executing imports."""
    roots = [*root.glob("agents_extensions/*/hooks"), root / "scripts/hooks"]
    hooks = {path for directory in roots for path in directory.rglob("*.py")}
    files = set(hooks)
    for path in hooks:
        files.update(_script_imports(path.read_text(encoding="utf-8"), path, root))
    return sorted(files)


def _script_imports(source: str, path: Path, root: Path) -> set[Path]:
    """Resolve local module files and package initializers for scripts imports."""
    tree = ast.parse(source, filename=str(path))
    scopes = _Scopes(tree)
    files: set[Path] = set()

    def add_module(name: str, *, required: bool = True) -> None:
        parts = name.split(".")
        if parts[0] != "scripts":
            return
        target = root.joinpath(*parts)
        module = target.with_suffix(".py")
        if module.is_file():
            files.add(module)
        elif not target.is_dir():
            if required:
                raise FileNotFoundError(f"{path.relative_to(root)}: unresolved scripts import: {name}")
            return  # A from-import member can be an exported name rather than a module.
        for index in range(1, len(parts) + 1):
            initializer = root.joinpath(*parts[:index], "__init__.py")
            if initializer.is_file():
                files.add(initializer)

    for node, scope in scopes.by_node.items():
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_module(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = path.parent.relative_to(root).parts
                module = ".".join((*package[: len(package) - node.level + 1], *filter(None, (module,))))
            add_module(module)
            for alias in node.names:
                if alias.name != "*":
                    add_module(f"{module}.{alias.name}", required=False)
        elif isinstance(node, ast.Call) and _resolve(node.func, scope) in (
            _Reference("__import__"),
            _Reference("importlib.import_module"),
        ):
            value = _resolve(node, scope)
            if isinstance(value, _Reference):
                add_module(value.name)
    return files


def _assert_boundary(sites: list[dict[str, str]], violations: list[str], baseline: list[dict[str, str]]) -> None:
    def counts(entries: list[dict[str, str]]) -> Counter:
        assert all(set(entry) == {"path", "symbol", "site"} for entry in entries), "Invalid baseline site schema"
        return Counter((entry["path"], entry["symbol"], entry["site"]) for entry in entries)

    observed, expected = counts(sites), counts(baseline)
    added, removed = observed - expected, expected - observed
    assert not (added or removed or violations), (
        "Hook shell parser boundary violated. Move new parsing behind shell_shlex/shell_redirects; "
        "use only enumerated public exports. Shrink the baseline when removing legacy sites.\n"
        f"New/replaced sites: {list(added.elements())}\n"
        f"Removed sites (update baseline): {list(removed.elements())}\n"
        f"API violations: {violations}"
    )


def _assert_frozen_baseline(baseline: list[dict[str, str]]) -> None:
    digests = [hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest() for entry in baseline]
    assert len(digests) == len(set(digests)), "Duplicate frozen baseline entries"
    assert set(digests) <= FROZEN_SITE_DIGESTS, "The frozen parser baseline may only shrink"


def test_hook_shell_parser_boundary() -> None:
    sites, violations = [], []
    files = _hook_files(ROOT)
    assert files, "Hook scan unexpectedly found no Python files"
    for path in files:
        found, errors = _scan(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix())
        sites.extend(found)
        violations.extend(errors)
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    _assert_frozen_baseline(baseline)
    _assert_boundary(sites, violations, baseline)


HOOK = "agents_extensions/shared/hooks/example.py"


@pytest.mark.parametrize(
    "source",
    [
        "import shlex\nshlex.split(command)",
        "import shlex as s\ns.shlex(command)",
        "from shlex import split as tokenize\ntokenize(command)",
        "import shlex\ntokenize = shlex.split\ntokenize(command)",
        "import shlex\ndef parse():\n    return shlex.split(command)",
        "import bashlex as b\nb.parse(command)",
        "from tree_sitter_bash import language as grammar\ngrammar()",
        "import importlib\np = importlib.import_module('bashlex')\np.parse(command)",
        "import subprocess as sp\nsp.run(['bash', '-n', 'script.sh'])",
        "from subprocess import check_call as run\nargv = ['/bin/sh', '-n', 'script']\nrun(argv)",
        "import subprocess\nsubprocess.run(args=['sh'] + ['-nv', 'script'])",
        "import os\nos.system('bash -n script')",
        "import asyncio\nasyncio.create_subprocess_exec('/bin/bash', '-n', 'script')",
    ],
)
def test_new_parser_site_fails(source: str) -> None:
    sites, violations = _scan(source, HOOK)
    assert sites
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, violations, [])


@pytest.mark.parametrize("use", ["", "split(command)", "shlex(command)"])
def test_shlex_star_import_fails(use: str) -> None:
    sites, violations = _scan(f"from shlex import *\n{use}", HOOK)
    assert any(site["site"] == "import:shlex.*" for site in sites)
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, violations, [])


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess\nsubprocess.run(['bash', '-n', path])",
        "import subprocess\nsubprocess.run(['bash', '-n'] + [path])",
        "import subprocess\nsubprocess.run(['bash', '-n'] + paths)",
        "import subprocess\nsubprocess.run(('bash', '-n', path))",
        "import subprocess\nsubprocess.run(['bash', '-n', *paths])",
        "import subprocess\nsubprocess.run('bash -n ' + path)",
        "import subprocess\nsubprocess.run(f'bash -n {path}')",
        "import subprocess\nsubprocess.run(f'bash -n {path!r}')",
        "import subprocess\nsubprocess.run(f'bash -n \"{path}\"')",
        "import subprocess\nsubprocess.run(f\"bash -n '{path}'\")",
        "import subprocess\nsubprocess.run('bash -n \"' + path + '\"')",
        "import subprocess\nsubprocess.run('bash ' + '-n ' + path)",
        "from subprocess import check_output as run\nargv = ['sh', '-nv', path]\nrun(args=argv)",
        "import os\nos.system('sh --noexec ' + path)",
        "import os\nos.popen(f'/bin/sh -xn {path}')",
        "import asyncio\nasyncio.create_subprocess_exec('bash', '-n', path)",
        "import asyncio\nasyncio.create_subprocess_shell(f'bash -n {path}')",
        "import subprocess\ncmd = 'bash -n ' + path\nsubprocess.run(cmd)",
    ],
)
def test_syntax_check_with_dynamic_tail_fails(source: str) -> None:
    sites, violations = _scan(source, HOOK)
    assert len(sites) == 1 and sites[0]["site"].startswith("syntax-check:")
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, violations, [])


@pytest.mark.parametrize(
    "command",
    [
        "[shell, '-n', path]",
        "['bash', flag, '-n', path]",
        "['bash', '-c', path, '-n']",
        "['bash', '--', '-n', path]",
        "['bash', path, '-n']",
        "['bash', *flags, '-n']",
        "'bash -' + flag",
        "f'bash -{flag} {path}'",
        "f'{shell} -n {path}'",
        "'bash -n' + suffix",
        "'bash -n\\\\ ' + suffix",
        "f\"bash '-n {path}'\"",
        "f'bash -c {path} -n'",
    ],
)
def test_syntax_check_requires_a_known_executable_and_option_prefix(command: str) -> None:
    _assert_boundary(*_scan(f"import subprocess\nsubprocess.run({command})", HOOK), [])


@pytest.mark.parametrize("supports_show_empty", [False, True])
def test_site_identity_preserves_empty_fields_across_dump_versions(
    monkeypatch: pytest.MonkeyPatch, supports_show_empty: bool
) -> None:
    legacy_dump = ast.dump
    canonical_kwargs = {"show_empty": True} if "show_empty" in inspect.signature(legacy_dump).parameters else {}
    source = "import shlex\nshlex.split(words[start:], posix=True)"
    baseline, _ = _scan(source, HOOK)

    def old_dump(node, *, include_attributes=False):
        return legacy_dump(node, include_attributes=include_attributes, **canonical_kwargs)

    def modern_dump(node, *, include_attributes=False, show_empty=False):
        assert show_empty is True
        return legacy_dump(node, include_attributes=include_attributes, **canonical_kwargs)

    monkeypatch.setattr(ast, "dump", modern_dump if supports_show_empty else old_dump)
    _assert_boundary(*_scan(source, HOOK), baseline)
    assert "keywords=[]" in _ast_identity(ast.parse("parse()", mode="eval"))
    # The existing six identities and their frozen digests stay byte-identical.
    fixture = json.loads(BASELINE.read_text(encoding="utf-8"))
    sites = []
    for path in sorted({entry["path"] for entry in fixture}):
        found, errors = _scan((ROOT / path).read_text(encoding="utf-8"), path)
        assert not errors
        sites.extend(found)
    _assert_frozen_baseline(fixture)
    _assert_boundary(sites, [], fixture)


@pytest.mark.parametrize(
    "source",
    [
        "from shell_shlex import _expose_backtick_bodies as helper",
        "from agents_extensions.shared.hooks.shell_redirects import _tokenize",
        "import shell_shlex as s\ns._expose_backtick_bodies(command)",
        "from . import shell_redirects as s\ns._tokenize(command)",
        "from shell_shlex import shlex",
        "from shell_redirects import *",
        "import shell_shlex as s\ngetattr(s, 'preprocess_shell_command')(command)",
        "import shell_redirects as s\nvars(s)[name](command)",
        "import shell_shlex\nshell_shlex.__dict__[name](command)",
        "import shell_shlex\nalias = shell_shlex\ngetattr(alias, name)(command)",
        "import importlib\ns = importlib.import_module('shell_shlex')\ns._body_substitutions(command)",
    ],
)
def test_private_or_dynamic_shared_access_fails(source: str) -> None:
    sites, violations = _scan(source, HOOK)
    assert violations
    with pytest.raises(AssertionError, match="API violations"):
        _assert_boundary(sites, violations, [])


def test_removing_baselined_site_requires_fixture_update() -> None:
    baseline, _ = _scan("import shlex\ndef parse():\n    return shlex.split(command)", HOOK)
    sites, errors = _scan("def parse():\n    return []", HOOK)
    with pytest.raises(AssertionError, match="Removed sites"):
        _assert_boundary(sites, errors, baseline)
    _assert_boundary(sites, errors, [])


def test_replacements_duplicates_and_symbol_moves_fail() -> None:
    source = "import shlex\ndef parse():\n    return shlex.split(command)"
    baseline, _ = _scan(source, HOOK)
    for replacement in [
        source.replace("shlex.split(command)", "shlex.shlex(command)"),
        source.replace("return shlex.split(command)", "shlex.split(command)\n    return shlex.split(command)"),
        source.replace("def parse", "def other"),
    ]:
        with pytest.raises(AssertionError, match="New/replaced sites"):
            _assert_boundary(*_scan(replacement, HOOK), baseline)


def test_site_identity_ignores_formatting_and_import_aliases() -> None:
    baseline, _ = _scan("import shlex\nshlex.split(command, posix=True)", HOOK)
    source = "import shlex as lexer\n# comment\nlexer.split(\n  command,\n  posix = True,\n)"
    _assert_boundary(*_scan(source, HOOK), baseline)


@pytest.mark.parametrize(
    "source",
    [
        "import shlex\nshlex.quote(command)\nshlex.join(words)",
        "from shlex import quote as q, join as j\nq(command)\nj(words)",
        "import shlex\ndef run(shlex):\n    return shlex.split(command)",
        "import shlex\ndef run():\n    shlex = other\n    return shlex.split(command)",
        "import shlex\n[shlex.split(command) for shlex in things]",
        "import shlex\nf = lambda shlex: shlex.split(command)",
        "import subprocess\nsubprocess.run(['echo', 'bash', '-n'])",
        "import subprocess\nsubprocess.run(['bash', '-c', 'echo -n hi'])",
        "import subprocess\nsubprocess.run(['bash', 'script', '-n'])",
        "import subprocess\nsubprocess.run(dynamic_argv)",
        "from shell_shlex import preprocess_shell_command as parse\nparse(command)",
        "import shell_redirects as s\ns.scope_events(command)",
        "from agents_extensions.shared.hooks import shell_shlex as s\ns.split_operator_run(token)",
        "import shell_shlex\nalias = shell_shlex\nalias.split_quote_preserving(command)",
        "# shlex.split(command)\ntext = 'bash -n script'",
    ],
)
def test_allowed_quoting_public_api_and_shadowed_names(source: str) -> None:
    _assert_boundary(*_scan(source, HOOK), [])


def test_lexical_scopes_and_enclosing_symbols() -> None:
    source = """import shlex as s
class C:
    s = other
    def parse(self):
        def inner():
            return s.split(command)
        return inner()
def other(s):
    return s.split(command)
"""
    sites, errors = _scan(source, HOOK)
    assert not errors
    assert [site["symbol"] for site in sites] == ["C.parse.inner"]


@pytest.mark.parametrize("path", sorted(BOUNDARY))
def test_only_canonical_shared_modules_are_exempt(path: str) -> None:
    source = "import shlex\nfrom shell_shlex import _body_substitutions\nshlex.split(command)"
    _assert_boundary(*_scan(source, path), [])
    sites, violations = _scan(source, path.replace("shared", "codex"))
    assert sites and violations


def test_scan_recurses_into_both_hook_roots(tmp_path: Path) -> None:
    paths = ["agents_extensions/codex/hooks/nested/hook.py", "scripts/hooks/deep/hook.py"]
    for path in [*paths, "scripts/other.py"]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("import shlex\nshlex.split(command)", encoding="utf-8")
    assert [path.relative_to(tmp_path).as_posix() for path in _hook_files(tmp_path)] == paths
    with pytest.raises(SyntaxError):
        _scan("def broken(", HOOK)


@pytest.mark.parametrize(
    "hook_import",
    [
        "import scripts.helpers.parser as parser",
        "import scripts.helpers.parser",
        "from scripts.helpers import parser as parse",
        "from scripts.helpers.parser import parse",
        "from scripts.helpers.parser import *",
        "from scripts import helpers",
        "import importlib\nimportlib.import_module('scripts.helpers.parser')",
        "from importlib import import_module as load\nload('scripts.helpers.parser')",
        "__import__('scripts.helpers.parser')",
    ],
)
def test_scan_includes_imported_scripts_and_package_initializers(tmp_path: Path, hook_import: str) -> None:
    sources = {
        HOOK: hook_import,
        "scripts/__init__.py": "",
        "scripts/helpers/__init__.py": "import shlex\nshlex.split(command)",
        "scripts/helpers/parser.py": "import shlex\ndef parse(cmd):\n    return shlex.split(cmd)",
    }
    for path, source in {**sources, "scripts/unimported.py": "import bashlex"}.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    files = _hook_files(tmp_path)
    expected = set(sources)
    if hook_import == "from scripts import helpers":
        expected.remove("scripts/helpers/parser.py")
    assert {path.relative_to(tmp_path).as_posix() for path in files} == expected
    sites, violations = [], []
    for path in files:
        found, errors = _scan(path.read_text(encoding="utf-8"), path.relative_to(tmp_path).as_posix())
        sites.extend(found)
        violations.extend(errors)
    assert {site["path"] for site in sites} == expected - {HOOK, "scripts/__init__.py"}
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, violations, [])


def test_scan_resolves_relative_scripts_imports_and_namespace_packages(tmp_path: Path) -> None:
    hook = tmp_path / "scripts/hooks/example.py"
    helper = tmp_path / "scripts/helpers/parser.py"
    for path, source in [(hook, "from ..helpers import parser"), (helper, "import bashlex")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    assert _hook_files(tmp_path) == sorted([hook, helper])
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(*_scan(helper.read_text(encoding="utf-8"), "scripts/helpers/parser.py"), [])


@pytest.mark.parametrize(
    ("source", "error"),
    [
        ("import scripts.missing", FileNotFoundError),
        ("from scripts.missing import parse", FileNotFoundError),
    ],
)
def test_import_inventory_fails_closed_on_missing_modules(tmp_path: Path, source: str, error: type) -> None:
    hook = tmp_path / HOOK
    hook.parent.mkdir(parents=True)
    hook.write_text(source, encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "helper.py").write_text("def broken(", encoding="utf-8")
    with pytest.raises(error):
        _hook_files(tmp_path)


def test_imported_helper_must_be_readable_and_parseable(tmp_path: Path) -> None:
    hook = tmp_path / HOOK
    hook.parent.mkdir(parents=True)
    hook.write_text("import scripts.helper", encoding="utf-8")
    helper = tmp_path / "scripts/helper.py"
    helper.parent.mkdir()
    for source, error in [(b"def broken(", SyntaxError), (b"\xff", UnicodeDecodeError)]:
        helper.write_bytes(source)
        files = _hook_files(tmp_path)
        assert helper in files
        with pytest.raises(error):
            for path in files:
                _scan(path.read_text(encoding="utf-8"), path.relative_to(tmp_path).as_posix())


@pytest.mark.parametrize(
    "source",
    [
        "import shlex as s; s.split(command)",
        "import shlex; parse = shlex.split; parse(command)",
        "import shlex\ndef parse():\n    global shlex\n    return shlex.split(command)",
        "def parse():\n    global s\n    import shlex as s\n    return s.split(command)",
        "def outer():\n    import shlex as s\n    def inner():\n        nonlocal s\n        return s.split(command)",
        "import shlex\nparse: object = shlex.split\nparse(command)",
        "import shlex\nparse, other = (shlex.split, None)\nparse(command)",
        "import shlex\n(parse := shlex.split)(command)",
        "import shlex\ns = shlex\ns = s\ns.split(command)",
        "import shlex\nclass C:\n    parse = shlex.split(command)",
        "import shlex\nf = lambda: shlex.split(command)",
        "import shlex\n[shlex.split(command) for item in items]",
        "import shlex\n{item: shlex.split(command) for item in items}",
        "import shlex\n{shlex.split(command) for item in items}",
        "import shlex\n(shlex.split(command) for item in items)",
        "import shlex\ndef parse(words=shlex.split(command)):\n    pass",
        "from shlex import shlex as Lexer\nasync def parse():\n    return Lexer(command)",
        "import subprocess\nargv = ['bash', '-n', 'script']\nrun = subprocess.run\nrun(argv)",
        "import os\nos.popen('sh --noexec script')",
        "import asyncio\nasyncio.create_subprocess_shell('sh -n script')",
    ],
)
def test_scope_and_assignment_alias_mutations_fail(source: str) -> None:
    sites, violations = _scan(source, HOOK)
    assert sites
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, violations, [])


def test_static_syntax_check_replacement_changes_identity() -> None:
    source = "import subprocess\nargv = ['bash', '-n', 'script']\nsubprocess.run(argv)"
    baseline, _ = _scan(source, HOOK)
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(*_scan(source.replace("'bash'", "'sh'"), HOOK), baseline)


def test_fixture_may_only_shrink() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    _assert_frozen_baseline(baseline)
    _assert_frozen_baseline(baseline[:-1])
    _assert_frozen_baseline([])
    added, _ = _scan("import shlex\nshlex.split(new_command)", HOOK)
    with pytest.raises(AssertionError, match="may only shrink"):
        _assert_frozen_baseline([*baseline, *added])
    with pytest.raises(AssertionError, match="Duplicate"):
        _assert_frozen_baseline([*baseline, baseline[0]])


@pytest.mark.parametrize(
    "source",
    [
        "import shlex; shlex = other; shlex.split(command)",
        "import shlex\ndef f():\n    import shlex as s\n    return s.quote(command)\ndef g(s):\n    return s.split(command)",
        "import shlex\ndef f():\n    return shlex.split(command)\n    shlex = other",
        "import shlex\nwith manager() as shlex:\n    shlex.split(command)",
        "import shlex\nfor shlex in items:\n    shlex.split(command)",
        "import shlex\ntry:\n    pass\nexcept Exception as shlex:\n    shlex.split(command)",
        "import subprocess\nsubprocess.run('bash -n \\\"')",
        "import subprocess\nsubprocess.run(['bash', '--', '-n'])",
        "import subprocess\nsubprocess.run(['bash', '-x', script])",
        "from subprocess import run\ndef f(run):\n    run(['bash', '-n'])",
    ],
)
def test_unrelated_or_shadowed_references_pass(source: str) -> None:
    _assert_boundary(*_scan(source, HOOK), [])


@pytest.mark.parametrize(
    "source",
    [
        "import shlex\ngetattr(shlex, 'split')(command)",
        "import shlex as s\ngetattr(s, 'shlex')(command)",
        "import shlex as s\ndef f():\n    global s\n    s.split(command)",
        "def outer():\n    import shlex as s\n    def inner():\n        nonlocal s\n        s.split(command)",
        "import shlex\nclass C:\n    shlex = other\n    words = [shlex.split(command) for item in items]",
    ],
)
def test_reflective_parser_references_and_outer_scopes_fail(source: str) -> None:
    sites, errors = _scan(source, HOOK)
    assert sites
    with pytest.raises(AssertionError, match="New/replaced sites"):
        _assert_boundary(sites, errors, [])


@pytest.mark.parametrize(
    "source",
    [
        "from shell_shlex import split_operator_run as split\ngetattr(split, '__globals__')",
        "import shell_shlex as s\ns.split_operator_run.__globals__",
        "import builtins\nimport shell_shlex as s\nbuiltins.getattr(s, name)",
        "import shell_shlex as s\nfrom builtins import getattr as read\nread(s, name)",
    ],
)
def test_reflective_export_access_fails(source: str) -> None:
    sites, errors = _scan(source, HOOK)
    assert errors
    with pytest.raises(AssertionError, match="API violations"):
        _assert_boundary(sites, errors, [])
