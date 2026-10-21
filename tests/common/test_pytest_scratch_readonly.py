"""The pytest scratch plugin on a shared root a reviewer sandbox mounts read-only (#11317).

One row per shared-root state in the issue's denominator. In-process rows make
every write at or below the shared root fail the way a read-only bind does
(``EROFS``; ``EEXIST`` first for a path that exists). The end-to-end row runs a
real pytest under a real read-only bind where bubblewrap can make one.
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.common import pytest_scratch
from scripts.common.task_scratch import TaskScratchError

REPO = Path(__file__).resolve().parents[2]
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def _fd_path(fd: int) -> Path:
    return Path(os.readlink(f"/proc/self/fd/{fd}"))


def install_readonly(
    root: Path, patch: Callable[[object, str, object], None] = setattr, code: int = errno.EROFS
) -> list[tuple[str, str]]:
    """Fail every write at or below ``root`` like a read-only bind (or with ``code``); return the refused attempts."""
    root = Path(os.path.realpath(root))
    real_mkdir, real_chmod, real_fchmod, real_open = os.mkdir, os.chmod, os.fchmod, os.open
    refused: list[tuple[str, str]] = []

    def target(path, dir_fd=None) -> Path:
        text = os.fsdecode(path)
        if dir_fd is not None and not os.path.isabs(text):
            text = os.path.join(_fd_path(dir_fd), text)
        return Path(os.path.realpath(text))

    def guarded(path: Path) -> bool:
        return path == root or root in path.parents

    def refuse(op: str, path: Path, errcode: int = code):
        refused.append((op, str(path)))
        raise OSError(errcode, os.strerror(errcode), str(path))

    def mkdir(path, mode=0o777, *, dir_fd=None):
        resolved = target(path, dir_fd)
        if guarded(resolved):
            # The kernel reports an existing name before the read-only mount.
            refuse("mkdir", resolved, errno.EEXIST if os.path.lexists(resolved) else code)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    def chmod(path, mode, *, dir_fd=None, follow_symlinks=True):
        if guarded(target(path, dir_fd)):
            refuse("chmod", target(path, dir_fd))
        return real_chmod(path, mode, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    def fchmod(fd, mode):
        if guarded(_fd_path(fd)):
            refuse("fchmod", _fd_path(fd))
        return real_fchmod(fd, mode)

    def open_(path, flags, mode=0o777, *, dir_fd=None):
        if flags & _WRITE_FLAGS and guarded(target(path, dir_fd)):
            refuse("open", target(path, dir_fd))
        return real_open(path, flags, mode, dir_fd=dir_fd)

    for name, value in (("mkdir", mkdir), ("chmod", chmod), ("fchmod", fchmod), ("open", open_)):
        patch(os, name, value)
    return refused


@dataclass
class World:
    shared: Path
    temp: Path
    shm: Path
    monkeypatch: pytest.MonkeyPatch
    cleanups: list[Callable[[], None]] = field(default_factory=list)
    fchmods: list[Path] = field(default_factory=list)

    @property
    def runs_root(self) -> Path:
        return self.shared / pytest_scratch.NAMESPACE

    def make_runs_root(self, mode: int = 0o700) -> Path:
        self.runs_root.mkdir()
        self.runs_root.chmod(mode)
        return self.runs_root

    def readonly(self, code: int = errno.EROFS) -> list[tuple[str, str]]:
        return install_readonly(self.shared, self.monkeypatch.setattr, code)

    def configure(self, *, basetemp: str | None = None, worker: bool = False) -> SimpleNamespace:
        config = SimpleNamespace(option=SimpleNamespace(basetemp=basetemp), add_cleanup=self.cleanups.append)
        if worker:
            config.workerinput = {"workerid": "gw0"}
        pytest_scratch.pytest_configure(config)
        return config


def _listing(path: Path) -> list[str]:
    return sorted(str(entry.relative_to(path)) for entry in path.rglob("*"))


def _require_unreplaceable(path: Path) -> None:
    """Fail loudly when the test's own temp could be replaced by another user: the plugin rightly refuses it."""
    for directory in (path, *path.parents):
        st = directory.lstat()
        mode = stat.S_IMODE(st.st_mode)
        if st.st_uid not in (0, os.geteuid()) or (mode & 0o022 and not mode & stat.S_ISVTX):
            pytest.fail(
                f"tmp_path sits below {directory}, which another user could replace, so the plugin refuses "
                "every TMPDIR here; run with a --basetemp whose ancestors are owned by you or root and are "
                "not group- or other-writable unless sticky"
            )


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _require_unreplaceable(tmp_path)
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o700)
    temp = tmp_path / "sandbox-temp"
    temp.mkdir(mode=0o700)
    shm = tmp_path / "shm"
    shm.mkdir()
    shm.chmod(0o1777)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(shared))
    monkeypatch.setenv("TMPDIR", str(temp))
    monkeypatch.setattr(pytest_scratch, "SHARED_MEMORY_TEMP", shm, raising=False)
    state = World(shared=shared, temp=temp, shm=shm, monkeypatch=monkeypatch)
    real_fchmod = os.fchmod

    def spy(fd, mode):
        state.fchmods.append(_fd_path(fd))
        return real_fchmod(fd, mode)

    monkeypatch.setattr(os, "fchmod", spy)
    previous_tempdir = tempfile.tempdir
    try:
        yield state
    finally:
        for cleanup in reversed(state.cleanups):
            cleanup()
        tempfile.tempdir = previous_tempdir


