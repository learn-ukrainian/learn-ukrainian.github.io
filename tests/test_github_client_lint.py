"""GitHub I/O has one client; exclusions are separately owned migrations."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS = {
    "scripts/delegate.py": (2, "#9878: accountable driver migrates after concurrent edit settles"),
}
CLIENT = "scripts/common/github_client.py"
# Exact API and upload hosts, compared as parsed hostnames.
_GITHUB_API_HOSTS = frozenset({"api.github.com", "uploads.github.com"})
# Shell text is split on whitespace and on quotes so each URL is its own token.
_TOKEN_SEPARATOR = re.compile(r"""[\s'"]+""")


def _exact_host(value: str | None) -> str | None:
    """Hostname for an exact compare: lower case, trailing DNS dots removed."""
    if not value:
        return None
    host = value.rstrip(".").lower()
    return host or None


def _host_before_path_slash(token: str) -> str:
    """Authority text used when ``urlsplit`` raises.

    Choice: do not search the token for a GitHub name. Take the text before
    the first path ``/`` (a ``scheme://`` separator is not a path slash), drop
    userinfo, one unmatched leading ``[``, and a numeric port, then compare
    that hostname exactly. ``https://[api.github.com/...`` is therefore
    ``api.github.com``. A name that appears only after the slash is not.
    """
    _, separator, remainder = token.partition("://")
    authority = remainder if separator else token
    if not separator and authority.startswith("//"):
        authority = authority[2:]
    authority = authority.split("/", 1)[0]
    if "@" in authority:
        authority = authority.rsplit("@", 1)[1]
    if authority.startswith("[") and not authority.endswith("]"):
        authority = authority[1:]
    elif authority.startswith("[") and authority.endswith("]"):
        authority = authority[1:-1]
    if authority.count(":") == 1:
        host_text, _, port = authority.rpartition(":")
        if port.isdigit():
            authority = host_text
    return authority


def _is_shell_variable_name(name: str) -> bool:
    """True for a POSIX name: a letter or underscore, then letters, digits or underscores."""
    if not name or not name.isascii():
        return False
    first, rest = name[0], name[1:]
    return (first.isalpha() or first == "_") and all(char.isalnum() or char == "_" for char in rest)


def _is_long_option_name(name: str) -> bool:
    """True for the name in ``--name=``: a letter or digit, then letters, digits, ``_`` or ``-``."""
    if not name or not name.isascii():
        return False
    first, rest = name[0], name[1:]
    return first.isalnum() and all(char.isalnum() or char in "_-" for char in rest)


def _without_shell_prefix(token: str) -> str:
    """Drop one leading ``NAME=`` or ``--option=``. A query ``=`` is not that prefix."""
    if token.startswith("--"):
        name, separator, value = token[2:].partition("=")
        if separator and _is_long_option_name(name):
            return value
        return token
    name, separator, value = token.partition("=")
    if separator and _is_shell_variable_name(name):
        return value
    return token


def _shell_token_for_host(token: str) -> str:
    """Remove shell syntax that sits outside the URL, then leave the rest to the host parse.

    A token may be wrapped in ``()`` or ``<>`` and may carry one leading ``NAME=`` or
    ``--option=`` prefix. Those peel in either order (``U=(https://...)``,
    ``(--url=https://...)``). The prefix is only a shell variable or a long option, so
    the first ``=`` inside a query stays with its real host.
    """
    wrappers = {"(": ")", "<": ">"}
    while token:
        closer = wrappers.get(token[0])
        if closer is not None and len(token) > 1 and token[-1] == closer:
            token = token[1:-1]
            continue
        peeled = _without_shell_prefix(token)
        if peeled == token:
            return token
        token = peeled
    return token


def _token_is_github_http(token: str) -> bool:
    """True when this token's parsed hostname is a GitHub API, upload, or web host."""
    token = _shell_token_for_host(token)
    if not token:
        return False
    if token.startswith("://"):
        # f"{scheme}://host/..." leaves the authority in this piece.
        token = "//" + token[3:]
    try:
        parts = urlsplit(token)
    except ValueError:
        return _exact_host(_host_before_path_slash(token)) in _GITHUB_API_HOSTS
    host = _exact_host(parts.hostname)
    if host is None and "://" not in token and not any(char.isspace() for char in token):
        # ``api.github.com:443/x`` is parsed with the host in the scheme.
        if parts.scheme in _GITHUB_API_HOSTS and not parts.netloc:
            host = parts.scheme
        elif not parts.scheme:
            host = _exact_host(parts.path.split("/", 1)[0])
    return host in _GITHUB_API_HOSTS or (
        host == "github.com" and parts.scheme == "https" and parts.path.startswith("/")
    )


def _is_github_http_literal(value: str) -> bool:
    """True when a whitespace- or quote-separated token is a GitHub URL.

    ``urlsplit`` supplies the host. A shell command is split so a URL inside
    it is parsed on its own. Before that parse, each token loses a leading
    ``NAME=`` or ``--option=`` prefix and a surrounding ``()`` or ``<>`` pair.
    Scheme-less ``host`` and ``host/path`` tokens are compared exactly,
    because they do not land in ``hostname``. A look-alike host, or a path
    or query that only contains the name, does not match.
    """
    return any(_token_is_github_http(token) for token in _TOKEN_SEPARATOR.split(value) if token)


def bypasses(source: str, path: str) -> list[str]:
    tree = ast.parse(source)
    violations = []
    gh_functions = set()
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    function_names = {node.name for node in functions}
    functions.append(
        ast.FunctionDef(
            name="__module__",
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))],
            decorator_list=[],
        )
    )
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases.update({item.asname or item.name: item.name for item in node.names})
        elif isinstance(node, ast.ImportFrom):
            aliases.update({item.asname or item.name: f"{node.module}.{item.name}" for item in node.names})
    http_objects = set()

    def qualified(node):
        name = ast.unparse(node)
        first, dot, rest = name.partition(".")
        return aliases.get(first, first) + (dot + rest if dot else "")

    constructors = {
        "requests.Session",
        "httpx.Client",
        "httpx.AsyncClient",
        "urllib.request.build_opener",
        "http.client.HTTPSConnection",
        "http.client.HTTPConnection",
    }
    for assignment in ast.walk(tree):
        if (
            isinstance(assignment, (ast.Assign, ast.AnnAssign))
            and isinstance(assignment.value, ast.Call)
            and qualified(assignment.value.func) in constructors
        ):
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            http_objects.update(n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name))
    tainted = set()

    def is_gh(node):
        return any(
            (
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and (
                    Path(n.value).name == "gh"
                    or re.search(r"(?:^|[;&|]\s*)gh\s", n.value)
                    or _is_github_http_literal(n.value)
                    or n.value == "asset_url"
                )
            )
            or (isinstance(n, ast.Name) and n.id in tainted)
            for n in ast.walk(node)
        )

    def track(assignments):
        for _ in range(len(assignments) + 1):
            old = set(tainted)
            for node in assignments:
                if node.value is not None and is_gh(node.value):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    tainted.update(n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name))
            if old == tainted:
                break

    track([n for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))])
    module_tainted = set(tainted)
    # Track commands stored in variables and local wrapper call chains.
    for function in functions:
        tainted = set(module_tainted)
        track([n for n in ast.walk(function) if isinstance(n, (ast.Assign, ast.AnnAssign))])
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and node.args and is_gh(node.args[0]):
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                if name in function_names:
                    gh_functions.add(name)
    github_http = any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and (node.value == "asset_url" or _is_github_http_literal(node.value))
        for node in ast.walk(tree)
    )
    for function in functions:
        tainted = set(module_tainted)
        track([n for n in ast.walk(function) if isinstance(n, (ast.Assign, ast.AnnAssign))])
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            name = ast.unparse(node.func)
            first, dot, rest = name.partition(".")
            name = aliases.get(first, first) + (dot + rest if dot else "")
            subprocess_call = name in {
                "subprocess.run",
                "subprocess.Popen",
                "subprocess.check_output",
                "subprocess.call",
                "subprocess.check_call",
            }
            if subprocess_call and (
                (node.args and is_gh(node.args[0]))
                or any(k.arg in {"args", "command"} and is_gh(k.value) for k in node.keywords)
                or function.name in gh_functions
            ):
                # Git-only invocations in mixed functions are not GitHub I/O.
                argument = node.args[0] if node.args else None
                if (
                    isinstance(argument, (ast.List, ast.Tuple))
                    and argument.elts
                    and isinstance(argument.elts[0], ast.Constant)
                    and argument.elts[0].value in {"git", "jq"}
                ):
                    continue
                if (
                    isinstance(argument, (ast.List, ast.Tuple))
                    and len(argument.elts) > 1
                    and ast.unparse(argument.elts[0]) == "sys.executable"
                    and not (isinstance(argument.elts[1], ast.Constant) and argument.elts[1].value == "-c")
                ):
                    continue
                violations.append(f"{path}:{node.lineno}: gh bypasses shared client")
            if github_http and (
                (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"open", "get", "post", "put", "patch", "delete", "head", "request"}
                    and (
                        (isinstance(node.func.value, ast.Name) and node.func.value.id in http_objects)
                        or (isinstance(node.func.value, ast.Call) and qualified(node.func.value.func) in constructors)
                    )
                    and (is_gh(node) or function.name in gh_functions)
                )
                or (
                    (is_gh(node) or function.name in gh_functions)
                    and name
                    in {
                        "urllib.request.urlopen",
                        "urllib.request.urlretrieve",
                        "urlopen",
                        "requests.get",
                        "requests.post",
                        "requests.put",
                        "requests.patch",
                        "requests.delete",
                        "requests.head",
                        "requests.request",
                        "httpx.get",
                        "httpx.post",
                        "httpx.put",
                        "httpx.patch",
                        "httpx.delete",
                        "httpx.request",
                    }
                )
            ):
                violations.append(f"{path}:{node.lineno}: GitHub HTTP bypasses shared client")
    return sorted(set(violations))


