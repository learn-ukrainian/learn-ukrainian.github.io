"""Snapshot supported gh writes after shell expansion, before any outbound call."""

from __future__ import annotations

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

VALUE_OPTIONS = {
    "--description",
    "-d",
    "--color",
    "--name",
    "--repo",
    "-R",
    "--hostname",
    "--body",
    "-b",
    "--body-file",
    "--title",
    "-t",
    "--comment",
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
    "--jq",
    "-q",
    "--template",
    "-T",
    "--recover",
    "--reviewer",
    "-r",
    "--assignee",
    "-a",
    "--label",
    "-l",
    "--milestone",
    "-m",
    "--project",
    "-p",
    "--match-head-commit",
    "--add-label",
    "--remove-label",
    "--add-assignee",
    "--remove-assignee",
    "--add-reviewer",
    "--remove-reviewer",
    "--add-project",
    "--remove-project",
    "--reason",
    "--header",
    "--cache",
    "--preview",
}
TEXT_OPTIONS = {
    "--description",
    "-d",
    "--name",
    "--body",
    "-b",
    "--title",
    "-t",
    "--comment",
    "--subject",
    "--notes",
    "-n",
}
FILE_OPTIONS = {"--body-file", "--notes-file", "--input"}


@dataclass
class FrozenCommand:
    argv: list[str]
    destination: str = "unknown"
    texts: list[str] = field(default_factory=list)
    write: bool = False
    stdin: bytes | None = None


def options(argv: list[str]) -> tuple[list[tuple[int, str, str]], list[str]]:
    """Parse value flags including attached short flags; retain argv indexes for rewriting."""
    found, positional = [], []
    api = "api" in argv[:3]
    review = "review" in argv[:3] and "pr" in argv[:2]
    i = 0
    while i < len(argv):
        arg = argv[i]
        name, sep, value = arg.partition("=")
        if review and arg in {"--comment", "-c"}:
            i += 1
            continue
        if not api and name == "-F":
            name = "--body-file"
        if name in VALUE_OPTIONS:
            if not sep:
                i += 1
                if i >= len(argv):
                    raise PublishBlocked("OPSEC: option value missing; write refused.")
                value = argv[i]
            found.append((i, name, value))
        elif len(arg) > 2 and arg[:2] in VALUE_OPTIONS and not arg.startswith("--"):
            found.append((i, arg[:2], arg[2:]))
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
    """Pin explicit repo, URL, API route or remote. Only positive private identity exempts."""
    values = {name: value for _, name, value in found}
    host = values.get("--hostname", environment.get("GH_HOST", "github.com"))
    api = positional and positional[0] == "api"
    route = positional[1] if api and len(positional) > 1 else ""
    if api and (route == "graphql" or route.endswith("/graphql")):
        return "unknown"
    explicit = values.get("--repo", values.get("-R"))
    match = re.search(r"(?:^|/)repos/([^/]+)/([^/?]+)", route)
    if match and "{" not in match.group(0):
        if route.startswith(("https://", "http://")):
            from urllib.parse import urlsplit

            host = urlsplit(route).hostname or "unknown"
            if host == "api.github.com":
                host = "github.com"
        return normalize_repository(f"{match[1]}/{match[2]}", host)
    if api and not match:
        return "unknown"
    urls = [p for p in positional if p.startswith(("https://", "http://"))]
    if urls:
        return normalize_repository(urls[-1], host)
    if explicit:
        return normalize_repository(explicit, host)
    if environment.get("GH_REPO"):
        return normalize_repository(environment["GH_REPO"], host)
    # Resolve local remotes without an outbound lookup. Ambiguous multi-remote
    # selection requires an explicit repo rather than accidentally exempting it.
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
    frozen = FrozenCommand(list(argv))
    found, positional = options(argv)
    if not positional:
        yield frozen
        return
    group = positional[0]
    verb = positional[1] if len(positional) > 1 else ""
    api = group == "api"
    graphql = api and (verb == "graphql" or verb.endswith("/graphql"))
    values = {name: value for _, name, value in found}
    if api:
        method = values.get(
            "--method",
            values.get(
                "-X",
                "POST"
                if any(name in {"-f", "-F", "--field", "--raw-field", "--input"} for _, name, _ in found)
                else "GET",
            ),
        ).upper()
        frozen.write = method not in {"GET", "HEAD", "OPTIONS"}
    else:
        frozen.write = group in {"issue", "pr", "release", "label"} and verb in {
            "create",
            "edit",
            "comment",
            "review",
            "close",
            "merge",
        }
    if not frozen.write and not (graphql):
        yield frozen
        return
    frozen.destination = destination(argv, found, positional, cwd=cwd, environment=environment, reader=reader)
    if is_private(frozen.destination):
        yield frozen
        return
    with tempfile.TemporaryDirectory(prefix="lu-publish-") as temp:
        if group == "label" and len(positional) > 2:
            frozen.texts.append(positional[2])
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
                    target = str(Path(temp) / str(len(copies)))
                    Path(target).write_bytes(content)
                    copies[value] = (content, target)
                except Exception:
                    raise PublishBlocked("OPSEC: text input unreadable; use a UTF-8 --body-file.") from None
            return copies[value]

        def replace(index: int, name: str, value: str):
            original = frozen.argv[index]
            if original.startswith(name + "="):
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
                frozen.texts.append(decoded)
                if name == "--input":
                    with suppress(ValueError):
                        frozen.texts.extend(json_strings(json.loads(decoded)))
                if name == "--input" and graphql:
                    try:
                        payload = json.loads(content)
                        fields.update(payload)
                    except Exception:
                        raise PublishBlocked("OPSEC: GraphQL input must be JSON; write refused.") from None
            elif name in TEXT_OPTIONS:
                frozen.texts.append(value)
            elif api and name in {"-F", "--field", "-f", "--raw-field"}:
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
                frozen.texts.append(content)
        if graphql:
            document = fields.get("query", "")
            frozen.write = graphql_write(document)
            frozen.texts.extend(json_strings(fields))
            for quoted in re.findall(r'"(?:\\.|[^"\\])*"', document):
                with suppress(ValueError):
                    frozen.texts.append(json.loads(quoted))
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
                frozen.argv.extend(["--repo", frozen.destination])
            elif group != "release":
                raise PublishBlocked("OPSEC: destination unresolved; use --repo OWNER/REPO.")
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
                    frozen.texts.append(title)
                    values["--title"] = title
                if not any(name in values for name in {"--body", "-b", "--body-file"}):
                    frozen.argv.extend(["--body", body])
                    frozen.texts.append(body)
                    values["--body"] = body
            body_present = any(
                name in values for name in {"--body", "-b", "--body-file", "--notes", "-n", "--notes-file"}
            )
            if verb == "edit" and not found:
                raise PublishBlocked("OPSEC: interactive edit refused; use --title or --body-file.")
            if group != "label" and verb in {"comment", "review", "create"} and not body_present:
                raise PublishBlocked("OPSEC: interactive body refused; use --body-file (empty files are allowed).")
            if group != "label" and verb == "create" and not any(name in values for name in {"--title", "-t"}):
                raise PublishBlocked("OPSEC: interactive title refused; use --title.")
            if verb == "merge" and "--disable-auto" not in argv and not {"--body", "--subject"} <= values.keys():
                raise PublishBlocked("OPSEC: merge message unresolved; use --subject and --body explicitly.")
        yield frozen
