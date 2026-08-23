"""Tests for /tmp usability probe canary (#7164)."""

from __future__ import annotations

import errno
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.audit import check_tmp_usability as ctu


def test_classify_os_error() -> None:
    edquot = getattr(errno, "EDQUOT", None)
    if edquot is not None:
        assert ctu._classify_os_error(OSError(edquot, "Disk quota exceeded")) == "edquot"
    assert ctu._classify_os_error(OSError(errno.ENOSPC, "No space left on device")) == "enospc"
    assert ctu._classify_os_error(OSError(errno.EACCES, "Permission denied")) == f"oserror-{errno.EACCES}"
    assert ctu._classify_os_error(OSError(errno.EIO, "Input/output error")) == f"oserror-{errno.EIO}"


def test_probe_tmp_usability_healthy(tmp_path: Path) -> None:
    res = ctu.probe_tmp_usability(tmp_path)
    assert res["ok"] is True
    assert res["writable"] is True
    assert res["error"] is None
    assert isinstance(res["used_pct"], (int, float))
    assert isinstance(res["free_bytes"], int)
    assert res["free_bytes"] > 0
    # Probe file must be deleted cleanly
    assert not list(tmp_path.glob(".lu-tmp-probe-*"))


def test_probe_tmp_usability_default_path() -> None:
    res = ctu.probe_tmp_usability()
    assert isinstance(res["ok"], bool)
    assert isinstance(res["writable"], bool)
    assert "error" in res
    assert "used_pct" in res
    assert "free_bytes" in res
    # Opsec: ensure no absolute path leaks in result string
    for val in res.values():
        if isinstance(val, str):
            assert not val.startswith("/")


def test_probe_tmp_usability_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    res = ctu.probe_tmp_usability(missing)
    assert res["ok"] is False
    assert res["writable"] is False
    assert res["error"] == f"oserror-{errno.ENOENT}"


def test_probe_tmp_usability_simulated_edquot_on_write(tmp_path: Path) -> None:
    edquot_errno = getattr(errno, "EDQUOT", 122)

    def fake_write(fd, data):
        raise OSError(edquot_errno, "Disk quota exceeded")

    with patch.object(os, "write", side_effect=fake_write):
        res = ctu.probe_tmp_usability(tmp_path)
        assert res["ok"] is False
        assert res["writable"] is False
        assert res["error"] == "edquot"
        assert not list(tmp_path.glob(".lu-tmp-probe-*"))


def test_probe_tmp_usability_simulated_enospc_on_mkstemp(tmp_path: Path) -> None:
    def fake_mkstemp(*args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    with patch.object(tempfile, "mkstemp", side_effect=fake_mkstemp):
        res = ctu.probe_tmp_usability(tmp_path)
        assert res["ok"] is False
        assert res["writable"] is False
        assert res["error"] == "enospc"


def test_probe_tmp_usability_simulated_disk_usage_error(tmp_path: Path) -> None:
    def fake_disk_usage(path):
        raise OSError(errno.EACCES, "Permission denied")

    with patch.object(shutil, "disk_usage", side_effect=fake_disk_usage):
        res = ctu.probe_tmp_usability(tmp_path)
        assert res["ok"] is False
        assert res["writable"] is False
        assert res["error"] == f"oserror-{errno.EACCES}"