_SCAN_MARKERS = (
    "subprocess",
    "requests",
    "urllib",
    "httpx",
    "http.client",
    "api.github.com",
    "uploads.github.com",
    "github.com/",
)


def inventory_violations(root):
    violations = []
    for path in (root / "scripts").rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        if relative == CLIENT:
            continue
        source = path.read_text(encoding="utf-8")
        # The walker only matches these modules and URL literals. Skipping the
        # rest keeps one full parse per candidate instead of a second walk.
        if not any(marker in source for marker in _SCAN_MARKERS):
            continue
        found = bypasses(source, relative)
        if relative in EXCLUSIONS:
            count, owner = EXCLUSIONS[relative]
            if len(found) != count:
                violations.append(f"{relative}: expected {count} deferred sites ({owner}), found {len(found)}")
        else:
            violations.extend(found)
    return violations


@pytest.mark.repo_wide
def test_scripts_have_one_github_client():
    found = inventory_violations(ROOT)
    assert not found, "\n".join(found)


@pytest.mark.parametrize(
    "source",
    [
        'import subprocess\ndef probe():\n return subprocess.run(["gh","pr","list"])',
        'import subprocess\ndef probe():\n command=["gh","api","repos/o/r/issues"]\n return subprocess.run(command)',
        'import urllib.request\ndef probe():\n return urllib.request.urlopen("https://api.github.com/repos/o/r/issues")',
        'import requests\ndef probe():\n return requests.get("https://api.github.com/repos/o/r/issues")',
        'import urllib.request\ndef probe():\n return urllib.request.urlretrieve("https://github.com/o/r/releases/download/v/asset", "out")',
        'import urllib.request\ndef probe(pointer):\n request=urllib.request.Request(pointer["asset_url"])\n return urllib.request.urlopen(request)',
        'from subprocess import run as invoke\ndef probe():\n return invoke(["/usr/bin/gh","pr","list"])',
        'import subprocess as sp\ngh_bin="gh"\ndef probe():\n return sp.run([gh_bin,"pr","list"])',
        'import subprocess\nsubprocess.run(["gh","api","user"])',
        'import subprocess\nsubprocess.run(args=["gh","api","user"])',
        'import requests\nrequests.delete(url="https://api.github.com/repos/o/r/issues/1")',
        'import subprocess\ndef probe():\n return subprocess.run(["sh","-c","gh pr list"])',
        'import urllib.request\ndef probe():\n request=urllib.request.Request("https://api.github.com/user")\n return urllib.request.build_opener().open(request)',
        'import requests\ndef probe():\n session=requests.Session()\n return session.get("https://api.github.com/user")',
        'from requests import get as fetch\ndef probe():\n return fetch("https://api.github.com/repos/o/r/issues")',
        'import urllib.request\ndef fetch(url):\n return urllib.request.urlopen(url)\ndef probe():\n return fetch("https://api.github.com/user")',
        'import requests\ndef probe():\n return requests.get("api.github.com/user")',
        'import requests\ndef probe():\n return requests.get("https://token@api.github.com/user")',
        'import urllib.request\ndef probe():\n return urllib.request.urlopen("uploads.github.com/repos/o/r")',
        'import subprocess\ndef probe():\n return subprocess.run("curl -s https://api.github.com/user", shell=True)',
        'import subprocess\ndef probe(repo):\n return subprocess.run(f"curl -s https://api.github.com/repos/{repo}", shell=True)',
        'import urllib.request\ndef probe(scheme):\n return urllib.request.urlopen(f"{scheme}://api.github.com/user")',
        'import requests\ndef probe():\n return requests.get("https://api.github.com./user")',
        'import requests\ndef probe():\n return requests.get("API.GITHUB.COM/user")',
        'import requests\ndef probe():\n return requests.get("https://[api.github.com/user")',
        'import subprocess\ndef probe():\n return subprocess.run("U=https://api.github.com/user; curl $U", shell=True)',
        'import subprocess\ndef probe():\n return subprocess.run("curl --url=https://api.github.com/user", shell=True)',
        'import subprocess\ndef probe():\n return subprocess.run("curl (https://api.github.com/user)", shell=True)',
        'import subprocess\ndef probe():\n return subprocess.run("curl <https://api.github.com/user>", shell=True)',
    ],
)
def test_mutation_is_rejected(source, tmp_path):
    mutation = tmp_path / "scripts" / "synthetic_mutation.py"
    mutation.parent.mkdir()
    mutation.write_text(source)
    assert inventory_violations(tmp_path)


