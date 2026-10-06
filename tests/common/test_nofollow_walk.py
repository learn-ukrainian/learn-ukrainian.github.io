"""One directory component is opened without following a symlink (#9889)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from scripts.common.nofollow_walk import ComponentOpenError, open_directory_component, open_leaf_descriptor


def _fd_count() -> int:
    return len(os.listdir("/proc/self/fd"))


def test_nested_components_open_relative_to_the_parent(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"
    target.mkdir(parents=True)
    root = open_directory_component(None, os.fspath(tmp_path))
    try:
        child = open_directory_component(root, "a")
        try:
            leaf = open_directory_component(child, "b")
            try:
                assert os.path.samestat(os.fstat(leaf), target.stat())
            finally:
                os.close(leaf)
        finally:
            os.close(child)
    finally:
        os.close(root)


def test_symlink_component_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    root = open_directory_component(None, os.fspath(tmp_path))
    try:
        with pytest.raises(ComponentOpenError) as caught:
            open_directory_component(root, "link")
        assert caught.value.kind == "symlinked"
    finally:
        os.close(root)
    assert outside.is_dir()


def test_non_directory_component_is_refused(tmp_path: Path) -> None:
    (tmp_path / "file").write_text("x")
    root = open_directory_component(None, os.fspath(tmp_path))
    try:
        with pytest.raises(ComponentOpenError) as caught:
            open_directory_component(root, "file")
        assert caught.value.kind == "non-directory"
    finally:
        os.close(root)


def test_component_replaced_before_open_is_refused_and_closes_the_fd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "real").mkdir()

    class FakeStat:
        st_dev = -1
        st_ino = -1
        st_mode = stat.S_IFDIR

    monkeypatch.setattr(os, "fstat", lambda _fd: FakeStat())
    before = _fd_count()
    with pytest.raises(ComponentOpenError) as caught:
        open_directory_component(None, os.fspath(tmp_path / "real"))
    assert caught.value.kind == "changed"
    assert _fd_count() == before


def test_leaf_descriptor_type_is_fstat_of_the_opened_file(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"payload")
    note = tmp_path / "note"
    note.write_bytes(b"symlink\nnot-a-link")
    link = tmp_path / "link"
    link.symlink_to("target")
    dangling = tmp_path / "dangling"
    dangling.symlink_to("missing")
    directory = tmp_path / "outside"
    directory.mkdir()
    (directory / "secret").write_text("hidden")
    directory_link = tmp_path / "dir-link"
    directory_link.symlink_to(directory, target_is_directory=True)
    root = open_directory_component(None, os.fspath(tmp_path))
    try:
        note_fd, note_info = open_leaf_descriptor(root, "note")
        try:
            assert stat.S_ISREG(note_info.st_mode)
            assert os.path.samestat(note_info, note.stat())
        finally:
            os.close(note_fd)
        link_fd, link_info = open_leaf_descriptor(root, "link")
        try:
            assert stat.S_ISLNK(link_info.st_mode)
            assert os.path.samestat(link_info, link.lstat())
            assert not os.path.samestat(link_info, target.stat())
            assert os.readlink("", dir_fd=link_fd) == "target"
        finally:
            os.close(link_fd)
        dangling_fd, dangling_info = open_leaf_descriptor(root, "dangling")
        try:
            assert stat.S_ISLNK(dangling_info.st_mode)
            assert os.readlink("", dir_fd=dangling_fd) == "missing"
        finally:
            os.close(dangling_fd)
        dir_fd, dir_info = open_leaf_descriptor(root, "dir-link")
        try:
            assert stat.S_ISLNK(dir_info.st_mode)
            assert not stat.S_ISDIR(dir_info.st_mode)
            assert os.readlink("", dir_fd=dir_fd) == os.readlink(directory_link)
        finally:
            os.close(dir_fd)
    finally:
        os.close(root)
    assert (directory / "secret").read_text() == "hidden"


def test_leaf_fstat_failure_closes_the_fd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "note").write_text("x")
    root = open_directory_component(None, os.fspath(tmp_path))
    try:
        def boom(_fd: int) -> os.stat_result:
            raise OSError("fstat failed")

        monkeypatch.setattr(os, "fstat", boom)
        before = _fd_count()
        with pytest.raises(OSError, match="fstat failed"):
            open_leaf_descriptor(root, "note")
        assert _fd_count() == before
    finally:
        os.close(root)
