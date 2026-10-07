"""Hermetic declaration, refusal, alias and call-time contract proofs (#9977)."""

import sqlite3

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology as t


@pytest.fixture
def roots(tmp_path, monkeypatch):
    primary = tmp_path / 'primary'
    worker = tmp_path / 'worker'
    for root in (primary, worker):
        (root / 'data').mkdir(parents=True)
        (root / '.git').mkdir()
    monkeypatch.setattr(t, 'main_checkout_root', lambda root: primary)
    monkeypatch.setattr(t, '_store_locality', lambda path: 'local')
    return primary, worker


def refusal(result, reason):
    assert result == t.StoreRefusal(result.store, reason)
    assert set(vars(result)) == {'store', 'reason'}


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('intent', ['update', 'create'])
@pytest.mark.parametrize('operation', ['sqlite', 'replace'])
def test_binding_and_existing_target(roots, store, intent, operation):
    primary, worker = roots
    db = primary / 'data' / f'{store}.db'
    db.write_bytes(b'existing')
    result = t.resolve_store_for_write(store, worker, intent=intent, operation=operation, env={})
    assert isinstance(result, t.WriteStoreBinding)
    assert not isinstance(result, t.StoreBinding)
    assert result.path == db
    assert (result.intent, result.operation, result.role, result.access_mode) == (intent, operation, 'active', 'write')
    assert result.sqlite_uri == (db.as_uri() + ('?mode=rwc' if intent == 'create' else '?mode=rw') if operation == 'sqlite' else None)
    assert db.read_bytes() == b'existing'


@pytest.mark.parametrize('store', ['sources', 'vesum'])
@pytest.mark.parametrize('role', ['active', 'staging', 'shadow'])
@pytest.mark.parametrize('intent', ['create', 'update'])
def test_worktree_slots_refused_even_absent(roots, store, role, intent):
    _primary, worker = roots
    for root in (worker, worker.parent / 'another'):
        (root / 'data').mkdir(parents=True, exist_ok=True)
        (root / '.git').touch(exist_ok=True) if not (root / '.git').exists() else None
        path = root / 'data' / f'{store}.db'
        refusal(t.resolve_store_for_write(store, worker, intent=intent,
                target=t.ExplicitStoreWriteTarget(path, role), env={}), 'worktree_local_store')
        assert not path.exists()


@pytest.mark.parametrize(('raw', 'reason'), [('', 'empty_override'), ('  ', 'empty_override'),
    ('file:/store', 'uri_override'), ('relative.db', 'relative_override'), ('../bad', 'invalid_target')])
def test_invalid_selected_input_never_falls_back(roots, raw, reason):
    primary, worker = roots
    (primary / 'data' / 'sources.db').touch()
    refusal(t.resolve_store_for_write('sources', worker, intent='create', env={'LU_SOURCES_DB': raw}), reason)


def test_invalid_bindings_and_requests(roots):
    primary, worker = roots
    db = primary / 'existing'
    db.touch()
    refusal(t.resolve_store_for_write('sources', worker, intent='update', target=t.StoreBinding('sources', db)), 'invalid_binding')
    for kwargs in ({'intent': 'invalid'}, {'intent': 'update', 'operation': 'invalid'},
                   {'intent': 'update', 'target': object()},
                   {'intent': 'update', 'target': t.ExplicitStoreWriteTarget(db, 'invalid')},
                   {'intent': 'update', 'target': t.ExplicitStoreWriteTarget(None, 'active')}):
        refusal(t.resolve_store_for_write('sources', worker, **kwargs), 'invalid_target')
    with pytest.raises(ValueError, match='unsupported logical store'):
        t.resolve_store_for_write('unknown', worker, intent='update')
    with pytest.raises(ValueError, match='unsupported logical store'):
        t.unresolved_store_placeholder('unknown')