def _assert_contained_run(config: SimpleNamespace, parent: Path) -> Path:
    """The run sits in the given parent, and fixtures and tempfile share its payload."""
    basetemp = Path(config.option.basetemp)
    payload = basetemp.parent
    assert payload.name == "scratch" and basetemp.name == "base"
    assert payload.is_relative_to(parent)
    # Every default tempfile producer resolves its directory through gettempdir().
    assert os.environ["TMPDIR"] == str(payload) == tempfile.gettempdir()
    lease = json.loads((payload.parent / "lease.json").read_text())
    assert lease["task_id"] == "pytest" and lease["state"] == "registered"
    return payload


def _assert_private_fallback(world: World, config: SimpleNamespace, base: Path) -> None:
    """A fresh owner-only directory below the writable temp holds the run, nothing else."""
    payload = _assert_contained_run(config, base)
    entries = list(base.iterdir())
    assert len(entries) == 1
    private = entries[0]
    assert private.name.startswith(pytest_scratch.FALLBACK_PREFIX)
    st = private.lstat()
    assert stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o700 and st.st_uid == os.geteuid()
    assert payload.relative_to(private).parts[0] == pytest_scratch.RUNS_DIRNAME


# ---- writable shared root ------------------------------------------------------------------------------------


def test_writable_correct_mode_root_is_used_without_any_chmod(world):
    """Defect class: an unconditional fchmod writes a root that is already private (the sandbox crash)."""
    world.make_runs_root(0o700)
    config = world.configure()
    _assert_contained_run(config, world.runs_root / pytest_scratch.RUNS_DIRNAME)
    assert world.runs_root not in world.fchmods
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


@pytest.mark.parametrize("mode", [0o775, 0o750, 0o777], ids=oct)
def test_writable_wrong_mode_root_is_corrected_once(world, mode):
    """Defect class: skipping the mode correction leaves a collaborative-umask root group-accessible."""
    world.make_runs_root(mode)
    config = world.configure()
    assert stat.S_IMODE(world.runs_root.stat().st_mode) == 0o700
    assert world.fchmods.count(world.runs_root) == 1
    _assert_contained_run(config, world.runs_root / pytest_scratch.RUNS_DIRNAME)


# ---- read-only shared root -----------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["private", "missing", "unwritable-but-private-mode"])
def test_readonly_root_runs_from_private_writable_temp(world, state):
    """AC-01. Defect class: a read-only shared root stops configure (fchmod or allocate EROFS)."""
    if state == "private":
        world.make_runs_root(0o700)
    elif state == "unwritable-but-private-mode":
        world.make_runs_root(0o750)
    before = _listing(world.shared)
    refused = world.readonly()
    config = world.configure()
    _assert_private_fallback(world, config, world.temp)
    assert _listing(world.shared) == before
    if state == "private":
        assert ("fchmod", str(world.runs_root)) not in refused
    assert list(world.shm.iterdir()) == []


@pytest.mark.parametrize("tmpdir", ["unset", "inside-readonly-root", "missing"])
def test_readonly_root_uses_shared_memory_when_tmpdir_is_unusable(world, tmpdir):
    """Defect class: the fallback trusts TMPDIR even when it is absent or on the same read-only mount."""
    world.make_runs_root(0o700)
    if tmpdir == "unset":
        world.monkeypatch.delenv("TMPDIR")
    elif tmpdir == "inside-readonly-root":
        world.monkeypatch.setenv("TMPDIR", str(world.shared))
    else:
        world.monkeypatch.setenv("TMPDIR", str(world.temp / "absent"))
    world.readonly()
    config = world.configure()
    _assert_private_fallback(world, config, world.shm)


def test_fallback_in_world_writable_temp_gets_a_private_subdirectory(world):
    """Defect class: the fallback allocates straight into a world-writable parent another user can race."""
    world.make_runs_root(0o700)
    world.temp.chmod(0o1777)
    world.readonly()
    config = world.configure()
    _assert_private_fallback(world, config, world.temp)


def test_no_writable_fallback_raises_typed_error(world):
    """Defect class: with nowhere writable the plugin crashes untyped or writes somewhere uncontained."""
    world.make_runs_root(0o700)
    world.monkeypatch.setenv("TMPDIR", str(world.temp / "absent"))
    world.monkeypatch.setattr(pytest_scratch, "SHARED_MEMORY_TEMP", world.shm / "absent")
    world.readonly()
    with pytest.raises(TaskScratchError, match="no private writable temp"):
        world.configure()
    assert world.cleanups == []
    assert os.environ["TMPDIR"] == str(world.temp / "absent")


# ---- refusals ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", [0o770, 0o707, 0o777, 0o720], ids=oct)
def test_readonly_group_or_other_writable_root_refuses(world, mode):
    """AC-02. Defect class: a tamperable shared root is silently bypassed instead of refused."""
    world.make_runs_root(mode)
    world.readonly()
    with pytest.raises(TaskScratchError, match="group- or other-writable"):
        world.configure()
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []
    assert world.cleanups == []


