#!/usr/bin/env python3
"""Check Python CLI help and a shrink-only inventory of existing violations.

Use in CI or before pushing CLI changes; this does not run normal CLI commands.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.common.scratch import ensure_scratch_root

BASELINE_PATH = "scripts/hygiene/cli_help_baseline.txt"
HELP_TIMEOUT = 5

# No target is imported by the checker. The child denies effects before loading
# the target, including effects outside its temporary cwd. This is a check of
# trusted repository CLIs, not a sandbox for hostile Python/native code.
_HELP_PROBE = r'''
import argparse
import contextlib
import io
import json
import os
import runpy
import sys

script, root = sys.argv[1:]
sys.path[:0] = [os.path.dirname(script), root]
sys.argv = [script, "--help"]
sys.dont_write_bytecode = True
blocked = []
parsers = []

class WorkAttempt(BaseException):
    pass

def audit(event, args):
    forbidden = (
        "subprocess.", "socket.", "sqlite3.", "ctypes.",
        "os.exec", "os.spawn", "os.posix_spawn", "os.fork",
    )
    mutations = {
        "os.system", "os.remove", "os.rename", "os.rmdir", "os.mkdir",
        "os.link", "os.symlink", "os.chmod", "os.chown", "os.truncate",
        "os.utime", "os.kill", "os.killpg",
        "os.chdir", "os.fchdir", "os.startfile", "os.setxattr", "os.removexattr",
        "os.scandir",
    }
    writing = False
    data_read = False
    if event == "open":
        filename, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            )
        )
        # Import loaders may read code. Data/config reads belong after parsing
        # --help, just like database access and directory scans.
        if isinstance(filename, (str, bytes)):
            name = os.fsdecode(filename)
            data_read = not name.endswith((".py", ".pyc", ".so", ".pyd"))
    if writing or data_read or event in mutations or event.startswith(forbidden):
        blocked.append(event)
        raise WorkAttempt(event)

original_print_help = argparse.ArgumentParser.print_help

def print_help(parser, file=None):
    parsers.append({
        "description": parser.description,
        "epilog": parser.epilog,
        "text": parser.format_help(),
        "arguments": [str(a.help or "").strip() for a in parser._actions
                      if a.help != argparse.SUPPRESS],
    })
    original_print_help(parser, file)

argparse.ArgumentParser.print_help = print_help
out, err = io.StringIO(), io.StringIO()
code = 0
sys.addaudithook(audit)
try:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
except BaseException as exc:
    code = 1
    # Exception text can contain private paths or environment values.
    err.write(type(exc).__name__)
print(json.dumps({"code": code, "stdout": out.getvalue(), "stderr": err.getvalue(),
                  "parsers": parsers, "blocked": blocked}))
'''


def has_main(tree: ast.AST) -> bool:
    """Recognize a __name__/__main__ comparison, including reversed operands."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            if (any(isinstance(n, ast.Name) and n.id == "__name__" for n in operands)
                    and any(isinstance(n, ast.Constant) and n.value == "__main__" for n in operands)):
                return True
    return False


def source_problem(tree: ast.AST) -> str | None:
    """Reject provably incomplete argparse help without executing old scripts.

    Other frameworks remain baseline violations until they have a supported,
    inspectable help path. Missing help is never a reason to run normal work.
    """
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    parsers = [n for n in calls if (
        isinstance(n.func, ast.Attribute) and n.func.attr == "ArgumentParser"
    ) or (isinstance(n.func, ast.Name) and n.func.id == "ArgumentParser")]
    if not parsers:
        return "no inspectable argparse help path (not executed)"
    complete = [n for n in parsers if {"description", "epilog"} <= {k.arg for k in n.keywords}]
    if not complete:
        return "parser lacks description or epilog (not executed)"
    epilogs = [k.value for n in complete for k in n.keywords if k.arg == "epilog"]
    if all(isinstance(e, ast.Constant) and isinstance(e.value, str)
           and not all(re.search(r"\b" + section + r"\s*:", e.value, re.IGNORECASE)
                       for section in ("Examples", "Exit codes")) for e in epilogs):
        return "epilog must name Examples: and Exit codes: (not executed)"
    for node in calls:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            helps = [k.value for k in node.keywords if k.arg == "help"]
            if not helps or any(isinstance(h, ast.Constant) and not h.value for h in helps):
                return f"argument lacks help at line {node.lineno} (not executed)"
    return None


