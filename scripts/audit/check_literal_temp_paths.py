"""Reject executable literal temp paths and unmanaged tempfile calls (#8755).

Python uses AST nodes so comments, docstrings and argparse help are ignored.
Shell uses POSIX tokenization, ignoring comments and help/usage display strings.
This is a static prevention check, not runtime proof of scratch ownership.
"""

from __future__ import annotations

import argparse
import ast
import io
import os
import posixpath
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = frozenset(
    {
        "scripts/common/scratch.py",
        "scripts/orchestration/tmp_leak_sweep.py",
        "scripts/orchestration/reap_worktrees.py",
        "scripts/agent_runtime/runner.py",
    }
)
TEMP_CALLS = {"mkdtemp", "mkstemp", "TemporaryDirectory"}
SCRATCH_NAMES = {"TMPDIR", "LU_TASK_SCRATCH_DIR", "LU_RUNTIME_TMP_ROOT", "tmp_path"}
SCRATCH_HELPERS = {"ensure_scratch_root", "resolve_scratch_root"}
ENV_NAMES = SCRATCH_NAMES - {"tmp_path"}
SOURCE_SUFFIXES = {".py", ".sh", ".bash"}
SKIP_DIRS = {".git", ".worktrees", ".venv", "node_modules", "__pycache__", "batch_state"}
# Character classes keep the detector's own pattern from being a literal path.
TEMP_PATH = re.compile(r"(?<![\w./~])[/](?:var[/])?tmp(?=$|[/$\s'\";,:)}\]])(?:[/][^\s'\";,:)}\]]*)?")
MANAGED_ROOT = "/" + "var/tmp/lu"


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    message: str


def has_literal_temp_path(value: str) -> bool:
    """Detect temp roots at path boundaries, excluding the managed root subtree."""
    for match in TEMP_PATH.finditer(value):
        literal = match.group()
        path = posixpath.normpath(literal)
        if not (
            (literal == MANAGED_ROOT or literal.startswith(MANAGED_ROOT + "/"))
            and (path == MANAGED_ROOT or path.startswith(MANAGED_ROOT + "/"))
        ):
            return True
    return False


def qualified_name(node: ast.AST, aliases: dict[str, str]) -> str:
    """Resolve a dotted name through explicit import aliases."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return qualified_name(node.value, aliases) + "." + node.attr
    return ""


def is_scratch_expression(node: ast.AST, aliases: dict[str, str]) -> bool:
    """Accept explicit scratch sources and relative Path operations only."""
    if isinstance(node, ast.Name):
        return node.id in SCRATCH_NAMES
    if isinstance(node, ast.Subscript):
        return (
            qualified_name(node.value, aliases) == "os.environ"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in ENV_NAMES
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return (
            is_scratch_expression(node.left, aliases)
            and isinstance(node.right, ast.Constant)
            and isinstance(node.right.value, str)
            and not node.right.value.startswith("/")
            and ".." not in node.right.value.split("/")
        )
    if not isinstance(node, ast.Call):
        return False
    name = qualified_name(node.func, aliases)
    if name.rsplit(".", 1)[-1] in SCRATCH_HELPERS:
        return not node.args and not node.keywords
    if name in {"os.getenv", "os.environ.get"}:
        return (
            1 <= len(node.args) <= 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in ENV_NAMES
            and (len(node.args) == 1 or is_scratch_expression(node.args[1], aliases))
            and not node.keywords
        )
    if name in {"Path", "pathlib.Path"}:
        return len(node.args) == 1 and not node.keywords and is_scratch_expression(node.args[0], aliases)
    return name in {"tmp_path_factory.mktemp", "tmp_path_factory.getbasetemp"} and all(
        not has_literal_temp_path(n.value)
        for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )


def documentation_strings(node: ast.AST) -> set[ast.AST]:
    """Exclude literal help text, retaining executable interpolated expressions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node}
    if isinstance(node, ast.JoinedStr):
        return {value for value in node.values if isinstance(value, ast.Constant)}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return documentation_strings(node.left) | documentation_strings(node.right)
    return set()


def scan_python(source: str, path: str) -> list[Finding]:
    """Check executable strings and tempfile calls without executing source."""
    tree = ast.parse(source, filename=path)
    aliases: dict[str, str] = {}
    ignored: set[ast.AST] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".")[0]] = item.name if item.asname else item.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for item in node.names:
                aliases[item.asname or item.name] = node.module + "." + item.name
        if (
            isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
        ):
            value = node.body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                ignored.add(value)
        if isinstance(node, ast.Call):
            name = qualified_name(node.func, aliases)
            help_keys = {"help"} if name.endswith(".add_argument") else set()
            if name.rsplit(".", 1)[-1] == "ArgumentParser":
                help_keys = {"description", "epilog"}
            for keyword in node.keywords:
                if keyword.arg in help_keys:
                    ignored.update(documentation_strings(keyword.value))
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node not in ignored:
            value = node.value.decode("utf-8", errors="replace") if isinstance(node.value, bytes) else node.value
            if isinstance(value, str) and has_literal_temp_path(value):
                findings.append(Finding(path, node.lineno, "literal system temp path; use managed scratch"))
        if isinstance(node, ast.Call):
            name = qualified_name(node.func, aliases)
            if name in {"tempfile." + call for call in TEMP_CALLS}:
                directory = next((k.value for k in node.keywords if k.arg == "dir"), None)
                if directory is None or not is_scratch_expression(directory, aliases):
                    findings.append(Finding(path, node.lineno, "tempfile call requires an approved dir= expression"))
    return sorted(set(findings))


