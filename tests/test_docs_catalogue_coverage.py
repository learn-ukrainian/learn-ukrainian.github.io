"""Blocking catalogue gate on the repository's own tree (#9412), run inside the CI Gate.

* Every tracked path under docs/, registry/ and curriculum/l2-uk-en/evidence/ resolves to
  exactly one catalogue family; every glob matches a file; zero validation errors.
* Every ``data/<name>.db|.sqlite|.sqlite3`` store that scripts/ code names has a
  data_store entry (or a reasoned exemption).
* Front matter, banners and catalogue overrides agree; the README's generated family
  table is current.
* The development lookups (tests/fixtures/docs_find_dev_lookups.yaml and the natural-wording
  set docs_find_dev_lookups_natural.yaml) are answered from the one entry point, as short
  queries and as full questions.

Failure messages name the exact path and print a ready-to-paste stub
(``python -m scripts.docs.catalogue check --suggest``).
"""
import posixpath
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.docs import catalogue as cat
from scripts.docs import find as find_module
from scripts.docs.find import find

# Reads the whole tracked denominator and scripts/ code, so the module is registered in
# tests/test_repo_wide_marker_invariant.py.
pytestmark = pytest.mark.repo_wide

REPO = Path(__file__).resolve().parents[1]


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


def test_status_markers_are_verified_not_skipped(checked):
    report, catalogue = checked
    assert cat.superseded_markdown(catalogue), 'no superseded Markdown override to verify'
    assert report.markers_unverifiable == 0


def test_the_readme_block_is_generated_from_the_catalogue(checked):
    _, catalogue = checked
    text = (REPO / cat.README_PATH).read_text(encoding='utf-8')
    assert cat.render_readme(text, catalogue) == text, (
        f'{cat.README_PATH} is stale: run python -m scripts.docs.catalogue readme')
    assert 'python -m scripts.docs.find' in text  # the one entry point is named


# ------------------------------------------------------------------ the entry point answers real lookups

# The development lookups (tests/fixtures/docs_find_dev_lookups.yaml): resources, documents, data
# stores, status ("is X current, what replaced it?") and process ("where is X implemented?")
# questions, each with its authority path and the evidence that it is that authority. The
# held-out acceptance lookups are separate and never used here.
DEV_LOOKUPS = yaml.safe_load((REPO / 'tests/fixtures/docs_find_dev_lookups.yaml').read_text(encoding='utf-8'))
DEV_KINDS = {'resource', 'doc', 'data_store', 'status', 'process'}


def _verify_command(check: dict) -> list[str]:
    return ['git', '-C', str(REPO), 'grep', '--cached', '-n', '-F', '-i', '-e', check['contains'], '--', check['path']]


def test_dev_lookups_are_verified_authorities():
    lookups = DEV_LOOKUPS['lookups']
    assert len(lookups) >= 30 and {lk['kind'] for lk in lookups} == DEV_KINDS
    assert len({lk['id'] for lk in lookups}) == len(lookups)
    assert all(1 <= len(lk['query'].split()) <= 8 for lk in lookups)
    failed = [(lk['id'], ' '.join(_verify_command(check))) for lk in lookups for check in lk['verify']
              if subprocess.run(_verify_command(check), capture_output=True, timeout=60).returncode != 0]
    assert failed == []


def _rank(lookup: dict, field: str) -> int | None:
    # Ranking, not latency, is measured here: a loaded CI runner must not cut the search short.
    result = find(lookup[field], 50, repo=REPO, budget_seconds=60)
    assert not result['coverage']['incomplete'], (lookup['id'], result['coverage']['incomplete_reasons'])
    paths = [hit['path'] for hit in result['hits']]
    found = [paths.index(p) + 1 for p in lookup['expect'] if p in paths]
    return min(found) if found else None


