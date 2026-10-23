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
    parser_names = {"ArgumentParser"} | {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        and any(
            (isinstance(base, ast.Name) and base.id == "ArgumentParser")
            or (isinstance(base, ast.Attribute) and base.attr == "ArgumentParser"
                and isinstance(base.value, ast.Name) and base.value.id == "argparse")
            for base in node.bases
        )
    }
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    parsers = [n for n in calls if (
        isinstance(n.func, ast.Attribute) and n.func.attr == "ArgumentParser"
    ) or (isinstance(n.func, ast.Name) and n.func.id in parser_names)]
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
                or Path(path).as_posix() != path or ".." in Path(path).parts
                or any(c.isspace() or ord(c) < 32 for c in path) or path in entries):
            raise ValueError("invalid or duplicate CLI help baseline entry")
        entries[path] = digest
    return entries


def shallow_baseline_unprovable(root: Path) -> bool:
    """Require the baseline blob on origin/main when Git history is shallow."""
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=root,
        capture_output=True, text=True, timeout=30, check=True,
    )
    main_tree = subprocess.run(
        ["git", "ls-tree", "origin/main", "--", BASELINE_PATH], cwd=root,
        capture_output=True, text=True, timeout=30, check=False,
    )
    return shallow.stdout.strip() == "true" and (
        main_tree.returncode != 0 or re.search(r"^\d{6} blob ", main_tree.stdout) is None
    )


def git_bytes(root: Path, *args: str) -> bytes:
    """Read Git evidence, failing closed on unavailable objects or revisions."""
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          check=True, timeout=30).stdout


def authoritative_main(root: Path) -> str:
    """Pin the remote-tracking main commit; no caller revision grants eligibility."""
    return git_bytes(root, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}").decode().strip()


def committed_baseline(root: Path, sha: str) -> dict[str, str] | None:
    """Distinguish proven absence from a missing tree or unreadable baseline."""
    entry = git_bytes(root, "ls-tree", sha, "--", BASELINE_PATH)
    if not entry:
        return None
    if not entry.startswith((b"100644 blob ", b"100755 blob ")):
        raise ValueError("baseline must be a regular Git blob")
    return load_baseline(git_bytes(root, "show", f"{sha}:{BASELINE_PATH}").decode())


