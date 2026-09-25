"""Every worktree removal under ``scripts/`` goes through the guarded chokepoint (#8610).

A removal that skips the per-worktree lock and the active-claim scan can take
a checkout a dispatch worker just attached to. Sol's r3 and r4 reviews each
found such a remover outside the paths the previous round had guarded, so this
test closes the class: it scans every production source for removal call
sites and fails on any outside :data:`ALLOWLIST`.

A removal call site is any of:

* Python: a literal ``"worktree", "remove"`` pair or a dynamic action after
  ``"worktree"`` in a Git argv list or helper call; a ``worktree remove`` script handed to a shell
  (``shell=True``, ``os.system``/``os.popen``, or an argv ``-c`` script); a
  reference to, or import of, a low-level remover (:data:`LOW_LEVEL_REMOVERS`).
* YAML: a sequence holding adjacent ``worktree`` and ``remove`` scalars (a
  trail argv), a dynamic action after ``worktree``, or a scalar containing a
  removal command (a shell script).
* Shell and other code: a non-comment line containing ``worktree remove`` or
  a quoted ``"worktree", "remove"`` pair; backslash continuations are joined.

Operator hints that merely print ``git worktree remove`` are not call sites.
Shell and YAML callers use ``python -m scripts.orchestration.worktree_claims
remove``; Python callers use ``worktree_claims.remove_unclaimed_worktree``.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.repo_wide

# (file, innermost enclosing function) -> why that site may remove a worktree.
ALLOWLIST: dict[tuple[str, str | None], str] = {
    ("scripts/orchestration/worktree_claims.py", "git_worktree_remove"): (
        "the repository's one raw `git worktree remove`"
    ),
    ("scripts/orchestration/worktree_claims.py", "remove_unclaimed_worktree"): (
        "the chokepoint: calls the raw remover only under the lock, ownership proof, and claim scan"
    ),
    ("scripts/orchestration/reap_worktrees.py", "_reap_qualified_worktree"): (
        "the reaper pipeline: calls the raw remover only under _enter_dispatch_worktree_guard (same lock and scan)"
    ),
}

# Names of functions that remove a worktree without the guard, current or
# historical. A reference outside the allowlist is a bypass.
LOW_LEVEL_REMOVERS = frozenset({"git_worktree_remove", "_git_worktree_remove", "remove_worktree", "_remove_worktree"})

_SHELL_PHRASE = re.compile(r'''(?:\bworktree\b|["']worktree["'])\s+(?:\bremove\b|["']remove["'])''')
_DYNAMIC_ACTION = re.compile(r"(?:\$[A-Za-z_{]|\{\{.*\}\}|\*\w+)")
_QUOTED_ARGV_PAIR = re.compile(r"""["']worktree["']\s*,\s*["']remove["']""")
_SHELL_SCRIPT_FLAG = re.compile(r"^-[A-Za-z]*c$")
_SHELL_CALLS = frozenset({"system", "popen", "getoutput", "getstatusoutput"})
_YAML_SUFFIXES = frozenset({".yaml", ".yml"})
_LINE_COMMENT = {
    ".sh": "#",
    ".bash": "#",
    ".ps1": "#",
    ".zsh": "#",
    ".js": "//",
    ".mjs": "//",
    ".ts": "//",
    ".go": "//",
}


@dataclass(frozen=True)
class Site:
    path: str
    function: str | None
    line: int
    kind: str


