"""Local, private, rolling count of the REST core requests the GitHub client sends.

Every request the shared client (:mod:`scripts.common.github_client`) sends to GitHub's core
pool adds one row: when, who called and which endpoint. The caller is the dispatched task id
when there is one, else the calling command (a module or script name, never its arguments). The
endpoint is a template: owner, repository, numbers, commit SHAs and every named account, branch,
tag or label are replaced. A ``304`` is counted but not charged, because GitHub does not charge
a conditional request that returns it; a native ``gh`` command has no status here and counts once,
as charged. A landing call is never counted, so counting never adds a lock wait to it.

The rows live in the client's own cache file, owner-only. Each is written in a short transaction of
its own, after the call's budget observation and cache writes committed, that waits at most a quarter
second to open and lock the file: a row SQLite refuses is dropped and never fails the call or costs an
observation. Each write drops rows older than :data:`RETENTION_SECONDS`.

Print the top consumers of the last hour::

    .venv/bin/python -m scripts.common.github_usage top
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import sqlite3
import sys
import time
from contextlib import suppress
from pathlib import Path

RETENTION_SECONDS = 6 * 60 * 60
TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
SCHEMA = (
    "CREATE TABLE usage (at REAL, caller TEXT, endpoint TEXT, status INTEGER)",
    "CREATE INDEX usage_at ON usage(at)",
)
_REPOSITORY = Path(__file__).resolve().parents[2]
_GH_ENTRY = "scripts/opsec/gh_entry.py"
_PYTHON = re.compile(r"python[0-9.]*")
_SHELL = re.compile(r"bash|dash|sh|zsh")


def _script_name(arg):
    """A script path as the repository-relative path, else as given when relative, else its name."""
    path = Path(arg)
    if not path.is_absolute():
        return arg
    return path.relative_to(_REPOSITORY).as_posix() if path.is_relative_to(_REPOSITORY) else path.name


def _python_target(options, program):
    """The module or script of a Python command line, read in the interpreter's own option grammar."""
    for arg in options:
        if arg == "--":
            return _script_name(next(options, program))
        if arg == "-" or not arg.startswith("-"):
            return _script_name(arg)
        if arg.startswith("--"):
            if arg == "--check-hash-based-pycs":
                next(options, None)
            continue
        for index, flag in enumerate(arg[1:], 1):
            if flag == "c":
                return f"{program} -c"
            if flag == "m":
                return arg[index + 1 :] or next(options, program)
            if flag in "WX":
                if index + 1 == len(arg):
                    next(options, None)
                break
    return program


def _shell_target(options, program):
    """The script of a shell command line; ``-c``'s inline text and ``-s``'s positional arguments are never read."""
    for arg in options:
        if arg == "--":
            return _script_name(next(options, program))
        if arg.startswith("--"):
            if arg in ("--rcfile", "--init-file"):
                next(options, None)
        elif arg[:1] in ("-", "+") and len(arg) > 1:
            if arg[0] == "-" and "c" in arg:
                return f"{program} -c"
            if arg[0] == "-" and "s" in arg:
                return f"{program} -s"
            if arg[-1] in "oO":
                next(options, None)
        else:
            return _script_name(arg)
    return program


def _command_name(argv):
    """A command's module or script, read only from the interpreter's own position in ``argv``.

    Arguments after the module or script, and inline code, belong to the application and are
    never read.
    """
    argv = [str(arg) for arg in argv]
    if not argv:
        return "unknown"
    program = Path(argv[0]).name
    if _PYTHON.fullmatch(program):
        return _python_target(iter(argv[1:]), program)
    if _SHELL.fullmatch(program):
        return _shell_target(iter(argv[1:]), program)
    return _script_name(argv[0])


@functools.cache
def _command():
    """This process's calling command; for the ``gh`` shim, the command that ran ``gh``."""
    spec = getattr(sys.modules.get("__main__"), "__spec__", None)
    if spec is not None and spec.name:
        name = spec.name
    else:
        script = sys.argv[0] if sys.argv else ""
        name = "python -c" if script == "-c" else _script_name(script) if script else "unknown"
    if name != _GH_ENTRY:
        return name
    try:
        parent = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().split(b"\0")
        return "gh via " + _command_name([part.decode(errors="replace") for part in parent if part])
    except OSError:
        return "gh via unknown"


def caller():
    """The dispatched task id with its command, else the calling command."""
    task = os.environ.get(TASK_ENV, "").strip()
    return f"{task} ({_command()})" if task else _command()


