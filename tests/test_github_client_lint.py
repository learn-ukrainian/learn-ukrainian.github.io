"""GitHub I/O has one client; exclusions are separately owned migrations."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS = {
    "scripts/delegate.py": (2, "#9878: accountable driver migrates after concurrent edit settles"),
}
CLIENT = "scripts/common/github_client.py"


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
                    or "api.github.com" in n.value
                    or "uploads.github.com" in n.value
                    or n.value.startswith("https://github.com/")
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
    github_http = "api.github.com" in source or "uploads.github.com" in source
    github_http = github_http or "asset_url" in source or "https://github.com/" in source
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
    ],
)
def test_mutation_is_rejected(source, tmp_path):
    mutation = tmp_path / "scripts" / "synthetic_mutation.py"
    mutation.parent.mkdir()
    mutation.write_text(source)
    assert inventory_violations(tmp_path)


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
    mutation = source + '\ndef replay():\n    import subprocess\n    subprocess.run(["gh", "pr", "comment", "1"], timeout=30)\n'
    assert len(bypasses(mutation, path)) == 1
    assert "gh bypasses shared client" in bypasses(mutation, path)[0]
    assert path not in EXCLUSIONS
