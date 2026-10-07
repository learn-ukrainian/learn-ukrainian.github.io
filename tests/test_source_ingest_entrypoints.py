"""Offline import smoke over the source-tool CLI import closure (#9991).

Compute the static denominator, including deferred imports and regular package
initializers, so new dependent CLIs automatically receive both import probes.
Only the ingest entrypoints are executed with --help; legacy main logic is out
of scope. Each probe uses a fresh interpreter without pytest's sys.path.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import time
from collections import defaultdict
from importlib.util import resolve_name
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IMPORT_TARGETS = {"scripts.rag.source_query", "scripts.wiki.slovnyk_me"}
# Six probes at 15 seconds each remain below pytest's 120-second test timeout.
BATCH_SIZE = 3


def source_tool_clis(root: Path) -> list[str]:
    """Return tracked __main__ files reaching either helper in the import graph."""
    paths = subprocess.run(
        ["git", "ls-files", "-z", "scripts/**/*.py", "scripts/*.py"],
        cwd=root, capture_output=True, text=True, check=True, timeout=30,
    ).stdout.rstrip("\0").split("\0")
    modules = {path[:-3].replace("/", ".").removesuffix(".__init__"): path for path in paths}
    reverse: dict[str, set[str]] = defaultdict(set)
    mains = set()
    for module, path in modules.items():
        package = module if path.endswith("/__init__.py") else module.rpartition(".")[0]
        names = set()
        for node in ast.walk(ast.parse((root / path).read_bytes(), filename=path)):
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    pair = [test.left, *test.comparators]
                    if any(isinstance(n, ast.Name) and n.id == "__name__" for n in pair) and any(
                        isinstance(n, ast.Constant) and n.value == "__main__" for n in pair
                    ):
                        mains.add(module)
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                name = node.module or ""
                if node.level:
                    name = resolve_name("." * node.level + name, package)
                names.update([name, *(name + "." + alias.name for alias in node.names)])
        # Importing a submodule executes its own regular package initializers.
        names.update(".".join(module.split(".")[:i]) for i in range(1, len(module.split("."))))
        for name in names:
            target = name if name in modules else "scripts." + name
            if target in modules:
                reverse[target].add(module)
    assert modules.keys() >= IMPORT_TARGETS, "source-tool graph roots must exist"
    reached = IMPORT_TARGETS.copy()
    pending = list(reached)
    while pending:
        for importer in reverse[pending.pop()] - reached:
            reached.add(importer)
            pending.append(importer)
    return sorted(modules[module] for module in mains & reached)


IMPORT_PROBE = """
import importlib
import runpy
import sys
from pathlib import Path

def offline(event, args):
    if event in {'socket.connect', 'socket.sendto', 'socket.getaddrinfo',
                 'socket.gethostbyname', 'socket.gethostbyaddr', 'socket.getnameinfo', 'socket.sendmsg'}:
        raise RuntimeError('IMPORT_SMOKE_BLOCKED_NETWORK: ' + event)
    # Shared root resolvers use this local Git plumbing command at import time.
    # Permit it without permitting shell commands or a network-capable Git verb.
    if event == 'subprocess.Popen' and Path(args[0]).name == 'git':
        argv = args[1]
        if isinstance(argv, (list, tuple)):
            command = list(argv[1:])
            if len(command) >= 2 and command[0] == '-C':
                command = command[2:]
            if command and command[0] == 'rev-parse':
                return
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec'}:
        raise RuntimeError('IMPORT_SMOKE_BLOCKED_SUBPROCESS: ' + event)

sys.addaudithook(offline)
style, path = sys.argv[1:]
sys.argv = [path]
if style == 'module':
    importlib.import_module(path[:-3].replace('/', '.'))
else:
    runpy.run_path(path, run_name='__smoke__')
