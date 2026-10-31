"""Reader defaults resolve current inputs and never consume a worktree store."""

import importlib

import pytest

from scripts.storage import topology as t


def test_config_and_verification_import_do_not_resolve(monkeypatch):
    from scripts.rag import config
    from scripts.verification import vesum

    def forbidden(*args, **kwargs):
        pytest.fail("module import resolved a store")
    monkeypatch.setattr(t, "resolve_store", forbidden)
    importlib.reload(config)
    importlib.reload(vesum)


def test_connection_owner_uses_current_override_and_path_free_refusal(tmp_path, monkeypatch):
    from scripts.atlas import teacher_vesum_attest as reader

    monkeypatch.setattr(t, "_store_locality", lambda path: "local")
    first, second = tmp_path / "first.db", tmp_path / "second.db"
    first.touch()
    second.touch()
    monkeypatch.setenv(t.ENV_VESUM_DB, str(first))
    assert reader._store_path("vesum") == first
    monkeypatch.setenv(t.ENV_VESUM_DB, str(second))
    assert reader._store_path("vesum") == second
    monkeypatch.setenv(t.ENV_VESUM_DB, "file:/private/store")
    with pytest.raises(FileNotFoundError, match=r"^uri_override$"):
        reader._open_read_only(None)


def test_explicit_worktree_link_never_becomes_a_read_binding(tmp_path, monkeypatch):
    primary = tmp_path / "primary"
    (primary / ".git" / "worktrees" / "worker").mkdir(parents=True)
    (primary / "data").mkdir()
    db = primary / "data" / "vesum.db"
    db.touch()
    worker = tmp_path / "worker"
    (worker / "data").mkdir(parents=True)
    (worker / ".git").write_text(f"gitdir: {primary}/.git/worktrees/worker\n")
    (worker / "data" / "vesum.db").symlink_to(db)
    monkeypatch.setattr(t, "_store_locality", lambda path: "local")
    assert t.resolve_store("vesum", worker, binding=t.StoreBinding("vesum", db), env={}) == t.StoreRefusal("vesum", "worktree_local_store")


def test_esum_derived_lookup_uses_current_override_and_replacement(tmp_path, monkeypatch):
    import sqlite3

    from scripts.ingest import esum_ingest as reader

    monkeypatch.setattr(t, "_store_locality", lambda path: "local")
    first, second, replacement = (tmp_path / name for name in ("first.db", "second.db", "replacement.db"))
    for path, lemma in ((first, "first"), (second, "second"), (replacement, "replacement")):
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE forms(lemma TEXT)")
            connection.execute("INSERT INTO forms VALUES (?)", (lemma,))
    try:
        monkeypatch.setenv(t.ENV_VESUM_DB, str(first))
        assert reader._vesum_has_lemma("first") is True
        monkeypatch.setenv(t.ENV_VESUM_DB, str(second))
        assert reader._vesum_has_lemma("first") is False
        assert reader._vesum_has_lemma("second") is True
        replacement.replace(second)
        assert reader._vesum_has_lemma("second") is False
        assert reader._vesum_has_lemma("replacement") is True
    finally:
        if reader._VESUM_CONN is not None:
            reader._VESUM_CONN.close()
        reader._VESUM_CONN = None
        reader._VESUM_LEMMAS = None


def test_practice_verifier_resolves_default_at_connection_time(tmp_path, monkeypatch):
    import sqlite3

    from scripts.audit.generate_practice_deck import RealVesumVerifier

    monkeypatch.setattr(t, "_store_locality", lambda path: "local")
    verifier = RealVesumVerifier()
    for name in ("first", "second"):
        path = tmp_path / f"{name}.db"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE forms(word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
            connection.execute("INSERT INTO forms VALUES (?, ?, 'noun', 'fixture')", (name, name))
        monkeypatch.setenv(t.ENV_VESUM_DB, str(path))
        assert verifier.verify_words(["first", "second"]) == {
            "first": [{"lemma": "first", "pos": "noun", "tags": "fixture"}] if name == "first" else [],
            "second": [{"lemma": "second", "pos": "noun", "tags": "fixture"}] if name == "second" else [],
        }


def test_config_reload_replaces_a_stale_legacy_attribute_with_current_resolution(tmp_path, monkeypatch):
    from scripts.rag import config

    current = tmp_path / "current.db"
    current.touch()
    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(config, "VESUM_DB_PATH", tmp_path / "stale.db")
            scoped.setattr(t, "_store_locality", lambda path: "local")
            scoped.setenv(t.ENV_VESUM_DB, str(current))
            importlib.reload(config)
            assert current == config.VESUM_DB_PATH
    finally:
        importlib.reload(config)