def test_missing_and_invalid_parent_or_leaf(roots):
    _primary, worker = roots
    refusal(t.resolve_store_for_write('sources', worker, intent='update', env={}), 'store_missing')
    result = t.resolve_store_for_write('sources', worker, intent='create', env={})
    assert isinstance(result, t.WriteStoreBinding)
    assert not result.path.exists()
    for path, reason in ((worker / 'missing' / 'output', 'parent_missing'),
                         (worker / 'data', 'not_a_file')):
        refusal(t.resolve_store_for_write('sources', worker, intent='create',
                target=t.ExplicitStoreWriteTarget(path, 'staging'), env={}), reason)
    leaf = worker / 'file'
    leaf.touch()
    refusal(t.resolve_store_for_write('sources', worker, intent='create',
            target=t.ExplicitStoreWriteTarget(leaf / 'output', 'staging'), env={}), 'parent_missing')


@pytest.mark.parametrize('locality', ['network', 'unknown'])
def test_locality_requires_positive_evidence(roots, monkeypatch, locality):
    _primary, worker = roots
    monkeypatch.setattr(t, '_store_locality', lambda path: locality)
    refusal(t.resolve_store_for_write('sources', worker, intent='create', env={}), f'locality_{locality}')


def test_os_error_is_path_free(roots, monkeypatch):
    _primary, worker = roots
    def fail(path):
        raise PermissionError('private path')
    monkeypatch.setattr(t, '_store_locality', fail)
    refusal(t.resolve_store_for_write('sources', worker, intent='create', env={}), 'store_unavailable')


@pytest.mark.parametrize('kind', ['symlink', 'hardlink'])
def test_nonactive_roles_refuse_live_alias(roots, kind):
    primary, worker = roots
    active = primary / 'data' / 'sources.db'
    active.touch()
    alias = worker / 'alias'
    if kind == 'symlink':
        alias.symlink_to(active)
    else:
        alias.hardlink_to(active)
    for role in ('staging', 'shadow'):
        refusal(t.resolve_store_for_write('sources', worker, intent='update',
                target=t.ExplicitStoreWriteTarget(alias, role), env={}), 'target_is_active_store')
    result = t.resolve_store_for_write('sources', worker, intent='update',
            target=t.ExplicitStoreWriteTarget(alias, 'active'), env={})
    assert isinstance(result, t.WriteStoreBinding)
    if kind == 'symlink':
        refusal(t.resolve_store_for_write('sources', worker, intent='update', operation='replace',
                target=t.ExplicitStoreWriteTarget(alias, 'active'), env={}), 'symlink_replace_target')


def test_lexical_and_resolved_slots_and_dangling_link(roots):
    primary, worker = roots
    lexical = worker / 'data' / 'vesum.db'
    active = primary / 'data' / 'vesum.db'
    active.touch()
    lexical.symlink_to(active)
    refusal(t.resolve_store_for_write('vesum', worker, intent='create', env={}), 'worktree_local_store')
    lexical.unlink()
    alias = worker / 'alias'
    alias.symlink_to(worker / 'data', target_is_directory=True)
    refusal(t.resolve_store_for_write('vesum', worker, intent='create',
            target=t.ExplicitStoreWriteTarget(alias / 'vesum.db', 'staging'), env={}), 'worktree_local_store')
    dangling = worker / 'dangling'
    dangling.symlink_to(worker / 'absent')
    refusal(t.resolve_store_for_write('vesum', worker, intent='create',
            target=t.ExplicitStoreWriteTarget(dangling, 'staging'), env={}), 'store_missing')


