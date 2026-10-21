"""Blocking catalogue gate on the repository's own tree (#9412), run inside the CI Gate.

* Every tracked path under docs/, registry/ and curriculum/l2-uk-en/evidence/ resolves to
  exactly one catalogue family; every glob matches a file; zero validation errors.
* Every ``data/<name>.db|.sqlite|.sqlite3`` store that scripts/ code names has a
  data_store entry (or a reasoned exemption).
* Front matter, banners and catalogue overrides agree; the README's generated family
  table is current.
* The SQLite store registry agrees with code and the backup allowlist, and the checkout's
  data/, .agent/, .mcp/ and batch_state/ hold no SQLite file it does not claim (#11092).
* The development lookups (tests/fixtures/docs_find_dev_lookups.yaml and the natural-wording
  set docs_find_dev_lookups_natural.yaml) are verified authorities, and the one entry point
  answers them as short queries and as full questions (the top-n sweep is split over
  tests/test_docs_find_lookups_part<k>.py; the resource and multi-answer gates are here).

Failure messages name the exact path and print a ready-to-paste stub
(``python -m scripts.docs.catalogue check --suggest``).
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.docs import catalogue as cat
from scripts.docs import find as find_module
from scripts.docs import store_census
from scripts.docs.find import find

# Reads the whole tracked denominator and scripts/ code, so the module is registered in
# tests/test_repo_wide_marker_invariant.py.
pytestmark = pytest.mark.repo_wide

REPO = Path(__file__).resolve().parents[1]

# Every search whose answer or completeness is asserted passes this budget, never the 10 s default:
# a loaded CI runner reaches the default and reports an incomplete result (#9535). It matches the
# budget of tests/helpers/docs_find_lookups.py.
SEARCH_BUDGET_SECONDS = 60


@pytest.fixture(scope='module')
def checked():
    return cat.repository_check(REPO)


def _fix_hint(report, catalogue) -> str:
    parts = []
    if report.uncovered:
        parts.append('Paste-ready family stubs (python -m scripts.docs.catalogue check --suggest):\n'
                     + cat.suggest(report, catalogue))
    for store in cat.unclaimed_stores(catalogue, report.store_literals or {}):
        parts.append(f'Paste-ready store stub for {store}:\n' + cat.store_stub(store))
    return '\n'.join(parts)


def test_every_tracked_path_resolves_to_one_family(checked):
    report, catalogue = checked
    assert report.denominator > 0 and report.denominator == len(report.resolved)
    assert report.uncovered == [], ('Uncovered tracked paths:\n' + '\n'.join(map(cat.shown, report.uncovered))
                                    + '\n' + _fix_hint(report, catalogue))


def test_the_catalogue_check_has_zero_errors(checked):
    report, catalogue = checked
    assert report.errors == [], '\n'.join(report.errors) + '\n' + _fix_hint(report, catalogue)


def test_every_data_store_named_in_scripts_has_an_entry(checked):
    report, catalogue = checked
    assert report.store_literals, 'the scan found no data/ store names; the scanner is broken'
    missing = cat.unclaimed_stores(catalogue, report.store_literals)
    assert missing == [], '\n'.join(f'{s} named in {", ".join(report.store_literals[s])}' for s in missing) + (
        '\n' + _fix_hint(report, catalogue))


# ------------------------------------------------------------------ the SQLite store registry (#11092)

def test_the_store_registry_is_checked_against_code_and_the_allowlist(checked):
    report, catalogue = checked
    registry = store_census.registry(catalogue)
    assert len(registry['stores']) == 49, 'expected 40 present stores and 9 declared-absent defaults'
    assert [e for e in report.errors if e.startswith(store_census.REGISTRY_KEY)] == []


def test_this_checkout_has_no_unregistered_sqlite_file(checked):
    # In CI this is the real tree: data/, .agent/, .mcp/ and batch_state/ hold no SQLite file
    # that the registry does not claim. A copy left in a worktree fails here too.
    _, catalogue = checked
    result = store_census.census(REPO, catalogue)
    assert result.ok, '\n'.join(store_census.census_lines(result, store_census.registry(catalogue)))


def test_the_check_command_fails_on_an_unregistered_store_under_the_store_root(tmp_path, capsys):
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/foo.sqlite3').write_bytes(b'SQLite format 3\x00' + bytes(84))
    assert cat.main(['check', '--repo', str(REPO), '--store-root', str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert 'errors 0' in out and 'UNREGISTERED SQLITE data/foo.sqlite3' in out


# ------------------------------------------------------------------ the entry point answers real lookups

# The development lookups (tests/helpers/docs_find_lookups.py) are verified authorities here; their
# top-n sweep runs one lookup per test in tests/test_docs_find_lookups_part<k>.py, split so the CI
# shard splitter spreads it over shards. The resource and multi-answer gates below rank theirs.


def test_the_route_serves_the_real_tree_ungated(monkeypatch):
    # The router calls find() with the library's default budget; this test measures the answer, not
    # latency, so the real search (not a stub) runs here under the same explicit budget as the rest.
    searched = []

    def budgeted(*args, **kwargs):
        searched.append(find(*args, **kwargs, budget_seconds=SEARCH_BUDGET_SECONDS))
        return searched[-1]

    monkeypatch.setattr(find_module, 'find', budgeted)
    monkeypatch.setattr(api_main.app.state, 'ctx', api_main.app.state.ctx.with_roots(live_repo_root=REPO))
    client = TestClient(api_main.app, raise_server_exceptions=False)
    response = client.get('/api/knowledge/find', params={'q': 'trusted sources', 'limit': 5})
    assert response.status_code == 200
    body = response.json()
    assert len(searched) == 1  # the route reached the real search through the wrapper
    assert body['coverage']['incomplete'] is False, body['coverage']
    assert 'docs/resources/trusted_sources.yaml' in [h['path'] for h in body['hits']]
# A store asked for by its common name and format is answered by its own record (#9531): the
# storage-topology topic (bulk raw sources, active SQLite databases) also holds every word of the
# question, but the store's record names it the sources database and its purpose says SQLite
# database, so the store is held among the first three, ahead of code that only opens it.
@pytest.mark.parametrize('query', ['where is the sources sqlite database', 'sources database',
                                   'where is the sources db'])
def test_a_store_asked_by_its_name_and_format_ranks_its_own_record(query):
    hits = find(query, repo=REPO, budget_seconds=60)['hits']
    stores = [i for i, hit in enumerate(hits) if (hit['path'], hit['match']) == ('data/sources.db', 'data_store')]
    assert stores and stores[0] < 3, [hit['path'] for hit in hits[:5]]