_NAMED_AFTER = frozenset(
    {
        "assignees",
        "collaborators",
        "environments",
        "following",
        "labels",
        "members",
        "orgs",
        "secrets",
        "statuses",
        "teams",
        "users",
        "variables",
        "workflows",
    }
)
"""Path words whose next segment names an account, label, team, workflow, secret or variable."""
_REF_AFTER = frozenset({"blobs", "matching-refs", "readme", "ref", "refs", "starred", "tarball", "trees", "zipball"})
"""Path words after which the rest of the path is one ref, whose own name may contain slashes."""
_COMMIT_TAILS = frozenset({"branches-where-head", "check-runs", "check-suites", "comments", "pulls", "status", "statuses"})
"""What may follow a commit SHA in ``commits/<sha>/...``."""


def endpoint_template(method, path):
    """``METHOD path`` with the repository, numbers, SHAs and every named component replaced."""
    path = str(path or "").split("?", 1)[0].strip("/")
    path = re.sub(r"^repos/[^/]+/[^/]+", "repos/:repo", path)
    path = re.sub(r"/(heads|tags|branches|compare|contents)/.*$", r"/\1/:ref", path)
    parts = path.split("/")
    segments = []
    index = 0
    while index < len(parts):
        segment, previous, index = parts[index], segments[-1] if segments else "", index + 1
        if previous in _REF_AFTER:
            segments.append(":name")
            break
        if previous == "commits":
            # A commit SHA, with at most one tail word, keeps its shape. Anything else is a ref whose
            # own name may hold slashes and tail words, so it is replaced whole.
            rest = parts[index - 1 :]
            if re.fullmatch(r"[0-9a-f]{7,64}", rest[0]) and (len(rest) == 1 or (len(rest) == 2 and rest[1] in _COMMIT_TAILS)):
                segments.extend([":sha", *rest[1:]])
            else:
                segments.append(":name")
            break
        if segment.isdigit():
            segment = ":n"
        elif re.fullmatch(r"[0-9a-f]{7,64}", segment):
            segment = ":sha"
        elif previous in _NAMED_AFTER or previous == "commits":
            segment = ":name"
        segments.append(segment)
    return f"{str(method).upper()} {'/'.join(segments)}"


def record(db, *, endpoint, status, now=None):
    """Count one request on a cache connection the client opened.

    A statement SQLite refuses drops the row and never fails the call or the writes beside it.
    """
    now = time.time() if now is None else now
    with suppress(sqlite3.Error):
        db.execute("INSERT INTO usage VALUES(?,?,?,?)", (now, caller(), endpoint, status))
        db.execute("DELETE FROM usage WHERE at<?", (now - RETENTION_SECONDS,))


def top(directory, *, hours=1.0, limit=20, now=None):
    """The heaviest callers and endpoints of the last ``hours``, most charged first."""
    from scripts.lib.readonly_sqlite import open_readonly

    path = Path(directory) / "cache.sqlite3"
    if not path.is_file():
        return []
    now = time.time() if now is None else now
    db = open_readonly(path)
    try:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='usage'").fetchone() is None:
            return []
        rows = db.execute(
            """SELECT caller, endpoint, count(*) AS requests, sum(status IS NOT 304) AS charged
            FROM usage WHERE at>=? GROUP BY caller, endpoint
            ORDER BY charged DESC, requests DESC, caller, endpoint LIMIT ?""",
            (now - hours * 3600, limit),
        ).fetchall()
    finally:
        db.close()
    return [dict(zip(("caller", "endpoint", "requests", "charged"), row, strict=True)) for row in rows]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("top", help="print the top REST core consumers")
    report.add_argument("--hours", type=float, default=1.0, help="window to count (default: 1, at most 6)")
    report.add_argument("--limit", type=int, default=20, help="rows to print (default: 20)")
    report.add_argument("--dir", type=Path, help="cache directory (default: the GitHub client's)")
    report.add_argument("--json", action="store_true", help="print JSON rows")
    args = parser.parse_args(argv)
    directory = args.dir
    if directory is None:
        from scripts.common.github_client import _cache_directory

        directory = _cache_directory()
    rows = top(directory, hours=args.hours, limit=args.limit) if directory is not None else []
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    print(f"{'charged':>8} {'requests':>8}  caller  endpoint")
    for row in rows:
        print(f"{row['charged']:>8} {row['requests']:>8}  {row['caller']}  {row['endpoint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
