"""Offline import smoke over the source-tool CLI import closure (#9991).

Compute the static denominator, including deferred imports and regular package
initializers, so new dependent CLIs automatically receive both import probes.
File probes run as __main__ with --help and real script paths, including path
setup. Module probes import without running legacy main logic. Each probe uses
a fresh interpreter without pytest's sys.path. The
known-failures baseline is a shrink-only ratchet: regressions and fixed rows
both fail until the baseline reflects the remaining failures. Its denominator
inventory prevents silent removals; newly discovered CLIs are probed without
requiring a snapshot refresh. Reviewed removals require an explicit refresh.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections import defaultdict
from importlib.util import resolve_name
from pathlib import Path

import pytest

# The import probes compute the repository graph during fixture setup.
pytestmark = pytest.mark.repo_wide

ROOT = Path(__file__).resolve().parents[1]
IMPORT_TARGETS = {"scripts.rag.source_query", "scripts.wiki.slovnyk_me"}
# Six probes at 15 seconds each remain below pytest's 120-second test timeout.
BATCH_SIZE = 3
BASELINE_PATH = Path(__file__).with_name("source_tool_import_baseline.json")
URGENT_CLIS = {"scripts/ingest/grac_frequency_ingest.py", "scripts/ingest/slovnyk_me_ingest.py"}
STYLES = ("module", "file")


def tracked_script_paths(root: Path) -> list[str]:
    """List candidates without reading or parsing any script bodies."""
    return subprocess.run(
        ["git", "ls-files", "-z", "scripts/**/*.py", "scripts/*.py"],
        cwd=root, capture_output=True, text=True, check=True, timeout=30,
    ).stdout.rstrip("\0").split("\0")


def source_tool_clis(root: Path) -> list[str]:
    """Return tracked __main__ files reaching either helper in the import graph."""
    paths = tracked_script_paths(root)
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


OFFLINE_GUARD = """
import os
import sys
from pathlib import Path

private_tmp = Path(os.environ['TMPDIR']).resolve()

def private_path(path, dir_fd=None):
    # Resolve symlinks and '..'. On Linux, resolve directory descriptors too:
    # tempfile cleanup uses unlink/rmdir relative to an open directory fd.
    # Missing descriptor telemetry fails closed on other platforms.
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    target = Path(os.fsdecode(path))
    if dir_fd not in (None, -1):
        try:
            directory = Path('/proc/self/fd/' + str(dir_fd)).resolve(strict=True)
        except (OSError, RuntimeError):
            return False
        if not directory.is_relative_to(private_tmp):
            return False
        target = directory / target
    return target.resolve().is_relative_to(private_tmp)

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
    # Only the fresh private probe directory is writable. This also permits
    # tempfile.gettempdir() to validate it without hiding subsequent imports.
    if event == 'open' and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
        # The open audit event omits dir_fd: only absolute paths are safe to
        # authorize, since a relative name may target another directory fd.
        if not private_path(args[0]) or not os.path.isabs(args[0]):
            raise RuntimeError('IMPORT_SMOKE_BLOCKED_WRITE: ' + event)
    if event in {'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.link',
                 'os.symlink', 'os.truncate', 'os.chmod', 'os.chown', 'os.utime'}:
        path_fds = {
            'os.mkdir': ((0, 2),), 'os.remove': ((0, 1),), 'os.rename': ((0, 2), (1, 3)),
            'os.rmdir': ((0, 1),), 'os.link': ((0, 2), (1, 3)), 'os.symlink': ((0, None), (1, 2)),
            'os.truncate': ((0, None),), 'os.chmod': ((0, 2),), 'os.chown': ((0, 3),),
            'os.utime': ((0, 3),),
        }[event]
        if not all(private_path(args[p], args[fd] if fd is not None else None) for p, fd in path_fds):
            raise RuntimeError('IMPORT_SMOKE_BLOCKED_WRITE: ' + event)
    if event == 'sqlite3.connect' and args[0] != ':memory:' and 'mode=ro' not in str(args[0]):
        if not private_path(args[0]):
            raise RuntimeError('IMPORT_SMOKE_BLOCKED_WRITE: ' + event)