# One test per kind and protocol keeps each well inside the per-test timeout (a lookup takes ~1-2 s).
@pytest.mark.parametrize('kind', sorted(DEV_KINDS))
@pytest.mark.parametrize('field', ['query', 'question'])
def test_dev_lookups_are_answered_in_one_query(field, kind):
    bar = DEV_LOOKUPS['top_n'][field]
    lookups = [lk for lk in DEV_LOOKUPS['lookups'] if lk['kind'] == kind and lk['id'] not in DEV_LOOKUPS['known_misses']
               and 'gate' not in lk]
    with ThreadPoolExecutor(max_workers=2) as pool:  # each lookup mostly waits on git grep subprocesses
        ranks = dict(zip((lk['id'] for lk in lookups), pool.map(lambda lk: _rank(lk, field), lookups), strict=True))
    misses = {lk['id']: (lk[field], ranks[lk['id']]) for lk in lookups
              if ranks[lk['id']] is None or ranks[lk['id']] > bar}
    assert misses == {}, f'expected path not within the first {bar} hits: {misses}'


# The second development lookups (tests/fixtures/docs_find_dev_lookups_natural.yaml): natural
# wording that avoids the answer's own name, with a blind one-shot query. A miss not listed in
# known_misses for its protocol fails; a listed miss that now passes is reported so the list shrinks.
NATURAL_LOOKUPS = yaml.safe_load((REPO / 'tests/fixtures/docs_find_dev_lookups_natural.yaml').read_text(encoding='utf-8'))


def test_natural_lookups_are_verified_authorities():
    lookups = NATURAL_LOOKUPS['lookups']
    assert len(lookups) >= 60 and {lk['kind'] for lk in lookups} <= DEV_KINDS
    assert len({lk['id'] for lk in lookups}) == len(lookups)
    assert set(NATURAL_LOOKUPS['known_misses']) <= {lk['id'] for lk in lookups}
    failed = [(lk['id'], ' '.join(_verify_command(check))) for lk in lookups for check in lk['verify']
              if subprocess.run(_verify_command(check), capture_output=True, timeout=60).returncode != 0]
    assert failed == []


# Chunks of NATURAL_CHUNK lookups keep each test well inside the per-test timeout.
NATURAL_CHUNK = 8
NATURAL_CHUNKS = range(0, len(NATURAL_LOOKUPS['lookups']), NATURAL_CHUNK)


@pytest.mark.parametrize('start', NATURAL_CHUNKS)
@pytest.mark.parametrize('field', ['query', 'question'])
def test_natural_lookups_are_answered_in_one_query(field, start):
    bar = NATURAL_LOOKUPS['top_n'][field]
    known = {i for i, miss in NATURAL_LOOKUPS['known_misses'].items() if field in miss}
    lookups = NATURAL_LOOKUPS['lookups'][start:start + NATURAL_CHUNK]
    with ThreadPoolExecutor(max_workers=2) as pool:
        ranks = dict(zip((lk['id'] for lk in lookups), pool.map(lambda lk: _rank(lk, field), lookups), strict=True))
    misses = {i: rank for i, rank in ranks.items() if (rank is None or rank > bar) and i not in known}
    assert misses == {}, f'expected path not within the first {bar} hits (not a known miss): {misses}'


def test_the_motivating_lookup_ranks_the_live_list_above_its_backup():
    result = find('ULP 1-02', repo=REPO)
    # The one-character word is matched in names, the catalogue and the phrase only: complete.
    assert result['coverage']['incomplete'] is False and result['coverage']['name_only_terms'] == ['1']
    top = result['hits'][:3]
    assert all(hit['status'] == 'current' and 'ULP 1-02' in hit['excerpt'] for hit in top)
    assert ('docs/resources/podcasts/raw_lists/seasons_1_3.txt', 2) in [(hit['path'], hit['line']) for hit in top]
    paths = [hit['path'] for hit in result['hits']]
    backup = 'docs/resources/external_resources.yaml.backup'
    if backup in paths:
        hit = result['hits'][paths.index(backup)]
        assert hit['superseded_by'] == 'docs/resources/external_resources.yaml'
        assert paths.index(backup) > paths.index('docs/resources/podcasts/raw_lists/seasons_1_3.txt')


