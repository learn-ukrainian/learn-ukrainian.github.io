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
    "CREATE TABLE usage (at REAL, caller TEXT, endpoint TEXT, status INTEGER)",
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


def _text(value):
    """``value`` as text SQLite can store: an undecodable byte becomes a replacement character."""
    return str(value).encode("utf-8", "replace").decode("utf-8")


def caller():
    """The dispatched task id with its command, else the calling command."""
    task = os.environ.get(TASK_ENV, "").strip()
    return _text(f"{task} ({_command()})" if task else _command())


_ROUTES = {
    "": (
        "rate_limit", "notifications", "notifications/threads/:n", "gists", "gists/:name", "repositories", "meta",
        "graphql", "app", "app/installations", "app/installations/:n/access_tokens", "installation/repositories",
        "search/code", "search/commits", "search/issues", "search/labels", "search/repositories", "search/topics",
        "search/users", "teams/:n", "teams/:n/members", "teams/:n/repos", "user", "user/blocks", "user/blocks/:name",
        "user/emails", "user/followers", "user/following", "user/following/:name", "user/installations",
        "user/issues", "user/keys", "user/memberships/orgs", "user/memberships/orgs/:name", "user/orgs",
        "user/repos", "user/starred", "user/starred/:repo", "user/subscriptions", "user/teams",
    ),
    "users/:name": (
        "", "events", "followers", "following", "following/:name", "gists", "keys", "orgs", "received_events",
        "repos", "starred",
    ),
    "orgs/:name": (
        "", "actions/runners", "actions/secrets", "actions/secrets/:name", "actions/variables",
        "actions/variables/:name", "events", "hooks", "hooks/:n", "installations", "invitations", "members",
        "members/:name", "memberships/:name", "outside_collaborators", "outside_collaborators/:name",
        "properties/schema", "repos", "rulesets", "rulesets/:n", "teams", "teams/:name", "teams/:name/members",
        "teams/:name/memberships/:name", "teams/:name/repos", "teams/:name/repos/:repo",
    ),
    "repos/:repo": (
        "", "actions/artifacts", "actions/artifacts/:n", "actions/artifacts/:n/:name", "actions/caches",
        "actions/caches/:n", "actions/jobs/:n", "actions/jobs/:n/logs", "actions/jobs/:n/rerun",
        "actions/permissions", "actions/runners", "actions/runs", "actions/runs/:n", "actions/runs/:n/approve",
        "actions/runs/:n/artifacts", "actions/runs/:n/attempts/:n", "actions/runs/:n/attempts/:n/jobs",
        "actions/runs/:n/attempts/:n/logs", "actions/runs/:n/cancel", "actions/runs/:n/force-cancel",
        "actions/runs/:n/jobs", "actions/runs/:n/logs", "actions/runs/:n/pending_deployments",
        "actions/runs/:n/rerun", "actions/runs/:n/rerun-failed-jobs", "actions/runs/:n/timing",
        "actions/secrets", "actions/secrets/:name", "actions/variables", "actions/variables/:name",
        "actions/workflows", "actions/workflows/:name", "actions/workflows/:name/dispatches",
        "actions/workflows/:name/disable", "actions/workflows/:name/enable", "actions/workflows/:name/runs",
        "actions/workflows/:name/timing", "assignees", "assignees/:name", "branches", "branches/:ref",
        "check-runs/:n", "check-runs/:n/annotations", "check-suites/:n", "check-suites/:n/check-runs",
        "check-suites/:n/rerequest", "code-scanning/alerts", "code-scanning/alerts/:n", "collaborators",
        "collaborators/:name", "collaborators/:name/permission", "comments", "comments/:n", "community/profile",
        "compare/:ref", "contents", "contents/:ref", "contributors", "dependabot/alerts", "dependabot/alerts/:n",
        "deployments", "deployments/:n", "deployments/:n/statuses", "dispatches", "environments",
        "environments/:name", "events", "forks", "git/blobs/:sha", "git/commits/:sha", "git/matching-refs/:ref",
        "git/ref/:ref", "git/refs", "git/refs/:ref", "git/tags/:sha", "git/trees/:ref", "hooks", "hooks/:n",
        "invitations", "issues", "issues/:n", "issues/:n/comments", "issues/:n/events", "issues/:n/labels",
        "issues/:n/labels/:name", "issues/:n/timeline", "issues/comments", "issues/comments/:n", "issues/events",
        "keys", "labels", "labels/:name", "languages", "license", "merge-upstream", "merges", "milestones",
        "milestones/:n", "pages", "pulls", "pulls/:n", "pulls/:n/comments", "pulls/:n/commits", "pulls/:n/files",
        "pulls/:n/merge", "pulls/:n/requested_reviewers", "pulls/:n/reviews", "pulls/:n/reviews/:n",
        "pulls/:n/reviews/:n/comments", "pulls/:n/update-branch", "pulls/comments", "pulls/comments/:n",
        "readme", "readme/:ref", "releases", "releases/:n", "releases/:n/assets", "releases/assets/:n",
        "releases/latest", "releases/tags/:ref", "rules/branches/:ref", "rulesets", "rulesets/:n",
        "secret-scanning/alerts", "secret-scanning/alerts/:n", "stargazers", "stats/contributors",
        "statuses/:ref", "subscribers", "subscription", "tags", "tarball", "tarball/:ref", "topics",
        "traffic/clones", "traffic/views", "zipball", "zipball/:ref", "commits", "commits/:sha",
        "commits/:sha/branches-where-head", "commits/:sha/check-runs", "commits/:sha/check-suites",
        "commits/:sha/comments", "commits/:sha/pulls", "commits/:sha/status", "commits/:sha/statuses",
        "commits/:ref",
    ),
}  # fmt: skip
"""The REST routes a template may name; ``:n`` is a number, ``:sha`` a hex SHA, ``:name`` one segment,
``:repo`` an owner and repository, and ``:ref`` the rest of the path (a ref may hold slashes)."""
_KINDS = {":n": r"\d+", ":sha": r"[0-9a-f]{7,64}", ":name": r"[^/]+", ":repo": r"[^/]+/[^/]+", ":ref": r".+"}
_ROOTS = frozenset({"repos", "orgs", "users", "user", "teams", "search", "notifications", "gists", "app", "installation"})