def _literal_text(node: ast.AST) -> str | None:
    """Return a string literal's text; an f-string's placeholders become ``{}``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
    return None


def _has_argv_pair(words: list[str | None]) -> bool:
    return any(words[index : index + 2] == ["worktree", "remove"] for index in range(len(words) - 1))


def _has_dynamic_git_worktree_action(words: list[str | None], *, allow_bare: bool = False) -> bool:
    """Catch a worktree argv whose action is supplied by a variable or template."""
    dynamic_pair = any(
        words[index] == "worktree"
        and (
            words[index + 1] is None
            or _DYNAMIC_ACTION.search(words[index + 1]) is not None
        )
        for index in range(len(words) - 1)
    )
    has_git_prefix = words[:1] == ["git"]
    return dynamic_pair and (has_git_prefix or allow_bare)


def _nested_literals(nodes: list[ast.expr]) -> list[str]:
    texts: list[str] = []
    for node in nodes:
        for child in ast.walk(node):
            text = _literal_text(child)
            if text is not None:
                texts.append(text)
    return texts


def python_sites(source: str, relpath: str) -> list[Site]:
    """Return the removal call sites in one Python source."""
    tree = ast.parse(source, filename=relpath)
    owners: dict[ast.AST, str | None] = {}
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

    def assign_owners(node: ast.AST, owner: str | None) -> None:
        for child in ast.iter_child_nodes(node):
            child_owner = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else owner
            owners[child] = child_owner
            assign_owners(child, child_owner)

    assign_owners(tree, None)
    sites: set[Site] = set()

    def add(node: ast.AST, kind: str) -> None:
        sites.add(Site(relpath, owners.get(node), getattr(node, "lineno", 0), kind))

    for node in ast.walk(tree):
        if isinstance(node, ast.List | ast.Tuple):
            words = [_literal_text(element) for element in node.elts]
            parent = parents.get(node)
            parent_func = (
                parent.func.attr if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute)
                else parent.func.id if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name)
                else None
            )
            git_variable_prefix = bool(node.elts) and isinstance(node.elts[0], ast.Name) and node.elts[0].id == "git"
            nested_git_runner = parent_func in {"run_git", "_run_git"}
            if _has_argv_pair(words) or _has_dynamic_git_worktree_action(
                words,
                allow_bare=git_variable_prefix or nested_git_runner,
            ):
                add(node, "argv")
            flag_seen = False
            for word in words:
                if word is not None and _SHELL_SCRIPT_FLAG.match(word):
                    flag_seen = True
                elif flag_seen and word is not None and _SHELL_PHRASE.search(word):
                    add(node, "shell -c script")
        elif isinstance(node, ast.Call):
            call_words = [_literal_text(arg) for arg in node.args]
            func_name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else None
            if _has_argv_pair(call_words) or _has_dynamic_git_worktree_action(
                call_words,
                allow_bare=func_name in {"run_git", "_run_git"},
            ):
                add(node, "argv")
            name = func_name
            shell = name in _SHELL_CALLS or any(
                keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
                for keyword in node.keywords
            )
            if shell and any(_SHELL_PHRASE.search(text) for text in _nested_literals(node.args)):
                add(node, "shell string")
        elif isinstance(node, ast.ImportFrom):
            if any(alias.name in LOW_LEVEL_REMOVERS for alias in node.names):
                add(node, "low-level remover import")
        elif (isinstance(node, ast.Attribute) and node.attr in LOW_LEVEL_REMOVERS) or (
            isinstance(node, ast.Name) and node.id in LOW_LEVEL_REMOVERS and isinstance(node.ctx, ast.Load)
        ):
            add(node, "low-level remover reference")
    return sorted(sites, key=lambda site: (site.line, site.kind))


def yaml_sites(source: str, relpath: str) -> list[Site]:
    """Return the removal call sites in one YAML source, from its node graph."""
    sites: list[Site] = []

    def walk(node: yaml.Node) -> None:
        if isinstance(node, yaml.SequenceNode):
            words = [child.value if isinstance(child, yaml.ScalarNode) else None for child in node.value]
            if _has_argv_pair(words) or _has_dynamic_git_worktree_action(words, allow_bare=True):
                sites.append(Site(relpath, None, node.start_mark.line + 1, "argv"))
            for child in node.value:
                walk(child)
        elif isinstance(node, yaml.MappingNode):
            for key, value in node.value:
                walk(key)
                walk(value)
        elif isinstance(node, yaml.ScalarNode) and (
            _SHELL_PHRASE.search(node.value)
            or re.search(r"\bworktree\b\s+(?:\$[A-Za-z_{]|\{\{)", node.value)
        ):
            sites.append(Site(relpath, None, node.start_mark.line + 1, "command string"))

    for document in yaml.compose_all(source, Loader=yaml.SafeLoader):
        if document is not None:
            walk(document)
    return sites


def text_sites(source: str, relpath: str, comment: str | None) -> list[Site]:
    """Return the removal call sites in one shell or other code source."""
    sites: list[Site] = []
    lines = source.splitlines()
    for number, line in enumerate(lines, start=1):
        logical = line
        # A backslash continuation cannot split the command past the scan.
        following = number
        while logical.endswith("\\") and following < len(lines):
            logical = logical[:-1] + " " + lines[following]
            following += 1
        if comment is not None and logical.lstrip().startswith(comment):
            continue
        if _SHELL_PHRASE.search(logical) or _QUOTED_ARGV_PAIR.search(logical):
            sites.append(Site(relpath, None, number, "command line"))
    return sites


def production_sites(project_root: Path = PROJECT_ROOT) -> list[Site]:
    """Scan every production source under ``scripts/``.

    Every call-site shape contains both ``worktree`` and ``remove``: the argv
    pair, the shell phrase, and each low-level remover name. All UTF-8 source
    files are scanned regardless of suffix; documentation, bytecode, and
    notebooks are excluded. A source lacking ``worktree`` is skipped unparsed,
    which keeps the scan to a few seconds. Dynamic worktree actions may not
    contain the word ``remove``, so ``worktree`` alone is the pre-filter.
    """
    sites: list[Site] = []
    for source_path in sorted((project_root / "scripts").rglob("*")):
        suffix = source_path.suffix
        if not source_path.is_file() or suffix in {".md", ".txt", ".pyc", ".ipynb"}:
            continue
        raw = source_path.read_bytes()
        if b"worktree" not in raw:
            continue
        relpath = source_path.relative_to(project_root).as_posix()
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if suffix in {".py", ".pyi"}:
            sites.extend(python_sites(source, relpath))
        elif suffix in _YAML_SUFFIXES:
            sites.extend(yaml_sites(source, relpath))
        else:
            sites.extend(text_sites(source, relpath, _LINE_COMMENT.get(suffix)))
    return sites


def test_every_worktree_removal_goes_through_the_guarded_chokepoint() -> None:
    """#8610 r5: no production code removes a worktree outside the allowlisted chokepoint."""
    sites = production_sites()

    unexpected = [site for site in sites if (site.path, site.function) not in ALLOWLIST]
    assert not unexpected, "unguarded worktree removal call sites:\n" + "\n".join(
        f"  {site.path}:{site.line} in {site.function or '<module>'}: {site.kind}" for site in unexpected
    )
    stale = set(ALLOWLIST) - {(site.path, site.function) for site in sites}
    assert not stale, f"allowlist entries without a removal call site: {sorted(stale, key=str)}"


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ('subprocess.run(["git", "worktree", "remove", path])', "argv"),
        ('run_git(["worktree", "remove", "--force", str(path)], cwd=root)', "argv"),
        ('_run_git(root, "worktree", "remove", str(path))', "argv"),
        ('subprocess.run([git, "-C", str(root), "worktree", "remove", p])', "argv"),
        ('subprocess.run(["git", "worktree", action, path])', "argv"),
        ('_run_git(root, "worktree", action, path)', "argv"),
        ('run_git(["worktree", action])', "argv"),
        ('subprocess.run([git, "worktree", action, path])', "argv"),
        ('subprocess.run(f"git worktree remove {path}", shell=True)', "shell string"),
        ('subprocess.run("git \\"worktree\\" \\"remove\\" x", shell=True)', "shell string"),
        ('os.system("git -C repo worktree remove x")', "shell string"),
        ('subprocess.run(["sh", "-c", f"git worktree remove {path}"])', "shell -c script"),
        ('subprocess.run(["bash", "-lc", "git worktree remove x && echo ok"])', "shell -c script"),
        ("reap_worktrees._remove_worktree(root, info)", "low-level remover reference"),
        ("worktree_claims.git_worktree_remove(root, path, force=True)", "low-level remover reference"),
        ("safety.remove_worktree(root, path)", "low-level remover reference"),
        ("cleanup(remover=reap_worktrees._remove_worktree)", "low-level remover reference"),
        ("from scripts.orchestration.reap_worktrees import _remove_worktree as rm", "low-level remover import"),
    ],
)
def test_scanner_flags_every_python_removal_shape(source: str, kind: str) -> None:
    """Each bypass shape a reviewer found, or that could replace one, is a call site."""
    sites = python_sites(f"def helper():\n    {source}\n", "scripts/example.py")

    assert kind in {site.kind for site in sites}
    assert {site.function for site in sites} == {"helper"}