@pytest.mark.parametrize("mount", ["writable", "readonly"])
def test_foreign_owned_root_refuses_without_chmod(world, mount):
    """AC-02. Defect class: another user's root is chmodded or replaced by a fallback instead of refused."""
    world.make_runs_root(0o750)
    if mount == "readonly":
        world.readonly()
    real = os.geteuid()
    world.monkeypatch.setattr(os, "geteuid", lambda: real + 1)
    with pytest.raises(TaskScratchError, match="owned by uid"):
        world.configure()
    assert world.fchmods == []
    assert stat.S_IMODE(world.runs_root.stat().st_mode) == 0o750
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


def test_ownership_is_rechecked_on_the_descriptor_before_fchmod(world):
    """AC-02. Defect class: a root swapped for a foreign one after the path check still gets fchmodded."""
    world.make_runs_root(0o750)
    real_fstat = os.fstat

    def fstat(fd):
        st = real_fstat(fd)
        if _fd_path(fd) != world.runs_root:
            return st
        fields = list(st[:10])
        fields[4] = st.st_uid + 1
        return os.stat_result(fields)

    world.monkeypatch.setattr(os, "fstat", fstat)
    with pytest.raises(TaskScratchError, match="owned by uid"):
        world.configure()
    assert world.fchmods == []
    assert stat.S_IMODE(world.runs_root.stat().st_mode) == 0o750


@pytest.mark.parametrize("mount", ["writable", "readonly"])
def test_symlinked_root_refuses(world, tmp_path, mount):
    """AC-02. Defect class: a symlinked root redirects the run, or the fallback hides the redirect."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(mode=0o700)
    world.runs_root.symlink_to(elsewhere, target_is_directory=True)
    if mount == "readonly":
        world.readonly()
    with pytest.raises(TaskScratchError, match="symlink"):
        world.configure()
    assert list(elsewhere.iterdir()) == []
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


@pytest.mark.parametrize("mount", ["writable", "readonly"])
@pytest.mark.parametrize("mode", [0o333, 0o303], ids=oct)
def test_unreadable_group_or_other_writable_root_refuses(world, mount, mode):
    """AC-02. Defect class: a tamperable root the owner cannot open is bypassed by the fallback, not refused."""
    world.make_runs_root(mode)
    real_chmod = os.chmod
    if mount == "readonly":
        world.readonly()
    try:
        with pytest.raises(TaskScratchError, match="group- or other-writable"):
            world.configure()
    finally:
        real_chmod(world.runs_root, 0o700)  # let tmp_path cleanup list the root
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []
    assert world.cleanups == []


def test_root_open_denied_does_not_fall_back(world):
    """Defect class: a denied read-open of the root (never a read-only-mount symptom) is taken for one."""
    world.make_runs_root(0o700)
    world.readonly()
    guarded_open = os.open

    def open_(path, flags, mode=0o777, *, dir_fd=None):
        if dir_fd is None and Path(os.fsdecode(path)) == world.runs_root:
            raise OSError(errno.EACCES, os.strerror(errno.EACCES), os.fsdecode(path))
        return guarded_open(path, flags, mode, dir_fd=dir_fd)

    world.monkeypatch.setattr(os, "open", open_)
    with pytest.raises(OSError) as raised:
        world.configure()
    assert raised.value.errno == errno.EACCES
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


@pytest.mark.parametrize("mode", [0o700, 0o750], ids=oct)
def test_other_write_errors_on_the_shared_root_stay_loud(world, mode):
    """Defect class: any OSError (a full disk, an I/O error) is taken for a read-only mount and hidden."""
    world.make_runs_root(mode)
    world.readonly(errno.ENOSPC)
    with pytest.raises(OSError) as raised:
        world.configure()
    assert raised.value.errno == errno.ENOSPC
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


# ---- fallback containment ------------------------------------------------------------------------------------


def _swap_fallback_root(world: World, outside: Path, *, under: Path, when: str) -> list[Path]:
    """Rename the fresh fallback directory away and plant a symlink to ``outside`` in its place."""
    swapped: list[Path] = []

    def swap(private: Path) -> None:
        if private.parent == under and not swapped:
            private.rename(private.with_name(private.name + ".moved"))
            private.symlink_to(outside, target_is_directory=True)
            swapped.append(private)

    if when == "after-create":
        real_make = pytest_scratch._make_private_dir

        def make_private_dir(base_fd):
            name = real_make(base_fd)
            swap(_fd_path(base_fd) / name)
            return name

        world.monkeypatch.setattr(pytest_scratch, "_make_private_dir", make_private_dir)
    else:
        real_allocate = pytest_scratch.allocate

        def allocate(task_id, *, root, namespace_dirname):
            swap(root)
            return real_allocate(task_id, root=root, namespace_dirname=namespace_dirname)

        world.monkeypatch.setattr(pytest_scratch, "allocate", allocate)
    return swapped


@pytest.mark.parametrize("when", ["after-create", "before-allocate"])
def test_fallback_directory_swapped_for_a_symlink_fails_closed(world, tmp_path, when):
    """Defect class: a fallback path replaced after its check redirects the run outside the temp."""
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    world.make_runs_root(0o700)
    world.readonly()
    swapped = _swap_fallback_root(world, outside, under=world.temp, when=when)
    with pytest.raises(TaskScratchError, match=r"changed|symlink"):
        world.configure()
    assert swapped
    assert world.cleanups == []
    assert os.environ["TMPDIR"] == str(world.temp)


@pytest.mark.parametrize("mode", [0o777, 0o770], ids=oct)
def test_fallback_skips_a_temp_others_can_rename_entries_in(world, tmp_path, mode):
    """Defect class: a non-sticky shared temp lets another user swap the run directory after allocation."""
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    world.make_runs_root(0o700)
    world.temp.chmod(mode)
    world.readonly()
    swapped = _swap_fallback_root(world, outside, under=world.temp, when="before-allocate")
    config = world.configure()
    _assert_private_fallback(world, config, world.shm)
    assert swapped == [] and list(world.temp.iterdir()) == [] and list(outside.iterdir()) == []


@pytest.mark.parametrize("mode", [0o777, 0o770], ids=oct)
def test_shared_memory_others_can_rename_entries_in_is_refused(world, mode):
    """Defect class: with TMPDIR unusable, a non-sticky shared-memory temp is used and its run swapped."""
    world.make_runs_root(0o700)
    world.monkeypatch.setenv("TMPDIR", str(world.temp / "absent"))
    world.shm.chmod(mode)
    world.readonly()
    with pytest.raises(TaskScratchError, match=r"no private writable temp.*replaceable"):
        world.configure()
    assert list(world.shm.iterdir()) == [] and world.cleanups == []


# ---- TMPDIR ancestors ----------------------------------------------------------------------------------------


def _nested_tmpdir(world: World, chain: list[tuple[str, int]]) -> Path:
    """Point TMPDIR at an owner-only temp below ``(name, mode)`` ancestors made in the test's own temp."""
    parent = world.shared.parent
    for name, mode in chain:
        parent = parent / name
        parent.mkdir()
        parent.chmod(mode)
    temp = parent / "sandbox-temp"
    temp.mkdir(mode=0o700)
    world.monkeypatch.setenv("TMPDIR", str(temp))
    world.make_runs_root(0o700)
    world.readonly()
    return temp


