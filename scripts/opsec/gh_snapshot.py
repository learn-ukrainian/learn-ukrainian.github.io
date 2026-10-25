"""Raw gh exposure controls. Public writes belong to scripts.publish.github.

Read endpoints, flags and operands belong to gh. Only write admission and
credential, file-upload and external-host protections belong here.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from scripts.opsec.prepublish import PublishBlocked, check_texts, internal_environment, is_private, normalize_repository

# Write grammars retain their closed fields and private-destination proof.
REPO = {"--repo": True, "-R": True}
READ_HEADERS = {"accept", "if-none-match", "x-github-api-version"}


def _has_dot_only_segment(value: str) -> bool:
    cleaned = re.sub(r"%(?:2e|2E)", ".", value)
    return any(re.fullmatch(r"\.+", seg) for seg in re.split(r"[/?#\\]", cleaned))


def _validate_read_repo(repo_str: str) -> None:
    if _has_dot_only_segment(repo_str):
        raise PublishBlocked("OPSEC: dot-only segments refused in repository selector.")
    val = repo_str.strip().removesuffix(".git")
    val = re.sub(r"^git@([^:]+):", r"\1/", val)
    val = re.sub(r"^https?://", "", val)
    parts = [p for p in val.split("/") if p]
    if len(parts) >= 3:
        host = parts[0]
        if host.lower() != "github.com":
            raise PublishBlocked("OPSEC: non-github.com repository host refused for reads.")
    elif len(parts) == 2 and ("." in parts[0] or ":" in parts[0]) and parts[0].lower() != "github.com":
        raise PublishBlocked("OPSEC: non-github.com repository host refused for reads.")


def _validate_read_environment(environment: dict[str, str]) -> None:
    gh_host = environment.get("GH_HOST")
    if gh_host and gh_host.strip().lower() != "github.com":
        raise PublishBlocked("OPSEC: non-github.com GH_HOST refused for reads.")
    gh_repo = environment.get("GH_REPO")
    if gh_repo:
        _validate_read_repo(gh_repo)


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
            env=internal_environment(environment),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return normalize_repository(result.stdout.strip()) if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def admit(argv, *, cwd, environment, reader=subprocess.run):
    """Pass native reads without endpoint/flag inventories; retain write and exposure controls."""
    if tuple(argv) in {("--version",), ("version",)}:
        return FrozenCommand(list(argv), "unknown", False)
    if len(argv) < 2:
        raise PublishBlocked("OPSEC: use python -m scripts.publish <verb>; raw gh command refused.")
    if argv[0] == "api":
        from scripts.common import github_client

        _validate_read_environment(environment)
        call = github_client._gh_api_call(argv[1:], stdin=None, cwd=cwd)
        if call is None:
            # The shared native parser models gh's argument checks. A parsed
            # command that cannot build a request makes no HTTP call; gh owns
            # its original usage diagnostic (for example --slurp alone).
            if github_client._gh_api_argv(argv[1:]) is not None:
                return FrozenCommand(list(argv), "unknown", False)
            raise PublishBlocked("OPSEC: unresolved API request; use a typed publisher for writes.")
        host = call.host or environment.get("GH_HOST", "github.com")
        if host.lower() != "github.com":
            raise PublishBlocked("OPSEC: non-github.com API host refused.")
        host_class, path = github_client._canonical_endpoint(call.endpoint, host)
        if host_class == "rejected":
            raise PublishBlocked("OPSEC: external or malformed API host refused.")
        # Preview values become Accept header content even when -p consumes a
        # following apparent field flag. Keep the existing no-exposure scan.
        if call.flags.get("preview"):
            check_texts("unknown", call.flags["preview"], environment=environment)
        for value in call.flags.get("header", []):
            name, separator, _ = value.partition(":")
            if (not separator or name.lower() not in READ_HEADERS
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise PublishBlocked("OPSEC: credential, method-override or malformed API header refused.")
        # A GET can still upload a file or stdin. Preserve that exposure control.
        sources = call.flags.get("input", []) or [
            value for value in call.flags.get("field", []) if value.partition("=")[2].startswith("@")
        ]
        if not sources:
            if call.method in {"GET", "HEAD", "OPTIONS"}:
                return FrozenCommand(list(argv), "unknown", False)
            if path == "graphql" and call.method == "POST":
                body = call.body()
                if isinstance(body, bytes) and github_client._graphql_request(github_client._json_body(body))[0] == "query":
                    return FrozenCommand(list(argv), "unknown", False)
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
                "OPSEC: raw API refused; use python -m scripts.publish issue-comment-json or python -m scripts.publish read <name>."
            )
        pinned = [arg for arg in argv]
        pinned += ["--hostname", dest.split("/", 1)[0]]
        return FrozenCommand(pinned, dest, True)
    # Globals can precede a builtin; only the two repository selector forms.
    start, globals_ = 0, []
    while start < len(argv) and argv[start] in REPO:
        if start + 1 >= len(argv) or argv[start + 1].startswith("-"):
            raise PublishBlocked("OPSEC: missing repository selector.")
        globals_.extend(argv[start : start + 2])
        start += 2
    key = tuple(argv[start : start + 2])
    if key == ("pr", "checkout"):
        _validate_read_environment(environment)
        found, positional = parse(
            globals_ + argv[start + 2 :],
            (1, 1, {**REPO, "--branch": True, "-b": True, "--detach": False, "--force": False}),
        )
        for flag, value in found:
            if flag in REPO:
                _validate_read_repo(value)
            elif value and _has_dot_only_segment(value):
                raise PublishBlocked("OPSEC: dot-only segments refused in read command.")
        if any(_has_dot_only_segment(arg) for arg in positional):
            raise PublishBlocked("OPSEC: dot-only segments refused in read command.")
        for arg in positional:
            if arg.startswith(("http://", "https://")) or "://" in arg:
                _validate_read_repo(arg)
        import unicodedata
        from pathlib import Path

        supplied = Path(cwd).absolute()
        resolved = supplied.resolve()
        if (
            supplied != resolved
            or any(unicodedata.category(c).startswith("C") for c in str(supplied))
            or not re.search(r"/\.worktrees/dispatch/[^/]+/[^/]+(?:/|$)", str(resolved))
        ):
            raise PublishBlocked("OPSEC: pr checkout requires a dispatch worktree.")
        try:
            root = reader(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd,
                env=internal_environment(environment),
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
            )
            top = Path(root.stdout.strip()).resolve()
            if (
                root.returncode
                or not re.search(r"/\.worktrees/dispatch/[^/]+/[^/]+$", str(top))
                or not resolved.is_relative_to(top)
            ):
                raise ValueError
        except Exception:
            raise PublishBlocked("OPSEC: pr checkout requires a verified dispatch repository.") from None
        return FrozenCommand(list(argv), "unknown", False)
    if key not in WRITE_GRAMMARS:
        # Keep executable aliases/extensions and credential commands outside this
        # boundary. Native builtin subcommands supply their own read argument grammar.
        groups = {group for group, _ in WRITE_GRAMMARS} | {
            "run", "workflow", "repo", "auth", "gist", "label", "search", "ruleset",
        }
        write_actions = {
            "add", "archive", "cancel", "clone", "close", "comment", "create", "delete",
            "develop", "disable", "edit", "enable", "fork", "import", "install", "link", "lock",
            "merge", "pin", "publish", "ready", "remove", "rename", "reopen", "rerun",
            "revert", "review", "run", "set", "sync", "transfer", "unarchive", "uninstall",
            "unlink", "unlock", "unpin", "update", "update-branch", "upload",
        }
        nested_action = None
        if key in {("repo", "autolink"), ("repo", "deploy-key"), ("repo", "custom-property"), ("issue", "type")}:
            # Cobra finds the first non-flag command, skipping option values.
            # These parent commands inherit only the boolean help flag; other
            # separate long/single-short options consume the following value.
            index = start + 2
            while index < len(argv):
                token = argv[index]
                if token == "--":
                    break
                if token and not token.startswith("-"):
                    nested_action = token
                    break
                takes_value = (
                    "=" not in token and token not in {"--help", "-h"}
                    and (token.startswith("--") or (token.startswith("-") and len(token) == 2))
                )
                index += 2 if takes_value else 1
        if (len(key) != 2 or key[0] not in groups or key[1].startswith("-")
                or key[1] in write_actions or key[1].rsplit("-", 1)[-1] in write_actions
                or nested_action in write_actions
                or (key == ("repo", "autolink") and nested_action == "new")
                or (key[0] == "auth" and (key[1] != "status" or any(
                    arg.startswith("--show-token") or (arg.startswith("-") and not arg.startswith("--") and "t" in arg)
                    for arg in argv[start + 2 :]
                )))):
            raise PublishBlocked("OPSEC: raw write or executable/credential command refused; use a typed publisher.")
        _validate_read_environment(environment)
        tokens = globals_ + argv[start + 2 :]
        for index, token in enumerate(tokens):
            flag, equal, value = token.partition("=")
            if flag in REPO:
                if not equal:
                    value = tokens[index + 1] if index + 1 < len(tokens) else ""
                _validate_read_repo(value)
            elif token.startswith("-R") and token != "-R":
                _validate_read_repo(token[2:].removeprefix("="))
            elif "://" in token:
                _validate_read_repo(token)
        if key[0] == "repo" and len(argv) > start + 2 and not argv[start + 2].startswith("-"):
            _validate_read_repo(argv[start + 2])
        return FrozenCommand(list(argv), "unknown", False)
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
    # Pin the same repository and host whose private exemption was proven.
    pinned = [*key, *positional]
    for flag, value in found:
        if flag not in REPO:
            pinned.append(flag + "=" + value if WRITE_GRAMMARS[key][2][flag] else flag)
    pinned += ["--repo", dest]
    return FrozenCommand(pinned, dest, True)