@pytest.mark.parametrize(
    "source",
    [
        'print(f"  git worktree remove {path}")',
        'raise RuntimeError(f"remove it with `git worktree remove {path}`")',
        '"""Docstring: ``git worktree remove`` is forbidden here."""',
        "pass  # git worktree remove x",
        'subprocess.run([python, "-m", "scripts.orchestration.worktree_claims", "remove", path])',
        "worktree_claims.remove_unclaimed_worktree(path, repo_root=root, reason=r, owner_task_id=None)",
        'subprocess.run(["git", "worktree", "list", "--porcelain"])',
    ],
)
def test_scanner_ignores_hints_and_the_guarded_entry_points(source: str) -> None:
    """Printed hints, docs, and calls to the guarded chokepoint or CLI are not call sites."""
    assert python_sites(f"def helper():\n    {source}\n", "scripts/example.py") == []


@pytest.mark.parametrize(
    "source",
    [
        '_run_git(root, "worktree", "list")',
        'run_git(["worktree", "list"])',
        'subprocess.run([git, "worktree", "list"])',
    ],
)
def test_scanner_ignores_static_non_removal_worktree_actions(source: str) -> None:
    """A known non-removal action is not treated as a dynamic removal bypass."""
    assert python_sites(f"def helper():\n    {source}\n", "scripts/example.py") == []


