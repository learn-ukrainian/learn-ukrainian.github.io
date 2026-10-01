"""Validator behaviour of the document and data catalogue (#9412) on small fixtures, plus the real tree."""
import ast
import copy
import json
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.docs import catalogue as catalogue_module
from scripts.docs.catalogue import (
    CONTROL_CHARS,
    DRAFT_MARKERS,
    MAX_CATALOGUE_BYTES,
    MAX_CATALOGUE_DEPTH,
    MAX_CATALOGUE_NODES,
    CatalogueLoadError,
    GitProtocolError,
    Report,
    body_readable,
    control_path_error,
    coverage,
    draft_scan,
    glob_error,
    glob_regex,
    index_entries,
    is_catch_all,
    main,
    parse,
    read_heads,
    suggest,
    validate,
)

# The real-tree test below lists the whole tracked denominator, so the module is
# registered in tests/test_repo_wide_marker_invariant.py.
pytestmark = pytest.mark.repo_wide

REPO = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO / 'docs/knowledge/catalogue.schema.json').read_text(encoding='utf-8'))
OWNERS = {'docs-knowledge', 'infra-harness'}
FILES = ['docs/README.md', 'docs/guide/a.md', 'docs/guide/b.md', 'docs/guide/old/c.md',
         'registry/r.yaml', 'scripts/build.py', 'AGENTS.md']
ROOTS = ('docs', 'registry')


def family(eid, paths, **extra):
    entry = {'id': eid, 'kind': 'doc_family', 'paths': paths, 'purpose': f'{eid} documents',
             'keywords': [eid], 'lifecycle': 'active', 'owner': 'infra-harness',
             'query': [{'surface': 'git_grep', 'how': f'git grep -n -F x -- {paths[0]}'}],
             'content_searchable': True}
    entry.update(extra)
    return entry


def store_entry(eid, **extra):
    entry = {'id': eid, 'kind': 'data_store', 'store': ['data/main.db'], 'producer': ['scripts/build.py'],
             'local_only': True, 'purpose': f'{eid} store', 'keywords': [eid], 'lifecycle': 'active',
             'owner': 'infra-harness', 'query': [{'surface': 'sqlite', 'how': 'read-only SQL'}],
             'content_searchable': False}
    entry.update(extra)
    return entry


def catalogue(*entries, residual=()):
    return {'schema_version': 1,
            'denominator': {'tracked_roots': ['docs', 'registry', 'curriculum/l2-uk-en/evidence'],
                            'local_store_root': 'data'},
            'status_mapping': {'current': 'active', 'historical': 'archive', 'superseded': 'superseded'},
            'entries': list(entries), 'residual': list(residual)}


def base():
    return catalogue(family('entry-map', ['docs/README.md']),
                     family('guide', ['docs/guide/**']),
                     family('registry-data', ['registry/r.yaml'], kind='registry'))


def check(data, files=FILES):
    return validate(data, SCHEMA, files, OWNERS, ROOTS)


def errors_with(report, text):
    return [e for e in report.errors if text in e]


def test_valid_fixture_resolves_every_path_once():
    report = check(base())
    assert report.ok, report.errors
    assert report.denominator == 5  # scripts/ and root files are outside the roots
    assert report.resolved['docs/guide/old/c.md'] == ('guide', 'active')
    assert report.lifecycle_counts() == {'active': 5}


def test_most_specific_glob_wins_over_parent_family():
    data = base()
    data['entries'].append(family('guide-old', ['docs/guide/old/**'], lifecycle='archive'))
    report = check(data)
    assert report.ok, report.errors
    assert report.resolved['docs/guide/old/c.md'] == ('guide-old', 'archive')
    assert report.resolved['docs/guide/a.md'] == ('guide', 'active')


def test_equal_specificity_match_is_ambiguous():
    data = base()
    data['entries'].append(family('guide-twin', ['docs/guide/**']))
    report = check(data)
    assert len(errors_with(report, 'ambiguous match between guide, guide-twin')) == 3


def test_glob_that_matches_nothing_is_rejected():
    data = base()
    data['entries'][1]['paths'].append('docs/guide/missing-*.md')
    assert errors_with(check(data), "glob 'docs/guide/missing-*.md' matches no tracked file")


def test_glob_outside_tracked_roots_is_rejected():
    data = base()
    data['entries'].append(family('scripts', ['scripts/*.py']))
    assert errors_with(check(data), 'is outside the tracked roots')


def test_missing_supersession_target_is_rejected():
    data = base()
    data['entries'][1]['overrides'] = [{'path': 'docs/guide/a.md', 'lifecycle': 'superseded',
                                        'superseded_by': 'docs/guide/gone.md', 'evidence': 'banner'}]
    assert errors_with(check(data), "supersession target 'docs/guide/gone.md' does not exist")


def test_supersession_cycle_and_self_link_are_rejected():
    data = base()
    data['entries'][1]['overrides'] = [
        {'path': 'docs/guide/a.md', 'lifecycle': 'superseded', 'superseded_by': 'docs/guide/b.md', 'evidence': 'own banner'},
        {'path': 'docs/guide/b.md', 'lifecycle': 'superseded', 'superseded_by': 'docs/guide/a.md', 'evidence': 'own banner'},
        {'path': 'docs/guide/old/c.md', 'lifecycle': 'superseded', 'superseded_by': 'docs/guide/old/c.md#top',
         'evidence': 'own banner'}]
    report = check(data)
    assert errors_with(report, 'cycle or self-link: docs/guide/a.md -> docs/guide/b.md -> docs/guide/a.md')
    assert errors_with(report, 'cycle or self-link: docs/guide/old/c.md -> docs/guide/old/c.md')


def test_supersession_chain_must_end_at_active_or_archive():
    data = base()
    data['entries'][1]['overrides'] = [
        {'path': 'docs/guide/a.md', 'lifecycle': 'superseded', 'superseded_by': 'docs/guide/b.md', 'evidence': 'own banner'},
        {'path': 'docs/guide/b.md', 'lifecycle': 'draft', 'evidence': 'own banner'}]
    assert errors_with(check(data), "chain ends at 'docs/guide/b.md' with lifecycle 'draft'")
    data['entries'][1]['overrides'][1]['lifecycle'] = 'archive'
    assert check(data).ok


def test_chain_through_superseded_family_and_outside_target_is_valid():
    data = base()
    data['entries'].append(family('guide-old', ['docs/guide/old/**'], lifecycle='superseded',
                                  superseded_by='scripts/build.py'))
    data['entries'][1]['overrides'] = [{'path': 'docs/guide/a.md', 'lifecycle': 'superseded',
                                        'superseded_by': 'id:guide-old', 'evidence': 'own banner'}]
    report = check(data)
    assert report.ok, report.errors
    assert report.resolved['docs/guide/old/c.md'] == ('guide-old', 'superseded')


ENTRY_KINDS = ['doc_family', 'registry', 'evidence', 'resource_catalogue', 'generated', 'data_store']


def superseded_entry(kind, eid, target):
    if kind == 'data_store':
        return store_entry(eid, store=[f'data/{eid}.db'], lifecycle='superseded', superseded_by=target)
    return family(eid, ['docs/guide/old/**'], kind=kind, lifecycle='superseded', superseded_by=target)


