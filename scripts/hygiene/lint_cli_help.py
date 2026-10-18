#!/usr/bin/env python3
"""Ratchet: every scripts/**/*.py CLI must print agent-readable --help (#10955).

Use in CI and before review to enforce agents_extensions/shared/rules/cli-help-standard.md;
not a style linter for library modules or for scripts without a __main__ entry.

A CLI is a tracked or new scripts/**/*.py file with a module-level
``if __name__ == "__main__":`` block. Its ``--help`` passes when, run from a
temporary working directory, the process exits 0 within 5 seconds, attempts no
writes, process spawns, network or SQLite access, including in atexit callbacks
at interpreter shutdown (a PEP 578 audit hook blocks and records them), and the
argparse parser that printed help to stdout has a
description, a help text for every visible argument and subcommand, and an
epilog naming Examples and Exit codes.

Scripts with no argparse reference are never executed: their --help cannot be
proven without starting their work, so they fail statically. Packages CI does
not install (CI_ABSENT_IMPORTS) cannot be imported by a probe on any host.

Existing violators are frozen in cli_help_baseline.json, each pinned to the
SHA-256 of its exact file bytes. A pinned, byte-identical violator is tolerated
and not executed. A new script, or any script whose bytes differ from its pin,
must pass. An entry whose script passes, is gone or is no longer a CLI is stale
and fails, and the baseline may only lose entries relative to its merge base
with origin/main. --recheck-frozen also probes byte-identical entries, so an
entry that passes only through a changed import is reported stale too.
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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.scratch import ensure_scratch_root

BASELINE = Path(__file__).with_name("cli_help_baseline.json")
SCHEMA = "cli-help-baseline.v1"
HELP_TIMEOUT_SECONDS = 5.0
# Names whose presence makes a script worth probing; anything else ignores --help.
PARSER_NAMES = frozenset({"argparse", "ArgumentParser", "parse_args", "parse_known_args", "parse_intermixed_args"})
TIMEOUT_PREFIX = "--help did not exit within"
# Distributions .github/actions/python-ci-env leaves out of CI, by import name. The probe
# refuses them everywhere, so a host that has them reaches the verdict CI reaches.
CI_ABSENT_IMPORTS = {"torch": "torch", "torchvision": "torchvision", "open_clip_torch": "open_clip", "stanza": "stanza"}
EXAMPLES = re.compile(r"\bexamples?\b", re.IGNORECASE)
EXIT_CODES = re.compile(r"\bexit[ -]codes?\b", re.IGNORECASE)

# Runs inside the probed interpreter. Arguments: report path, mode, target, repo root and
# the JSON list of import names to refuse. The audit hook raises before each side effect,
# so a blocked action never happens. It detects ordinary Python side effects; it is not a
# containment boundary against code that bypasses auditing (ctypes, native extensions).
_PROBE = r'''
import argparse, atexit, json, os, runpy, sys, tempfile
_report = os.open(sys.argv[1], os.O_WRONLY)
tempfile.gettempdir()  # Resolve (and cache) the sandbox TMPDIR before writes are blocked.
_mode, _target, _root = sys.argv[2:5]
_absent = frozenset(json.loads(sys.argv[5]))
_WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_BLOCKED = frozenset({
    "os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.truncate", "os.symlink", "os.link",
    "os.chmod", "os.chown", "os.utime", "shutil.rmtree", "shutil.copyfile", "shutil.copytree",
    "shutil.move", "shutil.chown", "tempfile.mkstemp", "tempfile.mkdtemp",
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork",
    "os.forkpty", "os.kill", "os.killpg", "pty.spawn", "webbrowser.open",
    "socket.connect", "socket.sendto", "socket.getaddrinfo", "urllib.Request",
    "http.client.connect", "ftplib.connect", "smtplib.connect", "sqlite3.connect",
})
_events = []
_printed = []

def _hook(event, args):
    if event == "open":
        path, mode, flags = args
        if isinstance(path, int) or path == os.devnull:
            return
        writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & _WRITE)
        if not writes:
            return
    elif event not in _BLOCKED:
        return
    target = os.fsdecode(args[0]) if args and isinstance(args[0], (str, bytes, os.PathLike)) else ""
    detail = repr(target[:120]) if target else ""
    _events.append(f"{event} {detail}".strip())
    raise PermissionError(f"--help probe blocked {event}")

_print_help = argparse.ArgumentParser.print_help

def _recording_print_help(self, file=None):
    _printed.append((self, file is None or file is sys.stdout))
    return _print_help(self, file)

argparse.ArgumentParser.print_help = _recording_print_help

class _CIAbsent:
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] in _absent:
            raise ModuleNotFoundError(f"No module named {name!r} (not installed in CI)", name=name)
        return None

sys.meta_path.insert(0, _CIAbsent())

def _text(value):
    return value if isinstance(value, str) and value.strip() and value != argparse.SUPPRESS else ""

def _describe(parser, to_stdout):
    undocumented = []
    for action in parser._actions:
        if action.help == argparse.SUPPRESS:
            continue
        if isinstance(action, argparse._SubParsersAction):
            documented = {id(action.choices[c.dest]) for c in action._choices_actions
                          if c.dest in action.choices and isinstance(c.help, str) and c.help.strip()}
            seen = set()
            for name, sub in action.choices.items():
                if id(sub) not in documented and id(sub) not in seen:
                    undocumented.append(name)
                seen.add(id(sub))
            continue
        if not (isinstance(action.help, str) and action.help.strip()):
            undocumented.append("/".join(action.option_strings) or str(action.metavar or action.dest))
    return {"to_stdout": to_stdout, "description": _text(parser.description),
            "epilog": _text(parser.epilog), "undocumented": undocumented}

def _finish():
    # atexit runs callbacks last in, first out, so this one, registered before the target,
    # runs after every shutdown callback the target registered, with the hook still
    # installed. Exiting here skips module teardown, whose finalizers Python never promises.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except BaseException:
            pass
    report = {"exit": code, "error": error, "events": _events[:5],
              "parser": _describe(*_printed[-1]) if _printed else None}
    os.write(_report, json.dumps(report).encode())
    os._exit(code if 0 <= code < 256 else 1)

code, error = 0, ""
try:
    sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
    sys.argv = [_target, "--help"]
    sys.addaudithook(_hook)
    atexit.register(_finish)
    if _mode == "path":
        sys.path[:0] = [os.path.dirname(_target), _root]
        runpy.run_path(_target, run_name="__main__")
    else:
        # `python -m` from the repository root; the script's own directory goes
        # last so sibling imports resolve without shadowing installed modules.
        sys.path[:0] = [_root]
        sys.path.append(os.path.dirname(os.path.join(_root, *_target.split("."))))
        runpy.run_module(_target, run_name="__main__", alter_sys=True)
except SystemExit as exc:
    code = 0 if exc.code is None else exc.code if isinstance(exc.code, int) else 1
except BaseException as exc:
    code, error = 1, f"{type(exc).__name__}: {exc}".splitlines()[0][:200] if str(exc) else type(exc).__name__
# Falling off the end starts normal interpreter shutdown; _finish writes the report.
'''


@dataclass(frozen=True)
class Entry:
    path: str
    sha256: str
    reason: str


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare) or len(node.test.ops) != 1:
        return False
    if not isinstance(node.test.ops[0], ast.Eq):
        return False
    sides = [node.test.left, node.test.comparators[0]]
    names = [s for s in sides if isinstance(s, ast.Name) and s.id == "__name__"]
    consts = [s for s in sides if isinstance(s, ast.Constant) and s.value == "__main__"]
    return len(names) == 1 and len(consts) == 1


def classify(source: str, rel: str) -> tuple[bool, bool]:
    """Return (is_cli, references_argparse) from syntax alone."""
    tree = ast.parse(source, filename=rel)
    if not any(_is_main_guard(node) for node in tree.body):
        return False, False
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.update((node.name, *node.name.split(".")))
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.update(node.module.split("."))
    return True, bool(names & PARSER_NAMES)


def iter_scripts(root: Path) -> list[str]:
    """Tracked and untracked (not ignored) scripts/**/*.py, present on disk."""
    if (root / ".git").exists():
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "scripts/*.py"],
            cwd=root, check=True, capture_output=True, timeout=60,
        ).stdout.decode()
        rels = {p for p in out.split("\0") if p}
    else:
        rels = {p.relative_to(root).as_posix() for p in (root / "scripts").rglob("*.py")}
    return sorted(rel for rel in rels if (root / rel).is_file())


def _invocation(root: Path, rel: str) -> tuple[str, str]:
    """Mirror `python -m scripts.x.y` when the path is importable, else `python scripts/x-y.py`."""
    parts = Path(rel).with_suffix("").parts
    if all(p.isidentifier() for p in parts):
        return "module", ".".join(parts)
    return "path", str(root / rel)


def help_failures(report: dict, stdout: str) -> list[str]:
    """Every unmet requirement for one finished probe, in a stable order."""
    failures = []
    if report["events"]:
        failures.append("side effect during --help: " + "; ".join(report["events"]))
    if report["exit"] != 0:
        failures.append(f"--help exited {report['exit']}" + (f" ({report['error']})" if report["error"] else ""))
    parser = report["parser"]
    if parser is None:
        return [*failures, "no argparse help was printed"]
    if not parser["to_stdout"] or not stdout.strip():
        failures.append("help was not printed to stdout")
    if not parser["description"]:
        failures.append("missing description")
    if parser["undocumented"]:
        names = parser["undocumented"]
        shown = ", ".join(names[:5]) + (f", +{len(names) - 5} more" if len(names) > 5 else "")
        failures.append(f"{len(names)} argument(s) without help: {shown}")
    epilog = parser["epilog"]
    lacks = [label for label, rx in (("Examples", EXAMPLES), ("Exit codes", EXIT_CODES))
             if not (rx.search(epilog) and rx.search(stdout))]
    if lacks:
        failures.append("epilog lacks " + " and ".join(lacks))
    return failures


def probe(root: Path, rel: str, timeout: float = HELP_TIMEOUT_SECONDS) -> list[str]:
    """Run `<script> --help` sandboxed; return its failures (empty means it passes)."""
    mode, target = _invocation(root, rel)
    with tempfile.TemporaryDirectory(prefix="cli-help-", dir=ensure_scratch_root()) as scratch:
        sandbox = Path(scratch, "cwd")
        sandbox.mkdir()
        report_path = Path(scratch, "report.json")
        report_path.touch()
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(sandbox), "PYTHONSAFEPATH": "1"}
        env.pop("PYTHONSTARTUP", None)
        try:
            done = subprocess.run(
                [sys.executable, "-B", "-c", _PROBE, str(report_path), mode, target, str(root),
                 json.dumps(sorted(CI_ABSENT_IMPORTS.values()))],
                cwd=sandbox, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return [f"{TIMEOUT_PREFIX} {timeout:g}s"]
        raw = report_path.read_text(encoding="utf-8")
        residue = sorted(p.name for p in sandbox.iterdir())
    if not raw:
        return [f"--help exited {done.returncode} without a probe report (os._exit or crash)"]
    failures = help_failures(json.loads(raw), done.stdout.decode("utf-8", "replace"))
    if residue:
        failures.append("files left in the working directory: " + ", ".join(residue[:5]))
    return failures


def evaluate(root: Path, rel: str) -> str | None:
    """Return the failure reason for one CLI, or None when it passes."""
    try:
        source = (root / rel).read_text(encoding="utf-8")
        is_cli, has_parser = classify(source, rel)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
        return f"unreadable: {type(exc).__name__}"
    if not is_cli:
        return None
    if not has_parser:
        return "no argparse parser: --help ignored, not executed"
    failures = probe(root, rel)
    return scrub("; ".join(failures), root) if failures else None


def scrub(text: str, root: Path) -> str:
    """Keep reasons reproducible and free of host paths: repo-relative, else <path>."""
    text = text.replace(f"{root}/", "")
    return re.sub(r"(?<![\w.])/[^\s'\":;,()<>]+", "<path>", text)


def evaluate_all(root: Path, scripts: list[str], jobs: int) -> dict[str, str | None]:
    """Probe in parallel, then retry each timeout once alone so host load is not a verdict."""
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        reasons = dict(zip(scripts, pool.map(lambda rel: evaluate(root, rel), scripts), strict=True))
    for rel, reason in reasons.items():
        if reason is not None and reason.startswith(TIMEOUT_PREFIX):
            reasons[rel] = evaluate(root, rel)
    return reasons


def load_baseline(text: str) -> dict[str, Entry]:
    payload = json.loads(text)
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"cli help baseline schema must be {SCHEMA}")
    entries = [Entry(**row) for row in payload["entries"]]
    paths = [e.path for e in entries]
    if paths != sorted(set(paths)):
        raise ValueError("cli help baseline paths must be unique and sorted")
    for entry in entries:
        if not entry.path.startswith("scripts/") or ".." in Path(entry.path).parts or not entry.reason.strip():
            raise ValueError(f"invalid cli help baseline entry: {entry.path}")
        if not re.fullmatch(r"[0-9a-f]{64}", entry.sha256):
            raise ValueError(f"invalid cli help baseline sha256: {entry.path}")
    return {e.path: e for e in entries}


def dump_baseline(entries: list[Entry]) -> str:
    rows = [e.__dict__ for e in sorted(entries, key=lambda e: e.path)]
    return json.dumps({"schema": SCHEMA, "entries": rows}, indent=2, ensure_ascii=False) + "\n"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)


def growth_violations(root: Path, baseline_path: Path, current: dict[str, Entry]) -> list[str]:
    """The baseline may only lose entries relative to the merge base with origin/main."""
    rel = baseline_path.relative_to(root).as_posix()
    base = _git(root, "merge-base", "HEAD", "origin/main")
    if base.returncode:
        return [f"{rel}: cannot verify shrink-only baseline: no merge base with origin/main "
                "(fetch origin/main with history)"]
    prior = _git(root, "show", f"{base.stdout.strip()}:{rel}")
    if prior.returncode:
        return []  # The initial baseline has no predecessor to grow from.
    previous = {path: entry.sha256 for path, entry in load_baseline(prior.stdout).items()}
    return [f"{rel}: baseline may only shrink; {path} is new or re-pinned against the merge base"
            for path, entry in sorted(current.items()) if previous.get(path) != entry.sha256]


def find_violations(root: Path = REPO_ROOT, baseline_path: Path = BASELINE, *, jobs: int = 4,
                    check_growth: bool = True, recheck_frozen: bool = False) -> list[str]:
    """Probe every CLI except byte-identical baseline entries (all of them with recheck_frozen)."""
    root = root.resolve()
    baseline = load_baseline(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}
    violations = growth_violations(root, baseline_path.resolve(), baseline) if check_growth else []
    scripts = iter_scripts(root)
    frozen = set() if recheck_frozen else {
        rel for rel in scripts if rel in baseline and file_sha256(root / rel) == baseline[rel].sha256}
    reasons = evaluate_all(root, [rel for rel in scripts if rel not in frozen], jobs)
    for rel, reason in reasons.items():
        entry = baseline.get(rel)
        if entry is None:
            if reason is not None:
                violations.append(f"{rel}: --help fails the CLI help standard: {reason}")
        elif reason is None:
            violations.append(f"{rel}: stale baseline entry: script passes or is no longer a CLI; remove it")
        elif file_sha256(root / rel) != entry.sha256:
            violations.append(f"{rel}: changed since baselined, so --help must pass: {reason}")
    violations.extend(f"{path}: stale baseline entry: script is gone; remove it"
                      for path in sorted(baseline.keys() - set(scripts)))
    return violations


def census(root: Path = REPO_ROOT, *, jobs: int = 4) -> str:
    """Baseline JSON of every current violator (for the initial freeze and review)."""
    root = root.resolve()
    reasons = evaluate_all(root, iter_scripts(root), jobs)
    return dump_baseline([Entry(rel, file_sha256(root / rel), reason)
                          for rel, reason in reasons.items() if reason is not None])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.lint_cli_help\n"
            "  .venv/bin/python -m scripts.hygiene.lint_cli_help --recheck-frozen --jobs 8\n"
            "  .venv/bin/python -m scripts.hygiene.lint_cli_help --census > \"$TMPDIR/cli_help_census.json\"\n\n"
            "Outputs:\n"
            "  Diagnostics on stderr, or census JSON on stdout. Changes no repository file; each probe runs in a\n"
            "  private temporary directory with writes, spawns, network and SQLite blocked.\n\n"
            "Exit codes:\n"
            "  0 = every CLI passes or is an unchanged baseline entry (or census emitted);\n"
            "  1 = a violation, stale entry or baseline growth; 2 = invalid arguments.\n\n"
            "Related:\n"
            "  agents_extensions/shared/rules/cli-help-standard.md; scripts/hygiene/cli_help_baseline.json;\n"
            "  tests/hygiene/test_cli_help_ratchet.py; #10955."
        ),
    )
    parser.add_argument("--jobs", type=int, default=4,
                        help="Parallel --help probes (default: 4). Lower it on a loaded host; the 5 s limit is per probe.")
    parser.add_argument("--recheck-frozen", action="store_true",
                        help="Also probe byte-identical baseline entries, so an entry that now passes through a "
                             "changed import is reported stale (default: off; the nightly slow lane uses it).")
    parser.add_argument("--census", action="store_true",
                        help="Print baseline JSON of every current violator instead of linting. Use it only to "
                             "review the freeze: the committed baseline may never gain entries.")
    args = parser.parse_args(argv)
    if args.census:
        sys.stdout.write(census(jobs=args.jobs))
        return 0
    violations = find_violations(jobs=args.jobs, recheck_frozen=args.recheck_frozen)
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("OK: every scripts/ CLI passes --help or is an unchanged baseline entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
