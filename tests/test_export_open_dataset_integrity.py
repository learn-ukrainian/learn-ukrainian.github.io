"""Independent boundary controls for #10513; synthetic reviews stay temporary."""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import atlas_db
from scripts.atlas import export_runtime_shards as runtime
from scripts.atlas import word_card_certification as cert
from scripts.lexicon import export_open_dataset as export_mod
from scripts.lexicon import manifest_io, publish_manifest
from scripts.open_dataset import hydrate, publish
from tests.word_card_certification_fixtures import certification_fixture, sha  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value))


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def prepare(tmp_path, monkeypatch, certification):
    manifest = tmp_path / 'manifest.json'
    save(manifest, {'version': 'fixture', 'generated_at': '2026-01-01T00:00:00Z',
                    'cards': [certification.card]})
    dataset = tmp_path / 'dataset-source'
    monkeypatch.setattr(export_mod, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(export_mod, 'MANIFEST_PATH', manifest)
    monkeypatch.setattr(export_mod, 'DATASET_ROOT', dataset)
    monkeypatch.setattr(export_mod, 'DATASET_DIR', dataset / 'dataset')
    assert export_mod.export_dataset() == (1, 1)
    return manifest, dataset


def raw_package(tmp_path, dataset):
    """Build transport-valid bytes independently, even for deliberately bad cards."""
    files = [{'path': p.relative_to(dataset).as_posix(), 'content': p.read_text()}
             for p in sorted(dataset.rglob('*')) if p.is_file()]
    raw = json.dumps({'schema': 'atlas-open-dataset-package', 'schemaVersion': 1, 'files': files}).encode()
    compressed = gzip.compress(raw, mtime=0)
    asset, pointer = tmp_path / 'cached.gz', tmp_path / 'pointer.json'
    asset.write_bytes(compressed)
    save(pointer, {'asset_url': 'https://example.invalid/fixture', 'release_tag': 'fixture',
                   'package_schema_version': 1, 'gz_sha256': hashlib.sha256(compressed).hexdigest(),
                   'package_sha256': hashlib.sha256(raw).hexdigest(), 'gz_bytes': len(compressed),
                   'package_bytes': len(raw), 'file_count': len(files),
                   'files': [{'path': f['path'], 'bytes': len(f['content'].encode()),
                              'sha256': hashlib.sha256(f['content'].encode()).hexdigest()} for f in files]})
    return asset, pointer, files


def invalidate(fixture, fault):
    if fault == 'missing':
        fixture.ledger['approved_reviews'] = []
    elif fault == 'withdrawn':
        fixture.ledger['approved_reviews'][0]['status'] = 'withdrawn'
    elif fault == 'uncertified':
        fixture.card['quality']['linguistic_review'] = {'status': 'none'}
    elif fault == 'mismatched':
        fixture.card['key_at_creation']['spelling'] = 'changed'
        fixture.card['build']['card_version'] = 'cv_' + sha({k: v for k, v in fixture.card.items() if k != 'build'})[:24]
    elif fault == 'implementation':
        fixture.code.write_text('changed implementation')
    elif fault == 'rules':
        fixture.rules.write_text('changed rules')
    elif fault == 'permissions':
        fixture.register.write_text('changed permissions')
    elif fault in {'source', 'suppression', 'reimport'}:
        key = ('S', 'source') if fault in {'source', 'reimport'} else ('O', 'suppressions')
        fixture.snapshots[key].write_text('replacement snapshot')
    save(fixture.ledger_path, fixture.ledger)


BOUNDARIES = ('export', 'cli', 'accept', 'collect', 'build', 'publish', 'hydrate', 'manifest_read', 'manifest_gzip', 'manifest_publish', 'manifest_pointer')
FAULTS = ('valid', 'missing', 'withdrawn', 'uncertified', 'mismatched', 'implementation', 'rules',
          'permissions', 'source', 'suppression', 'reimport')


@pytest.mark.parametrize('boundary', BOUNDARIES)
@pytest.mark.parametrize('fault', FAULTS)
def test_public_boundaries(tmp_path, monkeypatch, certification, boundary, fault):
    manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    invalidate(certification, fault)
    manifest_value = {'cards': [certification.card], 'version': 'fixture',
                      'manifest_fingerprint': {'schema_version': 1, 'fingerprint': 'fixture'}}
    save(manifest, manifest_value)
    fingerprint = tmp_path / 'fingerprint.json'
    save(fingerprint, manifest_value['manifest_fingerprint'])
    counts = {'poc_thin_pages': 0, 'search_no_visible_gloss': 0, 'old_gate_no_english_anchor': 0}
    richness = {'bootstrap': False, 'baseline': counts, 'candidate': counts, 'regressions': {}, 'override_reason': None}
    monkeypatch.setattr(publish_manifest, 'evaluate_manifest_pointer_write_gate', lambda *_a, **_kw: richness)
    shard = dataset / 'dataset' / 'F.jsonl'
    shard.write_text(json.dumps(certification.card) + '\n')
    asset, pointer, files = raw_package(tmp_path, dataset)
    metadata = json.loads((dataset / 'dataset/_metadata.json').read_bytes())
    destination = tmp_path / 'destination'
    before = snapshot(dataset)
    pointer_gzip = tmp_path / 'pointer-input.gz'
    pointer_gzip.write_bytes(gzip.compress(manifest.read_bytes()))
    actions = {
        'export': lambda: export_mod.export_dataset(),
        'cli': lambda: export_mod.main(['--write']),
        'accept': lambda: atlas_db.migrate_manifest(manifest, destination / 'atlas.db'),
        'collect': lambda: publish.collect_dataset(dataset),
        'build': lambda: publish.build_package(metadata, files),
        'publish': lambda: publish.publish_open_dataset(dataset_root=dataset, gzip_path=destination / 'release.gz',
                                                       pointer_path=destination / 'pointer.json', dry_run=True),
        'hydrate': lambda: hydrate.hydrate_open_dataset(pointer_path=pointer, dataset_root=destination,
                                                       package_path=asset),
        'manifest_read': lambda: manifest_io.load_manifest(manifest),
        'manifest_gzip': lambda: publish_manifest.gzip_manifest(manifest, tmp_path / 'manifest.gz'),
        'manifest_publish': lambda: publish_manifest.publish_manifest(manifest_path=manifest,
            gzip_path=tmp_path / 'manifest.gz', pointer_path=destination / 'manifest-pointer.json',
            fingerprint_path=fingerprint, dry_run=True),
        'manifest_pointer': lambda: publish_manifest.build_pointer_payload(manifest_path=manifest,
            gzip_path=pointer_gzip, fingerprint_path=fingerprint, richness_gate=richness),
    }
    if fault == 'valid':
        result = actions[boundary]()
        if boundary == 'export':
            assert result == (1, 1)
        elif boundary == 'cli':
            assert result == 0
        elif boundary == 'accept':
            with sqlite3.connect(destination / 'atlas.db') as db:
                assert db.execute('SELECT review_state, entry_type FROM articles').fetchall() == [('approved', 'lemma')]
                assert json.loads(db.execute('SELECT payload_json FROM article_payloads').fetchone()[0]) == certification.card
        elif boundary == 'hydrate':
            assert json.loads((destination / 'dataset/F.jsonl').read_text()) == certification.card
        elif boundary == 'manifest_gzip':
            assert json.loads(gzip.decompress((tmp_path / 'manifest.gz').read_bytes())) == manifest_value
        elif boundary == 'manifest_read':
            assert result == manifest_value
    else:
        if boundary == 'cli':
            assert actions[boundary]() == 2
        else:
            with pytest.raises((cert.UncertifiedCardRefusal, publish.OpenDatasetPublishError,
                                hydrate.OpenDatasetHydrationError)):
                actions[boundary]()
        assert not destination.exists()
        assert not destination.with_name('destination.tmp').exists()
        assert not (tmp_path / 'manifest.gz').exists()
        assert snapshot(dataset) == before


def test_export_open_dataset_integrity(tmp_path, monkeypatch, certification):
    _manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    metadata = json.loads((dataset / 'dataset/_metadata.json').read_bytes())
    assert metadata['certified'] is True
    assert metadata['draft_engineering'] is False
    assert metadata['export_eligible'] is True
    assert metadata['shard_integrity'] == {'F.jsonl': {
        'sha256': hashlib.sha256((dataset / 'dataset/F.jsonl').read_bytes()).hexdigest(),
        'bytes': (dataset / 'dataset/F.jsonl').stat().st_size, 'entries': 1}}
    assert json.loads((dataset / 'dataset/F.jsonl').read_bytes()) == certification.card
    assert not list(dataset.rglob('*.tmp'))


def test_legacy_mixed_and_draft_isolation(tmp_path, monkeypatch, certification):
    manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    before = snapshot(dataset)
    for value in ({'entries': [{'lemma': 'legacy'}], 'card_certification': True},
                  {'cards': [certification.card], 'entries': [{'lemma': 'legacy'}]}):
        save(manifest, value)
        with pytest.raises(cert.UncertifiedCardRefusal):
            export_mod.export_dataset()
        assert snapshot(dataset) == before
    assert export_mod.export_dataset(allow_draft=True) == (0, 0)
    draft = dataset / 'draft/mechanics.json'
    assert json.loads(draft.read_bytes())['export_eligible'] is False
    assert not list((dataset / 'draft').rglob('*.jsonl'))
    with pytest.raises(publish.OpenDatasetPublishError):
        publish.collect_dataset(dataset)


@pytest.mark.parametrize('suffix', ['.jsonl.tmp', '.txt', '.md', '.bin', '.json', '.jsonl', '.json.gz', '.jsonl.gz'])
def test_package_file_types(tmp_path, monkeypatch, certification, suffix):
    _manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    bad = dataset / ('extra' + suffix)
    data = b'{"lemma":"uncertified"}\n'
    if suffix.endswith('.gz'):
        import base64
        data = gzip.compress(data)
        file = {'path': bad.name, 'content': base64.b64encode(data).decode(), 'encoding': 'base64'}
    else:
        file = {'path': bad.name, 'content': data.decode()}
    metadata, _, files = publish.collect_dataset(dataset)
    with pytest.raises(publish.OpenDatasetPublishError):
        publish.build_package(metadata, [*files, file])
    bad.write_bytes(data)
    with pytest.raises(publish.OpenDatasetPublishError):
        publish.collect_dataset(dataset)


def test_scope_schema_and_draft_rules(tmp_path, certification):
    card = certification.card
    assert cert.load_certified_card_for_export(card) == card
    for mutate in (
        lambda: card['quality']['linguistic_review'].update(approved_for=['site']),
        lambda: card['build'].update(rules_version='rules-v1-draft'),
        lambda: card.update(entry_type='lemma'),
    ):
        original = copy.deepcopy(card)
        mutate()
        certification.approve(card)
        with pytest.raises(cert.UncertifiedCardRefusal):
            cert.load_certified_card_for_export(card)
        card.clear()
        card.update(original)


def test_authority_cache_is_per_run(monkeypatch, certification):
    calls = []
    original = Path.open

    def counted(path, *args, **kwargs):
        calls.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', counted)
    with cert.certification_run():
        for _ in range(25):
            cert.load_certified_card_for_export(certification.card)
    assert calls.count(certification.ledger_path) == 1
    assert calls.count(certification.register) == 1
    assert calls.count(certification.code) == 1
    for path in certification.snapshots.values():
        assert calls.count(path) == 1
    invalidate(certification, 'withdrawn')
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(certification.card)


@pytest.mark.parametrize('fault', FAULTS)
def test_manifest_cache_rechecks_authority(tmp_path, monkeypatch, certification, fault):
    original = json.dumps({'cards': [certification.card]}).encode()
    cache = tmp_path / 'cache'
    cache.mkdir()
    cached = cache / 'unused.json'
    cached.write_bytes(original)
    destination = tmp_path / 'hydrated.json'
    pointer = {'gz_sha256': 'a' * 64, 'json_sha256': hashlib.sha256(original).hexdigest(),
               'asset_url': 'https://example.invalid/fixture'}
    monkeypatch.setattr(manifest_io, '_cache_file_for', lambda _sha: cached)
    monkeypatch.setattr(manifest_io, '_read_verified_cache', lambda *_args: original)
    invalidate(certification, fault)
    if fault in {'uncertified', 'mismatched'}:
        original = json.dumps({'cards': [certification.card]}).encode()
        cached.write_bytes(original)
        pointer['json_sha256'] = hashlib.sha256(original).hexdigest()
    if fault == 'valid':
        assert manifest_io._hydrate(destination, pointer) == {'cards': [certification.card]}
    else:
        # Artifact bytes and transport digests are unchanged; authority still wins.
        with pytest.raises(cert.UncertifiedCardRefusal):
            manifest_io._hydrate(destination, pointer)
        assert not destination.exists()


@pytest.mark.parametrize('fault', ['valid', 'missing', 'withdrawn', 'source', 'suppression', 'implementation',
                                   'rules', 'permissions', 'head', 'gloss', 'cefr', 'form_route', 'kind'])
def test_runtime_certification(tmp_path, monkeypatch, certification, fault):
    manifest, _dataset = prepare(tmp_path, monkeypatch, certification)
    db_path = tmp_path / 'atlas.db'
    atlas_db.migrate_manifest(manifest, db_path)
    out = tmp_path / 'runtime'
    runtime.export_runtime_shards(db_path=db_path, out_dir=out, include_decks=False, verify=True)
    before = snapshot(out)
    if fault in {'head', 'gloss', 'cefr', 'form_route', 'kind'}:
        with sqlite3.connect(db_path) as db:
            if fault == 'form_route':
                db.execute('DELETE FROM articles')
            else:
                column = {'head': 'display_head', 'gloss': 'gloss', 'cefr': 'cefr', 'kind': 'entry_type'}[fault]
                db.execute(f'UPDATE articles SET {column}=?', ('proper_name' if fault == 'kind' else 'changed',))
    else:
        invalidate(certification, fault)
    if fault == 'valid':
        runtime.export_runtime_shards(db_path=db_path, out_dir=out, include_decks=False, verify=True)
        assert runtime.verify_tree(out, 'atlas')['articles'] == 1
    else:
        with pytest.raises(runtime.ExportError):
            runtime.export_runtime_shards(db_path=db_path, out_dir=out, include_decks=False, verify=True)
        assert snapshot(out) == before
        if fault not in {'head', 'gloss', 'cefr', 'form_route', 'kind'}:
            with pytest.raises(runtime.ExportError):
                runtime.verify_tree(out, 'atlas')


def test_authoritative_ledger_and_census():
    ledger = json.loads((ROOT / 'docs/atlas/word-cards/review-evidence-ledger.json').read_bytes())
    assert ledger['approved_reviews'] == []
    census = json.loads((ROOT / 'docs/atlas/word-cards/acceptance-export-path-census.json').read_bytes())
    assert census['source_census_issue'] == 9401
    assert {row['path_id'] for row in census['frozen_paths']} == {
        'dataset_export', 'acceptance', 'runtime_export', 'runtime_verify', 'package_collect', 'package_build',
        'dataset_publish', 'dataset_hydrate', 'manifest_read', 'manifest_publish'}
    for row in census['frozen_paths']:
        assert (ROOT / row['entry_point']).is_file()


@pytest.mark.parametrize('kind,expected', [('lexeme', 'lemma'), ('mwe', 'multiword_term'),
                                           ('proper_name', 'proper_name')])
def test_card_kind_mapping(tmp_path, monkeypatch, certification, kind, expected):
    certification.card['card_kind'] = kind
    certification.approve(certification.card)
    manifest, _dataset = prepare(tmp_path, monkeypatch, certification)
    db_path = tmp_path / 'atlas.db'
    atlas_db.migrate_manifest(manifest, db_path)
    with sqlite3.connect(db_path) as db:
        assert db.execute('SELECT entry_type FROM articles').fetchall() == [(expected,)]
        assert db.execute('SELECT COUNT(*) FROM aliases').fetchone()[0] == 0
    out = tmp_path / 'out'
    result = runtime.export_runtime_shards(db_path=db_path, out_dir=out, include_decks=False, verify=True)
    assert result['counts']['articles'] == 1
    assert runtime.verify_tree(out, 'atlas')['articles'] == 1


def test_resolved_card_fields():
    value = {'fields': {'english_gloss': {'selected': 'reviewed'}}, 'assertions': [
        {'assertion_id': 'unselected', 'value': 'wrong', 'status': 'active'},
        {'assertion_id': 'reviewed', 'value': 'Reviewed gloss', 'status': 'active'}]}
    assert cert.card_field(value, 'english_gloss') == 'Reviewed gloss'
    assert cert.card_field(value, 'cefr') is None
    value['assertions'][1]['status'] = 'suppressed'
    assert cert.card_field(value, 'english_gloss') is None


@pytest.mark.parametrize('fault', ['schema', 'duplicate', 'scope_type', 'blank_record', 'empty', 'malformed',
                                   'missing_file', 'unknown_source', 'missing_suppression', 'unresolved', 'suppressed'])
def test_invalid_authority_and_cards(certification, fault):
    card = certification.card
    if fault == 'schema':
        certification.ledger['schema_version'] = 'invalid'
    elif fault == 'duplicate':
        certification.ledger['approved_reviews'] *= 2
    elif fault == 'scope_type':
        certification.ledger['approved_reviews'][0]['approved_for'] = 'dataset'
    elif fault == 'blank_record':
        card['quality']['linguistic_review']['record'] = ''
        certification.approve(card)
    elif fault == 'empty':
        certification.ledger['approved_reviews'] = {}
    elif fault == 'unknown_source':
        certification.ledger['snapshot_bindings']['S'] = {}
    elif fault == 'missing_suppression':
        del card['build']['inputs']['O']['suppressions']
        certification.approve(card)
    elif fault == 'unresolved':
        card['quality']['identity_confidence'] = 'unresolved'
        certification.approve(card)
    elif fault == 'suppressed':
        card['state'] = 'suppressed'
        certification.approve(card)
    save(certification.ledger_path, certification.ledger)
    if fault == 'malformed':
        certification.ledger_path.write_text('{')
    elif fault == 'missing_file':
        certification.ledger_path.unlink()
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(card)


@pytest.mark.parametrize('value', [None, [], {}, {'cards': {}}, {'entries': []}])
def test_invalid_inventory(value):
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.certified_inventory(value)


def test_lock_snapshot_and_duplicate_inventory(certification):
    lock = certification.snapshots['V', 'vesum']
    value = certification.card['build']['inputs']['V']['vesum']['content_sha256']
    save(lock, {'expected': {'canonical_jsonl_sha256': value}})
    certification.ledger['snapshot_bindings']['V']['vesum']['json_keys'] = ['expected', 'canonical_jsonl_sha256']
    save(certification.ledger_path, certification.ledger)
    assert cert.load_certified_card_for_export(certification.card) == certification.card
    with pytest.raises(cert.UncertifiedCardRefusal, match='duplicate'):
        cert.certified_inventory({'cards': [certification.card], 'entries': [certification.card]})
    save(lock, {'expected': {'canonical_jsonl_sha256': '0' * 64}})
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(certification.card)


@pytest.mark.parametrize('extension', ['.json', '.json.gz', '.jsonl.gz'])
def test_valid_extra_data_files_and_draft_parent(tmp_path, monkeypatch, certification, extension):
    # An unrelated ancestor directory named draft does not make a certified dataset a draft.
    parent = tmp_path / 'draft'
    parent.mkdir()
    _manifest, dataset = prepare(parent, monkeypatch, certification)
    data = json.dumps(certification.card).encode()
    if extension.endswith('.gz'):
        data = gzip.compress(data)
    (dataset / ('additional' + extension)).write_bytes(data)
    asset, pointer = parent / 'release.gz', parent / 'pointer.json'
    result = publish.publish_open_dataset(dataset_root=dataset, gzip_path=asset, pointer_path=pointer, dry_run=True)
    publish.write_pointer(pointer, result)
    destination = parent / 'hydrated'
    assert hydrate.hydrate_open_dataset(pointer_path=pointer, package_path=asset,
                                        dataset_root=destination)['file_count'] == 6
    assert (destination / ('additional' + extension)).read_bytes() == data


def test_assertion_withdrawal_reimport_and_rollback(tmp_path, monkeypatch, certification):
    card = certification.card
    assertion = {
        'assertion_id': 'wa_' + 'a' * 24, 'subject': {'kind': 'card', 'id': card['card_id']},
        'field': 'english_gloss', 'value': 'Reviewed fixture fact', 'value_norm': 'reviewed fixture fact',
        'source_id': 'source', 'snapshot_id': 'source-v1', 'locator': 'fixture:1',
        'extraction_version': 'fixture-v1', 'extraction_confidence': 'high',
        'producer': {'kind': 'source_extract', 'name': 'fixture'}, 'review': {'status': 'none'},
        'licence_ref': {'register_source_id': 'source', 'register_version': 1}, 'status': 'active',
    }
    card['assertions'] = [assertion]
    card['fields'] = {'english_gloss': {'state': 'single-source', 'values': [], 'comparison': 'scalar',
                                       'mapping_evidenced': True, 'selected': assertion['assertion_id']}}
    certification.approve(card)
    original = copy.deepcopy(card)
    manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    assert json.loads((dataset / 'dataset/F.jsonl').read_bytes())['assertions'][0]['value'] == 'Reviewed fixture fact'
    asset, pointer, _files = raw_package(tmp_path, dataset)
    db = tmp_path / 'atlas.db'
    atlas_db.migrate_manifest(manifest, db)
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT gloss FROM articles').fetchone()[0] == 'Reviewed fixture fact'
    out = tmp_path / 'runtime'
    runtime.export_runtime_shards(db_path=db, out_dir=out, include_decks=False, verify=True)
    before_runtime = snapshot(out)
    suppression = certification.snapshots['O', 'suppressions']
    suppression.write_text('fixture assertion withdrawn')
    card['build']['inputs']['O']['suppressions']['content_sha256'] = hashlib.sha256(suppression.read_bytes()).hexdigest()
    card['fields'] = {}
    card['assertions'] = [{'assertion_id': assertion['assertion_id'], 'status': 'suppressed', 'suppression_ref': 'fixture'}]
    certification.approve(card)
    save(manifest, {'cards': [card]})
    assert export_mod.export_dataset() == (1, 1)
    withdrawn = json.loads((dataset / 'dataset/F.jsonl').read_bytes())
    assert withdrawn['assertions'] == [{'assertion_id': assertion['assertion_id'], 'status': 'suppressed',
                                       'suppression_ref': 'fixture'}]
    assert b'Reviewed fixture fact' not in (dataset / 'dataset/F.jsonl').read_bytes()
    save(manifest, {'cards': [original]})
    before_db = db.read_bytes()
    with pytest.raises(cert.UncertifiedCardRefusal):
        atlas_db.migrate_manifest(manifest, db)
    assert db.read_bytes() == before_db
    with pytest.raises(hydrate.OpenDatasetHydrationError):
        hydrate.hydrate_open_dataset(pointer_path=pointer, dataset_root=tmp_path / 'restored', package_path=asset)
    assert not (tmp_path / 'restored').exists()
    with pytest.raises(runtime.ExportError):
        runtime.export_runtime_shards(db_path=db, out_dir=out, include_decks=False, verify=True)
    assert snapshot(out) == before_runtime


@pytest.mark.parametrize('module', [atlas_db, hydrate, publish_manifest])
def test_cli_help(module, monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', [module.__name__, '--help'])
    with pytest.raises(SystemExit) as result:
        module.main()
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert 'Outputs:' in help_text and 'Exit codes:' in help_text
    assert 'certif' in help_text


@pytest.mark.parametrize('table,columns,values', [
    ('aliases', 'alias,kind,source,target_slug,visibility', ('extra', 'canonical', 'fixture', None, 'public')),
    ('related_entries', 'slug,related_slug,entry_type,relation,provenance', (None, 'different-target', 'lemma', 'synonym', 'verified')),
    ('article_provenance', 'slug,source_family,source_locator,extraction_mode', (None, 'extra', 'fixture:2', 'extract')),
])
def test_runtime_refuses_database_additions(tmp_path, monkeypatch, certification, table, columns, values):
    manifest, _dataset = prepare(tmp_path, monkeypatch, certification)
    db = tmp_path / 'atlas.db'
    atlas_db.migrate_manifest(manifest, db)
    with sqlite3.connect(db) as conn:
        arguments = tuple(certification.card['card_id'] if value is None else value for value in values)
        conn.execute(f'INSERT INTO {table}({columns}) VALUES ({",".join("?" for _ in arguments)})', arguments)
    out = tmp_path / 'runtime'
    with pytest.raises(runtime.ExportError, match='outside the certified'):
        runtime.export_runtime_shards(db_path=db, out_dir=out, include_decks=False, verify=True)
    assert not out.exists()


@pytest.mark.parametrize('field,value', [('unreviewed', {'lemma': 'uncertified'}),
                                        ('version', {'assertion': 'uncertified'}),
                                        ('stats', {'cards': 'uncertified'}),
                                        ('shard_integrity', {'F.jsonl': {'extra': 'uncertified'}})])
def test_package_metadata_cannot_carry_extra_assertions(tmp_path, monkeypatch, certification, field, value):
    _manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    metadata, _, files = publish.collect_dataset(dataset)
    metadata[field] = value
    next(file for file in files if file['path'] == 'dataset/_metadata.json')['content'] = json.dumps(metadata)
    with pytest.raises(publish.OpenDatasetPublishError):
        publish.build_package(metadata, files)


def test_card_manifest_cannot_carry_extra_assertions(tmp_path, monkeypatch, certification):
    manifest, dataset = prepare(tmp_path, monkeypatch, certification)
    before = snapshot(dataset)
    save(manifest, {'cards': [certification.card], 'unchecked': {'lemma': 'uncertified'}})
    with pytest.raises(cert.UncertifiedCardRefusal):
        export_mod.export_dataset()
    with pytest.raises(cert.UncertifiedCardRefusal):
        publish_manifest.gzip_manifest(manifest, tmp_path / 'manifest.gz')
    assert snapshot(dataset) == before
    assert not (tmp_path / 'manifest.gz').exists()


@pytest.mark.parametrize('path', ['/not-repository-relative', '../outside.json'])
def test_snapshot_paths_are_repository_relative(certification, path):
    certification.ledger['snapshot_bindings']['S']['source']['path'] = path
    save(certification.ledger_path, certification.ledger)
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(certification.card)


def test_json_card_payload(certification):
    assert cert.load_certified_card_for_export(json.dumps(certification.card)) == certification.card
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export('{')