sys.addaudithook(offline)
"""

IMPORT_PROBE = OFFLINE_GUARD + """
import importlib
import runpy
style, path = sys.argv[1:]
if style == 'module':
    sys.argv = [path]
    importlib.import_module(path[:-3].replace('/', '.'))
else:
    # -c initially supplies cwd at sys.path[0]. Replace it with the directory
    # a real file launch uses; never supply the repository root to the script.
    root = str(Path.cwd())
    sys.path[:] = [str(Path(path).resolve().parent)] + [
        entry for entry in sys.path if entry and str(Path(entry).resolve()) != root
    ]
    sys.argv = [path, '--help']
    try:
        runpy.run_path(path, run_name='__main__')
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise
print('IMPORT_SMOKE_COMPLETE')
"""

REFRESH_COMMAND = (
    f"{shlex.quote(sys.executable)} tests/test_source_ingest_entrypoints.py --refresh-denominator"
)


def smoke_import(root: Path, path: str, style: str) -> str | None:
    """Return every failed probe's diagnostic, including nonzero SystemExit."""
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["LEXICON_SLOVNYK_OFFLINE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    temp_parent = Path(tempfile.gettempdir()).resolve()
    if temp_parent.is_relative_to(root.resolve()):
        raise ValueError("import smoke requires a temporary directory outside the checkout")
    with tempfile.TemporaryDirectory(prefix="source-import-", dir=temp_parent) as private_tmp:
        env.update(dict.fromkeys(("TMPDIR", "TEMP", "TMP"), private_tmp))
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


BASELINE = json.loads(BASELINE_PATH.read_text())
KNOWN_FAILURES = {
    (row["path"], row["form"], row["failure_class"]) for row in BASELINE["failures"]
}


@pytest.fixture(scope="module")
def source_clis() -> list[str]:
    """Scan once per worker at execution time, never during collection."""
    clis = source_tool_clis(ROOT)
    assert clis, "source-tool CLI denominator must not be empty"
    return clis


def pytest_generate_tests(metafunc) -> None:
    if metafunc.function.__name__ == "test_source_tool_cli_imports":
        # Candidates are a superset of the live graph, so growth is covered
        # without parsing scripts during collection or enlarging probe batches.
        paths = tracked_script_paths(ROOT)
        metafunc.parametrize(
            "batch", [paths[i:i + BATCH_SIZE] for i in range(0, len(paths), BATCH_SIZE)],
            indirect=True, ids=lambda batch: batch[0],
        )


@pytest.fixture
def batch(request, source_clis: list[str]) -> list[str]:
    return [path for path in request.param if path in source_clis]


def denominator_snapshot(clis: list[str]) -> dict:
    """Fingerprint the full inventory, including same-size substitutions."""
    return {
        "cli_count": len(clis),
        "probe_count": len(STYLES) * len(clis),
        "cli_paths": sorted(clis),
        "cli_paths_sha256": hashlib.sha256("\n".join(sorted(clis)).encode()).hexdigest(),
    }


def assert_denominator_fresh(clis: list[str], snapshot: dict) -> None:
    """Allow growth while rejecting removals and inconsistent saved inventories."""
    saved = snapshot.get("cli_paths", [])
    assert saved and len(saved) == len(set(saved)) and snapshot == denominator_snapshot(saved), (
        f"Invalid CLI inventory snapshot; review and refresh with: {REFRESH_COMMAND}"
    )
    removed = sorted(set(saved) - set(clis))
    assert not removed, (
        f"CLIs disappeared from the inventory: {removed}; review removals and refresh with: {REFRESH_COMMAND}"
    )


def refresh_denominator() -> None:
    """Refresh only the reviewed CLI inventory; never bless observed failures."""
    baseline = json.loads(BASELINE_PATH.read_text())
    baseline["denominator"] = denominator_snapshot(source_tool_clis(ROOT))
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")
    print(json.dumps(baseline["denominator"], sort_keys=True))


def failure_class(diagnostic: str) -> str:
    """Keep offline guard limitations distinct from import exceptions."""
    for kind in ("SUBPROCESS", "NETWORK"):
        if re.search(rf"^RuntimeError: IMPORT_SMOKE_BLOCKED_{kind}: .+$", diagnostic, re.MULTILINE):
            return "environment_blocked_" + kind.lower()
    if re.search(r"^ModuleNotFoundError:", diagnostic, re.MULTILINE):
        return "module_not_found"
    if re.search(r"^ImportError:", diagnostic, re.MULTILINE):
        return "import_error"
    if ": timeout after 15s\n" in diagnostic:
        return "timeout"
    return "other_import_failure"


@pytest.mark.repo_invariant
def test_source_tool_baseline_is_fresh(source_clis: list[str]) -> None:
    assert BASELINE["schema"] == "source-tool-import-baseline.v1"
    assert_denominator_fresh(source_clis, BASELINE["denominator"])
    assert len(KNOWN_FAILURES) == len(BASELINE["failures"]), "duplicate baseline rows"
    assert set(source_clis) >= URGENT_CLIS, "urgent ingest CLIs must stay in the denominator"
    for path, form, kind in KNOWN_FAILURES:
        assert path in source_clis and form in STYLES, f"obsolete baseline probe: {(path, form)}"
        assert path not in URGENT_CLIS, "urgent ingest imports must be clean, never baselined"
        assert kind in {"import_error", "module_not_found", "environment_blocked_subprocess",
                        "environment_blocked_network",
                        "other_import_failure", "timeout"}


@pytest.mark.parametrize("current", [
    ["scripts/a.py"],
    ["scripts/a.py", "scripts/c.py"],
    ["scripts/a.py", "scripts/c.py", "scripts/d.py"],
])
def test_denominator_freshness_rejects_removals_even_with_growth(current) -> None:
    snapshot = denominator_snapshot(["scripts/a.py", "scripts/b.py"])
    with pytest.raises(AssertionError, match=re.escape(REFRESH_COMMAND)):
        assert_denominator_fresh(current, snapshot)
    assert_denominator_fresh(current, denominator_snapshot(current))


@pytest.mark.parametrize("field, value", [
    ("cli_count", 1), ("probe_count", 1), ("cli_paths_sha256", "invalid"),
    ("cli_paths", ["scripts/a.py", "scripts/a.py"]),
])
def test_denominator_freshness_rejects_inconsistent_snapshot(field, value) -> None:
    snapshot = denominator_snapshot(["scripts/a.py", "scripts/b.py"])
    with pytest.raises(AssertionError, match="Invalid CLI inventory snapshot"):
        assert_denominator_fresh(snapshot["cli_paths"], {**snapshot, field: value})


def test_refresh_denominator_preserves_failure_rows(tmp_path: Path, monkeypatch, capsys) -> None:
    target = tmp_path / "baseline.json"
    baseline = {"schema": BASELINE["schema"], "denominator": {}, "failures": BASELINE["failures"]}
    target.write_text(json.dumps(baseline))
    monkeypatch.setattr(sys.modules[__name__], "BASELINE_PATH", target)
    monkeypatch.setattr(sys.modules[__name__], "source_tool_clis", lambda root: ["scripts/new.py"])
    refresh_denominator()
    updated = json.loads(target.read_text())
    assert updated == {**baseline, "denominator": denominator_snapshot(["scripts/new.py"])}
    assert json.loads(capsys.readouterr().out) == updated["denominator"]


@pytest.mark.parametrize("style", ["module", "file"])
@pytest.mark.parametrize("source, expected", [
    ('if __name__ == "__main__": raise RuntimeError("main ran")\n', "RuntimeError: main ran"),
    ('raise SystemExit(0)\n', "exit 0"),
    ('raise RuntimeError("import failed")\n', "RuntimeError: import failed"),
    ('import socket\nsocket.getaddrinfo("example.invalid", 443)\n', "IMPORT_SMOKE_BLOCKED_NETWORK"),
    ('import subprocess\nsubprocess.run(["unreachable-command"])\n', "IMPORT_SMOKE_BLOCKED_SUBPROCESS"),
    ('import subprocess\nsubprocess.run(["git", "rev-parse", "--is-inside-work-tree"])\n', None),
    ('import subprocess\nsubprocess.run(["git", "fetch", "origin"])\n', "IMPORT_SMOKE_BLOCKED_SUBPROCESS"),
    ('import hidden_dependency\n', "No module named 'hidden_dependency'"),
    ('open("unexpected-write", "w")\n', "IMPORT_SMOKE_BLOCKED_WRITE"),
    ('import sqlite3\nsqlite3.connect("unexpected-write")\n', "IMPORT_SMOKE_BLOCKED_WRITE"),
])
def test_smoke_probe_enforces_isolation(tmp_path: Path, monkeypatch, style: str,
                                       source: str, expected: str | None) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "__init__.py").write_text("")
    (tmp_path / "scripts" / "probe.py").write_text(source)
    (tmp_path / "hidden").mkdir()
    (tmp_path / "hidden" / "hidden_dependency.py").write_text("")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "hidden"))
    if source.startswith('if __name__') and style == "module":
        expected = None
    if source == 'raise SystemExit(0)\n' and style == "file":
        expected = None
    failure = smoke_import(tmp_path, "scripts/probe.py", style)
    if expected is None:
        assert failure is None
    else:
        assert failure is not None and expected in failure
    assert not (tmp_path / "unexpected-write").exists()


