"""Dump-directory resolution and writer-side retention (#10674)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.rag import hang_diagnostics as hd


def test_resolve_dump_dir_default_and_override(tmp_path: Path) -> None:
    assert hd.resolve_dump_dir(tmp_path, {}) == tmp_path / "batch_state" / "sources-dumps"
    assert hd.resolve_dump_dir(tmp_path, {hd.DUMP_DIR_ENV: str(tmp_path / "x")}) == tmp_path / "x"


def test_prune_keeps_the_newest_slow_calls(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    for stamp in ("20261015T010000Z", "20261015T020000Z", "20261015T030000Z"):
        (dump_dir / f"slow-call-{stamp}-pid77.txt").write_text("", encoding="utf-8")
    hd.prune_dump_dir(dump_dir, keep=2)
    assert sorted(path.name for path in dump_dir.iterdir()) == [
        "slow-call-20261015T020000Z-pid77.txt",
        "slow-call-20261015T030000Z-pid77.txt",
    ]


def test_prune_bounds_total_bytes_and_always_keeps_the_newest(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    for stamp in ("20261015T010000Z", "20261015T020000Z", "20261015T030000Z"):
        (dump_dir / f"slow-call-{stamp}-pid1.txt").write_text("x" * 100, encoding="utf-8")
    removed = hd.prune_dump_dir(dump_dir, keep=10, max_bytes=250)
    assert [path.name for path in removed] == ["slow-call-20261015T010000Z-pid1.txt"]
    hd.prune_dump_dir(dump_dir, keep=10, max_bytes=1)
    assert [path.name for path in dump_dir.iterdir()] == ["slow-call-20261015T030000Z-pid1.txt"]


def test_prune_leaves_unrelated_files_alone(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "faulthandler-77.log").write_text("keep", encoding="utf-8")
    assert hd.prune_dump_dir(tmp_path, keep=0, max_bytes=0) == []


def test_ensure_dump_dir_is_owner_only(tmp_path: Path) -> None:
    dump_dir = hd.ensure_dump_dir(tmp_path / "a" / "dumps")
    assert oct(dump_dir.stat().st_mode & 0o777) == "0o700"


def _old_dump(dump_dir: Path, stamp: str = "20261015T010000Z") -> str:
    name = f"slow-call-{stamp}-pid1.txt"
    (dump_dir / name).write_text("old", encoding="utf-8")
    return name


def test_prune_deletes_inside_the_opened_directory_when_it_is_swapped_for_a_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The directory is renamed and replaced by a symlink between scan and unlink."""
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    name = _old_dump(dump_dir)
    _old_dump(dump_dir, "20261015T020000Z")
    (outside / name).write_text("precious", encoding="utf-8")
    real_unlink = os.unlink
    swapped: list[bool] = []

    def swap_then_unlink(*args: object, **kwargs: object) -> None:
        if not swapped:
            swapped.append(True)
            dump_dir.rename(tmp_path / "moved")
            dump_dir.symlink_to(outside, target_is_directory=True)
        real_unlink(*args, **kwargs)

    monkeypatch.setattr(hd.os, "unlink", swap_then_unlink)
    removed = hd.prune_dump_dir(dump_dir, keep=1)
    assert swapped
    assert [path.name for path in removed] == [name]
    assert (outside / name).read_text(encoding="utf-8") == "precious"
    assert not (tmp_path / "moved" / name).exists()


def test_prune_refuses_a_symlinked_dump_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    name = _old_dump(outside)
    link = tmp_path / "dumps"
    link.symlink_to(outside, target_is_directory=True)
    assert hd.prune_dump_dir(link, keep=0, max_bytes=0) == []
    assert (outside / name).exists()


def test_prune_refuses_a_directory_owned_by_someone_else(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    name = _old_dump(dump_dir)
    other_uid = os.getuid() + 1
    monkeypatch.setattr(hd.os, "getuid", lambda: other_uid)
    assert hd.prune_dump_dir(dump_dir, keep=0, max_bytes=0) == []
    assert (dump_dir / name).exists()


def test_prune_refuses_a_missing_or_non_directory_path(tmp_path: Path) -> None:
    (tmp_path / "file").write_text("x", encoding="utf-8")
    assert hd.prune_dump_dir(tmp_path / "file") == []
    assert hd.prune_dump_dir(tmp_path / "absent") == []


def test_prune_removes_a_symlink_candidate_but_never_its_target(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    target = tmp_path / "target.txt"
    target.write_text("precious", encoding="utf-8")
    (dump_dir / "slow-call-20261015T010000Z-pid1.txt").symlink_to(target)
    _old_dump(dump_dir, "20261015T020000Z")
    removed = hd.prune_dump_dir(dump_dir, keep=1)
    assert [path.name for path in removed] == ["slow-call-20261015T010000Z-pid1.txt"]
    assert target.read_text(encoding="utf-8") == "precious"
