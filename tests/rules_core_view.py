"""Checkout views whose rules directory carries a chosen rules core, or none.

The rules core is read from the rules directory of the checkout the code runs from
(``scripts/lib/rules_core.py``) unless the machinery roots configuration names another one
(``LEARN_UKRAINIAN_RULES_DIR``, ``scripts/common/repo_root.py``), and a missing core refuses
every launch, dispatch and ask. A launcher test that needs a different core and leaves the
configuration unset therefore runs the launcher from a different checkout: a view.

Launcher wrappers and machinery are copied so physical root lookup stays in the view.
Other entries are linked, except paths named in ``overrides``: a file copied from
another file, written from text, or left out. The view is
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

import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from scripts.common.repo_root import PRODUCT_MARKER
from scripts.lib import rules_core
from tests.helpers import machinery_package, product_checkout
from tests.launcher_sandbox import launcher_environment

REPO = Path(__file__).resolve().parents[1]
CORE_FILES = (Path(rules_core.CORE_REL).name, Path(rules_core.CONTENT_ADDENDUM_REL).name)
_ABSENT_VIEW = pytest.StashKey[Path]()
_BYPASS_VIEW = pytest.StashKey[Path]()
_LAUNCH_VIEW = pytest.StashKey[Path]()
_LAUNCHER_LOADER = (machinery_package(), "lib", "rules_core.sh")
# What the stub does in place of the launcher loader: no core, no seat, launch as before.
_LOADER_STUB = """#!/usr/bin/env bash
# Test-only: the real helpers with the loader replaced by one that loads nothing.
source "$(dirname -- "${{BASH_SOURCE[0]}}")/rules_core.original.sh"
rules_core_load() {{
  LC_RULES_SEAT=""
  LC_RULES_CORE=""
  LC_RULES_CORE_BYTES=0
}}
"""

# A path maps to a file to link, text to write, or None to leave the entry out.
Overrides = Mapping[tuple[str, ...], "Path | str | None"]


def _link_tree(sources: tuple[Path, ...], view: Path, rel: tuple[str, ...], overrides: Overrides) -> None:
    """Link every entry of ``sources`` into ``view``; the first source holding an entry wins.

    A directory present as a real directory in several sources, or holding an override, is
    linked entry by entry, so the view is the union of the sources.
    """
    view.mkdir(parents=True, exist_ok=True)
    entries: dict[str, list[Path]] = {}
    for source in sources:
        for entry in source.iterdir():
            if entry.name != ".git":
                entries.setdefault(entry.name, []).append(entry)
    for name, found in entries.items():
        key = (*rel, name)
        directories = tuple(entry for entry in found if entry.is_dir())
        merged = len(found) > 1 and len(directories) == len(found) and not any(e.is_symlink() for e in found)
        if key in overrides:
            _apply(view / name, overrides[key])
        elif directories and (key[0] == machinery_package() or merged or any(path[: len(key)] == key for path in overrides)):
            _link_tree(directories, view / name, key, overrides)
        elif key[0] == machinery_package() or (len(key) == 1 and name.startswith("start-") and name.endswith(".sh")):
            shutil.copy2(found[0], view / name)
        else:
            (view / name).symlink_to(found[0])
    missing = {
        path[len(rel)]
        for path in overrides
        if path[: len(rel)] == rel and len(path) > len(rel)
    } - entries.keys()
    for name in sorted(missing):
        key = (*rel, name)
        if key in overrides:
            _apply(view / name, overrides[key])
        else:
            _link_tree((), view / name, key, overrides)


def _view_sources() -> tuple[Path, ...]:
    """The product checkout, then this machinery checkout: one source when they are the same.

    Once the machinery is extracted, a launcher runs from the product checkout (root wrappers,
    product data, the linked machinery package) and its machinery-owned files come from here.
    """
    product = product_checkout()
    if product.resolve() == REPO.resolve():
        return (product,)
    # Two checkouts only in the extracted layout: the machinery side must be the tested machinery
    # tree, never an unrenamed source checkout whose scripts/ still holds the machinery.
    assert machinery_package() != "scripts" and not (REPO / "scripts" / "common" / "repo_root.py").exists(), (
        f"the machinery side of a checkout view is an unrenamed source checkout: {REPO}"
    )
    return (product, REPO)


def _apply(target: Path, action: Path | str | None) -> None:
    if isinstance(action, Path):
        if action.is_file():
            shutil.copy2(action, target)
        else:
            # Some fixtures create their telemetry reader after the view.
            target.symlink_to(action)
    elif isinstance(action, str):
        target.write_text(action, encoding="utf-8")
        target.chmod(0o755)


def _build_view(view: Path, overrides: Overrides) -> Path:
    sources = _view_sources()
    view.parent.mkdir(parents=True, exist_ok=True)
    env = launcher_environment(tmp_path=view.parent)
    selected_overrides = dict(overrides)
    loader = REPO.joinpath(*_LAUNCHER_LOADER)
    original = (*_LAUNCHER_LOADER[:-1], "rules_core.original.sh")
    if overrides.get(_LAUNCHER_LOADER) == _LOADER_STUB.format():
        selected_overrides[original] = loader
    marker = Path(PRODUCT_MARKER)
    if marker.parts not in overrides and not any((source / marker).is_file() for source in sources):
        tracked = subprocess.run(
            ["git", "show", f"HEAD:{marker.as_posix()}"],
            cwd=sources[0],
            env=env,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if tracked.returncode == 0:
            selected_overrides[marker.parts] = tracked.stdout.decode("utf-8")
    _link_tree(sources, view, (), selected_overrides)
    if not (view / ".venv").exists():
        (view / ".venv").symlink_to(Path(sys.prefix))
    subprocess.run(["git", "init", "-q", "-b", "main", str(view)], env=env, check=True, timeout=30)
    return view


def install_loader_bypass(root: Path) -> None:
    """Give a synthetic launcher sandbox ``root`` the bypass loader (it does not test the core)."""
    target = root.joinpath(*_LAUNCHER_LOADER)
    target.parent.mkdir(parents=True, exist_ok=True)
    original = target.with_name("rules_core.original.sh")
    shutil.copy2(REPO.joinpath(*_LAUNCHER_LOADER), original)
    _apply(target, _LOADER_STUB.format())


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


def launch_checkout(request: pytest.FixtureRequest) -> Path:
    """This session's checkout view with the real rules core, to run the tracked wrappers from.

    Its own Git repository and interpreter link make it a primary checkout wherever the tests run
    (a dispatch worktree, or an extracted machinery tree beside a product checkout without a venv).
    """
    stash = request.config.stash
    if _LAUNCH_VIEW not in stash:
        factory = request.getfixturevalue("tmp_path_factory")
        stash[_LAUNCH_VIEW] = _build_view(factory.mktemp("launch") / "checkout", {})
    return stash[_LAUNCH_VIEW]


def bypass_checkout(request: pytest.FixtureRequest) -> Path:
    """This session's checkout view whose launcher loader loads nothing, built once per process."""
    stash = request.config.stash
    if _BYPASS_VIEW not in stash:
        factory = request.getfixturevalue("tmp_path_factory")
        stash[_BYPASS_VIEW] = _build_view(factory.mktemp("rules-core-bypass") / "checkout", {_LAUNCHER_LOADER: _LOADER_STUB.format()})
    return stash[_BYPASS_VIEW]


@pytest.fixture(autouse=True)
def rules_core_absent_when_marked(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a ``rules_core_absent`` test with the rules-core loader bypassed.

    Launchers, ACP calls and bridge builders prepend the rules core
    (``scripts/lib/rules_core.py``) and refuse without it. Dispatch v2 requires the
    core to exist without prepending it. Only tests that pin an exact
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