def test_private_tmpdir_name_replaceable_from_shared_ancestor_stays_contained(world, tmp_path):
    """Held-out regression from the round-2 review (#11317).

    Defect class: a 0700 TMPDIR below a non-sticky shared ancestor is renamed and
    replaced by a symlink between its check and the allocation, so the run lands
    outside the provisioned scratch.
    """
    ancestor = tmp_path / "shared-ancestor"
    ancestor.mkdir()
    ancestor.chmod(0o777)
    provisioned = ancestor / "sandbox-temp"
    provisioned.mkdir(mode=0o700)
    outside = tmp_path / "outside-provisioned"
    outside.mkdir(mode=0o700)
    provisioned_id = (provisioned.stat().st_dev, provisioned.stat().st_ino)
    world.monkeypatch.setenv("TMPDIR", str(provisioned))
    real_mkdir = os.mkdir
    swapped: list[bool] = []

    def mkdir(path, mode=0o777, *, dir_fd=None):
        # Another user swaps the TMPDIR name just before anything is created in it.
        parent = os.fstat(dir_fd) if dir_fd is not None else os.stat(Path(os.fsdecode(path)).parent)
        if (parent.st_dev, parent.st_ino) == provisioned_id and not swapped:
            provisioned.rename(ancestor / "sandbox-temp.saved")
            provisioned.symlink_to(outside, target_is_directory=True)
            swapped.append(True)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    world.monkeypatch.setattr(os, "mkdir", mkdir)
    world.make_runs_root(0o700)
    world.readonly()
    config = world.configure()
    assert Path(config.option.basetemp).is_relative_to(world.shm), "accepted payload outside provisioned scratch"
    _assert_private_fallback(world, config, world.shm)
    assert swapped == [] and list(outside.iterdir()) == [] and list(provisioned.iterdir()) == []


@pytest.mark.parametrize(
    "chain",
    [
        pytest.param([("parent", 0o777)], id="nonsticky-0777-parent"),
        pytest.param([("grandparent", 0o777), ("parent", 0o755)], id="nonsticky-0777-grandparent"),
        pytest.param([("grandparent", 0o770), ("parent", 0o700)], id="group-writable-grandparent"),
    ],
)
def test_tmpdir_below_an_ancestor_others_can_rename_in_is_skipped(world, chain):
    """Defect class: only TMPDIR's own mode is checked, so an ancestor another user can rename in redirects it."""
    temp = _nested_tmpdir(world, chain)
    config = world.configure()
    _assert_private_fallback(world, config, world.shm)
    assert list(temp.iterdir()) == []


def test_tmpdir_below_a_sticky_world_writable_ancestor_is_used(world):
    """Defect class: a normal sticky system temp on TMPDIR's path is refused, losing the sandbox's own temp."""
    temp = _nested_tmpdir(world, [("system-temp", 0o1777)])
    config = world.configure()
    _assert_private_fallback(world, config, temp)
    assert list(world.shm.iterdir()) == []