@pytest.mark.parametrize('kind', ENTRY_KINDS)
def test_supersession_is_validated_for_every_entry_kind(kind):
    data = base()
    data['entries'].append(superseded_entry(kind, 'old-thing', 'id:guide'))
    assert check(data).ok, check(data).errors
    data['entries'][-1]['superseded_by'] = 'id:no-such-entry'
    assert errors_with(check(data), "id:old-thing: supersession target 'id:no-such-entry' does not exist")
    data['entries'][-1]['superseded_by'] = 'docs/guide/gone.md'
    assert errors_with(check(data), "supersession target 'docs/guide/gone.md' does not exist")
    data['entries'][-1]['superseded_by'] = 'id:old-thing'
    assert errors_with(check(data), 'supersession cycle or self-link: id:old-thing -> id:old-thing')
    data['entries'][-1]['superseded_by'] = 'id:entry-map'
    data['entries'][0]['lifecycle'] = 'draft'
    assert errors_with(check(data), "id:old-thing: supersession chain ends at 'id:entry-map' with lifecycle 'draft'")


@pytest.mark.parametrize('kind', ENTRY_KINDS)
def test_two_entry_supersession_cycle_is_rejected_for_every_kind(kind):
    data = base()
    first = superseded_entry(kind, 'first', 'id:second')
    second = superseded_entry(kind, 'second', 'id:first')
    if kind != 'data_store':
        second['paths'] = ['docs/guide/a.md']
    data['entries'] += [first, second]
    assert errors_with(check(data), 'supersession cycle or self-link: id:first -> id:second -> id:first')


@pytest.mark.parametrize('mutate, message', [
    (lambda d: d['entries'][1].update(lifecycle='current'), "'current' is not one of"),
    (lambda d: d['entries'][1].update(lifecycle='historical'), "'historical' is not one of"),
    (lambda d: d['entries'][1].update(lifecycle='superseded'), "'superseded_by' is a required property"),
    (lambda d: d['entries'][1].update(superseded_by='docs/README.md'), 'should not be valid'),
    (lambda d: d['entries'][1].update(kind='doc'), 'schema: entries/1'),
    (lambda d: d['entries'][1].update(paths=['/abs/path']), 'schema: entries/1'),
])
def test_wrong_vocabulary_and_shape_fail_schema(mutate, message):
    data = base()
    mutate(data)
    assert errors_with(check(data), message)


def test_owner_must_be_a_stream_or_area_key():
    data = base()
    data['entries'][1]['owner'] = 'nobody'
    assert errors_with(check(data), "owner 'nobody' is not a stream or area key")


def test_override_must_belong_to_the_declaring_family():
    data = base()
    data['entries'][1]['overrides'] = [{'path': 'docs/README.md', 'lifecycle': 'archive', 'evidence': 'own banner'}]
    assert errors_with(check(data), "resolves to 'entry-map', not this entry")


def test_residual_marks_lifecycle_unclassified_and_needs_coverage():
    data = base()
    data['residual'] = [{'path': 'docs/guide/b.md', 'owner': 'docs-knowledge', 'reason': 'not yet read'},
                        {'path': 'docs/nowhere.md', 'owner': 'docs-knowledge', 'reason': 'missing'}]
    report = check(data)
    assert report.resolved['docs/guide/b.md'] == ('guide', 'residual')
    assert errors_with(report, "residual 'docs/nowhere.md' is not a covered tracked path")


def test_privacy_excluded_family_cannot_be_content_searchable():
    files = [*FILES, 'docs/session-state/current.md']
    data = base()
    data['entries'].append(family('routers', ['docs/session-state/**']))
    assert errors_with(check(data, files), 'content_searchable must be false')
    data['entries'][-1]['content_searchable'] = False
    assert check(data, files).ok


def test_privacy_follows_the_paths_a_family_owns_not_its_glob_text():
    # An innocuous glob that owns a private subdirectory.
    files = [*FILES, 'docs/guide/private/report.md']
    report = check(base(), files)
    assert errors_with(report, "guide: owns 1 inventory-excluded path(s) such as 'docs/guide/private/report.md'")
    # A more specific private family takes the path, so the parent family is clean again.
    data = base()
    data['entries'].append(family('guide-private', ['docs/guide/private/**'], content_searchable=False))
    assert check(data, files).ok
    # Every excluded component counts, not only session-state and private.
    data = base()
    assert errors_with(check(data, [*FILES, 'docs/guide/cache/blob.json']), 'content_searchable must be false')


def test_privacy_wildcard_glob_over_session_state_is_caught():
    files = [*FILES, 'docs/session-state/current.md']
    data = base()
    data['entries'].append(family('sessions', ['docs/session-*/**']))
    errors = check(data, files).errors
    assert any('sessions: owns 1 inventory-excluded path(s)' in e for e in errors)
    data['entries'][-1]['paths'] = ['docs/sess?on-state/*.md']
    assert errors_with(check(data, files), 'sessions: owns 1 inventory-excluded path(s)')


def test_data_store_producers_must_be_tracked():
    store = {'id': 'data-main', 'kind': 'data_store', 'store': ['data/main.db'],
             'producer': ['scripts/build.py'], 'local_only': True, 'purpose': 'Main store',
             'keywords': ['main'], 'lifecycle': 'active', 'owner': 'infra-harness',
             'query': [{'surface': 'sqlite', 'how': 'read-only SQL'}], 'content_searchable': False}
    data = base()
    data['entries'].append(store)
    report = check(data)
    assert report.ok and report.data_stores == 1
    broken = copy.deepcopy(data)
    broken['entries'][-1]['producer'] = ['scripts/missing.py']
    assert errors_with(check(broken), "producer 'scripts/missing.py' is not a tracked path")
    broken['entries'][-1]['producer'] = []
    assert errors_with(check(broken), 'needs producer_note')
    files = [*FILES, 'data/main/part.jsonl', 'data/empty/.gitkeep']
    tracked = copy.deepcopy(data)
    tracked['entries'][-1]['store'] = ['data/main/']
    assert errors_with(check(tracked, files), 'local_only is true but 1 store files are tracked')
    tracked['entries'][-1]['local_only'] = False
    assert check(tracked, files).ok
    tracked['entries'][-1]['store'] = ['data/empty/']
    assert errors_with(check(tracked, files), 'local_only is false but no store file is tracked')
    broken['entries'][-1]['store'] = ['/abs/main.db']
    assert errors_with(check(broken), 'schema: entries/3')


def test_uncovered_path_gets_a_pasteable_stub_that_covers_it():
    files = [*FILES, 'docs/newfam/x.md', 'docs/newfam/deep/y.md', 'docs/loose.md']
    data = base()
    report = check(data, files)
    assert report.uncovered == ['docs/loose.md', 'docs/newfam/deep/y.md', 'docs/newfam/x.md']
    text = suggest(report, data, ROOTS)
    assert 'nearest family: none' in text  # nothing shares a literal prefix below the root
    stubs = yaml.safe_load(text)
    assert sorted(s['paths'][0] for s in stubs) == ['docs/loose.md', 'docs/newfam/**']
    # Stubs are placeholders until a human fills the purpose.
    assert errors_with(check(catalogue(*data['entries'], *stubs), files), 'purpose is still a TODO placeholder')
    for stub in stubs:
        stub['purpose'] = f"Documents under {stub['paths'][0]}"
    filled = check(catalogue(*data['entries'], *stubs), files)
    assert filled.ok, filled.errors
    assert filled.resolved['docs/newfam/deep/y.md'][0] == 'newfam'


