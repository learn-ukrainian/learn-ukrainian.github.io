"""Snapshot supported gh writes after shell expansion, before any outbound call."""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path

from scripts.opsec.prepublish import PublishBlocked, is_private, normalize_repository

# Only options needed to materialize inputs are interpreted. This table never
# determines classification or the argument scan set.
VALUE_OPTIONS = {
    "--repo",
    "-R",
    "--hostname",
    "--body",
    "-b",
    "--body-file",
    "--title",
    "-t",
    "--comment",
    "-c",
    "--subject",
    "--notes",
    "--notes-file",
    "-n",
    "-F",
    "-f",
    "--field",
    "--raw-field",
    "--input",
    "--method",
    "-X",
    "--base",
    "-B",
    "--head",
    "-H",
    "--recover",
}
FILE_OPTIONS = {"--body-file", "--notes-file", "--input"}
READ_VERBS = {
    "pr": {"view", "list", "status", "checks", "diff", "checkout"},
    "issue": {"view", "list", "status"},
    "run": {"view", "list", "watch", "download"},
    "workflow": {"list", "view"},
    "repo": {"view", "list", "clone"},
    "release": {"view", "list", "download", "verify", "verify-asset"},
    "auth": {"status"},
    "search": {"code", "commits", "issues", "prs", "repos"},
    "gist": {"view", "list", "clone"},
    "label": {"list"},
    "project": {"view", "list", "field-list", "item-list"},
    "org": {"list"},
    "cache": {"list"},
    "ruleset": {"view", "list", "check"},
    "secret": {"list"},
    "variable": {"list", "get"},
    "ssh-key": {"list"},
    "gpg-key": {"list"},
}


@dataclass
class FrozenCommand:
    argv: list[str]
    destination: str = "unknown"
    texts: list[str] = field(default_factory=list)
    write: bool = False
    stdin: bytes | None = None
    field_names: list[str] = field(default_factory=list)

    def add_text(self, text: str, name: str = "payload") -> None:
        self.texts.append(text)
        self.field_names.append(name)

    def add_json(self, value, name: str = "input") -> None:
        for text in json_strings(value):
            self.add_text(text, name)


def command_indexes(argv: list[str]) -> list[int]:
    """Find group/verb without interpreting command-specific flag grammar."""
    indexes = []
    i = 0
    while i < len(argv) and len(indexes) < 2:
        arg = argv[i]
        if arg in {"--repo", "-R", "--hostname"}:
            i += 2
            continue
        if not arg.startswith("-"):
            indexes.append(i)
        i += 1
    return indexes


def command_parts(argv: list[str]) -> tuple[str, str]:
    parts = [argv[i] for i in command_indexes(argv)]
    return tuple([*parts, "", ""][:2])


def no_text_token(token: str) -> bool:
    """Structural flag, number, SHA or bare repository; labels remain text.

    Attached short values and long assignments are text, except a repository
    selector whose value is itself a bare OWNER/REPO. Command names are removed
    by index before this predicate is applied.
    """
    if token.startswith("--repo="):
        token = token.partition("=")[2]
    elif token.startswith("-R") and len(token) > 2:
        token = token[2:].removeprefix("=")
    return bool(
        re.fullmatch(r"(?:--[a-z][a-z0-9-]*|-[A-Za-z]|[0-9]+|[a-fA-F0-9]{7,40}|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", token)
    )


def expand_api_clusters(argv: list[str]) -> list[str]:
    """Split boolean API shorts before an attached value option, preserving replay."""
    if command_parts(argv)[0] != "api":
        return argv
    result = []
    for arg in argv:
        if len(arg) > 2 and arg.startswith("-") and not arg.startswith("--"):
            tail = arg[1:]
            while tail and tail[0] in "isp":
                result.append("-" + tail[0])
                tail = tail[1:]
            if tail:
                result.append("-" + tail)
        else:
            result.append(arg)
    return result