@pytest.mark.parametrize("owner", ["another-user", "root"])
def test_tmpdir_ancestor_owned_by_another_user_is_skipped(world, owner):
    """Defect class: an ancestor owned by another user (who may rename in it at will) is trusted; root is not one."""
    temp = _nested_tmpdir(world, [("owned", 0o755)])
    ancestor = temp.parent
    uid = 0 if owner == "root" else os.geteuid() + 1
    real_fstat = os.fstat

    def fstat(fd):
        st = real_fstat(fd)
        if _fd_path(fd) != ancestor:
            return st
        fields = list(st[:10])
        fields[4] = uid
        return os.stat_result(fields)

    world.monkeypatch.setattr(os, "fstat", fstat)
    config = world.configure()
    if owner == "root":
        _assert_private_fallback(world, config, temp)
        assert list(world.shm.iterdir()) == []
    else:
        _assert_private_fallback(world, config, world.shm)
        assert list(temp.iterdir()) == []


def test_tmpdir_below_a_symlinked_ancestor_is_skipped(world, tmp_path):
    """Defect class: a symlink on TMPDIR's path is followed, so whoever can re-point it chooses the run's home."""
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir(mode=0o700)
    target = real_parent / "sandbox-temp"
    target.mkdir(mode=0o700)
    link = tmp_path / "link-parent"
    link.symlink_to(real_parent, target_is_directory=True)
    world.monkeypatch.setenv("TMPDIR", str(link / "sandbox-temp"))
    world.make_runs_root(0o700)
    world.readonly()
    config = world.configure()
    _assert_private_fallback(world, config, world.shm)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize(
    "suffix",
    ["link/../leaf", "link/../leaf/", "link/./../leaf/.", "link/", "link/."],
)
def test_tmpdir_as_supplied_is_walked_so_a_symlink_before_dot_dot_is_skipped(world, tmp_path, suffix):
    """Defect class: normalizing TMPDIR before the walk erases a symlink component, so the walk verifies
    a different directory than TMPDIR names and the run lands outside the provisioned temp (round-3 F3).
    """
    lexical = tmp_path / "lexical"
    semantic = tmp_path / "semantic"
    target = semantic / "target"
    for directory in (lexical, semantic, target, lexical / "leaf", semantic / "leaf"):
        directory.mkdir(mode=0o700)
    (lexical / "link").symlink_to(target, target_is_directory=True)
    world.monkeypatch.setenv("TMPDIR", f"{lexical}/{suffix}")
    world.make_runs_root(0o700)
    world.readonly()
    config = world.configure()
    for directory in (lexical / "leaf", semantic / "leaf", target):
        assert list(directory.iterdir()) == [], f"the run landed in {directory}, not the provisioned TMPDIR"
    _assert_private_fallback(world, config, world.shm)


# ---- TMPDIR carried byte for byte ----------------------------------------------------------------------------


def _supply_tmpdir(world: World, value: str) -> None:
    world.monkeypatch.setenv("TMPDIR", value)
    world.make_runs_root(0o700)
    world.readonly()


def _fallbacks_in(directory: Path) -> list[Path]:
    """Private fallback directories made directly in ``directory``."""
    return [entry for entry in directory.iterdir() if entry.name.startswith(pytest_scratch.FALLBACK_PREFIX)]


def _siblings(tmp_path: Path, provisioned: str, *decoys: str) -> tuple[Path, list[Path]]:
    """Make the provisioned TMPDIR and decoy directories a transformed value would name, all owner-only."""
    parent = tmp_path / "named"
    parent.mkdir(mode=0o700)
    made = []
    for name in (provisioned, *decoys):
        directory = parent / name if name else parent
        directory.mkdir(mode=0o700, exist_ok=True)
        made.append(directory)
    return made[0], [decoy for decoy in made[1:] if decoy != made[0]]


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("temp ", id="trailing-space"),
        pytest.param(" temp", id="leading-space"),
        pytest.param("   ", id="spaces-only"),
        pytest.param("temp\n", id="trailing-newline"),
        pytest.param("temp\t", id="trailing-tab"),
        pytest.param("temp ", id="trailing-no-break-space"),
        pytest.param("temp\x1f", id="trailing-unit-separator"),
    ],
)
def test_tmpdir_whitespace_belongs_to_the_directory_name(world, tmp_path, name):
    """Held-out regression from the round-4 review (#11317).

    Defect class: whitespace is stripped from TMPDIR before verification, so a
    directory whose name starts or ends with whitespace is swapped for its
    stripped namesake and the run lands outside the provisioned temp.
    """
    provisioned, decoys = _siblings(tmp_path, name, name.strip())
    _supply_tmpdir(world, f"{provisioned.parent}/{name}")
    config = world.configure()
    for decoy in decoys:
        assert _fallbacks_in(decoy) == [], "whitespace stripping wrote outside the provisioned TMPDIR"
    _assert_private_fallback(world, config, provisioned)


