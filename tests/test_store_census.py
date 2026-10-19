"""SQLite store registry and census (#11092, DB plan step 1).

* The repository catalogue carries the registry: 39 named stores present (33 active, 3
  dormant, 2 staged, 1 orphan), 9 declared-absent defaults, the dynamic families and
  the evidence directories, each row with the required fields (AC-01, AC-03).
* The static check rejects wrong backup facts, protection below the nightly, keep
  without a recorded gap, undefined writers, unknown owners and stale examples.
* The census flags an unregistered SQLite file under data/, .agent/, .mcp/ and
  batch_state/ (by extension or header), passes registered stores, family globs and
  evidence directories, flags missing or unexpected stores and journal mismatches on
  the store host, reproduces the 39 count on a materialised tree and never writes.

Every census here walks a temporary tree; the walk of the real checkout is in
tests/test_docs_catalogue_coverage.py (repo_wide).
"""
from __future__ import annotations

import copy
import json
import os
import sqlite3
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from scripts.docs import catalogue as cat
from scripts.docs import store_census as sc

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = cat.load(REPO / cat.CATALOGUE_PATH)
SCHEMA = json.loads((REPO / cat.SCHEMA_PATH).read_text(encoding='utf-8'))
REGISTRY = sc.registry(CATALOGUE)
ALLOWLIST = json.loads((REPO / sc.ALLOWLIST_PATH).read_text(encoding='utf-8'))
STUDY_EVIDENCE_DIRS = {'batch_state/preserved', 'batch_state/devops-*', 'batch_state/codex-atlas',
                       'batch_state/briefs', 'batch_state/open-model-data-*', 'batch_state/review-receipts'}