print('IMPORT_SMOKE_COMPLETE')
"""


def smoke_import(root: Path, path: str, style: str) -> str | None:
    """Return every failed probe's diagnostic, including nonzero SystemExit."""
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["LEXICON_SLOVNYK_OFFLINE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            [sys.executable, "-c", IMPORT_PROBE, style, path],
            cwd=root, env=env, capture_output=True, text=True, timeout=15, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return f"{path} [{style}]: timeout after 15s\n{exc.stdout!r}\n{exc.stderr!r}"
    output = result.stdout + result.stderr
    if result.returncode != 0 or "Traceback (most recent call last)" in output or (
        "IMPORT_SMOKE_COMPLETE" not in result.stdout.splitlines()
    ):
        return f"{path} [{style}]: exit {result.returncode}\n{output}"
    return None


CLIS = source_tool_clis(ROOT)
assert CLIS, "source-tool CLI denominator must not be empty"


@pytest.mark.repo_invariant
@pytest.mark.repo_wide
@pytest.mark.parametrize("batch", [CLIS[i:i + BATCH_SIZE] for i in range(0, len(CLIS), BATCH_SIZE)],
                         ids=lambda batch: batch[0])
def test_source_tool_cli_imports(batch: list[str]) -> None:
    started = time.monotonic()
    failures = [failure for path in batch for style in ("module", "file")
                if (failure := smoke_import(ROOT, path, style))]
    summary = (f"{len(batch)} CLIs / {2 * len(batch)} import probes in "
               f"{time.monotonic() - started:.2f}s; {len(failures)} failures")
    assert not failures, summary + "\n" + "\n".join(failures)


def test_source_tool_graph_includes_new_deferred_and_package_dependents(tmp_path: Path, monkeypatch) -> None:
    files = {
        "scripts/rag/source_query.py": "",
        "scripts/wiki/slovnyk_me.py": "",
        "scripts/tool/pkg/__init__.py": "from ...rag import source_query\n",
        "scripts/tool/pkg/new_cli.py": 'if __name__ == "__main__": pass\n',
        "scripts/tool/helper.py": "from scripts.wiki import slovnyk_me\n",
        "scripts/tool/deferred.py": (
            'def main():\n    from . import helper\nif "__main__" == __name__: main()\n'
        ),
        "scripts/tool/library.py": "from . import helper\n",
        "scripts/tool/unrelated.py": 'import json\nif __name__ == "__main__": pass\n',
    }
    for path, source in files.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, stdout="\0".join(files) + "\0",
    ))
    assert source_tool_clis(tmp_path) == ["scripts/tool/deferred.py", "scripts/tool/pkg/new_cli.py"]


@pytest.mark.parametrize("style", ["module", "file"])
@pytest.mark.parametrize("source, expected", [
    ('if __name__ == "__main__": raise RuntimeError("main ran")\n', None),
    ('raise SystemExit(0)\n', "exit 0"),
    ('raise RuntimeError("import failed")\n', "RuntimeError: import failed"),
    ('import socket\nsocket.getaddrinfo("example.invalid", 443)\n', "IMPORT_SMOKE_BLOCKED_NETWORK"),
    ('import subprocess\nsubprocess.run(["unreachable-command"])\n', "IMPORT_SMOKE_BLOCKED_SUBPROCESS"),
    ('import subprocess\nsubprocess.run(["git", "rev-parse", "--is-inside-work-tree"])\n', None),
    ('import subprocess\nsubprocess.run(["git", "fetch", "origin"])\n', "IMPORT_SMOKE_BLOCKED_SUBPROCESS"),
    ('import hidden_dependency\n', "No module named 'hidden_dependency'"),
])
def test_smoke_probe_enforces_isolation(tmp_path: Path, monkeypatch, style: str,
                                       source: str, expected: str | None) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "__init__.py").write_text("")
    (tmp_path / "scripts" / "probe.py").write_text(source)
    (tmp_path / "hidden").mkdir()
    (tmp_path / "hidden" / "hidden_dependency.py").write_text("")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "hidden"))
    failure = smoke_import(tmp_path, "scripts/probe.py", style)
    if expected is None:
        assert failure is None
    else:
        assert failure is not None and expected in failure


@pytest.mark.repo_invariant
@pytest.mark.parametrize("module", ["grac_frequency_ingest", "slovnyk_me_ingest"])
@pytest.mark.parametrize("style", ["file", "module"])
def test_source_ingest_help_from_repository_root(module: str, style: str) -> None:
    argv = (
        [f"scripts/ingest/{module}.py"]
        if style == "file"
        else ["-m", f"scripts.ingest.{module}"]
    )
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["LEXICON_SLOVNYK_OFFLINE"] = "1"
    result = subprocess.run(
        [sys.executable, *argv, "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout.lower(), result.stdout + result.stderr
    assert "--help" in result.stdout