@pytest.mark.parametrize(
    ("source", "suffix", "flagged"),
    [
        ('git worktree remove "$wt_dir"', ".sh", True),
        ('    git -C "$REPO" worktree  remove --force x', ".sh", True),
        ('git -C "$REPO" worktree \\\n    remove "$wt_dir"', ".sh", True),
        ("# git worktree remove is forbidden", ".sh", False),
        ('"$python" -m scripts.orchestration.worktree_claims remove "$wt_dir"', ".sh", False),
        ('execFileSync("git", ["worktree", "remove", dir])', ".ts", True),
        ('// execFileSync("git", ["worktree", "remove", dir])', ".ts", False),
    ],
)
def test_scanner_flags_shell_and_code_command_lines(source: str, suffix: str, flagged: bool) -> None:
    """Non-comment command lines that remove a worktree are call sites; the CLI is not."""
    sites = text_sites(source, f"scripts/example{suffix}", _LINE_COMMENT[suffix])

    assert bool(sites) is flagged


def test_scanner_checks_source_files_with_unknown_suffixes(tmp_path: Path) -> None:
    """The inventory scans source files even when their suffix is unfamiliar."""
    path = tmp_path / "scripts" / "cleanup.unknown"
    path.parent.mkdir()
    path.write_text('git "worktree" "remove" "$target"\n', encoding="utf-8")

    sites = production_sites(tmp_path)

    assert [(site.path, site.kind) for site in sites] == [("scripts/cleanup.unknown", "command line")]


@pytest.mark.parametrize(
    ("source", "flagged"),
    [
        ("argv: [sh, -c, 'git worktree remove \".worktrees/dispatch/$LANE/$TASK_ID\"']", True),
        ("argv: [git, worktree, remove, x]", True),
        ("argv: [git, worktree, $ACTION, x]", True),
        ("argv: [worktree, '{{ action }}', x]", True),
        ("argv:\n  - git\n  - -C\n  - repo\n  - worktree\n  - remove\n  - x\n", True),
        ("run: |\n  cd repo\n  git worktree remove x\n", True),
        ("# git worktree remove x\nargv: [git, worktree, list]", False),
        ("argv: [git, worktree, list, x]", False),
        ("argv: [sh, -c, '.venv/bin/python -m scripts.orchestration.worktree_claims remove x >&2']", False),
    ],
)
def test_scanner_flags_yaml_argv_and_shell_scripts(source: str, flagged: bool) -> None:
    """A trail argv or shell script that removes a worktree is a call site, in flow or block style."""
    assert bool(yaml_sites(source, "scripts/example.yaml")) is flagged


def test_production_prefilter_parses_dynamic_action_without_remove_word(tmp_path: Path) -> None:
    """The production byte pre-filter must let dynamic worktree actions reach the parser."""
    path = tmp_path / "scripts" / "cleanup.py"
    path.parent.mkdir()
    path.write_text('def cleanup():\n    run_git(["worktree", action])\n', encoding="utf-8")

    sites = production_sites(tmp_path)

    assert [(site.path, site.kind) for site in sites] == [("scripts/cleanup.py", "argv")]