def _compile(route):
    return re.compile("/".join(_KINDS.get(part, re.escape(part)) for part in route.split("/")))


_PATTERNS = sorted(
    (
        (f"{prefix}/{rest}".strip("/"), _compile(f"{prefix}/{rest}".strip("/")))
        for prefix, rests in _ROUTES.items()
        for rest in rests
    ),
    key=lambda route: (":ref" in route[0], -len(route[0])),
)


def endpoint_template(method, path):
    """``METHOD route`` for a request path, where the route names the endpoint and nothing else.

    A path is matched against :data:`_ROUTES`, so a name is replaced by the position it holds in
    the route, however it is spelled and however deep it sits: an account called ``actions`` is
    still a name. A path no route matches keeps only its root and is ``:other`` after it.
    """
    path = _text(path or "").split("?", 1)[0].strip("/")
    for route, pattern in _PATTERNS:
        if pattern.fullmatch(path):
            return f"{_text(method).upper()} {route}"
    root = path.split("/", 1)[0]
    shape = "repos/:repo/:other" if root == "repos" and path.count("/") >= 2 else f"{root}/:other"
    return f"{_text(method).upper()} {shape if root in _ROOTS else ':other'}"


_GH_COMMANDS = {
    "api": (),
    "auth": ("login", "logout", "refresh", "setup-git", "status", "switch", "token"),
    "browse": (),
    "cache": ("delete", "list"),
    "gist": ("clone", "create", "delete", "edit", "list", "rename", "view"),
    "issue": (
        "close", "comment", "create", "delete", "develop", "edit", "list", "lock", "pin", "reopen",
        "status", "transfer", "unlock", "unpin", "view",
    ),
    "label": ("clone", "create", "delete", "edit", "list"),
    "pr": (
        "checkout", "checks", "close", "comment", "create", "diff", "edit", "list", "lock", "merge",
        "ready", "reopen", "revert", "review", "status", "unlock", "update-branch", "view",
    ),
    "release": ("create", "delete", "delete-asset", "download", "edit", "list", "upload", "verify", "view"),
    "repo": (
        "archive", "clone", "create", "delete", "edit", "fork", "list", "rename", "set-default", "sync",
        "unarchive", "view",
    ),
    "ruleset": ("check", "list", "view"),
    "run": ("cancel", "delete", "download", "list", "rerun", "view", "watch"),
    "search": ("code", "commits", "issues", "prs", "repos"),
    "secret": ("delete", "list", "set"),
    "status": (),
    "variable": ("delete", "get", "list", "set"),
    "workflow": ("disable", "enable", "list", "run", "view"),
}
"""The ``gh`` commands a native count may name; any other word on the command line is an argument."""


def command_label(args):
    """The ``gh`` command a count names: a known command and subcommand, never an argument or flag value."""
    words = [_text(arg) for arg in args[1:3]]
    subcommands = _GH_COMMANDS.get(words[0] if words else "")
    if subcommands is None:
        return "gh"
    return f"gh {words[0]} {words[1]}" if len(words) > 1 and words[1] in subcommands else f"gh {words[0]}"


def record(db, *, endpoint, status, now=None):
    """Count one request on a cache connection the client opened.

    The table is created here, on the counting connection only: the client's ordinary cache access
    (admission, budget storage, landing calls) never touches it. A statement SQLite refuses, a table
    that is not the expected one, or text it cannot store drops the row and never fails the call or
    the writes beside it. Damage to the file is the exception: it reaches the client's handling of
    that transaction, which sets the file aside.
    """
    now = time.time() if now is None else now
    try:
        for statement in SCHEMA:
            db.execute(
                statement.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ").replace(
                    "CREATE INDEX ", "CREATE INDEX IF NOT EXISTS "
                )
            )
        db.execute("INSERT INTO usage VALUES(?,?,?,?)", (now, caller(), _text(endpoint), status))
        db.execute("DELETE FROM usage WHERE at<?", (now - RETENTION_SECONDS,))
    except (sqlite3.Error, ValueError) as error:
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
