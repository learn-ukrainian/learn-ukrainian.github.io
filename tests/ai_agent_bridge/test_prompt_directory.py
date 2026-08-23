"""Tests for _prompt_directory scratch allocation in _dispatch_wrappers (#7164)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ai_agent_bridge._dispatch_wrappers import _prompt_directory


def test_prompt_directory_uses_runtime_tmp_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lease_dir = tmp_path / "task-lease"
    lease_dir.mkdir()
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(lease_dir))

    with _prompt_directory() as directory:
        assert directory == lease_dir
        assert directory.is_dir()

    # Runtime tmp lease managed by caller / lease owner; not deleted on context manager exit
    assert lease_dir.is_dir()


def test_prompt_directory_raises_on_invalid_runtime_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing_dir = tmp_path / "missing-lease"
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(missing_dir))

    with pytest.raises(RuntimeError, match="runtime tmp lease is not a directory"):
        with _prompt_directory():
            pass


def test_prompt_directory_allocates_under_scratch_root_when_no_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))

    yielded_dir = None
    with _prompt_directory() as directory:
        yielded_dir = directory
        assert directory.is_dir()
        assert directory.parent.resolve() == scratch_root.resolve()
        assert directory.name.startswith("learn-ukrainian-bridge-")

    # Temporary directory must be self-cleaned upon exit
    assert yielded_dir is not None
    assert not yielded_dir.exists()


def test_agy_ask_scratch_cwd_allocates_under_scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ai_agent_bridge._agy import _agy_ask_scratch_cwd

    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))

    cwd = _agy_ask_scratch_cwd()
    assert cwd.is_dir()
    assert cwd.resolve() == (scratch_root / "learn-ukrainian-bridge-asks" / "agy").resolve()