def options(argv: list[str]) -> tuple[list[tuple[int, str, str]], list[str]]:
    """Parse value flags including attached short flags; retain argv indexes for rewriting."""
    found, positional = [], []
    group, verb = command_parts(argv)
    api = group == "api"
    review = (group, verb) == ("pr", "review")
    value_options = set(VALUE_OPTIONS)
    if not api and (group, verb) != ("workflow", "run"):
        value_options -= {"-f", "--field", "--raw-field"}
    i = 0
    while i < len(argv):
        arg = argv[i]
        name, sep, value = arg.partition("=")
        if review and arg in {"--comment", "-c"}:
            i += 1
            continue
        if not api and (group, verb) != ("workflow", "run") and name == "-F":
            name = "--body-file"
        if name in value_options:
            if not sep:
                i += 1
                if i >= len(argv):
                    raise PublishBlocked("OPSEC: option value missing; write refused.")
                value = argv[i]
            found.append((i, name, value))
        elif len(arg) > 2 and arg[:2] in value_options and not arg.startswith("--"):
            found.append(
                (
                    i,
                    "--body-file" if not api and (group, verb) != ("workflow", "run") and arg[:2] == "-F" else arg[:2],
                    arg[2:],
                )
            )
        elif not arg.startswith("-"):
            positional.append(arg)
        i += 1
    return found, positional


def json_strings(value):
    """Inspect semantic JSON strings as well as their original encoded payload."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in json_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in json_strings(item)]
    return []


def graphql_write(document: str) -> bool:
    """Lex operation definitions outside strings/comments and selection-set nesting.

    Conservative across named operations: any mutation in a document is scanned.
    A query sent with POST stays a read. Invalid/unknown operations are refused.
    """
    tokens = re.findall(r'"""(?:\\"""|[\s\S])*?"""|"(?:\\.|[^"\\])*"|#[^\r\n]*|[A-Za-z_][A-Za-z0-9_]*|[^\s,]', document)
    tokens = [token for token in tokens if not token.startswith("#")]
    operations = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "{":
            operations.append("query")
        elif token in {"query", "mutation", "subscription", "fragment"}:
            if token != "fragment":
                operations.append(token)
            index += 1
            parentheses = 0
            while index < len(tokens):
                token = tokens[index]
                if token == "(":
                    parentheses += 1
                elif token == ")":
                    parentheses -= 1
                    if parentheses < 0:
                        raise PublishBlocked("OPSEC: unresolved GraphQL operation; write refused.")
                elif token == "{" and parentheses == 0:
                    break
                index += 1
            if index == len(tokens):
                raise PublishBlocked("OPSEC: unresolved GraphQL operation; write refused.")
        else:
            raise PublishBlocked("OPSEC: unresolved GraphQL operation; write refused.")
        braces = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if token == "{":
                braces += 1
            elif token == "}":
                braces -= 1
                if braces == 0:
                    break
        if braces:
            raise PublishBlocked("OPSEC: unresolved GraphQL operation; write refused.")
    if not operations or "subscription" in operations:
        raise PublishBlocked("OPSEC: unresolved GraphQL operation; write refused.")
    return "mutation" in operations