@pytest.mark.parametrize(
    ("prefix", "suffix"),
    [(" ", ""), ("\t", ""), ("", " "), ("", "\n")],
    ids=["leading-space", "leading-tab", "trailing-space", "trailing-newline"],
)
def test_tmpdir_padded_with_whitespace_is_not_trimmed_to_another_directory(world, prefix, suffix):
    """Defect class: a padded TMPDIR (relative, or naming no directory) is trimmed to one it does not name."""
    _supply_tmpdir(world, f"{prefix}{world.temp}{suffix}")
    config = world.configure()
    assert list(world.temp.iterdir()) == [], "a trimmed TMPDIR was used"
    _assert_private_fallback(world, config, world.shm)


@pytest.mark.parametrize("spelling", ["{p}/temp/", "{p}/temp//", "{p}//temp", "{p}/./temp", "{p}/temp/.", "/{p}/temp"])
def test_tmpdir_spelled_with_redundant_separators_lands_in_that_directory(world, tmp_path, spelling):
    """Defect class: an equivalent spelling (trailing slash, doubled slash, ".") is refused or allocated
    elsewhere, because the walk and the allocation each re-derive the path differently.
    """
    provisioned, _ = _siblings(tmp_path, "temp")
    value = spelling.replace("{p}", str(provisioned.parent))
    _supply_tmpdir(world, value)
    config = world.configure()
    # Lexically the run sits below the value as supplied (a leading "//" stays), which is the provisioned temp.
    assert Path(value).samefile(provisioned)
    _assert_private_fallback(world, config, Path(value))
    assert list(world.shm.iterdir()) == []


def test_tmpdir_dollar_name_is_not_expanded(world, tmp_path):
    """Defect class: TMPDIR goes through expandvars, so a directory named "$VAR" is swapped for $VAR's value."""
    provisioned, decoys = _siblings(tmp_path, "$LU_SCRATCH_PROBE", "decoy")
    world.monkeypatch.setenv("LU_SCRATCH_PROBE", "decoy")
    _supply_tmpdir(world, f"{provisioned.parent}/$LU_SCRATCH_PROBE")
    config = world.configure()
    assert _fallbacks_in(decoys[0]) == [], "TMPDIR was expanded"
    _assert_private_fallback(world, config, provisioned)


@pytest.mark.parametrize("value", ["~", "~/temp"])
def test_tmpdir_tilde_is_not_expanded_to_home(world, tmp_path, value):
    """Defect class: TMPDIR goes through expanduser, so a relative "~" value is taken for the home directory."""
    home = tmp_path / "home"
    (home / "temp").mkdir(parents=True, mode=0o700)
    home.chmod(0o700)
    world.monkeypatch.setenv("HOME", str(home))
    _supply_tmpdir(world, value)
    config = world.configure()
    assert _fallbacks_in(home) == [] and _fallbacks_in(home / "temp") == [], "TMPDIR was expanded to HOME"
    _assert_private_fallback(world, config, world.shm)


@pytest.mark.parametrize("value", ["temp", "./temp", "temp/"])
def test_relative_tmpdir_is_not_anchored_at_the_working_directory(world, tmp_path, value):
    """Defect class: a relative TMPDIR goes through abspath, so the current directory picks the run's home."""
    provisioned, _ = _siblings(tmp_path, "temp")
    world.monkeypatch.chdir(provisioned.parent)
    _supply_tmpdir(world, value)
    config = world.configure()
    assert _fallbacks_in(provisioned) == [], "a relative TMPDIR was made absolute"
    _assert_private_fallback(world, config, world.shm)


def test_tmpdir_that_is_a_symlink_is_skipped_not_resolved(world, tmp_path):
    """Defect class: TMPDIR goes through realpath or Path.resolve(), so a symlink is replaced by its target."""
    target, _ = _siblings(tmp_path, "target")
    link = target.parent / "link"
    link.symlink_to(target, target_is_directory=True)
    _supply_tmpdir(world, str(link))
    config = world.configure()
    assert list(target.iterdir()) == [], "a symlinked TMPDIR was resolved"
    _assert_private_fallback(world, config, world.shm)


def test_tmpdir_case_is_preserved(world, tmp_path):
    """Defect class: TMPDIR is case-folded, so "Temp" is swapped for a sibling "temp"."""
    provisioned, decoys = _siblings(tmp_path, "Temp", "temp")
    _supply_tmpdir(world, str(provisioned))
    config = world.configure()
    assert _fallbacks_in(decoys[0]) == [], "TMPDIR was case-folded"
    _assert_private_fallback(world, config, provisioned)


@pytest.mark.parametrize("name", ["a\nb", "\x1b[1mtemp", "temp\x7f", "tab\tin"], ids=["newline", "esc", "del", "tab"])
def test_tmpdir_with_control_characters_lands_in_that_directory(world, tmp_path, name):
    """Defect class: control characters are dropped or refused, so a legitimate name loses its temp or another
    directory is used.
    """
    provisioned, decoys = _siblings(tmp_path, name, "".join(char for char in name if char.isprintable()))
    _supply_tmpdir(world, str(provisioned))
    config = world.configure()
    for decoy in decoys:
        assert _fallbacks_in(decoy) == [], "control characters were dropped from TMPDIR"
    _assert_private_fallback(world, config, provisioned)


