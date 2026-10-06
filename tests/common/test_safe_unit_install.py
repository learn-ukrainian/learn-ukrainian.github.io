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
