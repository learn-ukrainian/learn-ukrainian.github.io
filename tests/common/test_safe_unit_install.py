"""Shared unit-install helper: no write, read or removal follows a symlink (#9875)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.common import safe_unit_install as safe
from scripts.common.safe_unit_install import InstallError


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def test_open_unit_dir_creates_missing_components_only_on_request(home: Path) -> None:
    unit_dir = home / "a" / "b"
    assert safe.open_unit_dir(unit_dir) is None
    assert not (home / "a").exists()
    fd = safe.open_unit_dir(unit_dir, create=True)
    assert fd is not None
    try:
        assert os.path.samestat(os.fstat(fd), unit_dir.stat())
    finally:
        os.close(fd)


def test_open_unit_dir_anchors_at_explicit_home(tmp_path: Path, home: Path) -> None:
    """A link above the given home is trusted; one below it is refused."""
    real = tmp_path / "real-home"
    (real / "Library").mkdir(parents=True)
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(tmp_path, target_is_directory=True)
    fd = safe.open_unit_dir(linked_parent / "real-home" / "Library", home=linked_parent / "real-home")
    assert fd is not None
    os.close(fd)
    with pytest.raises(InstallError, match="symlinked path component"):
        safe.open_unit_dir(linked_parent / "real-home" / "Library")  # anchored at "/" instead: the link is refused


def test_open_unit_dir_refuses_a_non_directory_component(home: Path) -> None:
    (home / "file").write_text("x")
    with pytest.raises(InstallError, match="non-directory path component"):
        safe.open_unit_dir(home / "file" / "units")


def test_install_unit_skips_identical_content_and_mode_and_repairs_mode(home: Path) -> None:
    unit = home / "units" / "a.service"
    assert safe.install_unit(unit, b"one", mode=0o600) is True
    assert safe.install_unit(unit, b"one", mode=0o600) is False
    unit.chmod(0o644)
    assert safe.install_unit(unit, b"one", mode=0o600) is True
    assert unit.stat().st_mode & 0o777 == 0o600
    assert safe.install_unit(unit, b"two", mode=0o644) is True
    assert (unit.read_bytes(), unit.stat().st_mode & 0o777) == (b"two", 0o644)
    assert safe.load_unit(unit) == (b"two", 0o644)
    assert sorted(path.name for path in unit.parent.iterdir()) == ["a.service"]


def test_load_unit_missing_and_refused(home: Path) -> None:
    assert safe.load_unit(home / "missing" / "a.service") is None
    (home / "units").mkdir()
    assert safe.load_unit(home / "units" / "a.service") is None
    (home / "units" / "subdir").mkdir()
    with pytest.raises(InstallError, match="non-regular or symlinked unit file"):
        safe.load_unit(home / "units" / "subdir")


def test_write_unit_removes_its_temporary_file_on_failure(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (home / "units").mkdir()
    fd = safe.open_unit_dir(home / "units")
    assert fd is not None

    def failing_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("rename refused")

    monkeypatch.setattr(safe.os, "replace", failing_replace)
    try:
        with pytest.raises(OSError, match="rename refused"):
            safe.write_unit(fd, "a.service", b"content", mode=0o600)
    finally:
        os.close(fd)
    assert list((home / "units").iterdir()) == []


def test_remove_unit_unlinks_a_link_itself_never_its_target(home: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.plist"
    outside.write_text("outside")
    (home / "units").mkdir()
    (home / "units" / "a.plist").symlink_to(outside)
    assert safe.remove_unit(home / "units" / "a.plist") is True
    assert outside.read_text() == "outside"
    assert safe.remove_unit(home / "units" / "a.plist") is False
    assert safe.remove_unit(home / "missing" / "a.plist") is False


def test_remove_unit_refuses_a_symlinked_ancestor(home: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    (outside / "LaunchAgents").mkdir(parents=True)
    (outside / "LaunchAgents" / "a.plist").write_text("outside")
    (home / "Library").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InstallError, match="symlinked path component"):
        safe.remove_unit(home / "Library" / "LaunchAgents" / "a.plist")
    assert (outside / "LaunchAgents" / "a.plist").read_text() == "outside"


def test_a_missing_home_is_absent_for_reads_and_refused_for_writes(tmp_path: Path) -> None:
    home = tmp_path / "missing-home"
    unit = home / "Library" / "LaunchAgents" / "a.plist"
    assert safe.load_unit(unit, home=home) is None
    assert safe.remove_unit(unit, home=home) is False
    safe.check_unit_dir(unit, home=home)
    with pytest.raises(InstallError, match="missing"):
        safe.install_unit(unit, b"x", mode=0o600, home=home)
    assert not home.exists()


def test_check_unit_dir_refuses_a_symlinked_home_but_not_a_symlinked_unit(home: Path, tmp_path: Path) -> None:
    """Callers check the directory before unloading a service; a link at the unit name is still removable."""
    outside = tmp_path / "outside"
    (outside / "units").mkdir(parents=True)
    linked_home = tmp_path / "linked-home"
    linked_home.symlink_to(outside, target_is_directory=True)
    with pytest.raises(InstallError, match="symlinked path component"):
        safe.check_unit_dir(linked_home / "units" / "a.plist", home=linked_home)
    (home / "units").mkdir()
    (home / "units" / "a.plist").symlink_to(outside / "units")
    safe.check_unit_dir(home / "units" / "a.plist")
    safe.check_unit_dir(home / "missing" / "a.plist")


def test_state_dirs_create_private_ancestors_and_chmod_only_requested_dirs(home: Path) -> None:
    runtime = home / ".codex" / "job"
    safe.ensure_state_dirs(runtime / "logs", runtime / "receipts" / "v2", home=home)
    for path in (home / ".codex", runtime, runtime / "logs", runtime / "receipts", runtime / "receipts" / "v2"):
        assert path.stat().st_mode & 0o777 == 0o700
    runtime.chmod(0o755)
    (runtime / "logs").chmod(0o755)
    safe.ensure_state_dirs(runtime / "logs", home=home)
    assert runtime.stat().st_mode & 0o777 == 0o755
    assert (runtime / "logs").stat().st_mode & 0o777 == 0o700


def test_state_preflight_refuses_later_sibling_before_any_creation(home: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (home / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InstallError, match="symlinked"):
        safe.ensure_state_dirs(home / "missing", home / "linked" / "state", home=home)
    assert not (home / "missing").exists()
    assert list(outside.iterdir()) == []


def test_state_creation_refuses_link_swapped_in_after_validation(
    home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    outside.chmod(0o755)
    directory = home / "logs"
    real_check = safe.check_state_paths

    def swap_after_check(*args, **kwargs):
        real_check(*args, **kwargs)
        directory.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(safe, "check_state_paths", swap_after_check)
    with pytest.raises(InstallError, match="symlinked"):
        safe.ensure_state_dirs(directory, home=home)
    assert list(outside.iterdir()) == []
    assert outside.stat().st_mode & 0o777 == 0o755


def test_state_chmod_uses_open_descriptor_after_directory_swap(
    home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = home / "logs"
    directory.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    outside.chmod(0o755)
    real_chmod = safe.os.fchmod

    def swap_before_chmod(fd, mode):
        directory.rename(home / "held")
        directory.symlink_to(outside, target_is_directory=True)
        real_chmod(fd, mode)

    monkeypatch.setattr(safe.os, "fchmod", swap_before_chmod)
    safe.ensure_state_dirs(directory, home=home)
    assert (home / "held").stat().st_mode & 0o777 == 0o700
    assert outside.stat().st_mode & 0o777 == 0o755
    assert list(outside.iterdir()) == []


def test_state_log_append_creates_private_file_and_refuses_special_file(home: Path) -> None:
    log = home / "state" / "job.log"
    for content in (b"one\n", b"two\n"):
        with os.fdopen(safe.open_state_log(log, home=home), "ab") as handle:
            handle.write(content)
    assert log.read_bytes() == b"one\ntwo\n"
    assert log.stat().st_mode & 0o777 == 0o600
    fifo = log.with_name("fifo")
    os.mkfifo(fifo)
    with pytest.raises(InstallError, match="non-regular"):
        safe.open_state_log(fifo, home=home)


def test_state_log_open_refuses_link_raced_in_after_preflight(
    home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = home / "logs" / "api.log"
    log.parent.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"untouched")
    real_open = safe.os.open

    def swap_before_open(name, flags, *args, **kwargs):
        if name == log.name:
            log.symlink_to(outside)
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(safe.os, "open", swap_before_open)
    with pytest.raises((InstallError, OSError)):
        safe.open_state_log(log, home=home)
    assert outside.read_bytes() == b"untouched"


def test_state_creation_refuses_missing_home_without_creating_it(tmp_path: Path) -> None:
    home = tmp_path / "missing-home"
    with pytest.raises(InstallError, match="missing"):
        safe.ensure_state_dirs(home / ".codex" / "logs", home=home)
    assert not home.exists()
