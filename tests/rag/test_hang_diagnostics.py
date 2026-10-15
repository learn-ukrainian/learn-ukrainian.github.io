"""Dump-directory resolution, SIGUSR1 stack dump and writer-side retention (#10674)."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.rag import hang_diagnostics as hd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_resolve_dump_dir_default_and_override(tmp_path: Path) -> None:
    assert hd.resolve_dump_dir(tmp_path, {}) == tmp_path / "batch_state" / "sources-dumps"
    assert hd.resolve_dump_dir(tmp_path, {hd.DUMP_DIR_ENV: str(tmp_path / "x")}) == tmp_path / "x"


def test_prune_keeps_newest_slow_calls_and_drops_dead_pid_logs(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    proc_root = tmp_path / "proc"
    (proc_root / "77").mkdir(parents=True)
    (dump_dir / "faulthandler-77.log").write_text("", encoding="utf-8")
    (dump_dir / "faulthandler-78.log").write_text("", encoding="utf-8")
    for stamp in ("20261015T010000Z", "20261015T020000Z", "20261015T030000Z"):
        (dump_dir / f"slow-call-{stamp}-pid77.txt").write_text("", encoding="utf-8")
    hd.prune_dump_dir(dump_dir, keep=2, proc_root=proc_root)
    assert sorted(path.name for path in dump_dir.iterdir()) == [
        "faulthandler-77.log",
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
    (tmp_path / "faulthandler-notapid.log").write_text("keep", encoding="utf-8")
    assert hd.prune_dump_dir(tmp_path, keep=0, max_bytes=0) == []


INSTALL_CHILD = textwrap.dedent(
    """\
    import sys, time
    from pathlib import Path
    sys.path.insert(0, sys.argv[2])
    from scripts.rag.hang_diagnostics import install_signal_dump

    print(install_signal_dump(Path(sys.argv[1])), flush=True)
    time.sleep(60)
    """
)


def test_install_signal_dump_prunes_dead_pid_logs(tmp_path: Path) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    (dump_dir / "faulthandler-4194999.log").write_text("old", encoding="utf-8")
    child = subprocess.Popen(
        [sys.executable, "-c", INSTALL_CHILD, str(dump_dir), str(PROJECT_ROOT)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        log = Path(child.stdout.readline().strip())
        assert log.name == f"faulthandler-{child.pid}.log"
        assert oct(log.stat().st_mode & 0o777) == "0o600"
        assert not (dump_dir / "faulthandler-4194999.log").exists()
    finally:
        child.kill()
        child.wait(timeout=10)


def test_install_signal_dump_truncates_a_reused_pid_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    stale = hd.faulthandler_log_path(dump_dir, os.getpid())
    stale.write_text("x" * 1000, encoding="utf-8")
    monkeypatch.setattr(hd.faulthandler, "register", lambda *_a, **_k: None)
    monkeypatch.setattr(hd.faulthandler, "enable", lambda *_a, **_k: None)
    monkeypatch.setattr(hd, "_DUMP_FILE", None)
    try:
        assert hd.install_signal_dump(dump_dir) == stale
        assert stale.stat().st_size == 0
    finally:
        if hd._DUMP_FILE is not None:
            hd._DUMP_FILE.close()
