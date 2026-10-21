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


def install_readonly(root: Path, patch: Callable[[object, str, object], None] = setattr) -> list[tuple[str, str]]:
    """Fail every write at or below ``root`` like a read-only bind; return the refused attempts."""
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

    def refuse(op: str, path: Path, code: int = errno.EROFS):
        refused.append((op, str(path)))
        raise OSError(code, os.strerror(code), str(path))

    def mkdir(path, mode=0o777, *, dir_fd=None):
        resolved = target(path, dir_fd)
        if guarded(resolved):
            # The kernel reports an existing name before the read-only mount.
            refuse("mkdir", resolved, errno.EEXIST if os.path.lexists(resolved) else errno.EROFS)
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

    def readonly(self) -> list[tuple[str, str]]:
        return install_readonly(self.shared, self.monkeypatch.setattr)

    def configure(self, *, basetemp: str | None = None, worker: bool = False) -> SimpleNamespace:
        config = SimpleNamespace(option=SimpleNamespace(basetemp=basetemp), add_cleanup=self.cleanups.append)
        if worker:
            config.workerinput = {"workerid": "gw0"}
        pytest_scratch.pytest_configure(config)
        return config


def _listing(path: Path) -> list[str]:
    return sorted(str(entry.relative_to(path)) for entry in path.rglob("*"))


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    shared = tmp_path / "shared"
    (shared / pytest_scratch.NAMESPACE).mkdir(parents=True, mode=0o700)
    shared.chmod(0o700)
    temp = tmp_path / "sandbox-temp"
    temp.mkdir(mode=0o700)
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
        'pytest_plugins = ["scripts.common.pytest_scratch"]\n'
    )
    (suite / "test_child.py").write_text(f"""
import os
import tempfile
from pathlib import Path

def test_payload(tmp_path):
    payload = Path(tempfile.gettempdir())
    parts = payload.relative_to({str(temp)!r}).parts
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
    (private,) = temp.iterdir()
    assert stat.S_IMODE(private.stat().st_mode) == 0o700
    (run,) = (private / pytest_scratch.RUNS_DIRNAME).iterdir()
    assert json.loads((run / "lease.json").read_text())["state"] == "preserved"
    assert list((run / "scratch" / "base").rglob("payload"))
