"""Checkout views whose rules directory carries a chosen rules core, or none.

The rules core is read from the checkout the code runs from (``scripts/lib/rules_core.py``);
nothing in the environment can point it elsewhere, and a missing core refuses every
launch, dispatch and ask. A launcher test that needs a different core therefore runs the
launcher from a different checkout: a view.

Every entry of the real checkout is a symlink in the view, except the paths named in
``overrides``: a file linked to another file, written from text, or left out. The view is
its own fresh git repository (the launcher refuses a symlinked ``.git``) and links the
running interpreter's venv when the checkout has none (a linked worktree uses the
primary checkout's).

Two views are built from this:

* ``checkout_view(view, core_dir)`` carries the chosen core files, or none (``None``):
  the tests that a missing core refuses, and that a present core loads.
* ``bypass_checkout`` keeps the checkout's own core but swaps ``scripts/lib/rules_core.sh``
  for a stub that skips the loader. It exists for tests that pin an exact argv or prompt
  block order; they carry ``@pytest.mark.rules_core_absent`` and their module imports
  ``rules_core_absent_when_marked``, which also bypasses the in-process loader. Only test
  code reaches the bypass: production has no switch that lets a launch go without the core.

The fixture lives here, not in ``tests/conftest.py``: the view links the whole
checkout, and the root conftest is in every test's import closure.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from scripts.lib import rules_core

REPO = Path(__file__).resolve().parents[1]
CORE_FILES = (Path(rules_core.CORE_REL).name, Path(rules_core.CONTENT_ADDENDUM_REL).name)
_ABSENT_VIEW = pytest.StashKey[Path]()
_BYPASS_VIEW = pytest.StashKey[Path]()
_LAUNCHER_LOADER = ("scripts", "lib", "rules_core.sh")
# What the stub does in place of the launcher loader: no core, no seat, launch as before.
_LOADER_STUB = """#!/usr/bin/env bash
# Test-only: the real helpers with the loader replaced by one that loads nothing.
source "{real}"
rules_core_load() {{
  LC_RULES_SEAT=""
  LC_RULES_CORE=""
  LC_RULES_CORE_BYTES=0
}}
"""

# A path maps to a file to link, text to write, or None to leave the entry out.
Overrides = Mapping[tuple[str, ...], "Path | str | None"]


def _link_tree(source: Path, view: Path, rel: tuple[str, ...], overrides: Overrides) -> None:
    view.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for entry in source.iterdir():
        if entry.name == ".git":
            continue
        seen.add(entry.name)
        key = (*rel, entry.name)
        if key in overrides:
            _apply(view / entry.name, overrides[key])
        elif any(path[: len(key)] == key for path in overrides):
            _link_tree(entry, view / entry.name, key, overrides)
        else:
            (view / entry.name).symlink_to(entry)
    for key, action in overrides.items():
        if key[:-1] == rel and key[-1] not in seen:
            _apply(view / key[-1], action)


def _apply(target: Path, action: Path | str | None) -> None:
    if isinstance(action, Path):
        target.symlink_to(action)
    elif isinstance(action, str):
        target.write_text(action, encoding="utf-8")
        target.chmod(0o755)


def _build_view(view: Path, overrides: Overrides) -> Path:
    _link_tree(REPO, view, (), overrides)
    if not (view / ".venv").exists():
        (view / ".venv").symlink_to(Path(sys.prefix))
    subprocess.run(["git", "init", "-q", "-b", "main", str(view)], check=True, timeout=30)
    return view


def install_loader_bypass(root: Path) -> None:
    """Give a synthetic launcher sandbox ``root`` the bypass loader (it does not test the core)."""
    target = root.joinpath(*_LAUNCHER_LOADER)
    target.parent.mkdir(parents=True, exist_ok=True)
    _apply(target, _LOADER_STUB.format(real=REPO.joinpath(*_LAUNCHER_LOADER)))


def checkout_view(view: Path, core_dir: Path | None) -> Path:
    """Build the view at ``view``; ``core_dir`` holds the core files, ``None`` leaves them out."""
    rules_dir = Path(rules_core.RULES_DIR_REL).parts
    overrides = {(*rules_dir, name): None if core_dir is None else core_dir / name for name in CORE_FILES}
    return _build_view(view, overrides)


def absent_checkout(request: pytest.FixtureRequest) -> Path:
    """This session's checkout view without the rules core, built once per process."""
    stash = request.config.stash
    if _ABSENT_VIEW not in stash:
        factory = request.getfixturevalue("tmp_path_factory")
        stash[_ABSENT_VIEW] = checkout_view(factory.mktemp("rules-core-absent") / "checkout", None)
    return stash[_ABSENT_VIEW]


def bypass_checkout(request: pytest.FixtureRequest) -> Path:
    """This session's checkout view whose launcher loader loads nothing, built once per process."""
    stash = request.config.stash
    if _BYPASS_VIEW not in stash:
        factory = request.getfixturevalue("tmp_path_factory")
        stub = _LOADER_STUB.format(real=REPO.joinpath(*_LAUNCHER_LOADER))
        stash[_BYPASS_VIEW] = _build_view(factory.mktemp("rules-core-bypass") / "checkout", {_LAUNCHER_LOADER: stub})
    return stash[_BYPASS_VIEW]


@pytest.fixture(autouse=True)
def rules_core_absent_when_marked(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a ``rules_core_absent`` test with the rules-core loader bypassed.

    Launchers, ``delegate.py``, ACP calls and bridge builders prepend the rules core
    (``scripts/lib/rules_core.py``) and refuse without it. Only tests that pin an exact
    argv or prompt block order carry the marker; every other test runs with the
    checkout's real core. In-process, the loader's ``require_core`` and ``with_core``
    become pass-throughs; ``run_launcher`` starts subprocess launchers from the bypass view.
    """
    if request.node.get_closest_marker("rules_core_absent") is None:
        return
    from tests import test_launcher_contract

    view = bypass_checkout(request)
    monkeypatch.setattr(rules_core, "require_core", lambda seat=None, root=None: rules_core.resolve_seat(seat))
    monkeypatch.setattr(rules_core, "with_core", lambda prompt, seat=None, root=None: prompt)
    monkeypatch.setattr(test_launcher_contract, "LAUNCH_ROOT", view)
