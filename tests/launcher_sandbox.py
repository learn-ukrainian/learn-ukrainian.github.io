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
import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Runs the gate's own calls (a registered slot, an unregistered slot and the
# per-provider listing used in the refusal message) and prints the repo files
# they needed: imported modules plus any data file opened (the roster, catalogs).
# Imports are recorded from the files the import system reads (a module's
# ``.py`` or its cached ``.pyc``), not from ``sys.modules``: compatibility shims
# such as ``scripts/fleet_comms/contracts.py`` replace their own entry there.
_PROBE = r"""
import importlib.util, json, os, sys
from pathlib import Path

root = Path.cwd().resolve()
sys.path.insert(0, str(root))  # the launcher runs the gate with `-m` from the repo root
opened = set()

def _record(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if path.endswith(".pyc") and os.path.basename(os.path.dirname(path)) == "__pycache__":
            path = importlib.util.source_from_cache(path)
        opened.add(path)

sys.addaudithook(_record)
from scripts.orchestration import handoff_slot_registry

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
        [sys.executable, "-c", _PROBE],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
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
