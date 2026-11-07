"""Shared pieces of the bootstrapped launcher sandboxes used by subprocess tests.

Launcher tests run the real ``start-*.sh`` entry points inside a throwaway git
repo that holds only the files the launcher needs.  Every driver launch passes
``launcher_require_registered_slot`` (#8303), which runs
``python -m scripts.orchestration.handoff_slot_registry`` from the sandbox root
and reads the fleet roster through ``scripts.ai_agent_bridge._channels``.  A
sandbox without that closure refuses every selector with exit 2 before the
provider starts.

The closure (the bridge package imports most of ``scripts/``) is not written
down here: it is measured once per test process by running the real gate calls
and recording every tracked repo file they import or open, so a new import in
the bridge cannot silently break the launcher sandboxes again.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from scripts.common.scratch import ensure_scratch_root
from tests.helpers import machinery_module, machinery_package, product_checkout
from tests.helpers.monitor import UNREACHABLE_MONITOR_URL, UNREACHABLE_TOOL_TIMING_URL

_REPO_ROOT = Path(__file__).resolve().parents[1]


def launcher_environment(*inputs: Mapping[str, str], **extra: str) -> dict[str, str]:
    """Build a fresh launcher environment, then overlay deliberate test inputs.

    Bash and its utilities need PATH and a UTF-8 locale. HOME and temporary
    files belong to this invocation, so credentials, Git config and seat state
    cannot come from the runner. Monitor calls fail locally unless a fixture
    supplies a stub endpoint. No ambient variable is copied, including PATH.
    """
    # The per-test scratch fixture owns cleanup; its root changes between tests.
    root = Path(tempfile.mkdtemp(prefix="launcher-environment-", dir=ensure_scratch_root()))
    for name in ("home", "tmp", "scratch", "guard-bin"):
        (root / name).mkdir()
    contact = root / "unexpected-manager-call"
    for name in ("systemd-run", "systemctl"):
        binary = root / "guard-bin" / name
        binary.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> "$LU_TEST_REAL_MANAGER_CONTACT"\nexit 97\n')
        binary.chmod(0o755)
    env = {
        "PATH": f"{root / 'guard-bin'}{os.pathsep}{os.defpath}",
        "HOME": str(root / "home"),
        "TMPDIR": str(root / "tmp"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TERM": "dumb",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "LU_MONITOR_LOOPBACK": UNREACHABLE_MONITOR_URL,
        "TOOL_TIMING_API_URL": UNREACHABLE_TOOL_TIMING_URL,
        "DELEGATE_MONITOR_API": UNREACHABLE_MONITOR_URL,
        "FLEET_COMMS_ROOT": str(root / "fleet-plane"),
        "LU_SCRATCH_ROOT": str(root / "scratch"),
        "LU_DRIVER_SCOPE_CONFIG": str(root / "no-driver-scope.env"),
        "LU_TEST_REAL_MANAGER_CONTACT": str(contact),
    }
    for values in inputs:
        env.update(values)
    env.update(extra)
    return env


def copy_launcher_sources(root: Path) -> None:
    """Copy the tracked launcher/deploy surface without an interpreter or Git init.

    Copy tracked files, rather than symlinking source directories: shell and
    Python helpers resolve their own physical location to choose deploy roots.
    Runtime mirrors and caches must never link back into the tested checkout.
    """
    root.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            "start-*.sh",
            "package.json",
            machinery_package(),
            "agents_extensions",
            "gemini_extensions",
            ".gemini/config.yaml",
            "docs/l2-uk-en",
            "docs/prompts/orchestrators",
            "curriculum/l2-uk-en/curriculum.yaml",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    for raw in tracked.stdout.split("\0"):
        if not raw:
            continue
        relative = Path(raw)
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = _REPO_ROOT / relative
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            # The real curriculum manifest may be sparse; use its tracked bytes.
            blob = subprocess.run(
                ["git", "show", f"HEAD:{relative.as_posix()}"],
                cwd=_REPO_ROOT,
                capture_output=True,
                check=True,
                timeout=30,
                env=launcher_environment(),
            )
            destination.write_bytes(blob.stdout)


def tracked_launcher_wrappers() -> tuple[str, ...]:
    """Every tracked public wrapper: the product's root ``start-*.sh`` and the machinery package's.

    The root wrappers are product files, listed in the product checkout; the machinery package's
    wrappers are listed here. :func:`launcher_wrapper_source` names the file to copy for each.
    """
    product = subprocess.run(
        ["git", "ls-files", "-z", "--", "start-*.sh"],
        cwd=product_checkout(),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    machinery = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{machinery_package()}/start-*.sh"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    listed = {raw for raw in (product.stdout + machinery.stdout).split("\0") if raw}
    return tuple(sorted(listed))


def launcher_wrapper_source(relative: str) -> Path:
    """The tracked file of the wrapper ``relative``: a product root wrapper or a machinery wrapper."""
    if "/" not in relative:
        return product_checkout() / relative
    return _REPO_ROOT / relative


def copy_interactive_launcher_checkout(root: Path) -> None:
    """Copy real launcher/deploy sources so production's root lookup stays in tmp."""
    copy_launcher_sources(root)
    # This is a temporary standalone fixture, not a dispatch worktree.
    (root / ".venv").symlink_to(Path(sys.prefix))
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, timeout=30, env=launcher_environment())
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--allow-empty",
            "-q",
            "-m",
            "Initial launcher fixture",
        ],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )


