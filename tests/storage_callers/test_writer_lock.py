"""No live Sources binding may escape lock or exact-selector checks."""

import pytest

from scripts.storage import generations as g
from scripts.storage import topology as t
from tests.storage_callers.test_write_contract import stores as store_fixture

stores = store_fixture


def test_live_binding_requires_lock_and_expires_on_release(stores):
    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    assert isinstance(request, t.ExplicitStoreWriteTarget)
    assert t.resolve_store_for_write("sources", stores, intent="update", target=request) == t.StoreRefusal("sources", "writer_lock_not_held")
    with g.store_writer(request.location):
        binding = t.resolve_store_for_write("sources", stores, intent="update", target=request)
        assert isinstance(binding, t.WriteStoreBinding)
        assert binding.path == stores / "data" / "sources.db"
        with pytest.raises(g.GenerationError, match="writer_lock_busy"):
            with g.store_writer(request.location):
                pass
    assert t.resolve_store_for_write("sources", stores, intent="update", target=request) == t.StoreRefusal("sources", "writer_lock_not_held")


def test_primary_classification_error_cannot_issue_lockless_binding(stores, monkeypatch):
    monkeypatch.setattr(t, "store_kind", lambda path: t.StoreRef("other"))
    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    with g.store_writer(request.location):
        result = t.resolve_store_for_write("sources", stores, intent="update", target=request)
    assert result == t.StoreRefusal("sources", "store_unavailable")


def test_selector_locality_is_checked_before_writer_lock_can_lift_it(stores, monkeypatch):
    directory = stores / "data" / t.GENERATIONS_DIRNAME
    directory.mkdir()
    generation = directory / "sources.20261031T000000Z-111111111111.db"
    generation.touch()
    selector = stores / "data" / t.SELECTOR_NAME
    selector.unlink()
    selector.symlink_to(generation.relative_to(selector.parent))
    monkeypatch.setattr(t, "_store_locality", lambda path: "network" if path == selector else "local")
    assert t._prepare_store_write_target("sources", stores, intent="update", env={}) == t.StoreRefusal("sources", "locality_network")
    assert not (stores / "data" / g.WRITER_LOCK_NAME).exists()


def test_request_freezes_environment_before_acquisition(stores, tmp_path, monkeypatch):
    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    other = tmp_path / "other.db"
    other.touch()
    monkeypatch.setenv(t.ENV_SOURCES_DB, str(other))
    with g.store_writer(request.location):
        result = t.resolve_store_for_write("sources", stores, intent="update", target=request)
    assert isinstance(result, t.WriteStoreBinding)
    assert result.path == stores / "data" / "sources.db"


def test_registered_holder_must_name_the_same_frozen_selector(stores):
    from scripts.lib.readonly_sqlite import register_store_writer, unregister_store_writer

    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    other = stores / "data" / "different.db"
    register_store_writer(other)
    try:
        assert t.resolve_store_for_write("sources", stores, intent="update", target=request) == t.StoreRefusal("sources", "not_selected_generation")
    finally:
        unregister_store_writer(other)


def test_selection_is_resolved_after_acquisition(stores):
    directory = stores / "data" / t.GENERATIONS_DIRNAME
    directory.mkdir()
    first = directory / "sources.20261031T000000Z-111111111111.db"
    second = directory / "sources.20261031T000001Z-222222222222.db"
    first.touch()
    second.touch()
    selector = stores / "data" / t.SELECTOR_NAME
    selector.unlink()
    selector.symlink_to(first.relative_to(selector.parent))
    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    selector.unlink()
    selector.symlink_to(second.relative_to(selector.parent))
    with g.store_writer(request.location):
        binding = t.resolve_store_for_write("sources", stores, intent="update", target=request)
        assert isinstance(binding, t.WriteStoreBinding)
        assert binding.path == second


def test_busy_lock_refuses_before_connection(stores):
    import fcntl

    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    with (stores / "data" / g.WRITER_LOCK_NAME).open("wb") as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(g.GenerationError, match="writer_lock_busy"):
            with g.store_writer(request.location):
                pytest.fail("busy lock was admitted")


def test_inherited_lock_is_reused_without_nested_acquisition(stores):
    import os
    import subprocess
    import sys

    from scripts.lib.readonly_sqlite import ENV_STORE_WRITER_FD, ENV_STORE_WRITER_SELECTOR

    directory = stores / "data" / t.GENERATIONS_DIRNAME
    directory.mkdir()
    generation = directory / "sources.20261031T000000Z-111111111111.db"
    generation.touch()
    selector = stores / "data" / t.SELECTOR_NAME
    selector.unlink()
    selector.symlink_to(generation.relative_to(selector.parent))
    program = '''
import sys
from pathlib import Path
from scripts.storage import topology as t, generations as g
path = Path(sys.argv[1])
request = t._prepare_store_write_target("sources", intent="update", target=t.ExplicitStoreWriteTarget(path))
assert isinstance(request, t.ExplicitStoreWriteTarget), request
with g.store_writer(request.location):
    binding = t.resolve_store_for_write("sources", intent="update", target=request)
    assert isinstance(binding, t.WriteStoreBinding), binding
    assert binding.path == path.resolve()
print("inherited binding verified")
'''
    with g.writer_lock(selector, lift=True) as held:
        run = subprocess.run([sys.executable, "-c", program, str(selector)], pass_fds=(held._fd,),
                             env={**os.environ, ENV_STORE_WRITER_FD: str(held._fd), ENV_STORE_WRITER_SELECTOR: str(selector)},
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stderr
        assert run.stdout == "inherited binding verified\n"
