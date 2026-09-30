"""A checkout view whose rules directory carries a chosen rules core, or none.

The rules core is read from the checkout the code runs from (``scripts/lib/rules_core.py``);
nothing in the environment can point it elsewhere. A launcher test that needs a
different core therefore runs the launcher from a different checkout: this view.

Every entry of the real checkout is a symlink in the view, except the path down to
the rules directory, which holds symlinks to the real rule files plus the chosen
``core.md`` / ``core-curriculum.md``. The view is its own fresh git repository (the
launcher refuses a symlinked ``.git``) and links the running interpreter's venv
when the checkout has none (a linked worktree uses the primary checkout's).

A test that pins an exact argv or prompt block order carries
``@pytest.mark.rules_core_absent`` and its module imports
``rules_core_absent_when_marked``, which runs it from the view without the core.
The fixture lives here, not in ``tests/conftest.py``: the view links the whole
checkout, and the root conftest is in every test's import closure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib import rules_core

REPO = Path(__file__).resolve().parents[1]
CORE_FILES = (Path(rules_core.CORE_REL).name, Path(rules_core.CONTENT_ADDENDUM_REL).name)
_ABSENT_VIEW = pytest.StashKey[Path]()


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


def absent_checkout(request: pytest.FixtureRequest) -> Path:
    """This session's checkout view without the rules core, built once per process."""
    stash = request.config.stash
    if _ABSENT_VIEW not in stash:
        factory = request.getfixturevalue("tmp_path_factory")
        stash[_ABSENT_VIEW] = checkout_view(factory.mktemp("rules-core-absent") / "checkout", None)
    return stash[_ABSENT_VIEW]


@pytest.fixture(autouse=True)
def rules_core_absent_when_marked(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a ``rules_core_absent`` test as if the checkout had no rules core.

    Launchers, ``delegate.py``, ACP calls and bridge builders prepend the rules core
    (``scripts/lib/rules_core.py``). Only tests that pin an exact argv or prompt block
    order carry the marker; every other test runs with the checkout's real core.
    In-process code sees the view's rules directory through the loader's
    ``core_dir`` resolver; ``run_launcher`` starts subprocess launchers from the view.
    """
    if request.node.get_closest_marker("rules_core_absent") is None:
        return
    from tests import test_launcher_contract

    view = absent_checkout(request)
    monkeypatch.setattr(rules_core, "core_dir", lambda root=None: view / rules_core.RULES_DIR_REL)
    monkeypatch.setattr(test_launcher_contract, "LAUNCH_ROOT", view)
