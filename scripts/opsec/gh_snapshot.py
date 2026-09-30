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
    "-c",
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
    field_names: list[str] = field(default_factory=list)

    def add_text(self, text: str, name: str = "payload") -> None:
        self.texts.append(text)
        self.field_names.append(name)

    def add_json(self, value, name: str = "input") -> None:
        for text in json_strings(value):
            self.add_text(text, name)


def command_parts(argv: list[str]) -> tuple[str, str]:
    """Locate the command after global repository/host selectors."""
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in {"--repo", "-R", "--hostname"}:
            i += 2
        elif arg.startswith("-"):
            i += 1
        else:
            return arg, argv[i + 1] if i + 1 < len(argv) else ""
    return "", ""


def expand_api_clusters(argv: list[str]) -> list[str]:
    """Split boolean API shorts before an attached value option, preserving replay."""
    if command_parts(argv)[0] != "api":
        return argv
    result = []
    for arg in argv:
        if len(arg) > 2 and arg.startswith("-") and not arg.startswith("--"):
            tail = arg[1:]
            while tail and tail[0] in "is":
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
    if group not in {"label", "gist"}:
        value_options.discard("-d")
    if (group, verb) == ("workflow", "list"):
        value_options.discard("-a")
    if review:
        value_options.discard("-a")
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
    if not api and len(positional) > 2 and positional[:2] == ["repo", "edit"]:
        return normalize_repository(positional[2], host)
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
    group, verb = command_parts(argv)
    # Reads return before value parsing: their option meanings cannot refuse publication.
    writes = {
        "issue": {"create", "edit", "comment", "close", "reopen"},
        "pr": {"create", "edit", "comment", "review", "close", "reopen", "merge"},
        "release": {"create", "edit"},
        "label": {"create", "edit"},
        "repo": {"edit"},
        "workflow": {"run"},
        "project": {"item-create"},
        "gist": {"create"},
    }
    if group != "api" and verb not in writes.get(group, set()):
        yield FrozenCommand(list(argv))
        return
    argv = expand_api_clusters(argv)
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
        frozen.write = verb in writes.get(group, set())
    if not frozen.write and not (graphql):
        yield frozen
        return
    frozen.destination = destination(argv, found, positional, cwd=cwd, environment=environment, reader=reader)
    if is_private(frozen.destination):
        yield frozen
        return
    with tempfile.TemporaryDirectory(prefix="lu-publish-") as temp:
        if group == "label" and len(positional) > 2:
            frozen.add_text(positional[2], "name")
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
                    if group == "gist":
                        target_path = target_path / (Path(value).name if value != "-" else "gistfile.txt")
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
            elif name in TEXT_OPTIONS:
                frozen.add_text(value, name.lstrip("-"))
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
            elif group not in {"release", "project", "gist"}:
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
                    frozen.add_text(title, "title")
                    values["--title"] = title
                if not any(name in values for name in {"--body", "-b", "--body-file"}):
                    frozen.argv.extend(["--body", body])
                    frozen.add_text(body, "body")
                    values["--body"] = body
            body_present = any(
                name in values for name in {"--body", "-b", "--body-file", "--notes", "-n", "--notes-file"}
            )
            if verb == "edit" and not found:
                raise PublishBlocked("OPSEC: interactive edit refused; use --title or --body-file.")
            if group in {"issue", "pr", "release"} and verb in {"comment", "review", "create"} and not body_present:
                raise PublishBlocked("OPSEC: interactive body refused; use --body-file (empty files are allowed).")
            if (
                group in {"issue", "pr", "release"}
                and verb == "create"
                and not any(name in values for name in {"--title", "-t"})
            ):
                raise PublishBlocked("OPSEC: interactive title refused; use --title.")
            if group == "gist":
                for value in positional[2:] or ["-"]:
                    content, target = copy_file(value)
                    frozen.add_text(content.decode("utf-8"), "gist-file")
                    if value in frozen.argv:
                        frozen.argv[frozen.argv.index(value)] = target
                    else:
                        frozen.argv.append(target)
        yield frozen