@pytest.mark.parametrize(
    "source",
    [
        'import requests\ndef probe():\n return requests.get("https://api.github.com.example.invalid/repos/o/r")',
        'import requests\ndef probe():\n return requests.get("https://example.invalid/api.github.com/repos/o/r")',
        'import requests\ndef probe():\n return requests.get("https://notapi.github.com/user")',
        'import urllib.request\ndef probe():\n return urllib.request.urlopen("https://uploads.github.com.example.invalid/repos/o/r")',
        'import requests\ndef probe():\n return requests.get("https://example.invalid/a?next=https://api.github.com/user")',
        'import requests\ndef probe():\n return requests.get("https://example.invalid/a?next=https://github.com/o/r")',
        'import requests\ndef probe():\n return requests.get("https://github.com.example.invalid/o/r")',
        'import subprocess\ndef probe():\n return subprocess.run("curl -s https://api.github.com.example.invalid/repos/o/r", shell=True)',
        'import subprocess\ndef probe():\n return subprocess.run("curl -s https://example.invalid/api.github.com/repos/o/r", shell=True)',
        'import subprocess\ndef probe():\n return subprocess.run("curl -s \\"https://example.invalid/a?next=https://api.github.com/user\\"", shell=True)',
        'import urllib.request\ndef probe(scheme):\n return urllib.request.urlopen(f"{scheme}://notapi.github.com/user")',
        'import urllib.request\ndef probe(scheme):\n return urllib.request.urlopen(f"{scheme}://api.github.com.example.invalid/repos/o/r")',
        'import requests\ndef probe():\n return requests.get("https://notapi.github.com./user")',
        'import requests\ndef probe():\n return requests.get("https://api.github.com.example.invalid./user")',
        'import requests\ndef probe():\n return requests.get("NOTAPI.GITHUB.COM/user")',
        'import requests\ndef probe():\n return requests.get("API.GITHUB.COM.EXAMPLE.INVALID/user")',
        'import requests\ndef probe():\n return requests.get("https://[notapi.github.com/user")',
        'import requests\ndef probe():\n return requests.get("https://[evil.example]/api.github.com")',
    ],
)
def test_lookalike_host_is_not_treated_as_github(source, tmp_path):
    mutation = tmp_path / "scripts" / "lookalike.py"
    mutation.parent.mkdir()
    mutation.write_text(source)
    assert bypasses(source, "scripts/lookalike.py") == []
    assert inventory_violations(tmp_path) == []


