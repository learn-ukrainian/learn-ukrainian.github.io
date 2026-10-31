"""Writer boundary rejects unsafe locations before any caller can mutate them."""

from pathlib import Path

import pytest

from scripts.storage import topology as t


@pytest.fixture
def stores(tmp_path, monkeypatch):
    root = tmp_path / "primary"
    (root / ".git" / "worktrees" / "worker").mkdir(parents=True)
    (root / "data").mkdir()
    for name in ("sources", "vesum"):
        (root / "data" / f"{name}.db").touch()
    monkeypatch.setattr(t, "_store_locality", lambda path: "local")
    monkeypatch.setattr(t, "live_store_path", lambda: root / "data" / "sources.db")
    return root


def test_active_creation_never_bootstraps_either_store(stores):
    for store in ("sources", "vesum"):
        result = t.resolve_store_for_write(store, stores, intent="create", env={})
        assert result == t.StoreRefusal(store, f"active_{store}_create_forbidden")


@pytest.mark.parametrize("store,operation,reason", [
    ("sources", "replace", "sources_replace_forbidden"),
    ("lexdata", "sqlite", "unsupported_write_store"),
])
def test_store_operation_admission_precedes_filesystem(store, operation, reason, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("refused store accessed the filesystem")
    monkeypatch.setattr(t, "default_repository_root", forbidden)
    result = t.resolve_store_for_write(store, intent="update", operation=operation)
    assert result == t.StoreRefusal(store, reason)


@pytest.mark.parametrize("raw,reason", [
    ("", "empty_override"), ("file:/private/db", "uri_override"),
    ("relative.db", "relative_override"),
])
def test_invalid_override_never_falls_back(stores, raw, reason):
    assert t.resolve_store_for_write("vesum", stores, intent="update", env={t.ENV_VESUM_DB: raw}) == t.StoreRefusal("vesum", reason)


@pytest.mark.parametrize("locality", ["network", "unknown"])
def test_locality_refusal_has_no_path(stores, monkeypatch, locality):
    monkeypatch.setattr(t, "_store_locality", lambda path: locality)
    result = t.resolve_store_for_write("vesum", stores, intent="update", env={})
    assert result == t.StoreRefusal("vesum", "locality_" + locality)
    assert str(stores) not in repr(result)


@pytest.mark.parametrize("role", ["active", "staging", "shadow"])
def test_absent_worktree_slot_cannot_be_created(stores, tmp_path, role):
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / ".git").write_text(f"gitdir: {stores}/.git/worktrees/worker\n")
    (worker / "data").mkdir()
    target = t.ExplicitStoreWriteTarget(worker / "data" / "sources.db", role)
    result = t.resolve_store_for_write("sources", worker, intent="create", target=target, env={})
    assert result == t.StoreRefusal("sources", "worktree_local_store")
    assert not Path(target.location).exists()


def test_staging_aliases_live_store_by_inode_or_symlink(stores, tmp_path):
    live = stores / "data" / "vesum.db"
    for name, make in (("hard.db", lambda p: p.hardlink_to(live)), ("link.db", lambda p: p.symlink_to(live))):
        alias = tmp_path / name
        make(alias)
        result = t.resolve_store_for_write("vesum", stores, intent="create", target=t.ExplicitStoreWriteTarget(alias, "staging"), env={})
        assert result == t.StoreRefusal("vesum", "target_is_active_store")


