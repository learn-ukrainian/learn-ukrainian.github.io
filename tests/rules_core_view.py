"""A checkout view whose rules directory carries a chosen rules core, or none.

The rules core is read from the checkout the code runs from (``scripts/lib/rules_core.py``);
nothing in the environment can point it elsewhere. A launcher test that needs a
different core therefore runs the launcher from a different checkout: this view.

Every entry of the real checkout is a symlink in the view, except the path down to
the rules directory, which holds symlinks to the real rule files plus the chosen
``core.md`` / ``core-curriculum.md``. The view is its own fresh git repository (the
launcher refuses a symlinked ``.git``) and links the running interpreter's venv
when the checkout has none (a linked worktree uses the primary checkout's).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.lib import rules_core

REPO = Path(__file__).resolve().parents[1]
CORE_FILES = (Path(rules_core.CORE_REL).name, Path(rules_core.CONTENT_ADDENDUM_REL).name)


def _link_tree(source: Path, view: Path, keep_open: tuple[str, ...], core_dir: Path | None) -> None:
    view.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        if entry.name == ".git":
            continue
        if keep_open and entry.name == keep_open[0]:
            _link_tree(entry, view / entry.name, keep_open[1:], core_dir)
        elif not keep_open and entry.name in CORE_FILES:
            continue
        else:
            (view / entry.name).symlink_to(entry)
    if not keep_open and core_dir is not None:
        for name in CORE_FILES:
            (view / name).symlink_to(core_dir / name)


def checkout_view(view: Path, core_dir: Path | None) -> Path:
    """Build the view at ``view``; ``core_dir`` holds the core files, ``None`` leaves them out."""
    _link_tree(REPO, view, Path(rules_core.RULES_DIR_REL).parts, core_dir)
    if not (view / ".venv").exists():
        (view / ".venv").symlink_to(Path(sys.prefix))
    subprocess.run(["git", "init", "-q", "-b", "main", str(view)], check=True, timeout=30)
    return view