def _read(args: list[str], *, cwd: Path, environment: dict, reader) -> str:
    result = reader(
        args,
        cwd=cwd,
        env={k: v for k, v in environment.items() if k != "LU_OPSEC_OVERRIDE"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if result.returncode:
        raise PublishBlocked(
            "OPSEC: generated text or destination could not be resolved; use explicit text and repository."
        )
    return result.stdout.strip()


def destination(argv: list[str], found: list, positional: list[str], *, cwd: Path, environment: dict, reader) -> str:
    """Exempt only agreeing, positive identities; ambiguous destinations are public."""
    from urllib.parse import urlsplit

    hosts = [value for _, name, value in found if name == "--hostname"]
    hosts += [environment["GH_HOST"]] if environment.get("GH_HOST") else []
    if len({host.lower() for host in hosts}) > 1:
        return "unknown"
    host = hosts[-1] if hosts else "github.com"
    identities = [normalize_repository(value, host) for _, name, value in found if name in {"--repo", "-R"}]
    if environment.get("GH_REPO"):
        identities.append(normalize_repository(environment["GH_REPO"], host))
    group, verb = command_parts(argv)
    if group == "api":
        route = positional[1] if len(positional) > 1 else ""
        match = re.search(r"(?:^|/)repos/([^/]+)/([^/?]+)", route)
        if not match or "{" in match.group(0):
            return "unknown"
        route_host = host
        if route.startswith(("https://", "http://")):
            route_host = urlsplit(route).hostname or "unknown"
            if route_host == "api.github.com":
                route_host = "github.com"
        identities.append(normalize_repository(f"{match[1]}/{match[2]}", route_host))
    elif group == "repo" and verb in {"edit", "create", "delete", "rename", "archive", "fork"}:
        if len(positional) > 2:
            identities.append(normalize_repository(positional[2], host))
    # URLs in flag values or arbitrary argument positions cannot grant an
    # exemption. They still veto conflicting/ambiguous destination evidence.
    indexes = command_indexes(argv)
    selector_index = indexes[1] + 1 if len(indexes) > 1 else -1
    selectors = [argv[selector_index]] if group in {"issue", "pr", "repo"} and 0 <= selector_index < len(argv) else []
    repo_urls = [value for _, name, value in found if name in {"--repo", "-R"}]
    for arg in argv:
        for url in re.findall(r"https?://[^\s]+", arg):
            if url in repo_urls:
                continue
            if url not in selectors and not (group == "api" and len(positional) > 1 and url == positional[1]):
                identities.append("unknown")
            elif group != "api":
                identities.append(normalize_repository(url, host))
    if identities:
        targets = set(identities)
        return targets.pop() if len(targets) == 1 else "unknown"
    # Remote inference is allowed only in the absence of explicit evidence.
    try:
        result = subprocess.run(
            ["git", "config", "--get-regexp", r"^remote\..*\.url$"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        targets = {
            normalize_repository(line.split(None, 1)[1], host)
            for line in result.stdout.splitlines()
            if len(line.split(None, 1)) == 2
        }
        if len(targets) == 1:
            return targets.pop()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


@contextmanager
def snapshot(
    argv: list[str], *, cwd: Path, environment: dict, stdin=None, reader=subprocess.run
) -> Iterator[FrozenCommand]:
    """Read each file/stdin once and forward controlled copies of precisely those bytes."""
    group, verb = command_parts(argv)
    # Unknown groups/verbs fail closed as writes. Reads never parse flags or
    # load private tooling. API needs its own payload/method semantics below.
    if group != "api" and verb in READ_VERBS.get(group, set()):
        yield FrozenCommand(list(argv))
        return
    original_argv = list(argv)
    argv = expand_api_clusters(argv)
    frozen = FrozenCommand(list(argv), write=True)
    found, positional = options(argv)
    values = {name: value for _, name, value in found}
    api = group == "api"
    # API flags can precede the endpoint; materialization finds it separately.
    if api:
        verb = positional[1] if len(positional) > 1 else ""
    graphql = api and (verb == "graphql" or verb.endswith("/graphql"))
    if api:
        method = values.get("--method", values.get("-X", "GET")).upper()
        has_payload = any(name in {"-f", "-F", "--field", "--raw-field", "--input"} for _, name, _ in found)
        frozen.write = has_payload or method not in {"GET", "HEAD", "OPTIONS"}
        if not frozen.write and not graphql:
            yield frozen
            return
    frozen.destination = destination(argv, found, positional, cwd=cwd, environment=environment, reader=reader)
    if is_private(frozen.destination):
        yield frozen
        return
    with tempfile.TemporaryDirectory(prefix="lu-publish-") as temp:
        copies: dict[str, tuple[bytes, str]] = {}

        def copy_file(value: str) -> tuple[bytes, str]:
            if value not in copies:
                try:
                    if value == "-":
                        content = stdin
                        if content is None:
                            if sys.stdin.isatty():
                                raise PublishBlocked("OPSEC: interactive text refused; use --body-file.")
                            content = sys.stdin.buffer.read()
                        if isinstance(content, str):
                            content = content.encode("utf-8")
                        frozen.stdin = content
                    else:
                        content = (cwd / value).read_bytes()
                    content.decode("utf-8")
                    target_path = Path(temp) / str(len(copies))
                    target_path = target_path / (Path(value).name if value != "-" else "stdin.txt")
                    target_path.parent.mkdir()
                    target = str(target_path)
                    Path(target).write_bytes(content)
                    copies[value] = (content, target)
                except Exception:
                    raise PublishBlocked("OPSEC: text input unreadable; use a UTF-8 --body-file.") from None
            return copies[value]

        def replace(index: int, name: str, value: str):
            original = frozen.argv[index]
            if name == "--body-file" and original.startswith("-F"):
                frozen.argv[index] = "-F=" + value if original.startswith("-F=") else "-F" + value
            elif original.startswith(name + "="):
                frozen.argv[index] = name + "=" + value
            elif original.startswith(name) and len(name) == 2 and original != name:
                frozen.argv[index] = name + value
            else:
                frozen.argv[index] = value

        fields = {}
        if (
            graphql
            and "--input" in values
            and any(
                name in {"-f", "-F", "--field", "--raw-field"} and value.partition("=")[0] == "query"
                for _, name, value in found
            )
        ):
            raise PublishBlocked("OPSEC: mixed GraphQL documents unresolved; use one --input JSON or one query field.")
        for index, name, value in found:
            if name in FILE_OPTIONS:
                content, target = copy_file(value)
                replace(index, name, target)
                decoded = content.decode("utf-8")
                frozen.add_text(decoded, name.lstrip("-"))
                if name == "--input":
                    with suppress(ValueError):
                        frozen.add_json(json.loads(decoded))
                if name == "--input" and graphql:
                    try:
                        payload = json.loads(content)
                        fields.update(payload)
                    except Exception:
                        raise PublishBlocked("OPSEC: GraphQL input must be JSON; write refused.") from None
            elif (api or (group, verb) == ("workflow", "run")) and name in {"-F", "--field", "-f", "--raw-field"}:
                key, _, content = value.partition("=")
                if name in {"-F", "--field"} and content.startswith("@"):
                    data, target = copy_file(content[1:])
                    content = data.decode("utf-8")
                    replace(index, name, key + "=@" + target)
                elif name in {"-F", "--field"} and content in {"{owner}", "{repo}", "{branch}"}:
                    parts = frozen.destination.split("/")
                    if content == "{branch}":
                        content = _read(
                            ["git", "branch", "--show-current"], cwd=cwd, environment=environment, reader=reader
                        )
                    elif len(parts) == 3:
                        content = parts[1 if content == "{owner}" else 2]
                    else:
                        raise PublishBlocked("OPSEC: field placeholder unresolved; use a literal field value.")
                    replace(index, name, key + "=" + content)
                fields[key] = content
                frozen.add_text(content, "api-field")
        if api and "/contents/" in verb:
            payload = fields
            if "--input" in values:
                try:
                    payload = json.loads(copies[values["--input"]][0])
                except (ValueError, TypeError):
                    raise PublishBlocked("OPSEC: contents input unresolved; use JSON fields.") from None
            if "content" in payload:
                try:
                    frozen.add_text(base64.b64decode(payload["content"], validate=True).decode("utf-8"), "content")
                except (ValueError, UnicodeDecodeError):
                    raise PublishBlocked("OPSEC: contents payload must be base64 UTF-8 text; write refused.") from None
        if graphql:
            document = fields.get("query", "")
            frozen.write = graphql_write(document)
            frozen.add_json(fields, "graphql")
            for quoted in re.findall(r'"(?:\\.|[^"\\])*"', document):
                with suppress(ValueError):
                    frozen.add_text(json.loads(quoted), "graphql")
        if not frozen.write:
            # GraphQL queries forward file snapshots too, without invoking matcher.
            yield frozen
            return
        frozen.destination = destination(argv, found, positional, cwd=cwd, environment=environment, reader=reader)
        if api:
            # Pin cwd placeholders so gh never re-resolves them after scanning.
            if "{" in verb:
                parts = frozen.destination.split("/")
                if len(parts) != 3 or "{branch}" in verb:
                    raise PublishBlocked("OPSEC: unresolved API placeholder; use an explicit API path.")
                endpoint = verb.replace("{owner}", parts[1]).replace("{repo}", parts[2])
                frozen.argv[frozen.argv.index(verb)] = endpoint
        else:
            if frozen.destination != "unknown":
                selector_present = len(positional) > 2
                if group == "pr" and verb in {"comment", "merge", "review"} and not selector_present:
                    environment["GH_REPO"] = frozen.destination
                elif group not in {"project", "gist", "repo"} and not any(name in values for name in {"--repo", "-R"}):
                    frozen.argv.extend(["--repo", frozen.destination])
            if (
                any(arg in {"-e", "--web", "-w", "--generate-notes"} or arg.startswith("--editor") for arg in argv)
                or "--recover" in values
            ):
                raise PublishBlocked("OPSEC: interactive/generated text refused; use explicit --title and --body-file.")
            if (
                group == "pr"
                and verb == "create"
                and any(arg in {"--fill", "-f", "--fill-first", "--fill-verbose"} for arg in argv)
            ):
                base = values.get("--base", values.get("-B"))
                if not base:
                    try:
                        ref = _read(
                            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                            cwd=cwd,
                            environment=environment,
                            reader=reader,
                        )
                        base = ref.removeprefix("refs/remotes/origin/")
                    except PublishBlocked:
                        raise PublishBlocked("OPSEC: default base unresolved; use --base with --fill.") from None
                head = values.get("--head", values.get("-H", "HEAD"))
                commits = _read(
                    [
                        "git",
                        "-c",
                        "log.ShowSignature=false",
                        "log",
                        "--cherry",
                        "--format=%s%x00%b%x00",
                        f"origin/{base}...{head}",
                    ],
                    cwd=cwd,
                    environment=environment,
                    reader=reader,
                ).split("\0")
                messages = [(commits[i].removeprefix("\n"), commits[i + 1]) for i in range(0, len(commits) - 1, 2)]
                if not messages:
                    raise PublishBlocked("OPSEC: commit text unresolved; use --title and --body-file.")
                if "--fill-first" in argv or len(messages) == 1:
                    title, body = messages[-1]
                else:
                    title = (
                        head
                        if head != "HEAD"
                        else _read(["git", "branch", "--show-current"], cwd=cwd, environment=environment, reader=reader)
                    )
                    title = title.replace("_", " ").replace("-", " ")
                    chunks = []
                    for index, (subject, text) in enumerate(reversed(messages)):
                        chunk = "- **" + subject + "**\n"
                        if "--fill-verbose" in argv:
                            chunk += re.sub(r"(?m)^", "  ", text)
                            if index < len(messages) - 1:
                                chunk += "\n\n"
                        chunks.append(chunk)
                    body = "".join(chunks)
                frozen.argv = [a for a in frozen.argv if a not in {"--fill", "-f", "--fill-first", "--fill-verbose"}]
                if not any(name in values for name in {"--title", "-t"}):
                    frozen.argv.extend(["--title", title])
                    frozen.add_text(title, "title")
                    values["--title"] = title
                if not any(name in values for name in {"--body", "-b", "--body-file"}):
                    frozen.argv.extend(["--body", body])
                    frozen.add_text(body, "body")
                    values["--body"] = body
            body_present = any(
                name in values for name in {"--body", "-b", "--body-file", "--notes", "-n", "--notes-file"}
            )
            if (
                verb == "edit"
                and group in {"issue", "pr", "release", "gist"}
                and not any(
                    a.startswith("-")
                    and a not in {"--repo", "-R", "--hostname"}
                    and not a.startswith(("--repo=", "-R", "--hostname="))
                    for a in argv
                )
            ):
                raise PublishBlocked("OPSEC: interactive edit refused; use --title or --body-file.")
            if group in {"issue", "pr", "release"} and verb in {"comment", "review", "create"} and not body_present:
                raise PublishBlocked("OPSEC: interactive body refused; use --body-file (empty files are allowed).")
            if (
                group in {"issue", "pr", "release"}
                and verb == "create"
                and not any(name in values for name in {"--title", "-t"})
            ):
                raise PublishBlocked("OPSEC: interactive title refused; use --title.")
        # The scan set is independent of the materialization option table:
        # inspect every original token, and every regular file named by a token
        # (including assignment/@/attached-short forms), even for unknown verbs.
        argument_texts = [(arg, f"argument[{i + 1}]") for i, arg in enumerate(original_argv)]
        gist_files = 0
        indexes = set(command_indexes(argv))
        payload = [arg for i, arg in enumerate(argv) if i not in indexes]
        for index, arg in enumerate(argv):
            candidates = [("", arg)]
            if arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
                candidates.append((arg[:2], arg[2:]))
            # A field may contain more than one assignment layer: --field=body=@file.
            for prefix, tail in list(candidates):
                while "=" in tail:
                    head, _, tail = tail.partition("=")
                    prefix += head + "="
                    candidates.append((prefix, tail))
            for prefix, value in candidates:
                if value.startswith("@"):
                    prefix += "@"
                    value = value[1:]
                if value == "-" and (prefix.endswith("@") or group == "gist"):
                    exists = True
                else:
                    try:
                        exists = (cwd / value).is_file()
                    except (OSError, ValueError):
                        exists = False
                if exists:
                    content, target = copy_file(value)
                    name = f"file[{index + 1}]"
                    if content.decode("utf-8") not in frozen.texts:
                        frozen.add_text(content.decode("utf-8"), name)
                    if not any(n in FILE_OPTIONS and v == value for _, n, v in found):
                        with suppress(ValueError):
                            frozen.add_json(json.loads(content), name)
                    # Text values that happen to name files are scanned too,
                    # but remain literal text. File-input options above already
                    # replay copies; gist operands and @ references do so here.
                    literal = any(i == index and n not in FILE_OPTIONS for i, n, _ in found)
                    previous = argv[index - 1] if index else ""
                    gist_file = group == "gist" and (
                        (verb == "create" and not literal and previous not in {"-d", "--desc"})
                        or (verb == "edit" and previous in {"--add", "-a"})
                    )
                    if index not in indexes and frozen.argv[index] == arg and (prefix.endswith("@") or gist_file):
                        frozen.argv[index] = prefix + target
                        if gist_file:
                            gist_files += 1
        if stdin is not None and frozen.stdin is None:
            frozen.stdin = stdin.encode("utf-8") if isinstance(stdin, str) else stdin
            try:
                frozen.add_text(frozen.stdin.decode("utf-8"), "stdin")
            except (AttributeError, UnicodeDecodeError):
                raise PublishBlocked("OPSEC: stdin must be UTF-8 text; write refused.") from None
        if (group, verb) == ("secret", "set") and not any(name in values for name in {"--body", "-b"}):
            content, _ = copy_file("-")
            frozen.add_text(content.decode("utf-8"), "stdin")
        if group == "gist" and verb == "create" and not gist_files:
            content, target = copy_file("-")
            frozen.add_text(content.decode("utf-8"), "stdin")
            frozen.argv.append(target)
        if frozen.texts or any(not no_text_token(arg) for arg in payload):
            for text, name in argument_texts:
                frozen.add_text(text, name)
        yield frozen