def test_stub_inherits_owner_of_the_nearest_family():
    files = [*FILES, 'docs/guide/new/z.md']
    data = base()
    data['entries'][1]['paths'] = ['docs/guide/*.md', 'docs/guide/old/**']
    data['entries'][1]['owner'] = 'docs-knowledge'
    report = check(data, files)
    assert report.uncovered == ['docs/guide/new/z.md']
    [stub] = yaml.safe_load(suggest(report, data, ROOTS))
    assert stub['owner'] == 'docs-knowledge' and stub['paths'] == ['docs/guide/new/**']


def test_stub_for_an_excluded_directory_is_not_content_searchable():
    files = [*FILES, 'docs/vault/x.md', 'docs/vault/private/y.md', 'docs/session-state/z.md', 'docs/open/w.md']
    data = base()
    report = check(data, files)
    stubs = {s['paths'][0]: s for s in yaml.safe_load(suggest(report, data, ROOTS))}
    assert {k: s['content_searchable'] for k, s in stubs.items()} == {
        'docs/vault/**': False, 'docs/session-state/**': False, 'docs/open/**': True}
    for stub in stubs.values():
        stub['purpose'] = f"Documents under {stub['paths'][0]}"
    filled = check(catalogue(*data['entries'], *stubs.values()), files)
    assert filled.ok, filled.errors


def test_glob_translation():
    assert glob_regex('docs/**/x.md').match('docs/x.md')
    assert glob_regex('docs/**/x.md').match('docs/a/b/x.md')
    assert not glob_regex('docs/*.md').match('docs/a/x.md')
    assert glob_regex('docs/a/**').match('docs/a/b/c')
    assert not glob_regex('docs/a/**').match('docs/a')
    assert glob_regex('docs/v?.md').match('docs/v2.md')
    assert not glob_regex('docs/v?.md').match('docs/v/.md')
    # Regex metacharacters are literals in the dialect.
    assert glob_regex('docs/a+(b).md').match('docs/a+(b).md')
    assert not glob_regex('docs/a+(b).md').match('docs/aa(b).md')
    assert not is_catch_all('docs/guide/*')
    assert not is_catch_all('curriculum/l2-uk-en/evidence/a1/**')
    assert is_catch_all('curriculum/l2-uk-en/evidence/**')


@pytest.mark.parametrize('pattern', ['docs/guide/[!]].md', 'docs/guide/[a-z].md', 'docs/[a-z]*/**',
                                     'docs/{guide,other}/*.md', 'docs/guide/{a}.md'])
def test_character_classes_and_braces_are_schema_errors(pattern):
    data = base()
    data['entries'][1]['paths'] = [pattern]
    errors = check(data).errors
    assert errors == [f'schema: entries/1/paths/0: {pattern!r} is not in the catalogue glob dialect: '
                      'character classes ([...]), braces ({...}) and control characters are not in the '
                      'catalogue glob dialect; list each path or use * and ?']


@pytest.mark.parametrize('pattern', ['docs/**', 'docs/*', 'docs/*/**', 'docs/a*/**', 'docs/*.md', 'docs/?uide/**',
                                     'registry/**/*', '**', '*/guide/*.md'])
def test_glob_without_a_literal_first_segment_below_its_root_is_a_catch_all(pattern):
    data = base()
    data['entries'].append(family('everything', [pattern]))
    assert errors_with(check(data), f"glob {pattern!r} is a catch-all")


def test_store_names_use_the_same_dialect():
    data = base()
    data['entries'].append(store_entry('data-main', store=['data/[ab].db']))
    assert errors_with(check(data), "'data/[ab].db' is not in the catalogue glob dialect")
    # Without the schema the validator still rejects it as a typed error.
    assert errors_with(validate(data, {}, FILES, OWNERS, ROOTS), "store 'data/[ab].db' is not in the catalogue")
    # '*' stays inside one segment for store names too.
    files = [*FILES, 'data/lexicon/a.json', 'data/lexicon/sub/b.json']
    data['entries'][-1].update(store=['data/lexicon/*.json'], local_only=True)
    assert errors_with(check(data, files), 'local_only is true but 1 store files are tracked')


# Odd globs: none may raise, and the schema and the code must agree on the dialect.
ODD_GLOBS = [
    '', '/', '//', 'docs', 'docs/', 'docs//a.md', '/docs/a.md', 'docs/./a.md', 'docs/../a.md',
    'docs/guide/..', 'docs/guide/[!]].md', 'docs/guide/[a-z].md', 'docs/guide/[', 'docs/guide/]',
    'docs/{a,b}.md', 'docs/{a', 'docs/a}', 'docs/guide/***', 'docs/guide/**x', 'docs/guide/x**',
    'docs/guide/**/**', 'docs/guide/a.md\n', 'docs/guide/\x00', 'docs/guide/\x7f', 'docs/guide/\x85', 'docs/guide/\x9f',
    'docs/guide/\xa0', 'docs/guide/\\',
    'docs/guide/(a|b).md', 'docs/guide/a+.md', 'docs/guide/^a$.md', 'docs/guide/.*', 'docs/guide/?',
    'docs/guide/??*?', 'docs/guide/a.md#x', 'docs/guide/ü.md', 'docs/guide/ a.md', 'docs/guide/ ',
    'docs/guide/%2e%2e', 'docs/guide/~', 'docs/guide/$HOME', '**', '*', '?', 'docs/**', 'docs/*/**',
    'registry/**/*', 'curriculum/l2-uk-en/evidence/**', 'docs/guide/*.md', 'docs/guide/old/**',
    'scripts/*.py', 'docs/guide/a.md/', 'docs/guide/.hidden/**', 'docs/guide/...',
]


@pytest.mark.parametrize('pattern', ODD_GLOBS)
def test_validator_is_total_and_schema_agrees_with_code(pattern):
    assert len(ODD_GLOBS) >= 30
    for schema in (SCHEMA, {}):  # {} bypasses the schema to reach the code-level checks
        data = base()
        data['entries'][1]['paths'] = [pattern, 'docs/guide/*.md']
        report = validate(data, schema, FILES, OWNERS, ROOTS)  # must not raise
        assert isinstance(report.errors, list)
    in_schema = Draft202012Validator(SCHEMA['$defs']['glob']).is_valid(pattern)
    assert in_schema == (glob_error(pattern) is None), glob_error(pattern)
    if in_schema:
        glob_regex(pattern)
    else:
        with pytest.raises(ValueError, match='not in the catalogue glob dialect'):
            glob_regex(pattern)
        bypassed = base()
        bypassed['entries'][1]['paths'] = [pattern]
        assert errors_with(validate(bypassed, {}, FILES, OWNERS, ROOTS), 'not in the catalogue glob dialect')


@pytest.mark.parametrize('name', ['data/a.db', 'data/a/', 'data/a/*.json', 'data/a.db.bak.*', 'data/[a].db',
                                  'data/{a,b}.db', 'data//a.db', 'data/../x', 'data/a/**x', 'data/a.db\n',
                                  'data/a\x85.db'])
def test_store_name_schema_agrees_with_code(name):
    in_schema = Draft202012Validator(SCHEMA['$defs']['storeName']).is_valid(name)
    assert in_schema == (glob_error(name, subtree=True) is None)


# ------------------------------------------------------------------ CLI on a real Git fixture

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, timeout=30)


