"""Compatibility access never falls back to a worktree-local VESUM store."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from scripts.rag import config
from scripts.storage import topology


@pytest.fixture(autouse=True)
def fresh_configuration():
    importlib.reload(config)
    yield
    importlib.reload(config)


@pytest.fixture
def roots(tmp_path: Path, monkeypatch):
    primary = tmp_path / "primary"
    (primary / ".git" / "worktrees" / "worker").mkdir(parents=True)
    (primary / "data").mkdir()
    worker = tmp_path / "worker"
    (worker / "data").mkdir(parents=True)
    (worker / ".git").write_text(f"gitdir: {primary}/.git/worktrees/worker\n")
    monkeypatch.setattr(config, "PROJECT_ROOT", worker)
    monkeypatch.setattr(topology, "_store_locality", lambda path: "local")
    monkeypatch.delenv(topology.ENV_VESUM_DB, raising=False)
    return primary, worker


def test_returns_default_when_it_already_exists(roots):
    primary, worker = roots
    (primary / "data" / "vesum.db").touch()
    local = worker / "data" / "vesum.db"
    local.touch()
    assert topology.unavailable_store_path("vesum") == config.VESUM_DB_PATH
    assert local != config.VESUM_DB_PATH


def test_missing_default_uses_primary_checkout_copy(roots):
    primary, worker = roots
    db = primary / "data" / "vesum.db"
    db.touch()
    assert db == config.VESUM_DB_PATH
    assert not (worker / "data" / "vesum.db").exists()


def test_falls_back_to_default_when_primary_copy_also_missing(roots):
    primary, worker = roots
    placeholder = topology.unavailable_store_path("vesum")
    assert placeholder == config.VESUM_DB_PATH
    assert not placeholder.parent.exists()
    assert not (primary / "data" / "vesum.db").exists()
    assert not (worker / "data" / "vesum.db").exists()


def test_falls_back_to_default_outside_a_git_repository(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv(topology.ENV_VESUM_DB, raising=False)
    assert topology.unavailable_store_path("vesum") == config.VESUM_DB_PATH
    assert not topology.unavailable_store_path("vesum").parent.exists()
    assert not (tmp_path / "data").exists()


def test_override_refreshes_at_each_access_and_invalid_never_falls_back(roots, tmp_path, monkeypatch):
    primary, _worker = roots
    (primary / "data" / "vesum.db").touch()
    first, second = tmp_path / "first.db", tmp_path / "second.db"
    first.touch()
    second.touch()
    monkeypatch.setenv(topology.ENV_VESUM_DB, str(first))
    assert first == config.VESUM_DB_PATH
    monkeypatch.setenv(topology.ENV_VESUM_DB, str(second))
    assert second == config.VESUM_DB_PATH
    monkeypatch.setenv(topology.ENV_VESUM_DB, "relative.db")
    assert topology.unavailable_store_path("vesum") == config.VESUM_DB_PATH


def test_import_resolves_nothing_and_from_import_survives_no_store(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("import resolved a store")
    with monkeypatch.context() as scoped:
        scoped.setattr(topology, "resolve_store", forbidden)
        importlib.reload(config)
    monkeypatch.setenv(topology.ENV_VESUM_DB, "invalid-relative.db")
    from scripts.rag.config import VESUM_DB_PATH
    assert topology.unavailable_store_path("vesum") == VESUM_DB_PATH
