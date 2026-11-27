"""The installed lu-machinery release runs a driver launch's real helper chain (machinery#100).

tests/test_launcher_interactive_scope.py proves scope entry on the release with recording
stand-ins at the provider, manager and interpreter boundaries. This module runs one dry-run
driver launch with nothing replaced: the frozen product wrapper sources the release's
launcher core, and its shell helpers, provider adapter and every Python child (model catalog,
handoff slot registry, rules core, git identity, plane mode, driver agent type) are the
installed release's own files. A dry run stops before scope entry, deployment, lease and
provider execution, so no provider is launched.

The project interpreter records each Python child: its argv, and for the release's isolated
module bootstrap and its host-binding children every file the child opened. The test fails if
any child imported or read machinery code that is not a file the release's RECORD lists, or
read this checkout.
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

from tests.launcher_libraries import (
    InstalledMachinery,
    freeze_product_wrapper,
    installed_machinery,
    link_installed_machinery,
)
from tests.launcher_sandbox import launcher_environment, launcher_wrapper_source

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REPO = Path(__file__).resolve().parents[1]
WRAPPER = "start-claude-driver.sh"
# Python helper modules a dry-run Claude driver launch runs through the module bootstrap.
HELPER_MODULES = {
    "review.model_catalog",
    "orchestration.handoff_slot_registry",
    "lib.rules_core",
    "lib.git_identity",
    "orchestration.driver_agent_type",
}
# Runs the bootstrap program it is handed, unchanged, after adding an audit hook that
# records every file the child opens. A release with a host binding also starts the bound
# interpreter as ``-I -B -m <module>`` or ``-I -B -c <program>``; those run audited in the
# same way, with sys.executable naming the bound project interpreter, which that release
# requires. Any other invocation is recorded and executed as is.
_AUDIT = r"""
import atexit, json, os, runpy, sys

log, interpreter, argv = sys.argv[1], sys.argv[2], sys.argv[3:]
record = {"argv": argv, "opened": []}