def test_tmpdir_with_non_utf8_bytes_lands_in_that_directory(world, tmp_path):
    """Defect class: an encoding round trip (replace or ignore) changes TMPDIR's bytes, so a sibling is used."""
    _, decoys = _siblings(tmp_path, "temp-", "temp-�")
    raw = os.fsencode(tmp_path / "named") + b"/temp-\xff"
    os.mkdir(raw, 0o700)
    provisioned = Path(os.fsdecode(raw))
    _supply_tmpdir(world, os.fsdecode(raw))
    assert os.environb[b"TMPDIR"] == raw
    config = world.configure()
    for decoy in decoys:
        assert _fallbacks_in(decoy) == [], "TMPDIR bytes were re-encoded"
    _assert_private_fallback(world, config, provisioned)


@pytest.mark.parametrize(
    "value",
    ["", "   ", "\n", "named/temp", "/named\0/temp", "/named/temp-\ud800"],
    ids=["empty", "spaces-only", "newline-only", "relative", "nul", "unencodable"],
)
def test_unrepresentable_tmpdir_is_skipped_for_shared_memory(world, tmp_path, value):
    """Defect class: a TMPDIR the OS cannot take verbatim crashes the walk (ValueError) or is coerced into
    another path. A NUL or an unencodable character cannot be put in a real environment, so the lookup
    itself returns them here.
    """
    provisioned, _ = _siblings(tmp_path, "temp")
    world.monkeypatch.chdir(tmp_path)
    world.make_runs_root(0o700)
    world.readonly()
    environ_type = type(os.environ)
    real_get = environ_type.get

    def get(mapping, key, default=None):
        return value if mapping is os.environ and key == "TMPDIR" else real_get(mapping, key, default)

    world.monkeypatch.setattr(environ_type, "get", get)
    bases = [os.fspath(base) for base, _ in pytest_scratch._fallback_bases()]
    assert bases == [os.fspath(world.shm)], "an unrepresentable TMPDIR was kept as a candidate"
    scratch = pytest_scratch._allocate_run()
    try:
        assert scratch.payload_dir.is_relative_to(world.shm)
    finally:
        scratch.preserve()
    assert _fallbacks_in(provisioned) == [] and _fallbacks_in(provisioned.parent) == []


def test_tmpdir_too_long_to_resolve_whole_is_skipped(world, tmp_path):
    """Defect class: a TMPDIR longer than the kernel resolves passes the per-component walk, then the
    allocation by path fails, so configure crashes instead of using the next candidate.
    """
    component = "d" * 250
    chain = tmp_path / "deep"
    chain.mkdir(mode=0o700)
    fd = os.open(chain, os.O_RDONLY | os.O_DIRECTORY)
    value = str(chain)
    try:
        while len(os.fsencode(value)) <= os.pathconf("/", "PC_PATH_MAX"):
            os.mkdir(component, 0o700, dir_fd=fd)
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = child
            value += "/" + component
        world.monkeypatch.setenv("TMPDIR", value)
        # The read-only shim resolves descriptors through /proc, which cannot name a path this long; stand in
        # for a safe read-only shared root directly so every call below is the real one.
        world.monkeypatch.setattr(pytest_scratch, "_private_shared_root", lambda: None)
        config = world.configure()
        assert os.listdir(fd) == [], "the over-long TMPDIR was written"
    finally:
        os.close(fd)
        shutil.rmtree(chain)
    _assert_private_fallback(world, config, world.shm)


def test_tmpdir_whose_dot_dot_detours_through_a_replaceable_directory_is_skipped(world, tmp_path):
    """Defect class: the walk verifies a normalized TMPDIR, so a symlink detour through a directory another
    user can rename in is trusted because ".." brings it back to the verified directory, and that user can
    re-point the detour between the check and the allocation.
    """
    lexical = tmp_path / "lexical"
    for directory in (lexical, lexical / "x", lexical / "leaf"):
        directory.mkdir(mode=0o700)
    public = tmp_path / "public"
    public.mkdir()
    public.chmod(0o777)
    (public / "x").symlink_to(lexical / "x", target_is_directory=True)
    (lexical / "link").symlink_to(public / "x", target_is_directory=True)
    value = f"{lexical}/link/../leaf"
    assert os.path.samefile(value, lexical / "leaf")
    _supply_tmpdir(world, value)
    config = world.configure()
    assert list((lexical / "leaf").iterdir()) == [], "a TMPDIR through a replaceable directory was used"
    _assert_private_fallback(world, config, world.shm)


def test_tmpdir_replaced_after_the_walk_fails_closed_without_writing_outside(world, tmp_path):
    """Defect class: the run directory is made by path after the walk, so a replaced TMPDIR still redirects it."""
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    world.make_runs_root(0o700)
    world.readonly()
    real_make = pytest_scratch._make_private_dir

    def make_private_dir(base_fd):
        # The same user (the only one left who can) swaps TMPDIR after it was verified and opened.
        world.temp.rename(world.temp.with_name("sandbox-temp.moved"))
        world.temp.symlink_to(outside, target_is_directory=True)
        return real_make(base_fd)

    world.monkeypatch.setattr(pytest_scratch, "_make_private_dir", make_private_dir)
    with pytest.raises(TaskScratchError, match="changed after creation"):
        world.configure()
    assert list(outside.iterdir()) == [] and world.cleanups == []
    (made,) = world.temp.with_name("sandbox-temp.moved").iterdir()
    assert made.name.startswith(pytest_scratch.FALLBACK_PREFIX)


