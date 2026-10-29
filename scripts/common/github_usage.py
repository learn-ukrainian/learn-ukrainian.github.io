"""Local, private, rolling count of the REST core requests the GitHub client sends.

Every request the shared client (:mod:`scripts.common.github_client`) sends to GitHub's core
pool adds one row: when, who called and which endpoint. The caller is the dispatched task id
when there is one, else the calling command (a module or script name, never its arguments). The
endpoint is a template: owner, repository, numbers, commit SHAs and ref names are replaced. A
``304`` is counted but not charged, because GitHub does not charge a conditional request that
returns it. The ledger is its own file beside the client's cache, owner-only, so a damaged cache
never loses the count, and it keeps a day. Recording never fails or holds a GitHub call.

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

FILENAME = "usage.sqlite3"
RETENTION_SECONDS = 24 * 60 * 60
BUSY_SECONDS = 0.1
"""Longest a record waits for another writer before it is dropped: the count never holds a call."""
TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS request (at REAL, caller TEXT, endpoint TEXT, status INTEGER, landing INTEGER)",
    "CREATE INDEX IF NOT EXISTS request_at ON request(at)",
)
_REPOSITORY = Path(__file__).resolve().parents[2]
_GH_ENTRY = "scripts/opsec/gh_entry.py"
_CORRUPT = frozenset({11, 26})
"""SQLite's primary result codes for a damaged file: ``SQLITE_CORRUPT`` and ``SQLITE_NOTADB``."""


def corrupt(error):
    """Whether a SQLite error says the database file itself is damaged."""
    code = getattr(error, "sqlite_errorcode", None)
    return isinstance(error, sqlite3.DatabaseError) and type(code) is int and code & 0xFF in _CORRUPT


def set_aside(path):
    """Move a damaged SQLite file to its one ``.corrupt`` slot; the next open starts an empty file.

    One slot per file keeps disk use bounded, and another process that already moved it wins.
    A journal is left in place: SQLite discards a journal beside an empty database, and moving
    it could take a live transaction's journal from a process that still has the old file open.
    """
    with suppress(OSError):
        os.replace(path, f"{path}.corrupt")


def _command_name(argv):
    """A command's module or script name, never its arguments."""
    argv = [str(arg) for arg in argv]
    if "-m" in argv[:-1]:
        return argv[argv.index("-m") + 1]
    for arg in argv[:3]:
        if arg.endswith((".py", ".sh")):
            path = Path(arg).resolve()
            return path.relative_to(_REPOSITORY).as_posix() if path.is_relative_to(_REPOSITORY) else path.name
    return Path(argv[0]).name if argv else "unknown"


@functools.cache
def _command():
    """This process's calling command; for the ``gh`` shim, the command that ran ``gh``."""
    spec = getattr(sys.modules.get("__main__"), "__spec__", None)
    name = spec.name if spec is not None and spec.name else _command_name(sys.argv or ["unknown"])
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


def endpoint_template(method, path):
    """``METHOD path`` with the repository, numbers, SHAs and ref names replaced."""
    path = str(path or "").split("?", 1)[0].strip("/")
    path = re.sub(r"^repos/[^/]+/[^/]+", "repos/:repo", path)
    path = re.sub(r"/(heads|tags|branches|compare|contents)/.*$", r"/\1/:ref", path)
    segments = [
        ":n" if segment.isdigit() else ":sha" if re.fullmatch(r"(?=.*\d)[0-9a-f]{7,64}", segment) else segment
        for segment in path.split("/")
    ]
    return f"{str(method).upper()} {'/'.join(segments)}"


def record(directory, *, endpoint, status, landing, now=None):
    """Count one request sent to the core pool. Best effort: an error or a busy ledger drops it."""
    if directory is None:
        return
    path = Path(directory) / FILENAME
    now = time.time() if now is None else now
    try:
        Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(path, timeout=BUSY_SECONDS)
        try:
            with suppress(OSError):
                os.chmod(path, 0o600)
            with db:
                for statement in _SCHEMA:
                    db.execute(statement)
                db.execute(
                    "INSERT INTO request VALUES(?,?,?,?,?)",
                    (now, caller(), endpoint, status, int(bool(landing))),
                )
                db.execute("DELETE FROM request WHERE at<?", (now - RETENTION_SECONDS,))
        finally:
            db.close()
    except (sqlite3.Error, OSError) as error:
        if corrupt(error):
            set_aside(path)


def top(directory, *, hours=1.0, limit=20, now=None):
    """The heaviest callers and endpoints of the last ``hours``, most charged first."""
    path = Path(directory) / FILENAME
    if not path.is_file():
        return []
    now = time.time() if now is None else now
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    try:
        rows = db.execute(
            """SELECT caller, endpoint, count(*) AS requests, sum(status IS NOT 304) AS charged, sum(landing) AS landing
            FROM request WHERE at>=? GROUP BY caller, endpoint
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
    report.add_argument("--hours", type=float, default=1.0, help="window to count (default: 1)")
    report.add_argument("--limit", type=int, default=20, help="rows to print (default: 20)")
    report.add_argument("--dir", type=Path, help="ledger directory (default: the GitHub client's cache directory)")
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
