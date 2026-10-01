"""Validator behaviour of the document and data catalogue (#9412) on small fixtures, plus the real tree."""
import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.docs.catalogue import (
    coverage,
    expand_braces,
    glob_regex,
    is_catch_all,
    main,
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


@pytest.mark.parametrize('pattern', ['docs/**', 'docs/*', 'docs/*.md', 'registry/**/*'])
def test_catch_all_glob_is_rejected(pattern):
    data = base()
    data['entries'].append(family('everything', [pattern]))
    assert errors_with(check(data), f"glob {pattern!r} is a catch-all")


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


def test_glob_translation():
    assert expand_braces('docs/{a,b{1,2}}/*.md') == ['docs/a/*.md', 'docs/b1/*.md', 'docs/b2/*.md']
    assert glob_regex('docs/**/x.md').match('docs/x.md')
    assert glob_regex('docs/**/x.md').match('docs/a/b/x.md')
    assert not glob_regex('docs/*.md').match('docs/a/x.md')
    assert glob_regex('docs/a/**').match('docs/a/b/c')
    assert not glob_regex('docs/a/**').match('docs/a')
    assert glob_regex('docs/v?.md').match('docs/v2.md')
    assert glob_regex('docs/[!x]*.md').match('docs/a.md')
    assert not is_catch_all('docs/guide/*')
    assert not is_catch_all('curriculum/l2-uk-en/evidence/a1/**')
    assert is_catch_all('curriculum/l2-uk-en/evidence/**')


# ------------------------------------------------------------------ CLI on a real Git fixture

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, timeout=30)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.email', 'fixture@example.invalid')
    git(tmp_path, 'config', 'user.name', 'Fixture')
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
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'fixture')
    return tmp_path


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


# ------------------------------------------------------------------ the repository's own tree

def test_repository_catalogue_has_zero_errors_and_full_coverage():
    report = coverage(REPO)
    assert report.errors == []
    assert report.uncovered == []
    assert report.data_stores > 0
    assert report.denominator == len(report.resolved)