# ---- callers that own their base temp ------------------------------------------------------------------------


@pytest.mark.parametrize("caller", ["explicit-basetemp", "xdist-worker"])
def test_callers_owning_their_base_temp_are_untouched(world, caller):
    """Defect class: an explicit --basetemp or an xdist worker is re-allocated or has TMPDIR rewritten."""
    world.make_runs_root(0o700)
    before = _listing(world.shared)
    refused = world.readonly()
    basetemp = str(world.temp / "gate-owned") if caller == "explicit-basetemp" else None
    config = world.configure(basetemp=basetemp, worker=caller == "xdist-worker")
    assert config.option.basetemp == basetemp
    assert world.cleanups == [] and refused == [] and world.fchmods == []
    assert os.environ["TMPDIR"] == str(world.temp)
    assert _listing(world.shared) == before
    assert list(world.temp.iterdir()) == [] and list(world.shm.iterdir()) == []


# ---- end to end ----------------------------------------------------------------------------------------------


def _readonly_bind(shared: Path) -> list[str]:
    """A real read-only bind of the shared root where bubblewrap can make one, else none."""
    binary = shutil.which("bwrap")
    if binary is None:
        return []
    prefix = [binary, "--dev-bind", "/", "/", "--ro-bind", str(shared), str(shared), "--die-with-parent"]
    try:
        probe = subprocess.run([*prefix, "true"], capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return prefix if probe.returncode == 0 else []


def test_real_pytest_on_readonly_shared_root_runs_to_completion(tmp_path):
    """AC-01 end to end. Defect class: a governed pytest in a read-only reviewer sandbox exits 3 at configure."""
    _require_unreplaceable(tmp_path)
    shared = tmp_path / "shared"
    (shared / pytest_scratch.NAMESPACE).mkdir(parents=True, mode=0o700)
    shared.chmod(0o700)
    temp = tmp_path / "sandbox-temp"
    temp.mkdir(mode=0o700)
    shm = tmp_path / "shm"
    shm.mkdir()
    shm.chmod(0o1777)
    suite = tmp_path / "suite"
    suite.mkdir()
    prefix = _readonly_bind(shared)
    # Without a real bind the child installs this module's read-only shim before configure.
    shim = (
        ""
        if prefix
        else (
            "from tests.common.test_pytest_scratch_readonly import install_readonly\n"
            f"install_readonly(Path({str(shared)!r}))\n"
        )
    )
    (suite / "conftest.py").write_text(
        f"import sys\nfrom pathlib import Path\nsys.path.insert(0, {str(REPO)!r})\n{shim}"
        "import scripts.common.pytest_scratch as plugin\n"
        f"plugin.SHARED_MEMORY_TEMP = Path({str(shm)!r})\n"
        'pytest_plugins = ["scripts.common.pytest_scratch"]\n'
    )
    (suite / "test_child.py").write_text(f"""
import os
import stat
import tempfile
from pathlib import Path

def _unreplaceable(path):
    for directory in (path, *path.parents):
        st = directory.lstat()
        mode = stat.S_IMODE(st.st_mode)
        if st.st_uid not in (0, os.geteuid()) or (mode & 0o022 and not mode & stat.S_ISVTX):
            return False
    return True

def test_payload(tmp_path):
    # The policy as this namespace sees it: an unprivileged user namespace shows root's directories as unmapped.
    temp = Path({str(temp)!r})
    expected = temp if _unreplaceable(temp) else Path({str(shm)!r})
    payload = Path(tempfile.gettempdir())
    parts = payload.relative_to(expected).parts
    assert parts[0].startswith("lu-pytest-") and parts[1] == "runs" and parts[-1] == "scratch"
    assert os.environ["TMPDIR"] == str(payload)
    assert tmp_path.is_relative_to(payload)
    (tmp_path / "payload").write_text("hello")
""")
    result = subprocess.run(
        [*prefix, sys.executable, "-m", "pytest", "-q", "-n", "2", "-p", "no:cacheprovider"],
        cwd=suite,
        capture_output=True,
        text=True,
        timeout=120,
        # A fixture suite, not a governed run: no inherited slot plugin or holder marker.
        env={"LU_SCRATCH_ROOT": str(shared), "TMPDIR": str(temp)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert _listing(shared) == [pytest_scratch.NAMESPACE]
    (used,) = [base for base in (temp, shm) if any(base.iterdir())]
    (private,) = used.iterdir()
    assert stat.S_IMODE(private.stat().st_mode) == 0o700
    (run,) = (private / pytest_scratch.RUNS_DIRNAME).iterdir()
    assert json.loads((run / "lease.json").read_text())["state"] == "preserved"
    assert list((run / "scratch" / "base").rglob("payload"))