def store(path: Path, *, wal: bool = False, tables: tuple[str, ...] = ('t',)) -> Path:
    """A real SQLite file at ``path`` (rollback journal unless ``wal``), closed and checkpointed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        if wal:
            conn.execute('PRAGMA journal_mode=WAL')
        for table in tables:
            conn.execute(f'CREATE TABLE {table} (x)')
        conn.commit()
    finally:
        conn.close()
    for suffix in sc.SQLITE_SIDECARS:
        Path(f'{path}{suffix}').unlink(missing_ok=True)
    return path


def rows(**match):
    return [r for r in REGISTRY['stores'] if all(r.get(k) == v for k, v in match.items())]


def row_by_path(reg: dict, path: str) -> dict:
    return next(r for r in reg['stores'] if r['path'] == path)


# ---------------------------------------------------------------- the registry (AC-01, AC-03)

def test_the_catalogue_validates_against_its_schema():
    assert cat.schema_errors(CATALOGUE, SCHEMA) == []
    assert cat.control_string_errors(CATALOGUE) == []


def test_the_registry_reproduces_the_reconciled_inventory():
    present = rows(presence='present')
    assert len(present) == 39
    assert Counter(r['activity'] for r in present) == {'active': 33, 'dormant': 3, 'staged': 2, 'orphan': 1}
    active = Counter(r['kind'] for r in present if r['activity'] == 'active')
    assert active == {'operational': 8, 'cache': 4, 'reference': 9, 'derived': 2, 'job_state': 8, 'telemetry': 2}
    assert {r['path'] for r in rows(activity='dormant')} == {
        'batch_state/agent_monitor.sqlite3', 'wiki/.state/progress.db', 'data/ulif_dump.db'}
    assert {r['path'] for r in rows(activity='staged')} == {'data/sum20_staging.db', 'data/sum20_slovnyk_staging.db'}
    assert {r['path'] for r in rows(activity='orphan')} == {'batch_state/fleet-comms/v1/artifacts/comms.sqlite3'}
    assert row_by_path(REGISTRY, 'batch_state/review-findings/a1.sqlite')['activity'] == 'active'


def test_the_registry_records_the_declared_defaults_families_and_evidence():
    absent = {r['path'] for r in rows(presence='declared_absent')}
    assert absent == {
        'batch_state/hramatka/lessons.sqlite3', 'batch_state/trails/runs.sqlite3',
        'batch_state/agent_runtime_failover_cooldowns.sqlite3', 'data/telemetry/module_builds.db',
        'data/telemetry/llm_qg.db', 'data/telemetry/llm_qg_shadow.db', 'data/embeddings/manifest.db',
        'data/ubertext-freq/frequency.db', 'data/atlas-synthetic.db'}
    families = {f['id'] for f in REGISTRY['families']}
    assert families >= {'review-findings', 'lexicon-runner-work', 'ulif-ledgers', 'dictionary-acquisition-staging',
                        'trail-certification', 'temporary-scratch', 'db-overrides', 'verbatim-shingle-index'}
    assert {f['id'] for f in REGISTRY['families'] if f['glob'] is None} == {
        'trail-certification', 'temporary-scratch', 'db-overrides'}
    assert {e['path'] for e in REGISTRY['evidence_dirs']} >= STUDY_EVIDENCE_DIRS


def test_every_store_row_carries_the_required_facts():
    required = {'path', 'owner', 'kind', 'activity', 'presence', 'writers', 'journal', 'busy_ms', 'busy_source',
                'protection', 'backup', 'retention'}
    for row in REGISTRY['stores']:
        assert required <= set(row), row['path']
        assert row['writers'] or row.get('writer_note'), row['path']
        assert row['protection'] in ('keep', 'rebuild', 'disposable'), row['path']


def test_registry_rows_name_stores_and_producers_never_host_locations():
    for section in ('stores', 'families', 'evidence_dirs', 'non_stores'):
        for row in REGISTRY[section]:
            for value in [row.get('path'), row.get('glob'), row.get('example'), *row.get('paths', []),
                          *row.get('writers', [])]:
                if value:
                    assert not value.startswith(('/', '~')) and '/home/' not in value and '/mnt/' not in value, value


# ---------------------------------------------------------------- static check

def writer_sources() -> tuple[set[str], dict[str, str]]:
    files = sc.writer_files(CATALOGUE)
    return files | {sc.ALLOWLIST_PATH}, {p: (REPO / p).read_text(encoding='utf-8') for p in files}


OWNERS = cat.owner_keys(REPO)


def static(catalogue: dict, literals: dict[str, list[str]] | None = None) -> list[str]:
    tracked, sources = writer_sources()
    return sc.registry_errors(catalogue, tracked, OWNERS, ALLOWLIST, sources, literals)


def test_the_repository_registry_has_no_static_errors():
    assert static(CATALOGUE) == []


def mutated(change) -> dict:
    catalogue = copy.deepcopy(CATALOGUE)
    change(sc.registry(catalogue))
    return catalogue


DROP = object()  # remove the field


def _set(path: str, **fields):
    def change(reg):
        row = row_by_path(reg, path)
        for key, value in fields.items():
            if value is DROP:
                row.pop(key, None)
            else:
                row[key] = value
    return change


MUTATIONS = {
    'backup fact contradicts the allowlist': (
        _set('batch_state/tasks/write-ownership.sqlite3', backup='keep', protection_gap=DROP),
        "backup is 'keep' but scripts/config/backup-allowlist.json gives 'none'"),
    'protection below the nightly': (_set('data/atlas.db', protection='rebuild'), 'backup reduction'),
    'keep without a recorded gap': (_set('batch_state/review-findings/a1.sqlite', protection_gap=DROP),
                                    'needs protection_gap'),
    'gap on a kept store': (_set('data/atlas.db', protection_gap='x'), 'remove the gap'),
    'undefined writer': (_set('batch_state/review-findings/a1.sqlite', writers=['scripts/review/findings_db.py:nope']),
                         "'nope' is not defined"),
    'untracked writer file': (_set('data/atlas.db', writers=['scripts/no/such.py:main']), 'untracked file'),
    'no writer and no note': (_set('data/mphdict/etym.db', writer_note=DROP), 'writer_note'),
    'unknown owner': (_set('data/atlas.db', owner='nobody'), "owner 'nobody'"),
    'present store marked not created': (_set('data/atlas.db', activity='not_created'), 'not_created'),
    'declared absent without a reason': (_set('data/atlas-synthetic.db', absent_reason=DROP), 'absent_reason'),
    'catalogue entry that does not claim it': (_set('data/atlas.db', catalogue_entry='data-atlas-synthetic'),
                                               'does not claim'),
    'unknown family': (_set('data/atlas.db', family='nope'), "family 'nope'"),
    'busy null with a writer': (_set('data/atlas.db', busy_ms=None), 'busy_ms is null'),
}


@pytest.mark.parametrize('name', sorted(MUTATIONS))
def test_the_static_check_rejects(name):
    change, needle = MUTATIONS[name]
    errors = static(mutated(change))
    assert any(needle in e for e in errors), errors


def test_a_family_example_must_match_its_glob_and_not_be_shadowed():
    def bad_example(reg):
        next(f for f in reg['families'] if f['id'] == 'ulif-ledgers')['example'] = 'batch_state/other/ledger.sqlite'
    assert any('does not match glob' in e for e in static(mutated(bad_example)))

    def shadowed(reg):
        broad = {**next(f for f in reg['families'] if f['id'] == 'lexicon-runner-work'),
                 'id': 'broad', 'glob': 'data/lexicon/**', 'example': 'data/lexicon/x.sqlite'}
        reg['families'].insert(0, broad)
    errors = static(mutated(shadowed))
    assert any("'lexicon-runner-work': example 'data/lexicon/runner_work/ledger.sqlite' resolves to 'broad'" in e
               for e in errors), errors


def test_a_store_inside_an_evidence_directory_and_duplicates_are_rejected():
    def inside(reg):
        reg['stores'].append({**row_by_path(reg, 'batch_state/agent_monitor.sqlite3'),
                              'path': 'batch_state/preserved/x.sqlite3', 'backup': 'drop'})
    assert any('inside an evidence directory' in e for e in static(mutated(inside)))

    def duplicate(reg):
        reg['stores'].append(copy.deepcopy(row_by_path(reg, 'data/atlas.db')))
    assert any("'data/atlas.db' is registered 2 times" in e for e in static(mutated(duplicate)))


def test_every_sqlite_store_name_in_scripts_needs_a_registry_row():
    assert static(CATALOGUE, {'data/atlas.db': ['scripts/a.py'], 'data/grac-10.db': ['scripts/b.py'],
                              'data/sources-copy.db': ['scripts/c.py'], 'data/x.duckdb': ['scripts/d.py']}) == []
    errors = static(CATALOGUE, {'data/new_store.sqlite3': ['scripts/new.py'], 'data/grac-10.db': ['scripts/b.py']})
    assert any("'data/new_store.sqlite3' (named in scripts/new.py) has no stores row" in e for e in errors)
    # A family literal that code no longer names is stale.
    assert any("family literal 'data/grac-10.db' is no longer named" in e for e in static(CATALOGUE, {}))


# ---------------------------------------------------------------- backup facts

@pytest.mark.parametrize(('path', 'fact'), [
    ('batch_state/tasks/write-ownership.sqlite3', 'none'),  # task_records stages records only
    ('batch_state/tasks/x.json', 'keep'),
    ('batch_state/tasks/archive/x.sqlite3', 'keep'),
    ('batch_state/tasks/x.json.lock', 'none'),
    ('data/lexicon/cache/ulif_raw.sqlite', 'keep'),  # a keep file beats the drop tree
    ('data/lexicon/cache/other.sqlite', 'drop'),
    ('data/wiki_cache.db', 'keep'),
    ('data/sub/wiki_cache.db', 'none'),  # glob_files is not recursive
    ('batch_state/devops-20261010/x.db', 'drop'),
    ('data/backups/x.db', 'drop'),
    ('batch_state/open-model-data/x.sqlite3', 'keep'),
    ('batch_state/open-model-data-20261016/x.sqlite3', 'none'),
    ('data/new.db', 'none'),
])
def test_backup_facts_follow_the_allowlist_semantics(path, fact):
    assert sc.backup_fact(path, ALLOWLIST) == fact


# ---------------------------------------------------------------- census

def run(root: Path, *, expect_present: bool = False) -> sc.Census:
    return sc.census(root, CATALOGUE, expect_present=expect_present)


def test_an_empty_checkout_passes(tmp_path):
    result = run(tmp_path)
    assert result.ok and result.found == {} and result.walked_roots == []


@pytest.mark.parametrize('path', ['data/foo.sqlite3', 'batch_state/x/foo.sqlite', '.agent/x/y.db',
                                  '.mcp/servers/x/z.sqlite3', 'data/mphdict/new.sqlite'])
def test_an_unregistered_store_is_flagged_in_every_census_root(tmp_path, path):
    store(tmp_path / path)
    result = run(tmp_path)
    assert result.unregistered == [path] and not result.ok


def test_a_file_is_a_store_by_header_or_by_extension(tmp_path):
    store(tmp_path / 'batch_state/x/blob')  # SQLite header, no extension
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/empty.db').write_bytes(b'')  # extension, no header
    (tmp_path / 'data/notes.txt').write_text('SQLite format 2\n')
    assert run(tmp_path).unregistered == ['batch_state/x/blob', 'data/empty.db']


def test_registered_stores_and_family_globs_pass(tmp_path):
    store(tmp_path / 'data/atlas.db', wal=True)
    store(tmp_path / 'batch_state/review-findings/b2.sqlite')
    store(tmp_path / 'data/lexicon/runner_work/deep/ledger.sqlite')
    result = run(tmp_path)
    assert result.ok, result.unregistered
    assert result.found == {'batch_state/review-findings/b2.sqlite': 'families', 'data/atlas.db': 'stores',
                            'data/lexicon/runner_work/deep/ledger.sqlite': 'families'}


def test_evidence_directories_are_classified_by_row_and_not_walked(tmp_path):
    store(tmp_path / 'batch_state/preserved/copy.sqlite3')
    store(tmp_path / 'batch_state/devops-20261099/a/b.db')
    store(tmp_path / 'batch_state/preserved-not-evidence/x.sqlite3')
    result = run(tmp_path)
    assert result.unregistered == ['batch_state/preserved-not-evidence/x.sqlite3']
    assert sorted(result.evidence) == ['batch_state/devops-20261099', 'batch_state/preserved']


def test_sidecars_and_symlinks_are_not_census_entries(tmp_path):
    outside = store(tmp_path / 'outside/real.sqlite3')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/foo.db-wal').write_bytes(b'x')
    (tmp_path / 'data/link.sqlite3').symlink_to(outside)
    (tmp_path / 'batch_state').mkdir()
    (tmp_path / 'batch_state/linked').symlink_to(outside.parent, target_is_directory=True)
    assert run(tmp_path).found == {}


def test_a_placeholder_that_stops_being_empty_is_a_mismatch(tmp_path):
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/comms_plane.db').write_bytes(b'')
    assert run(tmp_path).ok
    store(tmp_path / 'data/comms.db')
    result = run(tmp_path)
    assert result.problems == ['data/comms.db: registered as a zero-byte placeholder but is not empty']


def test_coverage_rows_are_confirmed_by_their_schema_table(tmp_path):
    store(tmp_path / 'batch_state/impl-1/coverage.sqlite', tables=('coverage_schema', 'meta'))
    assert run(tmp_path).ok
    store(tmp_path / 'batch_state/impl-2/coverage-copy.sqlite3')
    result = run(tmp_path)
    assert result.problems == ['batch_state/impl-2/coverage-copy.sqlite3: matches a coverage.py data row but is '
                               'not coverage.py data']


def test_presence_flags_missing_and_unexpected_stores_only_when_asked(tmp_path):
    assert run(tmp_path).ok  # a code-only checkout (CI, a sparse worktree) has no stores
    result = run(tmp_path, expect_present=True)
    assert not result.ok and len(result.missing) == 39
    store(tmp_path / 'batch_state/trails/runs.sqlite3')
    result = run(tmp_path, expect_present=True)
    assert 'batch_state/trails/runs.sqlite3: registered as declared_absent but present; update its row' in result.problems


def test_a_journal_mode_that_disagrees_with_the_header_is_flagged(tmp_path):
    store(tmp_path / 'data/atlas.db')  # the registry records WAL
    result = run(tmp_path, expect_present=True)
    assert "data/atlas.db: registry journal 'wal' but header byte 18 is 1 (1 rollback journal, 2 WAL)" in result.problems
    store(tmp_path / 'data/atlas.db', wal=True, tables=('u',))
    assert not any(p.startswith('data/atlas.db') for p in run(tmp_path, expect_present=True).problems)


def materialise(root: Path) -> None:
    subprocess.run(['git', 'init', '-q', str(root)], check=True, timeout=30)
    for row in rows(presence='present'):
        logical = row['path']
        if logical.startswith(sc.GIT_COMMON_DIR + '/'):
            logical = '.git/' + logical.split('/', 1)[1]
        store(root / logical, wal=row['journal'] == 'wal')


def test_a_materialised_registry_reproduces_the_39_count(tmp_path):
    materialise(tmp_path)
    result = run(tmp_path, expect_present=True)
    assert result.ok, (result.unregistered, result.problems, result.missing)
    counts = result.counts(REGISTRY)
    assert counts['named_stores_present'] == 39 and counts['missing'] == 0
    assert counts['by_activity'] == {'active': 33, 'dormant': 3, 'orphan': 1, 'staged': 2}
    assert counts['active_by_kind'] == {'cache': 4, 'derived': 2, 'job_state': 8, 'operational': 8,
                                        'reference': 9, 'telemetry': 2}
    assert counts['declared_absent_rows'] == 9


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    out = {}
    for directory, _, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            stat = path.lstat()
            out[str(path.relative_to(root))] = (stat.st_size, stat.st_mtime_ns)
    return out


def test_the_census_never_writes_or_creates_sidecars(tmp_path):
    materialise(tmp_path)
    store(tmp_path / 'batch_state/impl-1/coverage.sqlite', tables=('coverage_schema',))
    store(tmp_path / 'data/unregistered.sqlite3', wal=True)
    before = snapshot(tmp_path)
    run(tmp_path, expect_present=True)
    assert snapshot(tmp_path) == before


# ---------------------------------------------------------------- CLI

def test_the_census_command_reports_counts_and_exits_by_outcome(tmp_path, capsys):
    store(tmp_path / 'data/atlas.db', wal=True)
    assert cat.main(['census', '--repo', str(REPO), '--root', str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert 'SQLite files found 1 (stores 1)' in out and 'presence: not checked' in out
    store(tmp_path / 'batch_state/x/foo.sqlite3')
    assert cat.main(['census', '--repo', str(REPO), '--root', str(tmp_path), '--json']) == 1
    data = json.loads(capsys.readouterr().out)
    assert data['unregistered'] == ['batch_state/x/foo.sqlite3'] and data['ok'] is False
    assert data['counts']['named_stores_present'] == 1
    assert cat.main(['census', '--repo', str(REPO), '--root', str(tmp_path), '--expect-present']) == 1
    assert 'MISSING STORE data/movaua.db' in capsys.readouterr().out


def test_a_census_root_that_is_not_a_directory_is_an_error(tmp_path, capsys):
    assert cat.main(['census', '--repo', str(REPO), '--root', str(tmp_path / 'missing')]) == cat.EXIT_UNREADABLE
    assert 'is not a directory' in capsys.readouterr().out