# Runs the gate's own calls (a registered slot, an unregistered slot and the
# per-provider listing used in the refusal message) and prints the repo files
# they needed: imported modules plus any data file opened (the roster, catalogs).
# Imports are recorded from the files the import system reads (a module's
# ``.py`` or its cached ``.pyc``), not from ``sys.modules``: compatibility shims
# such as ``scripts/fleet_comms/contracts.py`` replace their own entry there.
# PYTHONPYCACHEPREFIX stores that bytecode beside a mirrored package directory,
# not under ``__pycache__``. Map both layouts back to the source path.
_PROBE = r"""
import importlib.util, json, os, sys
from pathlib import Path

root = Path.cwd().resolve()
sys.path.insert(0, str(root))  # the launcher runs the gate with `-m` from the repo root
opened = set()

def _source_for_bytecode(path):
    parent = os.path.basename(os.path.dirname(path))
    prefix = sys.pycache_prefix
    under_prefix = False
    if prefix:
        prefix = os.path.abspath(prefix)
        under_prefix = os.path.abspath(path).startswith(prefix + os.sep)
    if parent != "__pycache__" and not under_prefix:
        return path
    try:
        return importlib.util.source_from_cache(path)
    except (ValueError, OSError):
        return path

def _record(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if path.endswith(".pyc"):
            path = _source_for_bytecode(path)
        opened.add(path)

sys.addaudithook(_record)
handoff_slot_registry = importlib.import_module(sys.argv[1])

codes = [
    handoff_slot_registry.main(["--slot", "claude-devops"]),
    handoff_slot_registry.main(["--slot", "claude-unregistered-sandbox-probe"]),
    handoff_slot_registry.main(["--list", "claude"]),
]
if codes != [0, 3, 0]:
    raise SystemExit(f"slot registry probe returned {codes}")
paths = opened | {m.__file__ for m in list(sys.modules.values()) if getattr(m, "__file__", None)}
print(json.dumps(sorted(paths)))
"""


@functools.cache
def slot_registry_sources() -> tuple[Path, ...]:
    """Repo-relative tracked files the launcher's handoff-slot gate needs."""
    probe = subprocess.run(
        [sys.executable, "-c", _PROBE, machinery_module("orchestration.handoff_slot_registry")],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        env=launcher_environment(),
    )
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            env=launcher_environment(),
        ).stdout.split("\0")
    )
    sources: set[Path] = set()
    for raw in json.loads(probe.stdout.splitlines()[-1]):
        path = Path(raw)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        try:
            relative = path.resolve().relative_to(_REPO_ROOT)
        except ValueError:
            continue
        if relative.as_posix() in tracked:
            sources.add(relative)
    return tuple(sorted(sources))


def _copy_bytecode(source: Path, destination: Path) -> None:
    """Reuse the repo's compiled module so the sandbox does not recompile it.

    ``copy2`` keeps the source mtime and size, which is what the interpreter
    checks before trusting a cached ``.pyc``; a stale cache is recompiled as
    usual.  Without this every sandbox launch recompiles the bridge closure
    (about half a second per launcher run).
    """
    cached = Path(importlib.util.cache_from_source(source))
    if not cached.is_file():
        return
    target = Path(importlib.util.cache_from_source(destination))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.chmod(target.stat().st_mode | 0o200)
    shutil.copy2(cached, target)
    target.chmod(target.stat().st_mode | 0o200)


def copy_slot_registry(root: Path) -> None:
    """Give a launcher sandbox the real handoff-slot registry and its readers.

    Existing sandbox files are left alone so fixtures keep their stubs (for
    example the idle ``scripts/ai_agent_bridge/inbox_watch.sh``).
    """
    for relative in slot_registry_sources():
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / relative, destination)
        # A read-only canonical mode must not make the sandbox copy unwritable.
        destination.chmod(destination.stat().st_mode | 0o200)
        if relative.suffix == ".py":
            _copy_bytecode(_REPO_ROOT / relative, destination)
