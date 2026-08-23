"""Tests for shared fleet scratch-root resolution (#7164)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.common import scratch


def test_resolve_scratch_root_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(scratch.SCRATCH_ROOT_ENV_VAR, raising=False)
    monkeypatch.setattr(scratch, "_is_usable_scratch_dir", lambda _p: True)
    assert scratch.resolve_scratch_root() == scratch.DEFAULT_SCRATCH_ROOT


def test_resolve_scratch_root_fallback_when_default_unusable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(scratch.SCRATCH_ROOT_ENV_VAR, raising=False)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(scratch, "_is_usable_scratch_dir", lambda _p: False)
    assert scratch.resolve_scratch_root() == tmp_path / scratch.FALLBACK_SCRATCH_DIRNAME


def test_resolve_scratch_root_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    override = tmp_path / "custom-scratch"
    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(override))
    assert scratch.resolve_scratch_root() == override


def test_resolve_scratch_root_blank_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, "   ")
    monkeypatch.setattr(scratch, "_is_usable_scratch_dir", lambda _p: True)
    assert scratch.resolve_scratch_root() == scratch.DEFAULT_SCRATCH_ROOT


def test_ensure_scratch_root_creates_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    override = tmp_path / "custom-scratch-dir"
    assert not override.exists()
    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(override))

    res = scratch.ensure_scratch_root()
    assert res == override
    assert override.is_dir()


def test_ensure_scratch_root_override_error_propagates(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    override = tmp_path / "custom-scratch-dir"
    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(override))

    with patch.object(Path, "mkdir", side_effect=PermissionError("read-only filesystem")):
        with pytest.raises(PermissionError, match="read-only filesystem"):
            scratch.ensure_scratch_root()


def test_ensure_scratch_root_fallback_when_default_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(scratch.SCRATCH_ROOT_ENV_VAR, raising=False)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

    original_mkdir = Path.mkdir

    def fake_mkdir(self, *args, **kwargs):
        if self == scratch.DEFAULT_SCRATCH_ROOT:
            raise PermissionError("no access to /var/tmp")
        return original_mkdir(self, *args, **kwargs)

    with patch.object(Path, "mkdir", side_effect=fake_mkdir, autospec=True):
        res = scratch.ensure_scratch_root()
        assert res == tmp_path / scratch.FALLBACK_SCRATCH_DIRNAME
        assert res.is_dir()


def test_make_scratch_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(tmp_path))
    sub = scratch.make_scratch_dir(prefix="lu-test-")
    assert sub.is_dir()
    assert sub.parent == tmp_path
    assert sub.name.startswith("lu-test-")


def test_scratch_scan_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    base_root = tmp_path / "base"
    base_root.mkdir()
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()

    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(scratch_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(base_root))
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(temp_dir))

    roots = scratch.scratch_scan_roots()
    assert scratch_root.resolve() in roots
    assert base_root.resolve() in roots
    assert temp_dir.resolve() in roots


def test_scratch_scan_roots_deduplicates_and_ignores_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    scratch_root = tmp_path / "shared"
    scratch_root.mkdir()
    missing_dir = tmp_path / "does_not_exist"

    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(scratch_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(missing_dir))
    monkeypatch.setattr(scratch, "DEFAULT_SCRATCH_ROOT", missing_dir)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(scratch_root))

    roots = scratch.scratch_scan_roots()
    assert len(roots) == 1
    assert roots[0] == scratch_root.resolve()


def test_fallback_scratch_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert scratch.fallback_scratch_root() == tmp_path / scratch.FALLBACK_SCRATCH_DIRNAME


def test_scratch_scan_roots_includes_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    fallback_root = tmp_path / "temp" / scratch.FALLBACK_SCRATCH_DIRNAME
    fallback_root.mkdir(parents=True)

    monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(scratch_root))
    monkeypatch.delenv("LU_RUNTIME_TMP_BASE_ROOT", raising=False)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path / "temp"))

    roots = scratch.scratch_scan_roots()
    assert scratch_root.resolve() in roots
    assert fallback_root.resolve() in roots
    assert (tmp_path / "temp").resolve() in roots