def test_roles_have_distinct_behavior_and_relative_anchoring(roots, monkeypatch):
    primary, worker = roots
    monkeypatch.chdir(primary)
    staging = t.resolve_store_for_write('sources', worker, intent='create',
        target=t.ExplicitStoreWriteTarget('data/output', 'staging'), env={})
    assert staging.path == worker / 'data' / 'output'
    refusal(t.resolve_store_for_write('sources', worker, intent='create',
        target=t.ExplicitStoreWriteTarget('data/output', 'active'), env={}), 'relative_override')
    # Shadow refuses reserved primary slots even before update existence checks.
    refusal(t.resolve_store_for_write('vesum', worker, intent='update',
        target=t.ExplicitStoreWriteTarget(primary / 'data' / 'vesum.db', 'staging'), env={}), 'store_missing')
    refusal(t.resolve_store_for_write('vesum', worker, intent='update',
        target=t.ExplicitStoreWriteTarget(primary / 'data' / 'vesum.db', 'shadow'), env={}), 'target_is_active_store')
    # Shadow refuses the OTHER primary slot even for create; staging also
    # refuses canonical active aliases. Shadow supports whole-file replacement.
    for store in ('sources', 'vesum'):
        refusal(t.resolve_store_for_write(store, worker, intent='create', operation='replace',
            target=t.ExplicitStoreWriteTarget(primary / 'data' / 'vesum.db', 'shadow'), env={}), 'target_is_active_store')
    shadow = t.resolve_store_for_write('vesum', worker, intent='create', operation='replace',
        target=t.ExplicitStoreWriteTarget('data/output', 'shadow'), env={})
    assert shadow.path == staging.path and shadow.sqlite_uri is None


def test_configured_active_alias_and_invalid_comparison(roots):
    primary, worker = roots
    active = primary / 'configured'
    active.touch()
    refusal(t.resolve_store_for_write('sources', worker, intent='update',
            target=t.ExplicitStoreWriteTarget(active, 'staging'), env={'LU_SOURCES_DB': str(active)}), 'target_is_active_store')
    output = worker / 'output'
    for raw, reason in (('', 'empty_override'), ('relative', 'relative_override'),
                        ('file:/private', 'uri_override'), (str(worker / 'absent'), 'store_missing'),
                        (str(worker / 'data'), 'not_a_file')):
        refusal(t.resolve_store_for_write('vesum', worker, intent='create',
            target=t.ExplicitStoreWriteTarget(output, 'shadow'), env={'LU_SOURCES_DB': raw}), reason)
        assert not output.exists()


@pytest.mark.parametrize('name', ['percent%.db', 'question?.db', 'hash#.db', 'space name.db', 'кирилиця.db'])
def test_sqlite_uri_roundtrip_and_update_does_not_create(roots, name):
    _primary, worker = roots
    path = worker / name
    sqlite3.connect(path).close()
    result = t.resolve_store_for_write('sources', worker, intent='update',
        target=t.ExplicitStoreWriteTarget(path, 'staging'), env={})
    assert result.sqlite_uri == path.as_uri() + '?mode=rw'
    # Exercise the URI exactly as writers do, against a synthetic fixture.
    conn = sqlite3.connect(result.sqlite_uri, uri=True)
    conn.execute('CREATE TABLE proof(value)')
    conn.execute('INSERT INTO proof VALUES (42)')
    conn.commit()
    conn.close()
    with open_readonly(path) as reader:
        assert reader.execute('SELECT value FROM proof').fetchone() == (42,)
    path.unlink()
    with pytest.raises(Exception, match='unable to open database'):
        sqlite3.connect(result.sqlite_uri, uri=True)
    assert not path.exists()


def test_refresh_and_placeholder_never_admitted(roots, monkeypatch):
    _primary, worker = roots
    one, two = worker / 'one', worker / 'two'
    one.touch()
    two.touch()
    monkeypatch.setenv('LU_SOURCES_DB', str(one))
    assert t.resolve_store_for_write('sources', worker, intent='update').path == one
    monkeypatch.setenv('LU_SOURCES_DB', str(two))
    assert t.resolve_store_for_write('sources', worker, intent='update').path == two
    placeholder = t.unresolved_store_placeholder('sources')
    assert not placeholder.parent.exists()
    assert not any((p / '.git').exists() for p in placeholder.parents)
    refusal(t.resolve_store('sources', worker, binding=t.StoreBinding('sources', placeholder)), 'store_missing')
    refusal(t.resolve_store_for_write('sources', worker, intent='create',
            target=t.ExplicitStoreWriteTarget(placeholder, 'active'), env={}), 'invalid_target')