@pytest.mark.parametrize("operation", [
    "(private / 'escape' / 'write').write_text('blocked')",
    "os.rename(outside / 'original', private / 'moved')",
    "os.rename(private / 'original', outside / 'moved')",
    "os.link(outside / 'original', private / 'linked')",
    "os.symlink(outside / 'original', private / 'linked')",
    "os.remove('original', dir_fd=os.open(outside, os.O_RDONLY))",
    "os.chdir(private); os.open('original', os.O_WRONLY, dir_fd=os.open(outside, os.O_RDONLY))",
    "(Path(str(private) + '-sibling') / 'write').write_text('blocked')",
])
def test_private_temp_guard_blocks_escape(tmp_path: Path, monkeypatch, operation: str) -> None:
    (tmp_path / "original").write_text("unchanged")
    (tmp_path / "probe.py").write_text(
        "import os\nfrom pathlib import Path\n"
        "outside = Path.cwd()\nprivate = Path(os.environ['TMPDIR'])\n"
        "(private / 'original').write_text('private')\n" + operation + "\n"
    )
    original_run = subprocess.run

    def with_escape(*args, **kwargs):
        (Path(kwargs["env"]["TMPDIR"]) / "escape").symlink_to(tmp_path, target_is_directory=True)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", with_escape)
    failure = smoke_import(tmp_path, "probe.py", "file")
    assert failure is not None and "IMPORT_SMOKE_BLOCKED_WRITE" in failure
    assert (tmp_path / "original").read_text() == "unchanged"
    assert not (tmp_path / "moved").exists()
    assert not (tmp_path / "write").exists()


def test_private_temp_parent_cannot_be_checkout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    with pytest.raises(ValueError, match="outside the checkout"):
        smoke_import(tmp_path, "probe.py", "file")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Refresh the reviewed source-tool CLI inventory only.")
    parser.add_argument("--refresh-denominator", action="store_true", required=True,
                        help="Update the inventory fingerprint, preserving all failure rows.")
    parser.parse_args()
    refresh_denominator()