def test_shared_client_is_allowed():
    assert not bypasses(
        'from scripts.common.github_client import run\ndef probe():\n return run(["gh","pr","list"])',
        "scripts/probe.py",
    )


@pytest.mark.parametrize("path,count", [(path, entry[0]) for path, entry in EXCLUSIONS.items()])
def test_deferred_file_rejects_added_raw_call(tmp_path, path, count):
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(
        "import subprocess\n"
        + "\n".join(f'def bypass_{i}():\n return subprocess.run(["gh", "pr", "list"])' for i in range(count))
    )
    assert inventory_violations(tmp_path) == []
    target.write_text(target.read_text() + '\nsubprocess.run(["gh", "api", "user"])\n')
    assert len(inventory_violations(tmp_path)) == 1


@pytest.mark.parametrize("name", ["guard-pr-merge.py", "guard-admin-merge.py"])
def test_standalone_hook_colour_stripping_is_pinned(name, monkeypatch):
    source = (ROOT / "agents_extensions/shared/hooks" / name).read_text()
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_gh_env")
    import os

    namespace = {"os": os}
    exec(compile(ast.Module(body=[function], type_ignores=[]), name, "exec"), namespace)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    environment = namespace["_gh_env"]()
    assert "FORCE_COLOR" not in environment and "CLICOLOR_FORCE" not in environment
    assert environment["NO_COLOR"] == "1"


def test_shim_entry_mutation_cannot_bypass_shared_client():
    path = "scripts/opsec/gh_entry.py"
    source = (ROOT / path).read_text()
    assert bypasses(source, path) == []
    mutation = (
        source
        + '\ndef replay():\n    import subprocess\n    subprocess.run(["gh", "pr", "comment", "1"], timeout=30)\n'
    )
    assert len(bypasses(mutation, path)) == 1
    assert "gh bypasses shared client" in bypasses(mutation, path)[0]
    assert path not in EXCLUSIONS