def make_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    git(root, 'config', 'user.name', 'Fixture')
    files = {
        'docs/knowledge/catalogue.schema.json': json.dumps(SCHEMA),
        'docs/knowledge/catalogue.yaml': yaml.safe_dump(catalogue(
            family('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
            family('guide', ['docs/guide/**']))),
        'docs/guide/a.md': '# A\n',
        'scripts/config/issue_streams.yaml': 'streams:\n  docs-knowledge: {epics: [1]}\n',
        'scripts/config/area_assignments.yaml': 'assignments:\n  infra-harness: {slots: []}\n',
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'fixture')
    return root


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path)


def test_cli_passes_clean_tree_and_reads_only_the_index(repo, capsys):
    (repo / 'docs/untracked.md').write_text('not in the index\n')
    assert main(['check', '--repo', str(repo)]) == 0
    assert 'uncovered 0; errors 0' in capsys.readouterr().out
    assert coverage(repo).denominator == 3


def test_cli_fails_on_uncovered_path_and_suggests_stub(repo, capsys):
    (repo / 'docs/new/x.md').parent.mkdir()
    (repo / 'docs/new/x.md').write_text('# X\n')
    git(repo, 'add', 'docs/new/x.md')
    assert main(['check', '--repo', str(repo), '--suggest']) == 1
    out = capsys.readouterr().out
    assert 'UNCOVERED docs/new/x.md' in out
    assert "- docs/new/**" in out and 'id: new' in out
    assert main(['check', '--repo', str(repo), '--report-only']) == 0
    capsys.readouterr()
    assert main(['check', '--repo', str(repo), '--json']) == 1
    assert json.loads(capsys.readouterr().out)['uncovered'] == ['docs/new/x.md']


def test_cli_reports_unreadable_catalogue(repo, capsys):
    (repo / 'docs/knowledge/catalogue.yaml').write_text('a: 1\na: 2\n')
    assert main(['check', '--repo', str(repo)]) == 3
    assert 'could not run' in capsys.readouterr().out


@pytest.mark.parametrize('line, marker', [
    ('# Draft — Ingest a source', 'draft-heading'),
    ('## [DRAFT] notes', 'draft-heading'),
    ('> **Status:** Draft (issue #1)', 'status-draft'),
    ('status: "draft"', 'status-draft'),
    ('**Status**: Proposed', 'status-proposed'),
    ('lifecycle: draft', 'lifecycle-draft'),
    ('This page is a work in progress.', 'work-in-progress'),
    ('A proposal for the API.', 'proposal'),
])
def test_draft_markers_match_their_forms(line, marker):
    assert [name for name, pattern in DRAFT_MARKERS if pattern.search(line) and name == marker] == [marker]


@pytest.mark.parametrize('line', ['**Original status:** PROPOSED (awaiting sign-off)',
                                  '**Original status:** draft', 'The draft was merged.', 'Status: active'])
def test_superseded_status_lines_are_not_draft_status_markers(line):
    status_markers = {'status-draft', 'status-proposed', 'draft-heading', 'lifecycle-draft'}
    assert not [name for name, pattern in DRAFT_MARKERS if name in status_markers and pattern.search(line)]