def test_the_route_serves_the_real_tree_ungated(monkeypatch):
    monkeypatch.setattr(api_main.app.state, 'ctx', api_main.app.state.ctx.with_roots(live_repo_root=REPO))
    client = TestClient(api_main.app, raise_server_exceptions=False)
    response = client.get('/api/knowledge/find', params={'q': 'trusted sources', 'limit': 5})
    assert response.status_code == 200
    assert 'docs/resources/trusted_sources.yaml' in [h['path'] for h in response.json()['hits']]


# A document that says in its own opening lines that it is superseded, and links the document that
# superseded it, carries that record in the catalogue, so every hit for it is followed by the replacement.
BANNER = re.compile(r'superseded by', re.IGNORECASE)
LINK = re.compile(r'\]\(([^)\s#]+)')


def test_a_banner_naming_its_replacement_has_a_supersession_record(checked):
    report, _ = checked
    state = find_module.load_state(REPO)
    docs = sorted(p for p in report.resolved if p.endswith('.md') and cat.body_readable(report, p))
    heads, _ = cat.read_heads(REPO, report, docs, lines=15)
    missing, named = [], 0
    for path in docs:
        for line in heads.get(path, '').splitlines():
            if not (found := BANNER.search(line)):
                continue
            targets = [posixpath.normpath(posixpath.join(posixpath.dirname(path), link))
                       for link in LINK.findall(line[found.start():])]
            target = next((t for t in targets if t in report.resolved or t in state.files), None)
            if target:
                named += 1
                family, lifecycle = state.lifecycle_of(path)
                recorded = state.superseded_by(path, family, lifecycle)
                if recorded is None or cat.strip_fragment(recorded) != target:
                    missing.append(f'{path}: its banner names {target}; the catalogue records {recorded!r}')
                break
    assert named >= 10, 'the banner scan found almost nothing; it is broken'  # 15 on 2026-10-02
    assert missing == [], '\n'.join(missing)


def test_a_stale_plan_named_by_path_is_followed_by_what_replaced_it():
    result = find('Is docs/MASTER-PLAN.md still the current plan?', repo=REPO)
    paths = [hit['path'] for hit in result['hits']]
    at = paths.index('docs/MASTER-PLAN.md')
    assert at < 5 and result['hits'][at]['status'] == 'superseded'
    replacement = result['hits'][at + 1]
    assert (replacement['path'], replacement['match']) == ('docs/WORKSTREAMS.md', 'replacement')


def test_a_question_naming_a_session_router_is_answered_by_the_directory_readme(checked):
    report, _ = checked
    result = find('Is docs/session-state/current.claude.md still the live state?', repo=REPO)
    paths = [hit['path'] for hit in result['hits']]
    assert 'docs/session-state/README.md' in paths[:3]
    bodies = [p for p in report.resolved if p.startswith('docs/session-state/') and cat.is_excluded(p)]
    assert bodies and not set(bodies) & set(paths)


# Resource questions expect several catalogue files, the answers most easily crowded out by new
# evidence elsewhere (round 4 of #9412 lost one held-out resource lookup whole). Every resource
# lookup of both development sets is held within 20 under the CLI's own default limit, whose
# read pool is the one a reader gets, in both protocols.
RESOURCE_LOOKUPS = [(name, lk) for name, data in (('dev', DEV_LOOKUPS), ('natural', NATURAL_LOOKUPS))
                    for lk in data['lookups'] if lk['kind'] == 'resource' and 'gate' not in lk]


