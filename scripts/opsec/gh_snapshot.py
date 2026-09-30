"""Strict raw-gh admission. Public writes belong to scripts.publish.github.

No raw argv token is interpreted as public text. A command is a permitted read
only if its entire argv matches one closed grammar. API and extension commands
are never admitted as reads.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from scripts.opsec.prepublish import PublishBlocked, is_private, normalize_repository

# flag names -> whether a value is required. No abbreviation or short clusters.
FORMAT = {"--json": True, "--jq": True, "-q": True, "--template": True, "-t": True}
REPO = {"--repo": True, "-R": True}
VIEW = {**FORMAT, "--web": False, "-w": False}
LIST = {**FORMAT, "--limit": True, "-L": True}
READ_GRAMMARS = {
    ("pr", "view"): (0, 1, {**VIEW, **REPO, "--comments": False, "-c": False}),
    ("pr", "list"): (
        0,
        0,
        {
            **LIST,
            **REPO,
            "--state": True,
            "-s": True,
            "--base": True,
            "-B": True,
            "--head": True,
            "-H": True,
            "--label": True,
            "-l": True,
            "--author": True,
            "-A": True,
            "--assignee": True,
            "-a": True,
            "--search": True,
            "-S": True,
            "--draft": False,
        },
    ),
    ("pr", "status"): (0, 0, {**FORMAT, **REPO, "--conflict-status": False}),
    ("pr", "checks"): (
        0,
        1,
        {
            **FORMAT,
            **REPO,
            "--watch": False,
            "--interval": True,
            "-i": True,
            "--required": False,
            "--fail-fast": False,
            "--web": False,
            "-w": False,
        },
    ),
    ("pr", "diff"): (0, 1, {**REPO, "--patch": False, "--name-only": False, "--color": True}),
    ("issue", "view"): (1, 1, {**VIEW, **REPO, "--comments": False, "-c": False}),
    ("issue", "list"): (
        0,
        0,
        {
            **LIST,
            **REPO,
            "--state": True,
            "-s": True,
            "--label": True,
            "-l": True,
            "--assignee": True,
            "-a": True,
            "--author": True,
            "-A": True,
            "--search": True,
            "-S": True,
            "--milestone": True,
            "-m": True,
        },
    ),
    ("issue", "status"): (0, 0, {**FORMAT, **REPO}),
    ("run", "view"): (
        0,
        1,
        {
            **VIEW,
            **REPO,
            "--job": True,
            "-j": True,
            "--log": False,
            "--log-failed": False,
            "--exit-status": False,
            "--attempt": True,
            "-a": True,
            "--verbose": False,
            "-v": False,
        },
    ),
    ("run", "list"): (
        0,
        0,
        {
            **LIST,
            **REPO,
            "--workflow": True,
            "-w": True,
            "--branch": True,
            "-b": True,
            "--event": True,
            "-e": True,
            "--status": True,
            "-s": True,
            "--commit": True,
            "-c": True,
            "--user": True,
            "-u": True,
            "--created": True,
            "--all": False,
        },
    ),
    ("run", "watch"): (1, 1, {**REPO, "--interval": True, "-i": True, "--exit-status": False, "--compact": False}),
    ("run", "download"): (
        0,
        1,
        {**REPO, "--dir": True, "-D": True, "--name": True, "-n": True, "--pattern": True, "-p": True},
    ),
    ("workflow", "list"): (0, 0, {**LIST, **REPO, "--all": False, "-a": False}),
    ("workflow", "view"): (
        0,
        1,
        {**REPO, "--yaml": False, "-y": False, "--ref": True, "-r": True, "--web": False, "-w": False},
    ),
    ("repo", "view"): (0, 1, {**VIEW, "--branch": True, "-b": True}),
    ("repo", "list"): (
        0,
        1,
        {
            **LIST,
            "--archived": False,
            "--no-archived": False,
            "--fork": False,
            "--source": False,
            "--language": True,
            "--topic": True,
            "--visibility": True,
        },
    ),
    ("release", "view"): (0, 1, {**VIEW, **REPO}),
    ("release", "list"): (
        0,
        0,
        {**LIST, **REPO, "--exclude-drafts": False, "--exclude-pre-releases": False, "--order": True},
    ),
    ("release", "download"): (
        0,
        1,
        {
            **REPO,
            "--output": True,
            "-O": True,
            "--archive": True,
            "-A": True,
            "--dir": True,
            "-D": True,
            "--pattern": True,
            "-p": True,
            "--clobber": False,
            "--skip-existing": False,
        },
    ),
    ("auth", "status"): (0, 0, {**FORMAT, "--hostname": True, "-h": True, "--active": False}),
    ("gist", "view"): (
        1,
        1,
        {"--files": False, "--filename": True, "-f": True, "--raw": False, "--web": False, "-w": False},
    ),
    ("gist", "list"): (0, 0, {"--limit": True, "-L": True, "--public": False, "--secret": False}),
    ("label", "list"): (0, 0, {**LIST, **REPO, "--search": True, "-S": True, "--order": True, "--sort": True}),
}
READ_VERBS = {g: {v for group, v in READ_GRAMMARS if group == g} for g, _ in READ_GRAMMARS}

# Raw writes are only forwarded for a proven private destination. Closed flags
# prevent an unknown option/value from manufacturing that proof.
WRITE_GRAMMARS = {
    ("issue", "create"): (
        0,
        0,
        {
            **REPO,
            "--title": True,
            "-t": True,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--label": True,
            "-l": True,
            "--assignee": True,
            "-a": True,
            "--milestone": True,
            "-m": True,
        },
    ),
    ("issue", "comment"): (1, 1, {**REPO, "--body": True, "-b": True, "--body-file": True, "-F": True}),
    ("issue", "edit"): (
        1,
        1,
        {
            **REPO,
            "--title": True,
            "-t": True,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--add-label": True,
            "--remove-label": True,
            "--milestone": True,
            "-m": True,
            "--remove-milestone": False,
        },
    ),
    ("issue", "close"): (1, 1, {**REPO, "--comment": True, "-c": True, "--reason": True, "-r": True}),
    ("pr", "create"): (
        0,
        0,
        {
            **REPO,
            "--title": True,
            "-t": True,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--base": True,
            "-B": True,
            "--head": True,
            "-H": True,
            "--draft": False,
            "-d": False,
        },
    ),
    ("pr", "edit"): (
        0,
        1,
        {
            **REPO,
            "--title": True,
            "-t": True,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--add-label": True,
            "--remove-label": True,
        },
    ),
    ("pr", "comment"): (0, 1, {**REPO, "--body": True, "-b": True, "--body-file": True, "-F": True}),
    ("pr", "review"): (
        0,
        1,
        {
            **REPO,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--approve": False,
            "-a": False,
            "--comment": False,
            "-c": False,
            "--request-changes": False,
            "-r": False,
        },
    ),
    ("pr", "merge"): (
        0,
        1,
        {
            **REPO,
            "--squash": False,
            "-s": False,
            "--subject": True,
            "-t": True,
            "--body": True,
            "-b": True,
            "--body-file": True,
            "-F": True,
            "--match-head-commit": True,
            "--disable-auto": False,
        },
    ),
}


WRITE_GRAMMARS.update(
    {
        ("release", "create"): (
            1,
            1000,
            {
                **REPO,
                "--title": True,
                "-t": True,
                "--notes": True,
                "-n": True,
                "--notes-file": True,
                "-F": True,
                "--target": True,
                "--draft": False,
                "--prerelease": False,
            },
        ),
        ("release", "edit"): (
            1,
            1,
            {**REPO, "--title": True, "-t": True, "--notes": True, "-n": True, "--notes-file": True, "-F": True},
        ),
        ("release", "upload"): (2, 1000, {**REPO, "--clobber": False}),
        ("label", "create"): (
            1,
            1,
            {**REPO, "--description": True, "-d": True, "--color": True, "-c": True, "--force": False, "-f": False},
        ),
        ("label", "edit"): (
            1,
            1,
            {**REPO, "--description": True, "-d": True, "--color": True, "-c": True, "--name": True, "-n": True},
        ),
    }
)
PRIVATE_API = (
    1,
    1,
    {
        "--method": True,
        "-X": True,
        "--field": True,
        "-F": True,
        "--raw-field": True,
        "-f": True,
        "--input": True,
        "--hostname": True,
    },
)


@dataclass
class FrozenCommand:
    argv: list[str]
    destination: str
    write: bool


def parse(argv: list[str], grammar):
    """Consume every token with known arity; return option pairs and positionals."""
    low, high, flags = grammar
    found, positional = [], []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            key, sep, value = token.partition("=")
            if key not in flags:
                raise PublishBlocked("OPSEC: unknown raw gh flag; use a typed publisher verb.")
            if flags[key]:
                if not sep:
                    i += 1
                    if i >= len(argv) or (argv[i].startswith("-") and argv[i] != "-"):
                        raise PublishBlocked("OPSEC: missing raw gh flag value; use a typed publisher verb.")
                    value = argv[i]
                if not value:
                    raise PublishBlocked("OPSEC: empty raw gh flag value; use a typed publisher verb.")
            elif sep:
                raise PublishBlocked("OPSEC: boolean raw gh flags take no value.")
            found.append((key, value))
        else:
            positional.append(token)
        i += 1
    if not low <= len(positional) <= high:
        raise PublishBlocked("OPSEC: unexpected raw gh positional; use a typed publisher verb.")
    return found, positional


def repository(cwd, environment, explicit=None, reader=subprocess.run):
    """Explicit selection wins over GH_REPO, then the unambiguous Git origin."""
    selected = explicit or environment.get("GH_REPO")
    if selected:
        return normalize_repository(selected, environment.get("GH_HOST", "github.com"))
    try:
        result = reader(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return normalize_repository(result.stdout.strip()) if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def admit(argv, *, cwd, environment, reader=subprocess.run):
    """Admit an exact builtin read or a closed-grammar verified private write."""
    if tuple(argv) in {("--version",), ("version",)}:
        return FrozenCommand(list(argv), "unknown", False)
    if len(argv) < 2:
        raise PublishBlocked("OPSEC: use python -m scripts.publish <verb>; raw gh command refused.")
    if argv[0] == "api":
        found, positional = parse(argv[1:], PRIVATE_API)
        endpoint = positional[0]
        match = re.fullmatch(
            r"repos/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(?:issues|pulls|releases|statuses|milestones|labels)(?:/[A-Za-z0-9_-]+)*(?:\?[A-Za-z0-9_=&-]+)?",
            endpoint,
        )
        hosts = [value for flag, value in found if flag == "--hostname"]
        host = hosts[-1] if hosts else environment.get("GH_HOST", "github.com")
        dest = normalize_repository(f"{host}/{match[1]}/{match[2]}") if match else "unknown"
        if not is_private(dest):
            raise PublishBlocked(
                "OPSEC: raw API refused; use python -m scripts.publish issue-comment-json or a named read helper."
            )
        return FrozenCommand(list(argv), dest, True)
    # Globals can precede a builtin; only the two repository selector forms.
    start, globals_ = 0, []
    while start < len(argv) and argv[start] in REPO:
        if start + 1 >= len(argv) or argv[start + 1].startswith("-"):
            raise PublishBlocked("OPSEC: missing repository selector.")
        globals_.extend(argv[start : start + 2])
        start += 2
    key = tuple(argv[start : start + 2])
    if key in READ_GRAMMARS:
        parse(globals_ + argv[start + 2 :], READ_GRAMMARS[key])
        return FrozenCommand(list(argv), "unknown", False)
    if key not in WRITE_GRAMMARS:
        raise PublishBlocked(
            "OPSEC: raw gh refused; use python -m scripts.publish <verb> (API/aliases/extensions refused)."
        )
    found, positional = parse(globals_ + argv[start + 2 :], WRITE_GRAMMARS[key])
    selectors = [value for flag, value in found if flag in REPO]
    dest = repository(cwd, environment, selectors[-1] if selectors else None, reader)
    if key[0] in {"issue", "pr"} and positional:
        reference = positional[0]
        if re.fullmatch(r"https://[\w.-]+/[\w.-]+/[\w.-]+/(issues|pull)/[1-9][0-9]*", reference):
            dest = normalize_repository("/".join(reference.removeprefix("https://").split("/")[:3]))
        elif re.fullmatch(r"[1-9][0-9]*", reference) or (
            key[0] == "pr" and re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", reference)
        ):
            pass
        else:
            dest = "unknown"
    if not is_private(dest):
        raise PublishBlocked(f"OPSEC: raw public write refused; use python -m scripts.publish {key[0]}-{key[1]}.")
    return FrozenCommand(list(argv), dest, True)