def scan_shell(source: str, path: str) -> list[Finding]:
    """Tokenize shell code, excluding comments and help function display text."""
    stream = io.StringIO(source)
    lexer = shlex.shlex(stream, posix=True, punctuation_chars="();<>|&")
    lexer.whitespace_split = True
    tokens: list[tuple[str, int]] = []
    while (token := lexer.get_token()) is not None:
        # shlex consumes the terminating newline before yielding an unquoted word.
        ended_line = stream.tell() > 0 and source[stream.tell() - 1] == "\n"
        line = max(1, lexer.lineno - token.count("\n") - int(ended_line))
        tokens.append((token, line))
    findings = []
    help_depth = 0
    command = ""
    last_line = 0
    redirected = False
    for index, (token, line) in enumerate(tokens):
        if (
            token == "{"
            and index >= 2
            and tokens[index - 1][0] == "()"
            and tokens[index - 2][0] in {"help", "usage", "show_help", "print_help", "print_usage"}
        ):
            help_depth = 1
            command = ""
            continue
        if token in {"{", "}"}:
            if help_depth:
                help_depth += 1 if token == "{" else -1
            command = ""
            continue
        if token in {";", "&&", "||", "|"}:
            command = ""
            redirected = False
            last_line = line
            continue
        if line != last_line:
            command = ""
            redirected = False
        last_line = line
        if not command:
            command = token
        if token in {">", ">>", "<", "<<"}:
            redirected = True
        help_text = help_depth and command in {"echo", "printf"} and not redirected
        if not help_text and has_literal_temp_path(token):
            findings.append(Finding(path, line, "literal system temp path; use managed scratch"))
    return sorted(set(findings))


def scan_file(path: Path, repo_root: Path = REPO_ROOT) -> list[Finding]:
    """Apply exact repository-relative exemptions and scan a supported file."""
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        relative = absolute.as_posix()
    if path.suffix not in SOURCE_SUFFIXES:
        return []
    # Do not resolve a symlink into a different checkout or private source tree.
    if path.is_symlink():
        raise ValueError("refusing symlink source")
    if relative in ALLOWLIST:
        return []
    source = path.read_text(encoding="utf-8")
    return scan_python(source, relative) if path.suffix == ".py" else scan_shell(source, relative)


def collect_files(paths: list[Path]) -> list[Path]:
    """Walk requested directories without following symlinks or generated trees."""
    files: set[Path] = set()
    for path in paths:
        if not path.is_dir():
            files.add(path)
            continue
        for directory, children, names in os.walk(path, followlinks=False):
            children[:] = sorted(n for n in children if n not in SKIP_DIRS and not (Path(directory) / n).is_symlink())
            files.update(Path(directory) / n for n in names if Path(n).suffix in SOURCE_SUFFIXES)
    return sorted(files)


def changed_files(base: str, repo_root: Path = REPO_ROOT) -> list[Path]:
    """Select existing changed sources, including staged and unstaged changes."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--diff-filter=ACMR", base, "--"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return [repo_root / os.fsdecode(name) for name in result.stdout.split(b"\0") if name]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject literal system-temp paths and unmanaged tempfile calls.\n"
        "Use before review for scripts/tests; this does not verify runtime scratch ownership.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python scripts/audit/check_literal_temp_paths.py --changed-vs-base origin/main\n"
        "  .venv/bin/python scripts/audit/check_literal_temp_paths.py --files scripts/example.py tests/test_example.py\n"
        "  .venv/bin/python scripts/audit/check_literal_temp_paths.py scripts tests\n"
        "Outputs: locations and finding counts on stdout; errors on stderr; no files written.\n"
        "Exit codes: 0 clean; 1 lint findings; 2 invalid input, parse, read or Git error.\n"
        "Related: #8755; scripts/common/scratch.py; scripts/hygiene/lint_tmp_paths.py.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--changed-vs-base", metavar="REF", help="Diff against REF (default unset; example origin/main)."
    )
    group.add_argument(
        "--files", nargs="+", type=Path, help="Explicit file paths (default unset; example scripts/a.py)."
    )
    parser.add_argument(
        "directories", nargs="*", type=Path, help="Directories to walk (default scripts tests; example scripts/audit)."
    )
    args = parser.parse_args(argv)
    if args.directories and (args.files is not None or args.changed_vs_base is not None):
        parser.error("directory walks cannot be combined with --files or --changed-vs-base")
    try:
        if args.changed_vs_base is not None:
            files = changed_files(args.changed_vs_base)
        else:
            files = collect_files(args.files or args.directories or [REPO_ROOT / "scripts", REPO_ROOT / "tests"])
    except (OSError, subprocess.SubprocessError):
        print("Cannot select sources: Git or filesystem error", file=sys.stderr)
        return 2
    findings: list[Finding] = []
    errors = 0
    for path in files:
        try:
            findings.extend(scan_file(path))
        except (OSError, SyntaxError, ValueError, UnicodeError):
            print(f"{path.name}: cannot read or parse source", file=sys.stderr)
            errors += 1
    for finding in sorted(set(findings)):
        print(f"{finding.path}:{finding.line}: {finding.message}")
    print(f"literal_temp_findings={len(set(findings))} errors={errors}")
    return 2 if errors else int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
