"""Fail-closed logical store bindings; all data is synthetic and local."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology as storage


@pytest.fixture
def checkouts(tmp_path, monkeypatch):
    primary = tmp_path / 'primary'
    worktree = tmp_path / 'worker'
    for root in (primary, worktree):
        (root / 'scripts').mkdir(parents=True)
        (root / 'data').mkdir()
    gitdir = primary / '.git' / 'worktrees' / 'worker'
    gitdir.mkdir(parents=True)
    (worktree / '.git').write_text(f'gitdir: {gitdir}\n')
    monkeypatch.setattr(storage, '_fs_type_for_path', lambda path: 'ext4')
    return primary, worktree


def make_db(path):
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('CREATE TABLE proof (value TEXT)')
        conn.execute("INSERT INTO proof VALUES ('intended')")
        conn.commit()
    return path


def refusal(result, reason):
    assert isinstance(result, storage.StoreRefusal)
    assert result.reason == reason
    assert not hasattr(result, 'path')


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('linked', [False, True])
def test_primary_store_success(checkouts, store, linked):
    primary, worker = checkouts
    db = make_db(primary / 'data' / f'{store}.db')
    result = storage.resolve_store(store, worker if linked else primary, env={})
    assert result == storage.StoreBinding(store, db, provenance='primary_checkout')
    assert result.access_mode == 'read'
    with closing(open_readonly(result.path)) as conn:
        assert conn.execute('SELECT value FROM proof').fetchone() == ('intended',)
        with pytest.raises(sqlite3.OperationalError):
            conn.execute('CREATE TABLE forbidden (x)')


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('value,reason', [('', 'empty_override'), ('  ', 'empty_override'),
    ('relative/sources.db', 'relative_override'), ('file:/sources.db?mode=ro', 'uri_override')])
def test_invalid_override_has_no_path(checkouts, store, value, reason):
    primary, worker = checkouts
    make_db(primary / 'data' / f'{store}.db')
    refusal(storage.resolve_store(store, worker, env={f'LU_{store.upper()}_DB': value}), reason)


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('directory', [False, True])
def test_missing_or_directory_override(checkouts, store, directory):
    primary, worker = checkouts
    path = primary / 'override'
    if directory:
        path.mkdir()
    refusal(storage.resolve_store(store, worker, env={f'LU_{store.upper()}_DB': str(path)}),
            'not_a_file' if directory else 'store_missing')
    assert not (primary / 'data' / f'{store}.db').exists()


@pytest.mark.parametrize('store', ['sources', 'vesum'])
def test_missing_primary_has_no_path(checkouts, store):
    _, worker = checkouts
    refusal(storage.resolve_store(store, worker, env={}), 'store_missing')


@pytest.mark.parametrize('fs,reason', [('nfs', 'locality_network'), ('cifs', 'locality_network'),
                                      (None, 'locality_unknown'), ('unrecognized', 'locality_unknown')])
@pytest.mark.parametrize('injected', [False, True])
def test_locality_fail_closed(checkouts, monkeypatch, fs, reason, injected):
    primary, worker = checkouts
    db = make_db(primary / 'override.db')
    monkeypatch.setattr(storage, '_fs_type_for_path', lambda path: fs)
    refusal(storage.resolve_store('sources', worker,
        binding=storage.StoreBinding('sources', db) if injected else None,
        env={'LU_SOURCES_DB': str(db)}), reason)


def test_locality_dependency_unavailable(checkouts, monkeypatch):
    import sys
    primary, worker = checkouts
    db = make_db(primary / 'override.db')
    monkeypatch.undo()
    monkeypatch.setitem(sys.modules, 'psutil', None)
    refusal(storage.resolve_store('sources', worker, env={'LU_SOURCES_DB': str(db)}), 'locality_unknown')


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('symlink', [False, True, 'dangling'])
def test_worktree_store_refused_even_with_override(checkouts, store, symlink):
    primary, worker = checkouts
    db = make_db(primary / 'data' / f'{store}.db')
    own = worker / 'data' / f'{store}.db'
    if symlink:
        own.symlink_to(db if symlink is True else primary / 'absent.db')
    else:
        own.touch()
    refusal(storage.resolve_store(store, worker, env={f'LU_{store.upper()}_DB': str(db)}),
            'worktree_local_store')


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('symlink', [False, True])
def test_special_override_and_injected_precedence(checkouts, monkeypatch, store, symlink):
    primary, worker = checkouts
    target = make_db(primary / 'special ?#% evidence.db')
    db = primary / 'alias ?#%.db'
    if symlink:
        db.symlink_to(target)
    else:
        db = target
    key = f'LU_{store.upper()}_DB'
    monkeypatch.setenv(key, str(db))
    assert storage.resolve_store(store, worker).path == target
    monkeypatch.setenv(key, '')
    result = storage.resolve_store(store, worker, binding=storage.StoreBinding(store, db))
    assert result.path == target and result.provenance == 'injected'
    refusal(storage.resolve_store(store, worker), 'empty_override')


def test_injected_binding_mismatch_and_write_refused(checkouts):
    primary, worker = checkouts
    db = make_db(primary / 'fixture.db')
    refusal(storage.resolve_store('sources', worker, binding=storage.StoreBinding('vesum', db)), 'invalid_binding')
    refusal(storage.resolve_store('sources', worker,
            binding=storage.StoreBinding('sources', db, access_mode='write')), 'invalid_binding')


def test_invalid_store_rejected(checkouts):
    with pytest.raises(ValueError, match='unsupported'):
        storage.resolve_store('other', checkouts[1])


def test_unknown_and_network_locality_probes(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, '_fs_type_for_path', lambda path: '')
    assert storage._store_locality(tmp_path) == 'unknown'
    assert storage._store_locality(Path('//server/UkrainianData/store.db')) == 'network'


def test_injected_missing_store_never_falls_back(checkouts):
    primary, worker = checkouts
    make_db(primary / 'data' / 'sources.db')
    refusal(storage.resolve_store('sources', worker,
            binding=storage.StoreBinding('sources', primary / 'missing.db'), env={}), 'store_missing')


def test_uninspectable_path_has_no_path(checkouts, monkeypatch):
    _, worker = checkouts
    def unavailable(path, *args, **kwargs):
        raise OSError('unavailable')
    monkeypatch.setattr(storage, 'default_repository_root', unavailable)
    refusal(storage.resolve_store('sources', worker, env={}), 'store_unavailable')


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('injected', [False, True])
def test_nul_path_returns_path_free_refusal(checkouts, store, injected):
    primary, worker = checkouts
    db = make_db(primary / 'data' / f'{store}.db')
    raw = str(db) + '\0'
    refusal(storage.resolve_store(store, worker,
        binding=storage.StoreBinding(store, Path(raw)) if injected else None,
        env={f'LU_{store.upper()}_DB': raw}), 'store_unavailable')