def _baseline_policy(root: Path, current: dict[str, str], main_sha: str) -> list[str]:
    prior = committed_baseline(root, main_sha)
    if prior is None:
        if git_bytes(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
            return [f"{BASELINE_PATH}: origin/main or full Git history is required to prove the baseline only shrinks"]
        if git_bytes(root, "log", "--full-history", "--format=%H", main_sha, "--", BASELINE_PATH):
            return [f"{BASELINE_PATH}: previously landed baseline is absent on main {main_sha}"]
        git_bytes(root, "merge-base", "--is-ancestor", main_sha, "HEAD")
        errors = []
        for path, digest in sorted(current.items()):
            entry = git_bytes(root, "ls-tree", main_sha, "--", path)
            if not entry.startswith((b"100644 blob ", b"100755 blob ")) or hashlib.sha256(
                git_bytes(root, "show", f"{main_sha}:{path}")
            ).hexdigest() != digest:
                errors.append(f"{path}: initial exemption requires identical source bytes on main {main_sha}")
        return errors
    # Main's landed inventory supersedes pre-landing snapshots. Every baseline
    # commit unique to this branch remains binding, including earlier growth.
    refs = git_bytes(root, "log", "--full-history", "--format=%H", f"{main_sha}..HEAD",
                     "--", BASELINE_PATH).decode().splitlines()
    errors = []
    for ref in [main_sha, *refs]:
        previous = committed_baseline(root, ref)
        if previous is None:
            raise ValueError("landed baseline was removed in branch history")
        if not current.items() <= previous.items():
            errors.append(f"{BASELINE_PATH}: may only remove entries relative to {ref}")
    return errors


def baseline_policy_violations(root: Path, current: dict[str, str]) -> list[str]:
    """Reconcile the initial main inventory, then enforce shrink-only history."""
    if not (root / ".git").exists():
        return []
    if shallow_baseline_unprovable(root):
        return [f"{BASELINE_PATH}: origin/main or full Git history is required to prove the baseline only shrinks"]
    return _baseline_policy(root, current, authoritative_main(root))


def scan_paths(root: Path) -> list[Path]:
    """Scan tracked and new scripts, without traversing ignored scratch trees."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "scripts"],
            cwd=root, capture_output=True, check=True, timeout=30,
        )
        return [root / p for p in sorted(set(result.stdout.decode().split("\0"))) if p.endswith(".py")]
    return sorted((root / "scripts").rglob("*.py"))


def census(root: Path) -> tuple[list[str], dict[str, str], dict[str, str | None]]:
    """Discover the complete CLI denominator without trusting baseline entries."""
    root = root.resolve()
    errors = []
    failing = {}
    problems = {}
    for path in scan_paths(root):
        rel = path.relative_to(root).as_posix()
        if not path.exists():
            errors.append(f"{rel}: missing scan input; cannot prove complete CLI inventory")
            continue
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
        problems[rel] = problem = source_problem(tree) or probe_help(path, root)
        if problem:
            failing[rel] = hashlib.sha256(source).hexdigest()
    return errors, failing, problems


def find_violations(root: Path = REPO_ROOT) -> tuple[list[str], dict[str, str]]:
    """Check all current CLIs and reject new, changed, or stale exemptions."""
    root = root.resolve()
    baseline = load_baseline((root / BASELINE_PATH).read_text())
    errors, failing, problems = census(root)
    errors.extend(baseline_policy_violations(root, baseline))
    for rel, problem in problems.items():
        if problem and baseline.get(rel) != failing[rel]:
            errors.append(f"{rel}: {problem}; new or changed CLI must meet the help standard")
        elif not problem and rel in baseline:
            errors.append(f"{rel}: stale baseline entry; --help now passes")
    errors.extend(f"{rel}: stale baseline entry; script is gone or has no __main__ entry"
                  for rel in sorted(baseline.keys() - problems.keys()))
    return errors, failing


def emit_baseline(root: Path = REPO_ROOT) -> str:
    """Write a reproducible inventory only after proving every exemption eligible."""
    root = root.resolve()
    main_sha = authoritative_main(root)
    # Malformed inventories are errors, even when regenerating them.
    load_baseline((root / BASELINE_PATH).read_text())
    errors, failing, problems = census(root)
    errors.extend(_baseline_policy(root, failing, main_sha))
    if errors:
        raise ValueError("\n".join(errors))
    text = ("# Existing CLI help violations. SHA-256  repository-relative path.\n"
            "# Only removals are allowed after the initial inventory.\n"
            + "".join(f"{digest}  {path}\n" for path, digest in sorted(failing.items())))
    (root / BASELINE_PATH).write_text(text)
    identity = hashlib.sha256(text.encode()).hexdigest()
    return (f"Baseline emitted: main={main_sha} total={len(problems)} "
            f"passing={len(problems) - len(failing)} failing={len(failing)} sha256={identity}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.hygiene.lint_cli_help
  .venv/bin/python -m scripts.hygiene.lint_cli_help --emit-baseline
Outputs: default is read-only; --emit-baseline writes scripts/hygiene/cli_help_baseline.txt.
  Emission prints the pinned origin/main SHA, denominator and inventory SHA-256.
Exit codes: 0 = every CLI passes or is an unchanged baseline violation; 1 = a violation.
Related: #10955; agents_extensions/shared/rules/cli-help-standard.md.
""",
    )
    parser.add_argument("--emit-baseline", action="store_true", help=(
        "Regenerate sorted eligible failures (default: read-only lint), e.g. --emit-baseline. "
        "Initial inventory requires full history and identical origin/main source bytes."
    ))
    args = parser.parse_args(argv)
    try:
        if args.emit_baseline:
            print(emit_baseline())
            return 0
        errors, _ = find_violations()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"CLI help check could not finish: {type(exc).__name__}", file=sys.stderr)
        if isinstance(exc, ValueError):
            print(str(exc), file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: CLI help standard and shrink-only baseline pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
