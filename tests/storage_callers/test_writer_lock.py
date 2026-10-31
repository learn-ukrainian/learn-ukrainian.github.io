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


def test_request_freezes_environment_before_acquisition(stores, tmp_path, monkeypatch):
    request = t._prepare_store_write_target("sources", stores, intent="update", env={})
    other = tmp_path / "other.db"
    other.touch()
    monkeypatch.setenv(t.ENV_SOURCES_DB, str(other))
    with g.store_writer(request.location):
        result = t.resolve_store_for_write("sources", stores, intent="update", target=request)
    assert isinstance(result, t.WriteStoreBinding)
    assert result.path == stores / "data" / "sources.db"