def probe_help(path: Path, root: Path) -> str | None:
    """Run only --help, in a temporary cwd, with writes/work effects denied."""
    TMPDIR = os.environ.get("TMPDIR") or ensure_scratch_root()
    with tempfile.TemporaryDirectory(prefix="cli-help-", dir=TMPDIR) as temporary:
        env = {"PATH": os.defpath, "HOME": temporary, "TMPDIR": temporary,
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
               "LANG": "C.UTF-8"}
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-c", _HELP_PROBE, str(path.resolve()), str(root.resolve())],
                cwd=temporary, env=env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=HELP_TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "--help exceeded 5 seconds"
        if list(Path(temporary).iterdir()):
            return "--help wrote files in its temporary cwd"
    try:
        receipt = json.loads(result.stdout)
    except (ValueError, TypeError):
        return "--help probe did not return a receipt"
    if receipt["blocked"]:
        return "--help attempted work or writes (denied): " + ", ".join(sorted(set(receipt["blocked"])))
    if result.returncode or receipt["code"]:
        return f"--help did not exit 0 ({receipt['stderr'][:80]})"
    if result.stderr.strip() or receipt["stderr"].strip():
        return "--help printed diagnostics on stderr"
    output = receipt["stdout"]
    if not receipt["parsers"]:
        return "--help did not print parser help"
    if output != "".join(parser["text"] for parser in receipt["parsers"]):
        return "--help printed output outside parser help; possible real work"
    for parser in receipt["parsers"]:
        if not str(parser["description"] or "").strip():
            return "--help lacks a description"
        if not all(parser["arguments"]):
            return "--help lacks per-argument help"
        epilog = str(parser["epilog"] or "")
        if not all(re.search(r"\b" + section + r"\s*:", epilog, re.IGNORECASE)
                   and re.search(r"\b" + section + r"\s*:", output, re.IGNORECASE)
                   for section in ("Examples", "Exit codes")):
            return "--help epilog must name Examples: and Exit codes:"
    return None


def load_baseline(text: str) -> dict[str, str]:
    """Parse the pinned SHA-256/path inventory, rejecting ambiguous entries."""
    entries = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        digest, separator, path = line.partition("  ")
        if (not separator or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not path.startswith("scripts/") or not path.endswith(".py")
                or ".." in Path(path).parts or path in entries):
            raise ValueError("invalid or duplicate CLI help baseline entry")
        entries[path] = digest
    return entries


def baseline_policy_violations(root: Path, current: dict[str, str]) -> list[str]:
    """Like the SQLite checker, compare available committed predecessors."""
    if not (root / ".git").exists():
        return []
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=root,
        capture_output=True, text=True, timeout=30, check=True,
    )
    main_tree = subprocess.run(
        ["git", "ls-tree", "origin/main", "--", BASELINE_PATH], cwd=root,
        capture_output=True, text=True, timeout=30, check=False,
    )
    if shallow.stdout.strip() == "true" and main_tree.returncode:
        return [f"{BASELINE_PATH}: origin/main or full Git history is required to prove the baseline only shrinks"]
    history = subprocess.run(
        ["git", "log", "--format=%H", "HEAD", "--", BASELINE_PATH], cwd=root,
        capture_output=True, text=True, timeout=30, check=False,
    )
    violations = []
    for ref in dict.fromkeys(["HEAD", "HEAD^", "origin/main", *history.stdout.splitlines()]):
        previous = subprocess.run(
            ["git", "show", f"{ref}:{BASELINE_PATH}"], cwd=root,
            capture_output=True, text=True, timeout=30, check=False,
        )
        if previous.returncode:
            continue  # Initial introduction has no predecessor inventory.
        prior = load_baseline(previous.stdout)
        if not current.items() <= prior.items():
            violations.append(f"{BASELINE_PATH}: may only remove entries relative to {ref}")
    return violations


def scan_paths(root: Path) -> list[Path]:
    """Scan tracked and new scripts, without traversing ignored scratch trees."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "scripts"],
            cwd=root, capture_output=True, check=True, timeout=30,
        )
        return [root / p for p in sorted(set(result.stdout.decode().split("\0"))) if p.endswith(".py")]
    return sorted((root / "scripts").rglob("*.py"))


def find_violations(root: Path = REPO_ROOT) -> tuple[list[str], dict[str, str]]:
    """Return diagnostics and current violations for the initial safe census."""
    root = root.resolve()
    baseline = load_baseline((root / BASELINE_PATH).read_text())
    errors = baseline_policy_violations(root, baseline)
    failing = {}
    seen = set()
    for path in scan_paths(root):
        rel = path.relative_to(root).as_posix()
        if not path.exists():
            continue  # Deleted files are checked as stale entries below.
        if path.is_symlink():
            errors.append(f"{rel}: script symlinks cannot be safely checked")
            continue
        source = path.read_bytes()
        try:
            tree = ast.parse(source, filename=rel)
        except (SyntaxError, ValueError):
            errors.append(f"{rel}: cannot parse Python source")
            continue
        if path.name != "__main__.py" and not has_main(tree):
            continue
        seen.add(rel)
        problem = source_problem(tree) or probe_help(path, root)
        if problem:
            digest = hashlib.sha256(source).hexdigest()
            failing[rel] = digest
            if baseline.get(rel) != digest:
                errors.append(f"{rel}: {problem}; new or changed CLI must meet the help standard")
        elif rel in baseline:
            errors.append(f"{rel}: stale baseline entry; --help now passes")
    errors.extend(f"{rel}: stale baseline entry; script is gone or has no __main__ entry"
                  for rel in sorted(baseline.keys() - seen))
    return errors, failing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.hygiene.lint_cli_help
Outputs: diagnostics on stderr; no repository files or databases changed.
Exit codes: 0 = every CLI passes or is an unchanged baseline violation; 1 = a violation.
Related: #10955; agents_extensions/shared/rules/cli-help-standard.md.
""",
    )
    parser.parse_args(argv)
    try:
        errors, _ = find_violations()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"CLI help check could not finish: {type(exc).__name__}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: CLI help standard and shrink-only baseline pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