@pytest.mark.parametrize('field', ['query', 'question'])
@pytest.mark.parametrize('name', ['dev', 'natural'])
def test_resource_lookups_keep_their_answers_at_the_default_limit(name, field):
    known = {i for i, miss in NATURAL_LOOKUPS['known_misses'].items() if field in miss} if name == 'natural' else set()
    lookups = [lk for n, lk in RESOURCE_LOOKUPS if n == name and lk['id'] not in known]
    assert len(lookups) >= 6

    def rank(lk):
        result = find(lk[field], repo=REPO, budget_seconds=60)
        assert not result['coverage']['incomplete'], (lk['id'], result['coverage']['incomplete_reasons'])
        paths = [hit['path'] for hit in result['hits']]
        return min((paths.index(p) + 1 for p in lk['expect'] if p in paths), default=None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        ranks = dict(zip((lk['id'] for lk in lookups), pool.map(rank, lookups), strict=True))
    assert {i: r for i, r in ranks.items() if r is None} == {}


# The multi-answer gate (docs_find_dev_lookups.yaml, `gate: multi_answer`): sibling files under one
# directory that the question names by a word their path holds in another inflection (translated /
# translations, mapped / MAPPING). Round d of #9412 bounded how far a met word may run past the
# term or its stem, which lost every one of them (none within 200); the path must meet the word.
MULTI_ANSWER = [lk for lk in DEV_LOOKUPS['lookups'] if lk.get('gate') == 'multi_answer']
MULTI_ANSWER_GATE = DEV_LOOKUPS['multi_answer_gate']


def test_multi_answer_paths_are_name_candidates_of_their_query():
    assert len(MULTI_ANSWER) >= 5 and set(MULTI_ANSWER_GATE['known_misses']) <= {lk['id'] for lk in MULTI_ANSWER}
    state = find_module.load_state(REPO)
    missing = {}
    for lk in MULTI_ANSWER:
        text = find_module.clean_query(lk['query'])
        terms = find_module.query_terms(text)
        found = find_module._name_candidates(state, terms, find_module.words(text), None, find_module.compounds(text))
        if lost := [p for p in lk['expect'] if p not in found]:
            missing[lk['id']] = lost
    assert missing == {}


@pytest.mark.parametrize('field', ['query', 'question'])
def test_multi_answer_lookups_keep_an_answer_at_the_default_limit(field):
    bar = MULTI_ANSWER_GATE['top_n']
    known = {i for i, miss in MULTI_ANSWER_GATE['known_misses'].items() if field in miss}

    def rank(lk):
        result = find(lk[field], repo=REPO, budget_seconds=60)
        assert not result['coverage']['incomplete'], (lk['id'], result['coverage']['incomplete_reasons'])
        paths = [hit['path'] for hit in result['hits']]
        return min((paths.index(p) + 1 for p in lk['expect'] if p in paths), default=None)
    lookups = [lk for lk in MULTI_ANSWER if lk['id'] not in known]
    with ThreadPoolExecutor(max_workers=2) as pool:
        ranks = dict(zip((lk['id'] for lk in lookups), pool.map(rank, lookups), strict=True))
    assert {i: r for i, r in ranks.items() if r is None or r > bar} == {}


# A storage-layout question asked shortly is carried by the catalogue: the storage-topology entry
# point's topic and its family's keywords hold the words of the question, so the runbook is the
# family hit, and its sibling runbooks, which name no word of the question, are not listed.
@pytest.mark.parametrize('query', ['where do databases live', 'where data lives', 'data layout', 'storage layout'])
def test_a_short_storage_layout_question_is_answered_by_the_storage_topology_runbook(query):
    hits = find(query, repo=REPO, budget_seconds=60)['hits']
    assert hits[0]['path'] == 'docs/runbooks/storage-topology.md'
    assert [hit['path'] for hit in hits if hit['match'] == 'entrypoint'] == ['docs/runbooks/storage-topology.md']


# The same question asked in six to ten words: the runbook, whose catalogue topic names the layout,
# ranks above the inventory documents that mention its words in their body (the corpus inventory,
# the catalogue census), and within the first five.
@pytest.mark.parametrize('query', [
    'which disk holds the databases and raw sources',
    'how is data storage laid out across disks',
    'where do the sqlite databases and bulk sources live',
    'where are the databases and raw files kept',
    'how is the data folder organised on the server',
])
def test_a_storage_layout_question_in_a_few_words_ranks_the_runbook_above_inventories(query):
    paths = [hit['path'] for hit in find(query, repo=REPO, budget_seconds=60)['hits']]
    at = paths.index('docs/runbooks/storage-topology.md')
    inventories = [i for i, p in enumerate(paths) if p == 'docs/corpus-inventory.md' or p.startswith('docs/knowledge/inventory/')]
    assert at < 5 and all(at < i for i in inventories), paths[:8]
