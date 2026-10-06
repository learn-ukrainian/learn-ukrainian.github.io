"""One directory component is opened without following a symlink (#9889)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from scripts.common.nofollow_walk import ComponentOpenError, open_directory_component


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