@pytest.mark.parametrize("configured", ["primary", "configured", "generation"])
@pytest.mark.parametrize("role", ["staging", "shadow"])
@pytest.mark.parametrize("intent", ["update", "create"])
def test_output_hardlink_to_historical_sources_generation_is_refused(stores, tmp_path, configured, role, intent):
    """A differently named inode alias must not mutate a non-selected generation."""
    data = stores / "data" if configured == "primary" else tmp_path / "configured"
    data.mkdir(exist_ok=True)
    directory = data / t.GENERATIONS_DIRNAME
    directory.mkdir()
    selected = directory / "sources.20261031T010000Z-111111111111.db"
    selected.write_bytes(b"selected fixture")
    historical = directory / "sources.20261031T000000Z-222222222222.db"
    historical.write_bytes(b"historical fixture")
    selector = data / "sources.db"
    if configured == "primary":
        selector.unlink()
    selector.symlink_to(selected.relative_to(data))
    alias = tmp_path / "output.db"
    alias.hardlink_to(historical)
    environment = {} if configured == "primary" else {
        t.ENV_SOURCES_DB: str(selected if configured == "generation" else selector),
    }

    result = t.resolve_store_for_write(
        "sources", stores, intent=intent,
        target=t.ExplicitStoreWriteTarget(alias, role), env=environment,
    )

    assert result == t.StoreRefusal("sources", "target_is_active_store")
    assert historical.read_bytes() == b"historical fixture"
    assert selected.read_bytes() == b"selected fixture"


def test_write_alias_refused_when_primary_selector_resolves_outside_generations_dir(stores, tmp_path):
    directory = stores / "data" / t.GENERATIONS_DIRNAME
    directory.mkdir()
    historical = directory / "sources.20261031T000000Z-222222222222.db"
    historical.write_bytes(b"historical fixture")
    selected = tmp_path / "sources.20261031T010000Z-111111111111.db"
    selected.write_bytes(b"selected fixture")
    selector = stores / "data" / "sources.db"
    selector.unlink()
    selector.symlink_to(selected)
    alias = tmp_path / "output.db"
    alias.hardlink_to(historical)

    assert t.inspect_selector(selector).reason == "selector_target_outside_generations"
    for role in ("staging", "shadow"):
        for intent in ("update", "create"):
            result = t.resolve_store_for_write(
                "sources", stores, intent=intent,
                target=t.ExplicitStoreWriteTarget(alias, role), env={},
            )
            assert result == t.StoreRefusal("sources", "target_is_active_store")
    assert historical.read_bytes() == b"historical fixture"
    assert selected.read_bytes() == b"selected fixture"


def test_shadow_replacement_is_distinct_from_staging(stores, tmp_path):
    path = tmp_path / "shadow.db"
    target = t.ExplicitStoreWriteTarget(path, "shadow")
    result = t.resolve_store_for_write("vesum", stores, intent="create", operation="replace", target=target, env={})
    assert isinstance(result, t.WriteStoreBinding)
    assert result.path == path and result.sqlite_uri is None
    assert not path.exists()
    assert t.resolve_store_for_write("vesum", stores, intent="create", operation="replace", target=t.ExplicitStoreWriteTarget(path, "staging"), env={}) == t.StoreRefusal("vesum", "invalid_target")


@pytest.mark.parametrize("name", ["a%b.db", "a?b.db", "a#b.db", "a b.db", "словник.db"])
def test_sqlite_uri_encodes_filename_without_query_injection(stores, tmp_path, name):
    import sqlite3

    from scripts.lib.readonly_sqlite import open_readonly

    path = tmp_path / name
    result = t.resolve_store_for_write("vesum", stores, intent="create", target=t.ExplicitStoreWriteTarget(path, "staging"), env={})
    assert isinstance(result, t.WriteStoreBinding)
    assert result.sqlite_uri == path.as_uri() + "?mode=rwc"
    conn = sqlite3.connect(result.sqlite_uri, uri=True)
    try:
        conn.execute("CREATE TABLE proof(value TEXT)")
        conn.execute("INSERT INTO proof VALUES ('preserved')")
        conn.commit()
    finally:
        conn.close()
    with open_readonly(path) as reader:
        assert reader.execute("SELECT value FROM proof").fetchone()[0] == "preserved"


def test_placeholder_and_read_bindings_never_become_write_targets(stores):
    assert t.resolve_store_for_write("vesum", stores, intent="update", target=t.StoreBinding("vesum", stores / "data" / "vesum.db"), env={}) == t.StoreRefusal("vesum", "invalid_binding")
    assert t.resolve_store_for_write("vesum", stores, intent="update", target=t.ExplicitStoreWriteTarget(t.unavailable_store_path("vesum")), env={}) == t.StoreRefusal("vesum", "store_missing")
