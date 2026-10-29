"""Local, private, rolling count of the REST core requests the GitHub client sends.

Every request the shared client (:mod:`scripts.common.github_client`) sends to GitHub's core
pool adds one row: when, who called and which endpoint. The caller is the dispatched task id
when there is one, else the calling command (a module or script name, never its arguments). The
endpoint is a template: owner, repository, numbers, commit SHAs and every named account, branch,
tag or label are replaced. A ``304`` is counted but not charged, because GitHub does not charge
a conditional request that returns it; a native ``gh`` command has no status here and counts once, as charged, unless it
is on the landing path, where it is not counted. A landing request is counted only when its
transaction already writes the budget, so counting never adds a lock wait to it.

The rows live in the client's own cache file, owner-only. A request's row is written in the
transaction the client already opens to persist its response; a native command's row is written
after it ran, so its admission stays read-only. Counting never fails a call. Each write drops
rows older than :data:`RETENTION_SECONDS`.

Print the top consumers of the last hour::

    .venv/bin/python -m scripts.common.github_usage top
"""

from __future__ import annotations

import argparse
import fcntl
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
    "CREATE TABLE usage (at REAL, caller TEXT, endpoint TEXT, status INTEGER, landing INTEGER)",
    "CREATE INDEX usage_at ON usage(at)",
)
_REPOSITORY = Path(__file__).resolve().parents[2]
_GH_ENTRY = "scripts/opsec/gh_entry.py"
_PYTHON = re.compile(r"python[0-9.]*")
_SHELL = re.compile(r"bash|dash|sh|zsh")
_CORRUPT = frozenset({11, 26})
"""SQLite's primary result codes for a damaged file: ``SQLITE_CORRUPT`` and ``SQLITE_NOTADB``."""


def corrupt(error):
    """Whether a SQLite error says the database file itself is damaged."""
    code = getattr(error, "sqlite_errorcode", None)
    return isinstance(error, sqlite3.DatabaseError) and type(code) is int and code & 0xFF in _CORRUPT


def file_identity(path):
    """The file ``path`` names now, as ``(device, inode)``, else ``None``."""
    try:
        status = os.stat(path)
    except OSError:
        return None
    return status.st_dev, status.st_ino


def set_aside(path, identity):
    """Move the damaged file ``identity`` (:func:`file_identity`) to its one ``.corrupt`` slot.

    Only while ``path`` still names that file: once another process has set it aside and a
    fresh file replaced it, the replacement is left alone. The check and the move happen under
    one exclusive lock on the directory, so two clients that found the same damage cannot
    interleave them; a client that finds the lock taken leaves the move to the holder. One slot per file keeps disk use bounded. A journal is left in place:
    SQLite discards a journal beside an empty database, and moving it could take a live
    transaction's journal from a process that still has the old file open.
    """
    if identity is None:
        return
    with suppress(OSError):
        directory = os.open(os.path.dirname(os.fspath(path)) or ".", os.O_RDONLY)
        try:
            # Contended: another client is moving the file, so this one never waits for it.
            fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if file_identity(path) == identity:
                os.replace(path, f"{path}.corrupt")
        finally:
            os.close(directory)


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
        "labels",
        "members",
        "orgs",
        "statuses",
        "teams",
        "users",
        "workflows",
    }
)
"""Path words whose next segment names an account, label, team or workflow."""
_REF_AFTER = frozenset({"blobs", "ref", "refs", "tarball", "trees", "zipball"})
"""Path words after which the rest of the path is one ref, whose own name may contain slashes."""
_COMMIT_TAILS = frozenset({"branches-where-head", "check-runs", "check-suites", "comments", "pulls", "status", "statuses"})
"""What may follow a commit-ish in ``commits/<ref>/...``; the ref is everything before the last of them."""


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
            end = max((at for at in range(index, len(parts)) if parts[at] in _COMMIT_TAILS), default=len(parts))
            segment = "/".join(parts[index - 1 : end])
            index = end
        if segment.isdigit():
            segment = ":n"
        elif re.fullmatch(r"[0-9a-f]{7,64}", segment):
            segment = ":sha"
        elif previous in _NAMED_AFTER or previous == "commits":
            segment = ":name"
        segments.append(segment)
    return f"{str(method).upper()} {'/'.join(segments)}"


def record(db, *, endpoint, status, landing, now=None):
    """Count one request on a cache connection the client opened.

    A statement SQLite refuses drops the row and never fails the call or the writes beside it.
    Damage to the file is the exception: it reaches the client's handling of that transaction,
    which sets the file aside.
    """
    now = time.time() if now is None else now
    try:
        db.execute("INSERT INTO usage VALUES(?,?,?,?,?)", (now, caller(), endpoint, status, int(bool(landing))))
        db.execute("DELETE FROM usage WHERE at<?", (now - RETENTION_SECONDS,))
    except sqlite3.Error as error:
        if corrupt(error):
            raise


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
            """SELECT caller, endpoint, count(*) AS requests, sum(status IS NOT 304) AS charged, sum(landing) AS landing
            FROM usage WHERE at>=? GROUP BY caller, endpoint
            ORDER BY charged DESC, requests DESC, caller, endpoint LIMIT ?""",
            (now - hours * 3600, limit),
        ).fetchall()
    finally:
        db.close()
    return [dict(zip(("caller", "endpoint", "requests", "charged", "landing"), row, strict=True)) for row in rows]


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
    print(f"{'charged':>8} {'requests':>8} {'landing':>8}  caller  endpoint")
    for row in rows:
        print(f"{row['charged']:>8} {row['requests']:>8} {row['landing']:>8}  {row['caller']}  {row['endpoint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