def test_draft_scan_reports_both_kinds_of_mismatch(repo, capsys):
    (repo / 'docs/guide/wip.md').write_text('# Draft — not yet approved\n')
    (repo / 'docs/guide/late.md').write_text('\n' * 30 + 'Status: draft\n')  # beyond the scanned head
    (repo / 'docs/guide/logo.png').write_bytes(b'\x89PNG\x00draft')
    data = yaml.safe_load((repo / 'docs/knowledge/catalogue.yaml').read_text())
    data['entries'].append(family('guide-drafts', ['docs/guide/late.md'], lifecycle='draft'))
    (repo / 'docs/knowledge/catalogue.yaml').write_text(yaml.safe_dump(data))
    git(repo, 'add', '.')
    scan = draft_scan(repo, coverage(repo))
    assert scan['active_with_marker'] == {'docs/guide/wip.md': ['draft-heading']}
    assert scan['draft_without_marker'] == ['docs/guide/late.md']
    assert scan['binary_or_missing'] == 1
    assert main(['draft-scan', '--repo', str(repo)]) == 0
    out = capsys.readouterr().out
    assert 'ACTIVE WITH MARKER docs/guide/wip.md (draft-heading)' in out
    assert 'DRAFT WITHOUT MARKER docs/guide/late.md' in out
    assert main(['draft-scan', '--repo', str(repo), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['with_marker'] == 1


# ------------------------------------------------------------------ YAML shapes: the loader is total

def fixture_text(paths_yaml='["docs/guide/**"]'):
    """The CLI fixture catalogue as JSON (a YAML subset) with the guide paths replaced verbatim."""
    text = json.dumps(catalogue(family('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
                                family('guide', ['__GUIDE__'])))
    return text.replace('["__GUIDE__"]', paths_yaml)


def run_check(repo, tmp_path, text, capsys):
    path = tmp_path / 'candidate.yaml'
    path.write_bytes(text if isinstance(text, bytes) else text.encode('utf-8'))
    status = main(['check', '--repo', str(repo), '--catalogue', str(path), '--json'])
    return status, json.loads(capsys.readouterr().out)


BILLION_LAUGHS = 'a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]\n' + ''.join(
    f'{chr(98 + i)}: &{chr(98 + i)} [*{chr(97 + i)},*{chr(97 + i)},*{chr(97 + i)},*{chr(97 + i)},'
    f'*{chr(97 + i)},*{chr(97 + i)},*{chr(97 + i)},*{chr(97 + i)},*{chr(97 + i)}]\n' for i in range(8))


@pytest.mark.parametrize('text, code', [
    (fixture_text('[&a [*a], &b [*b]]'), 'anchor'),  # recursive aliases (review case 1)
    (fixture_text('[' * 10_000 + ']' * 10_000), 'too_deep'),  # deep flow nesting (review case 2)
    ('entries:\n' + '- ' * 10_000 + 'x\n', 'too_deep'),  # deep block nesting on one line
    (BILLION_LAUGHS, 'anchor'),
    ('entries: *undefined\n', 'alias'),  # an alias is rejected before it is resolved
    ('base: {a: 1}\nentry:\n  <<: {a: 1}\n', 'merge_key'),
    ('entries: !!python/object/apply:os.system ["true"]\n', 'tag'),
    ('entries: !custom x\n', 'tag'),
    ('schema_version: !!int 1\n', 'tag'),
    ('entries: []\nentries: []\n', 'duplicate_key'),
    ('1: x\n', 'non_string_key'),
    ('~: x\n', 'non_string_key'),
    ('? [a]\n: x\n', 'non_string_key'),
    ('- just\n- a list\n', 'not_mapping'),
    ('just a scalar\n', 'not_mapping'),
    ('', 'not_mapping'),
    ('a: 1\n---\nb: 2\n', 'syntax'),
    ('a: [1, 2\n', 'syntax'),
    (b'a: \xff\n', 'encoding'),
    ('[' + 'a,' * MAX_CATALOGUE_NODES + 'a]', 'too_many_nodes'),
    ('a: 2026-99-99\n', 'scalar'),  # a timestamp-shaped scalar with no such date
    ('a: ' + '1' * 5_000 + '\n', 'scalar'),  # over Python's integer-string digit limit
], ids=['recursive-aliases', 'deep-flow', 'deep-block', 'billion-laughs', 'alias', 'merge-key', 'python-tag',
        'custom-tag', 'core-tag', 'duplicate-key', 'int-key', 'null-key', 'sequence-key', 'list-root',
        'scalar-root', 'empty', 'two-documents', 'unclosed', 'not-utf8', 'too-many-nodes', 'bad-date',
        'huge-int'])
def test_catalogue_outside_the_yaml_subset_is_a_typed_rejection(repo, tmp_path, capsys, text, code):
    raw = text if isinstance(text, bytes) else text.encode('utf-8')
    with pytest.raises(CatalogueLoadError) as caught:
        parse(raw)
    assert caught.value.code == code
    status, out = run_check(repo, tmp_path, raw, capsys)
    assert status == 3
    assert out == {'error': {'kind': 'catalogue_rejected', 'code': code, 'message': out['error']['message']}}
    assert out['error']['message'].startswith(f'{code}: ')


def test_oversized_catalogue_is_rejected_after_a_bounded_read(repo, tmp_path, capsys):
    path = tmp_path / 'huge.yaml'
    with path.open('wb') as handle:  # 50 MB of an otherwise valid comment
        handle.write(b'#' * (50 * 1024 * 1024))
    reads = []
    original = Path.open

    def recording_open(self, *args, **kwargs):
        handle = original(self, *args, **kwargs)
        if self == path:
            read = handle.read
            handle.read = lambda size=-1: reads.append(size) or read(size)  # type: ignore[method-assign]
        return handle
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, 'open', recording_open)
        assert main(['check', '--repo', str(repo), '--catalogue', str(path), '--json']) == 3
    assert json.loads(capsys.readouterr().out)['error']['code'] == 'too_large'
    assert reads and all(0 <= size <= MAX_CATALOGUE_BYTES + 1 for size in reads)


def test_bounds_admit_the_repository_catalogue_with_headroom():
    raw = (REPO / 'docs/knowledge/catalogue.yaml').read_bytes()
    assert len(raw) * 10 < MAX_CATALOGUE_BYTES
    depth = nodes = top = 0
    for event in yaml.parse(raw.decode('utf-8')):
        nodes += isinstance(event, (yaml.ScalarEvent, yaml.SequenceStartEvent, yaml.MappingStartEvent))
        depth += isinstance(event, (yaml.SequenceStartEvent, yaml.MappingStartEvent))
        depth -= isinstance(event, (yaml.SequenceEndEvent, yaml.MappingEndEvent))
        top = max(top, depth)
    assert nodes * 10 < MAX_CATALOGUE_NODES and top * 2 < MAX_CATALOGUE_DEPTH
    assert parse(raw)['schema_version'] == 1


def test_depth_bound_is_exact():
    nested = lambda n: '[' * n + ']' * n  # noqa: E731
    assert parse(f'a: {nested(MAX_CATALOGUE_DEPTH - 1)}'.encode())  # the root mapping is one level
    with pytest.raises(CatalogueLoadError, match='too_deep'):
        parse(f'a: {nested(MAX_CATALOGUE_DEPTH)}'.encode())


@pytest.mark.parametrize('paths_yaml', ['null', '[null]', '"docs/guide/**"', '{"a": 1}', '[["docs/guide/**"]]',
                                        '[1]', '[true]', '[2026-10-01]'])
def test_wrong_shapes_that_parse_are_schema_errors(repo, tmp_path, capsys, paths_yaml):
    status, out = run_check(repo, tmp_path, fixture_text(paths_yaml), capsys)
    assert status == 1
    assert out['errors'] and all(e.startswith('schema: entries/1') for e in out['errors'])


@pytest.mark.parametrize('replace, where', [
    (('"entries": [', '"entries": [null, '), 'schema: entries/0'),
    (('"entries": [', '"entries": ["an entry", '), 'schema: entries/0'),
    (('"residual": []', '"residual": [null]'), 'schema: residual/0'),
    (('"residual": []', '"residual": null'), 'schema: residual'),
    (('"schema_version": 1', '"schema_version": null'), 'schema: schema_version'),
])
def test_null_and_scalar_entries_are_schema_errors_without_a_crash(repo, tmp_path, capsys, replace, where):
    text = fixture_text()
    assert replace[0] in text
    (repo / 'data').mkdir()  # store reconciliation must not run on a schema-invalid catalogue
    status, out = run_check(repo, tmp_path, text.replace(*replace), capsys)
    assert status == 1
    assert any(e.startswith(where) for e in out['errors']), out['errors']
    assert out['local_stores'] is None


@pytest.mark.parametrize('as_json', [True, False])
def test_unexpected_failure_is_a_typed_internal_error_not_a_traceback(repo, capsys, monkeypatch, as_json):
    def explode(*_args, **_kwargs):
        raise RecursionError('maximum recursion depth exceeded')
    monkeypatch.setattr(catalogue_module, 'validate', explode)
    args = ['check', '--repo', str(repo)] + (['--json'] if as_json else [])
    assert main(args) == 4
    monkeypatch.setattr(catalogue_module, 'draft_scan', explode)
    assert main(['draft-scan', '--repo', str(repo)] + (['--json'] if as_json else [])) == 4
    captured = capsys.readouterr()
    assert 'Traceback' not in captured.out + captured.err
    if as_json:
        first, second = (json.loads(part) for part in captured.out.replace('}\n{', '}\0{').split('\0'))
        assert first == second == {'error': {'kind': 'internal_error', 'code': 'RecursionError',
                                             'message': 'maximum recursion depth exceeded'}}
    else:
        assert captured.out.count('could not run (internal_error): RecursionError') == 2


# ------------------------------------------------------------------ privacy boundary for body reads

SENTINEL = 'docs/guide/sub/private/sentinel.md'


def add_and_catalogue(repo, files, *entries):
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding='utf-8')
    data = yaml.safe_load((repo / 'docs/knowledge/catalogue.yaml').read_text())
    data['entries'].extend(entries)
    (repo / 'docs/knowledge/catalogue.yaml').write_text(yaml.safe_dump(data))
    git(repo, 'add', '.')


def recorded_blob_reads(monkeypatch):
    """Every path -> object ID the gated reader requests."""
    requested = {}
    original = catalogue_module._index_blobs

    def recording(repo, objects):
        requested.update(objects)
        return original(repo, objects)
    monkeypatch.setattr(catalogue_module, '_index_blobs', recording)
    return requested


def test_draft_scan_never_reads_an_excluded_path_of_a_valid_private_family(repo, capsys, monkeypatch):
    add_and_catalogue(repo, {SENTINEL: '# Draft — private sentinel\n', 'docs/guide/open.md': '# Draft\n'},
                      family('guide-private', ['docs/guide/sub/private/**'], content_searchable=False))
    assert main(['check', '--repo', str(repo)]) == 0  # the catalogue is valid
    capsys.readouterr()
    requested = recorded_blob_reads(monkeypatch)
    scan = draft_scan(repo, coverage(repo))
    assert SENTINEL not in requested and 'docs/guide/open.md' in requested
    assert scan['skipped_private'] == 1
    assert scan['active_with_marker'] == {'docs/guide/open.md': ['draft-heading']}
    requested.clear()
    assert main(['draft-scan', '--repo', str(repo), '--json']) == 0
    out = capsys.readouterr().out
    assert SENTINEL not in requested and 'sentinel' not in out
    assert json.loads(out)['skipped_private'] == 1


def test_excluded_path_stays_unread_even_when_its_family_wrongly_claims_searchable(repo, monkeypatch):
    add_and_catalogue(repo, {SENTINEL: '# Draft — private sentinel\n'})  # owned by the searchable 'guide'
    report = coverage(repo)
    assert any('content_searchable must be false' in e for e in report.errors)
    requested = recorded_blob_reads(monkeypatch)
    scan = draft_scan(repo, report)
    assert SENTINEL not in requested and scan['skipped_private'] == 1 and scan['with_marker'] == 0


def test_non_searchable_family_is_unread_without_an_excluded_component(repo, monkeypatch):
    add_and_catalogue(repo, {'docs/guide/notes/n.md': 'status: draft\n'},
                      family('guide-notes', ['docs/guide/notes/**'], lifecycle='draft', content_searchable=False))
    report = coverage(repo)
    assert report.ok, report.errors
    requested = recorded_blob_reads(monkeypatch)
    scan = draft_scan(repo, report)
    assert 'docs/guide/notes/n.md' not in requested and scan['skipped_private'] == 1
    assert scan['draft_without_marker'] == []  # an unread path is never reported as lacking a marker


def test_body_gate_fails_closed():
    data = base()
    data['entries'].append(family('guide', ['docs/guide/old/**'], content_searchable=False))  # duplicate id
    report = check(data)
    assert 'guide' not in report.searchable_entries
    assert not body_readable(report, 'docs/guide/a.md')
    assert not body_readable(report, 'docs/unknown.md')  # unresolved
    assert body_readable(check(base()), 'docs/guide/a.md')


def test_only_the_gated_reader_reads_blob_bodies():
    tree = ast.parse(Path(catalogue_module.__file__).read_text(encoding='utf-8'))
    callers = [fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
               for call in ast.walk(fn) if isinstance(call, ast.Call)
               and getattr(call.func, 'id', None) == '_index_blobs']
    # read_heads gates document bodies with body_readable; store_literals reads scripts/ only and
    # withholds control-character and inventory-excluded paths before requesting any blob.
    assert sorted(callers) == ['read_heads', 'store_literals']
    # Git commands that print blob contents appear only in the gated reader and in
    # owner_keys, which reads the two fixed owner registries, never a catalogued path.
    readers = [fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
               for node in ast.walk(fn) if isinstance(node, ast.Constant) and node.value in ('cat-file', 'show')]
    assert sorted(readers) == ['_index_blobs', 'owner_keys']


# ------------------------------------------------------------------ pathnames are data, never protocol text

def blob_oid(repo, text):
    return subprocess.run(['git', '-C', str(repo), 'hash-object', '--stdin'], input=text.encode('utf-8'),
                          capture_output=True, check=True, timeout=30).stdout.decode('ascii').strip()


CONTROL_NAMES = ['docs/guide/a\nb.md', 'docs/guide/a\rb.md', 'docs/guide/a\tb.md', 'docs/guide/a\x01b.md',
                 'docs/guide/a\x1bb.md', 'docs/guide/a\x7fb.md', 'docs/guide/a\x85b.md', 'docs/guide/a\x9fb.md']
SAFE_NAMES = ['docs/guide/-rf.md', 'docs/guide/--help', 'docs/guide/with space.md', 'docs/guide/ґанок.md',
              'docs/guide/a\\000b.md', 'docs/guide/a\\nb.md', 'docs/guide/%00.md', "docs/guide/it's \"q\".md",
              'docs/guide/:colon.md', 'docs/guide/nbsp .md']


def test_newline_in_a_tracked_name_cannot_smuggle_a_private_blob_into_a_public_read(repo, capsys, monkeypatch):
    # The review reproduction: a tracked name '<public path>\n<private blob id>'.
    private_text = '# Draft — private sentinel\n'
    private_oid = blob_oid(repo, private_text)
    injected = f'docs/guide/000.md\n{private_oid}'
    add_and_catalogue(repo, {SENTINEL: private_text, injected: '# Public\n', 'docs/guide/z.md': '# Public z\n'},
                      family('guide-private', ['docs/guide/sub/private/**'], content_searchable=False))
    assert injected in index_entries(repo)  # Git really tracks the hostile name
    report = coverage(repo)
    assert report.errors == [control_path_error(injected)]
    assert repr(injected) in report.errors[0] and not CONTROL_CHARS.search(report.errors[0])
    assert injected not in report.resolved and injected not in report.uncovered
    requested = recorded_blob_reads(monkeypatch)
    scan = draft_scan(repo, report)
    assert private_oid not in requested.values() and SENTINEL not in requested and injected not in requested
    assert 'docs/guide/z.md' in requested
    assert scan['with_marker'] == 0 and scan['active_with_marker'] == {}
    assert main(['check', '--repo', str(repo)]) == 1
    out = capsys.readouterr().out
    assert f'ERROR {control_path_error(injected)}' in out
    assert not any(line.startswith(private_oid) for line in out.splitlines())
    assert main(['draft-scan', '--repo', str(repo), '--json']) == 0
    out = capsys.readouterr().out
    assert 'sentinel' not in out and json.loads(out)['with_marker'] == 0


@pytest.mark.parametrize('name', CONTROL_NAMES[:1] + SAFE_NAMES)
def test_blob_reader_answers_each_path_with_its_own_index_blob(repo, name):
    # Below the validator: even a newline name read directly cannot shift another path's response.
    private_text = '# Draft — private sentinel\n'
    private_oid = blob_oid(repo, private_text)
    hostile = name.replace('\nb', f'\n{private_oid}')
    files = {SENTINEL: private_text, hostile: f'body of {hostile!r}\n', 'docs/guide/z.md': 'body of z\n'}
    add_and_catalogue(repo, files)
    entries = index_entries(repo)
    objects = {p: entries[p].oid for p in (hostile, 'docs/guide/z.md')}
    blobs = catalogue_module._index_blobs(repo, objects)
    assert blobs == {p: files[p].encode('utf-8') for p in objects}


@pytest.mark.parametrize('name', SAFE_NAMES)
def test_unusual_but_safe_names_are_catalogued_and_read(repo, name):
    add_and_catalogue(repo, {name: f'# Draft {name!r}\n'})
    report = coverage(repo)
    assert report.ok, report.errors
    assert report.resolved[name] == ('guide', 'active')
    heads, withheld = read_heads(repo, report, [name, 'docs/guide/a.md'])
    assert withheld == 0 and heads == {name: f'# Draft {name!r}', 'docs/guide/a.md': '# A'}


@pytest.mark.parametrize('name', CONTROL_NAMES)
def test_control_characters_in_a_tracked_name_are_an_error_and_never_catalogued(repo, name):
    add_and_catalogue(repo, {name: '# Draft\n'})
    report = coverage(repo)
    assert report.errors == [control_path_error(name)]
    assert not CONTROL_CHARS.search(report.errors[0])  # the path is printed escaped
    assert name not in report.resolved and name not in report.uncovered
    assert report.denominator == 3
    heads, withheld = read_heads(repo, report, [name])
    assert heads == {} and withheld == 1


@pytest.mark.parametrize('char', ['\n', '\r', '\t', '\x00', '\x01', '\x1f', '\x7f', '\x80', '\x85', '\x9f'])
def test_validator_drops_control_paths_everywhere(char):
    hostile = [f'docs/guide/x{char}y.md', f'scripts/x{char}y.py']  # inside and outside the roots
    report = check(base(), FILES + hostile)
    assert report.errors == [control_path_error(p) for p in hostile]
    assert report.denominator == 5 and not set(hostile) & set(report.resolved)
    data = base()
    data['entries'][1]['entrypoints'] = [{'topic': 'guide', 'path': hostile[0]}]
    assert any(e.startswith('schema: entries/1/entrypoints/0/path') for e in check(data, FILES + hostile).errors)


def test_validator_accepts_non_control_unicode():
    names = ['docs/guide/ґанок.md', 'docs/guide/nbsp .md', 'docs/guide/  .md']
    report = check(base(), FILES + names)
    assert report.ok, report.errors
    assert all(report.resolved[n] == ('guide', 'active') for n in names)


def test_body_gate_refuses_a_resolved_control_path():
    report = Report(resolved={'docs/guide/a\nb.md': ('guide', 'active'), 'docs/guide/a.md': ('guide', 'active')},
                    searchable_entries={'guide'})
    assert not body_readable(report, 'docs/guide/a\nb.md')
    assert body_readable(report, 'docs/guide/a.md')


# ------------------------------------------------------------------ control characters in catalogue strings

# Python's regular-expression '$' also matches before a final newline, so each layer
# is tested alone: the schema (its patterns end with (?![\s\S])) and the code walk.
CONTROL_SUFFIXES = ['\n', '\r', '\t', '\x00', '\x7f', '\x85', '\x9f']
CLI_FILES = ['docs/guide/a.md', 'docs/knowledge/catalogue.schema.json', 'docs/knowledge/catalogue.yaml',
             'scripts/config/area_assignments.yaml', 'scripts/config/issue_streams.yaml']
PRODUCER = 'scripts/config/issue_streams.yaml'


def cli_catalogue():
    """The CLI fixture repository's own catalogue plus a data store: clean against CLI_FILES."""
    return catalogue(family('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
                     family('guide', ['docs/guide/**']), store_entry('store', producer=[PRODUCER]))


def guide(data):
    return data['entries'][1]


# field kind -> (reported location, mutation appending the suffix to one string)
FIELD_KINDS = {
    'id': ('entries/1/id', lambda d, c: guide(d).update(id='guide' + c)),
    'paths item': ('entries/1/paths/0', lambda d, c: guide(d).update(paths=['docs/guide/**' + c])),
    'purpose': ('entries/1/purpose', lambda d, c: guide(d).update(purpose='guide documents' + c)),
    'keyword': ('entries/1/keywords/0', lambda d, c: guide(d).update(keywords=['guide' + c])),
    'owner': ('entries/1/owner', lambda d, c: guide(d).update(owner='infra-harness' + c)),
    'entrypoint path': ('entries/1/entrypoints/0/path', lambda d, c: guide(d).update(
        entrypoints=[{'topic': 'guide start', 'path': 'docs/guide/a.md' + c}])),
    'entrypoint fragment': ('entries/1/entrypoints/0/path', lambda d, c: guide(d).update(
        entrypoints=[{'topic': 'guide start', 'path': 'docs/guide/a.md#heading' + c}])),
    'entrypoint topic': ('entries/1/entrypoints/0/topic', lambda d, c: guide(d).update(
        entrypoints=[{'topic': 'guide start' + c, 'path': 'docs/guide/a.md'}])),
    'superseded_by path fragment': ('entries/1/superseded_by', lambda d, c: guide(d).update(
        lifecycle='superseded', superseded_by=f'{PRODUCER}#heading{c}')),
    'superseded_by id': ('entries/1/superseded_by', lambda d, c: guide(d).update(
        lifecycle='superseded', superseded_by='id:knowledge' + c)),
    'overrides path': ('entries/1/overrides/0/path', lambda d, c: guide(d).update(
        overrides=[{'path': 'docs/guide/a.md' + c, 'lifecycle': 'archive', 'evidence': 'kept for history'}])),
    'override superseded_by': ('entries/1/overrides/0/superseded_by', lambda d, c: guide(d).update(
        overrides=[{'path': 'docs/guide/a.md', 'lifecycle': 'superseded', 'superseded_by': PRODUCER + c,
                    'evidence': 'replaced by config'}])),
    'query how': ('entries/1/query/0/how', lambda d, c: guide(d).update(
        query=[{'surface': 'git_grep', 'how': 'git grep -n -F x -- docs/guide' + c}])),
    'store name': ('entries/2/store/0', lambda d, c: d['entries'][2].update(store=['data/main.db' + c])),
    'producer': ('entries/2/producer/0', lambda d, c: d['entries'][2].update(producer=[PRODUCER + c])),
}


def mutated(kind, suffix):
    data = cli_catalogue()
    FIELD_KINDS[kind][1](data, suffix)
    return data


def control_errors_at(report, where, char):
    return [e for e in report.errors if e.startswith(f'control: {where}: ') and f'U+{ord(char):04X}' in e]


@pytest.mark.parametrize('kind', FIELD_KINDS)
def test_every_field_kind_is_clean_without_a_control(kind):
    assert check(mutated(kind, ''), CLI_FILES).ok, check(mutated(kind, ''), CLI_FILES).errors


@pytest.mark.parametrize('suffix', CONTROL_SUFFIXES)
@pytest.mark.parametrize('kind', FIELD_KINDS)
def test_control_in_any_field_kind_fails_the_schema_and_the_code_walk_alone(kind, suffix):
    data = mutated(kind, suffix)
    where = FIELD_KINDS[kind][0]
    assert not Draft202012Validator(SCHEMA).is_valid(data)  # the schema alone rejects it
    for schema in (SCHEMA, {}):  # {} leaves the code walk alone
        report = validate(data, schema, CLI_FILES, OWNERS, ROOTS)
        assert control_errors_at(report, where, suffix), report.errors
        assert not report.ok and not report.schema_ok
        assert not any(CONTROL_CHARS.search(e) for e in report.errors)  # values are printed escaped


@pytest.fixture(scope='module')
def shared_repo(tmp_path_factory):
    root = make_repo(tmp_path_factory.mktemp('controls'))
    (root / 'data').mkdir()  # store reconciliation must not run on a catalogue with a control
    assert sorted(catalogue_module.tracked_files(root)) == CLI_FILES
    return root


@pytest.mark.parametrize('suffix', ['', *CONTROL_SUFFIXES])
@pytest.mark.parametrize('kind', FIELD_KINDS)
def test_check_json_rejects_a_control_in_every_field_kind(shared_repo, tmp_path, capsys, kind, suffix):
    # Includes both reported cases: an entrypoint and a supersession target ending in '#heading\n'.
    status, out = run_check(shared_repo, tmp_path, json.dumps(mutated(kind, suffix)), capsys)
    if not suffix:
        # Since #9412 PR 2 a superseded Markdown override also needs its in-place markers
        # (front matter and banner), which this fixture's docs/guide/a.md does not carry:
        # exactly those two errors, and nothing else, are reported for that kind.
        marker_only = kind == 'override superseded_by'
        markers = [e for e in out['errors'] if marker_only and e.startswith('docs/guide/a.md: ')
                   and ('lifecycle: superseded' in e or 'missing the banner line' in e)]
        assert (status, len(markers), out['uncovered']) == ((1, 2, []) if marker_only else (0, 0, []))
        assert [e for e in out['errors'] if e not in markers] == []
        return
    assert status == 1
    assert [e for e in out['errors'] if e.startswith(f'control: {FIELD_KINDS[kind][0]}: ')], out['errors']
    assert out['local_stores'] is None


def test_control_in_a_key_or_a_nested_path_is_reported_escaped():
    data = cli_catalogue()
    guide(data)['note\n'] = 'kept\x85'
    report = validate(data, {}, CLI_FILES, OWNERS, ROOTS)
    controls = [e for e in report.errors if e.startswith('control: ')]
    assert controls == [
        "control: entries/1: key 'note\\n' contains control character U+000A; "
        'C0, DEL and C1 controls are not allowed in any catalogue string',
        "control: entries/1/'note\\n': 'kept\\x85' contains control character U+0085; "
        'C0, DEL and C1 controls are not allowed in any catalogue string']
    assert not report.schema_ok


def test_control_error_bounds_a_long_value():
    data = cli_catalogue()
    guide(data)['purpose'] = 'x' * 100_000 + '\n'
    [error] = [e for e in check(data, CLI_FILES).errors if e.startswith('control: ')]
    assert len(error) < 400 and "xxx'... contains control character U+000A" in error


def test_no_schema_pattern_uses_a_dollar_anchor():
    patterns = []

    def walk(node):
        if isinstance(node, dict):
            patterns.extend(v for k, v in node.items() if k == 'pattern')
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(SCHEMA)
    assert len(patterns) >= 8
    assert [p for p in patterns if '$' in p] == []


@pytest.mark.parametrize('suffix', CONTROL_SUFFIXES)
@pytest.mark.parametrize('name, sample', [
    ('text', 'abc'), ('repoPath', 'docs/a.md'), ('repoPath', 'docs/a.md#heading'), ('glob', 'docs/a/**'),
    ('storeName', 'data/a.db'), ('storeName', 'data/a/'), ('id', 'ab'), ('owner', 'ab'),
    ('supersessionTarget', 'docs/a.md#heading'), ('supersessionTarget', 'id:ab'),
])
def test_every_string_definition_rejects_a_trailing_control(name, sample, suffix):
    validator = Draft202012Validator(SCHEMA['$defs'][name])
    assert validator.is_valid(sample)
    assert not validator.is_valid(sample + suffix)
    keyword = Draft202012Validator(SCHEMA['$defs']['common']['properties']['keywords'])
    assert keyword.is_valid([sample]) and not keyword.is_valid([sample + suffix])


OID = 'a' * 40
OTHER = 'b' * 40


def fake_cat_file(monkeypatch, stdout):
    calls = []

    def run(*args, **kwargs):
        calls.append(kwargs['input'])
        return SimpleNamespace(stdout=stdout)
    monkeypatch.setattr(catalogue_module.subprocess, 'run', run)
    return calls


@pytest.mark.parametrize('stdout, code', [
    (f'{OTHER} blob 3\nhi\n\n'.encode(), 'response_mismatch'),
    (f'{OID} tree 3\nhi\n\n'.encode(), 'not_blob'),
    (f'{OID} commit 3\nhi\n\n'.encode(), 'not_blob'),
    (f'{OID} ambiguous\n'.encode(), 'not_blob'),
    (f'{OID} blob x\nhi\n'.encode(), 'not_blob'),
    (f'{OID} blob 9\nhi\n'.encode(), 'truncated'),
    (f'{OID} blob 2\nhi!'.encode(), 'truncated'),
    (b'', 'truncated'),
    (f'{OID} blob 2\nhi\n{OTHER} blob 2\nho\n'.encode(), 'trailing_output'),
])
def test_blob_reader_rejects_any_response_that_is_not_the_requested_blob(monkeypatch, stdout, code):
    calls = fake_cat_file(monkeypatch, stdout)
    with pytest.raises(GitProtocolError) as caught:
        catalogue_module._index_blobs(Path('.'), {'docs/guide/a.md': OID})
    assert caught.value.code == code
    assert calls == [f'{OID}\n'.encode()]  # the request is the object ID alone


def test_blob_reader_accepts_missing_and_sha256_objects(monkeypatch):
    long_oid = 'c' * 64
    fake_cat_file(monkeypatch, f'{OID} missing\n{long_oid} blob 2\nhi\n'.encode())
    assert catalogue_module._index_blobs(Path('.'), {'gone.md': OID, 'kept.md': long_oid}) == {'kept.md': b'hi'}


@pytest.mark.parametrize('oid', ['HEAD', ':docs/guide/a.md', OID[:39], f'{OID}\n{OTHER}', OID.upper(),
                                 OID + '0', 'c' * 63, ' ' + OID, ''])
def test_blob_reader_refuses_anything_but_a_full_object_id(monkeypatch, oid):
    calls = fake_cat_file(monkeypatch, b'')
    with pytest.raises(GitProtocolError) as caught:
        catalogue_module._index_blobs(Path('.'), {'docs/guide/a.md': oid})
    assert caught.value.code == 'object_id' and calls == []


@pytest.mark.parametrize('record, code', [
    (f'100644 {OID} 0 docs/a.md\0', 'index_record'),  # no tab before the path
    (f'100644 {OID[:-1]} 0\tdocs/a.md\0', 'index_record'),
    (f'1006x4 {OID} 0\tdocs/a.md\0', 'index_record'),
    (f'100644 {OID}\tdocs/a.md\0', 'index_record'),
    (f'100644 {OID} 2\tdocs/a.md\0', 'unmerged_index'),
])
def test_index_reader_validates_every_record(monkeypatch, record, code):
    monkeypatch.setattr(catalogue_module, 'git', lambda *_args: record.encode())
    with pytest.raises(GitProtocolError) as caught:
        index_entries(Path('.'))
    assert caught.value.code == code


def test_unmerged_index_is_a_typed_unreadable_repository(repo, capsys):
    oid = blob_oid(repo, 'x\n')
    subprocess.run(['git', '-C', str(repo), 'hash-object', '-w', '--stdin'], input=b'x\n', check=True,
                   capture_output=True, timeout=30)
    subprocess.run(['git', '-C', str(repo), 'update-index', '--index-info'], check=True, timeout=30,
                   input=f'100644 {oid} 1\tdocs/guide/c.md\n100644 {oid} 2\tdocs/guide/c.md\n'.encode())
    assert main(['check', '--repo', str(repo), '--json']) == 3
    assert json.loads(capsys.readouterr().out)['error']['code'] == 'unmerged_index'


def test_repository_path_keeps_trailing_whitespace(tmp_path, capsys):
    root = make_repo(tmp_path / 'repo ')
    assert main(['check', '--repo', str(root)]) == 0
    assert 'uncovered 0; errors 0' in capsys.readouterr().out


def test_stub_query_quotes_the_path_for_the_shell():
    uncovered = "docs/new dir/it's.md"
    stub = yaml.safe_load(suggest(check(base(), [*FILES, uncovered]), base()))[0]
    assert shlex.split(stub['query'][0]['how'])[-1] == 'docs/new dir'


def test_unmatched_store_names_are_printed_escaped(repo, capsys, tmp_path):
    data_root = tmp_path / 'local-data'
    data_root.mkdir()
    (data_root / 'odd\nUNMATCHED STORE forged').write_text('x')
    assert main(['check', '--repo', str(repo), '--data-root', str(data_root)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert "UNMATCHED STORE 'data/odd\\nUNMATCHED STORE forged'" in lines
    assert 'UNMATCHED STORE forged' not in lines


# ------------------------------------------------------------------ the repository's own tree

def test_repository_catalogue_has_zero_errors_and_full_coverage():
    report = coverage(REPO)
    assert report.errors == []
    assert report.uncovered == []
    assert report.data_stores > 0
    assert report.denominator == len(report.resolved)
