"""Exercise source discovery and copying with real imports and warm caches."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests import launcher_sandbox


@pytest.mark.parametrize("layout", ["default", "external"])
@pytest.mark.parametrize("dont_write_bytecode", [False, True], ids=["bytecode-on", "bytecode-off"])
def test_copy_registry_keeps_cached_alias_sources_only_when_tracked(
    tmp_path: Path, layout: str, dont_write_bytecode: bool,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    sources = {
        "scripts/__init__.py": "",
        "scripts/orchestration/__init__.py": "",
        "scripts/orchestration/handoff_slot_registry.py": '''
import os
from pathlib import Path
from scripts import compat, untracked

assert compat is os

def main(args):
    for path in ("scripts/roster.json", "scripts/legacy.pyc",
                 "scripts/__pycache__/invalid.too.many.parts.pyc", "../outside.py"):
        Path(path).read_bytes()
    # Exercise bytes, PathLike and descriptor audit inputs as well as strings.
    with open(os.fsencode("scripts/roster.json")) as stream:
        os.fstat(stream.fileno())
    descriptor = os.open(Path("scripts/roster.json"), os.O_RDONLY)
    with open(descriptor, closefd=True) as stream:
        stream.read()
    return 3 if args == ["--slot", "claude-unregistered-sandbox-probe"] else 0
''',
        "scripts/compat.py": "import os, sys\nsys.modules[__name__] = os\n",
        "scripts/roster.json": '{"fixture": true}\n',
        "scripts/legacy.pyc": "not a source cache",
        "scripts/__pycache__/invalid.too.many.parts.pyc": "not a source cache",
    }
    for relative, content in sources.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    (repo / "scripts/untracked.py").write_text("UNTRACKED = True\n")
    (tmp_path / "outside.py").write_text("OUTSIDE = True\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    subprocess.run(["git", "add", "-f", "--", *sources], cwd=repo, check=True, timeout=30)

    # Only this controlled child selects a cache layout. The actual launcher
    # modules run separately with the worker's inherited cache prefix intact.
    controller = r'''
import importlib.util, json, os, subprocess, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("launcher_sandbox", sys.argv[1])
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)
repo, destination = map(Path, sys.argv[2:])
sandbox._REPO_ROOT = repo

def probe(*, warm_cache=False):
    result = subprocess.run(
        [sys.executable, "-X", "pycache_prefix=" + (sys.pycache_prefix or ""), "-c", sandbox._PROBE],
        cwd=repo, capture_output=True, text=True, check=True, timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": ""} if warm_cache else None,
    )
    return json.loads(result.stdout.splitlines()[-1])

# Only warm-up may override inherited bytecode suppression. Measurement and
# discovery retain it, so cached alias recovery is exercised even without writes.
probe(warm_cache=True)
recorded = probe()
alias = repo / "scripts/compat.py"
cache = importlib.util.cache_from_source(str(alias))
assert importlib.util.source_from_cache(cache) == str(alias)
assert Path(cache).is_file()

# slot_registry_sources starts another interpreter; explicitly forward the
# controlled layout, while leaving the real worker's environment untouched.
os.environ["PYTHONPYCACHEPREFIX"] = sys.pycache_prefix or ""
selected = sandbox.slot_registry_sources()
sandbox.copy_slot_registry(destination)
print(json.dumps({
    "alias_recorded": str(alias) in recorded,
    "cache_recorded": cache in recorded,
    "cache_is_local": Path(cache).parent.name == "__pycache__",
    "dont_write_bytecode": sys.dont_write_bytecode,
    "selected": [p.as_posix() for p in selected],
    "copied": sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file() and p.suffix != ".pyc"),
}))
'''
    destination = tmp_path / "copied"
    cache_prefix = str(tmp_path / "cache") if layout == "external" else ""
    result = subprocess.run(
        [sys.executable, "-X", f"pycache_prefix={cache_prefix}", "-c", controller,
         str(Path(launcher_sandbox.__file__)), str(repo), str(destination)],
        capture_output=True, text=True, check=True, timeout=60,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1" if dont_write_bytecode else ""},
    )
    expected = sorted(relative for relative in sources if not relative.endswith(".pyc"))
    assert json.loads(result.stdout) == {
        "alias_recorded": True,
        "cache_recorded": False,
        "cache_is_local": layout == "default",
        "dont_write_bytecode": dont_write_bytecode,
        "selected": expected,
        "copied": expected,
    }
    for relative in expected:
        assert (destination / relative).read_bytes() == (repo / relative).read_bytes()
    assert not (destination / "scripts/untracked.py").exists()
    assert not (destination / "outside.py").exists()


@pytest.mark.parametrize(
    ("kind", "expected"),
    [("valid", 0), ("unknown", 3), ("missing", 2), ("unreadable", 2),
     ("missing-interpreter", 2), ("nonexecutable-interpreter", 2)],
)
def test_copied_registry_preserves_identity_rejections(tmp_path: Path, kind: str, expected: int) -> None:
    root = tmp_path / "copied"
    launcher_sandbox.copy_slot_registry(root)
    helper = root / "scripts/lib/handoff_identity.sh"
    helper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher_sandbox._REPO_ROOT / "scripts/lib/handoff_identity.sh", helper)
    interpreter = root / ".venv/bin/python"
    if kind in {"missing-interpreter", "nonexecutable-interpreter"}:
        interpreter.parent.mkdir(parents=True)
        if kind == "nonexecutable-interpreter":
            interpreter.write_text("unusable interpreter\n")
            interpreter.chmod(0o600)
    else:
        # Preserve the interpreter's installed runtime, including pyvenv.cfg.
        (root / ".venv").symlink_to(Path(sys.prefix))
    # Use a private explicit roster copy; never mutate the real roster or let
    # an ambient root override supply identity data from the tested checkout.
    roster = root / "roster.yaml"
    shutil.copy2(root / "scripts/config/area_assignments.yaml", roster)
    if kind == "missing":
        roster = root / "missing.yaml"
    elif kind == "unreadable":
        roster.chmod(0)
    slot = "claude-unregistered-sandbox-probe" if kind == "unknown" else "claude-devops"
    try:
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; _handoff_slot_registry --assignments "$2" --slot "$3"',
             "fixture", str(helper), str(roster), slot],
            cwd=root, env={**os.environ, "AB_REPO_ROOT": str(root), "LC_DURABLE_HELPER_ROOT": str(root)},
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        if kind in {"missing", "unreadable"}:
            assert "handoff slot registry unreadable" in result.stderr
    finally:
        if kind == "unreadable":
            roster.chmod(0o600)