def write():
    with open(log, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")


bound = argv[:2] == ["-I", "-B"] and argv[2:3] in (["-m"], ["-c"])
if argv[:2] != ["-I", "-c"] and not bound:
    write()
    os.execv(sys.executable, [sys.executable, *argv])


def hook(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        record["opened"].append(os.fsdecode(args[0]))


if bound:
    sys.dont_write_bytecode = True
    sys.executable = interpreter
mode, target, *rest = argv[2:] if bound else argv[1:]
sys.argv = [mode, *rest]
sys.addaudithook(hook)
atexit.register(write)
if mode == "-m":
    runpy.run_module(target, run_name="__main__", alter_sys=True)
else:
    exec(compile(target, "<string>", "exec"), {"__name__": "__main__"})
"""


def _release_relative(path: Path, root: Path, release: InstalledMachinery) -> PurePosixPath | None:
    """The package-relative release file that ``path`` is or caches, or None outside machinery."""
    if path.suffix == ".pyc" and path.parent.name == "__pycache__":
        path = Path(importlib.util.source_from_cache(path))
    package = root / release.name
    for base in (package, package.resolve(), release.directory, release.directory.resolve()):
        if path.is_relative_to(base):
            return PurePosixPath(path.relative_to(base).as_posix())
    return None


# The interpreter's own environment (standard library and installed dependencies). CI
# creates its virtual environment inside the checkout, so it is excluded by location.
_ENVIRONMENT = tuple({Path(prefix).resolve() for prefix in (sys.prefix, sys.base_prefix)})


def _assert_release_origin(path: Path, root: Path, release: InstalledMachinery) -> None:
    relative = _release_relative(path, root, release)
    if relative is None:
        resolved = path.resolve()
        if not any(resolved.is_relative_to(prefix) for prefix in _ENVIRONMENT):
            assert not resolved.is_relative_to(REPO), f"{path}: a child read this checkout"
        return
    assert relative in release.files, f"{path}: not a file the installed release records"
    source = path if path.suffix != ".pyc" else Path(importlib.util.source_from_cache(path))
    assert source.resolve() == (release.directory / relative).resolve(), path


def _bind_host(base: Path, product: Path, interpreter: Path, release: InstalledMachinery, env: dict[str, str]) -> None:
    """Select a scratch machinery.host.v1 binding for the fixture, with ``interpreter`` bound.

    It has the shape machinery's tests/host_context builds. A release without
    ``lu_machinery.host_context`` does not read it. A release with it refuses a launch whose
    environment disagrees with the binding, so the interpreter and state paths agree here.
    """
    state = base / "state"
    state.mkdir()
    state.chmod(0o700)
    machinery = base / "checkouts" / "machinery"
    machinery.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(machinery)], check=True, capture_output=True, timeout=30, env=env)
    for checkout, slug in (
        (machinery, "agentic-machinery/machinery"),
        (product, "learn-ukrainian/learn-ukrainian.github.io"),
    ):
        command = ["git", "-C", str(checkout), "remote", "add", "origin", f"https://github.com/{slug}.git"]
        subprocess.run(command, check=True, capture_output=True, timeout=30, env=env)
    unused = base / "unused-cto"
    binding = base / "host.v1.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "machinery.host.v1",
                "state_root": str(state),
                "runtime": {"python": str(interpreter), "lu_machinery": release.version, "wheel_sha256": "a" * 64},
                "repos": {"machinery": str(machinery), "public": str(product)},
                "products": {"public": {"repo": "public", "python": str(interpreter)}},
                "default_product": "public",
                "private_tools": {},
                "cto": {"workspace": str(unused), "starter": str(unused / "start"), "config_dir": str(unused)},
                "selector_file": str(base / "unused-selector.yaml"),
                "monitor_url": env["LU_MONITOR_LOOPBACK"],
            }
        ),
        encoding="utf-8",
    )
    binding.chmod(0o600)
    batch = state / "batch_state"
    env.update(
        LU_HOST_CONTEXT=str(binding),
        LU_PYTHON=str(interpreter),
        LEARN_UKRAINIAN_PYTHON=str(interpreter),
        LU_PRODUCT_ROOT=str(product),
        LU_TASKS_DIR=str(batch / "tasks"),
        FLEET_COMMS_ROOT=str(batch / "fleet-comms" / "v1"),
        LU_GITHUB_CACHE_DIR=str(batch / "github-client"),
    )


def test_installed_release_runs_a_driver_launch_helper_chain_without_a_provider(tmp_path: Path) -> None:
    tmp_path = tmp_path.resolve()  # The host binding names physical paths.
    release = installed_machinery()
    root = tmp_path / "repo"
    link_installed_machinery(root / release.name)
    freeze_product_wrapper(launcher_wrapper_source(WRAPPER), root / WRAPPER, release.name)
    env = launcher_environment(tmp_path=tmp_path, LAUNCHER_DRY_RUN="1")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, capture_output=True, timeout=30, env=env)
    children = tmp_path / "children.jsonl"
    audit = tmp_path / "audit.py"
    audit.write_text(_AUDIT, encoding="utf-8")
    interpreter = root / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(
        "#!/usr/bin/env bash\n"
        f"exec {shlex.join([sys.executable, '-I', str(audit), str(children), str(interpreter)])} \"$@\"\n"
    )
    interpreter.chmod(0o755)
    _bind_host(tmp_path, root, interpreter, release, env)

    result = subprocess.run(
        ["bash", str(root / WRAPPER), "--epic", "devops", "--model", "claude-sonnet-5-5", "--effort", "high"],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert not Path(env["LU_TEST_REAL_MANAGER_CONTACT"]).exists(), output
    for expected in (
        "LAUNCHER_DRY_RUN=1: would enter a verified per-driver memory-limited scope in lu-driver.slice",
        "launcher: rules core seat=core bytes=",
        "LAUNCHER_DRY_RUN=1: would deploy agent extensions (agents:deploy)",
        "launcher: session epic=devops slot=claude-devops ",
        "launcher: would select agent infra-orchestrator for lane devops",
        "would exec claude --model claude-sonnet-5-5 --effort high ",
    ):
        assert expected in output, (expected, output)
    assert "would exec claude" in result.stdout.splitlines()[-1]

    records = [json.loads(line) for line in children.read_text(encoding="utf-8").splitlines()]
    modules = set()
    for record in records:
        argv = record["argv"]
        if argv[:2] in (["-I", "-c"], ["-I", "-B"]):
            if argv[:2] == ["-I", "-c"]:
                # The release's module bootstrap, on this fixture's package directory.
                assert "module bootstrap:" in argv[2] and argv[3:5] == [str(root), release.name], argv[:6]
                if argv[5] == "-m":
                    assert argv[6].startswith(f"{release.name}."), argv[5:7]
                    modules.add(argv[6].removeprefix(f"{release.name}."))
            elif argv[2] == "-m":
                # The host-binding children: the release's host_context module and its version probe.
                assert argv[3] == f"{release.name}.host_context", argv
            else:
                assert argv[2] == "-c" and "distribution('lu-machinery')" in argv[3], argv
            assert record["opened"], argv[:7]
            for opened in record["opened"]:
                path = Path(opened)
                if path.is_file():
                    _assert_release_origin(path, root, release)
        else:
            # A release script run by its path, isolated.
            assert argv[0] == "-I", argv
            _assert_release_origin(Path(argv[1]), root, release)
    assert modules >= HELPER_MODULES, modules
    # The launch wrote nothing into the installed release.
    assert installed_machinery.__wrapped__() == release
