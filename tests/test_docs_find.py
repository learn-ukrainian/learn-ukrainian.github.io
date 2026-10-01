"""The one query surface (#9412): ``scripts/docs/find.py``, its CLI and ``GET /api/knowledge/find``.

Every test runs against a small Git fixture repository, never the real tree (the
real-tree checks, including the dev-set lookups, live in
``tests/test_docs_catalogue_coverage.py``).
"""
import ast
import json
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.docs import find as find_module
from scripts.docs.find import FindError, clean_query, ere_escape, escape_excerpt, find, main, query_terms

REPO = Path(__file__).resolve().parents[1]
SCHEMA = (REPO / 'docs/knowledge/catalogue.schema.json').read_text(encoding='utf-8')
BIDI = chr(0x202E)
ESC = chr(0x1B)
PRIVATE = 'docs/guide/sub/private/secret.md'
CONTROL_PATH = 'docs/guide/ctl\nname.md'
HOSTILE_NAMES = ['docs/guide/-rf.md', 'docs/guide/--help', 'docs/guide/with space.md',
                 "docs/guide/it's (x).md", 'docs/guide/:(exclude)evil.md', 'docs/guide/ґанок.md']


def entry(eid, paths, **extra):
    data = {'id': eid, 'kind': 'doc_family', 'paths': paths, 'purpose': f'{eid} documents',
            'keywords': [eid], 'lifecycle': 'active', 'owner': 'infra-harness',
            'query': [{'surface': 'git_grep', 'how': f'git grep -n -i -F <term> -- {paths[0]}'}],
            'content_searchable': True}
    data.update(extra)
    return data


def fixture_catalogue():
    return {
        'schema_version': 1,
        'denominator': {'tracked_roots': ['docs', 'registry', 'curriculum/l2-uk-en/evidence'],
                        'local_store_root': 'data'},
        'status_mapping': {'current': 'active', 'historical': 'archive', 'superseded': 'superseded'},
        'entries': [
            entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
            entry('guide', ['docs/guide/**'], keywords=['handbook', 'guide'],
                  entrypoints=[{'topic': 'guide index', 'path': 'docs/guide/index.md'}]),
            entry('guide-private', ['docs/guide/sub/private/**'], content_searchable=False),
            entry('resources', ['docs/resources/**'], kind='resource_catalogue', keywords=['podcast list'],
                  overrides=[{'path': 'docs/resources/list.txt.backup', 'lifecycle': 'superseded',
                              'superseded_by': 'docs/resources/list.txt', 'evidence': 'Stray backup copy.'}]),
            entry('old', ['docs/old/**'], lifecycle='archive'),
            {'id': 'data-main', 'kind': 'data_store', 'store': ['data/main.db'], 'producer': ['scripts/build.py'],
             'local_only': True, 'purpose': 'Main store for the fixture', 'keywords': ['main database'],
             'lifecycle': 'active', 'owner': 'infra-harness',
             'query': [{'surface': 'sqlite', 'how': 'read-only SQL on data/main.db'}], 'content_searchable': False},
        ],
        'residual': [],
    }


FILES = {
    'docs/knowledge/catalogue.schema.json': SCHEMA,
    'docs/guide/index.md': '# Guide\nHow to rebuild the teacher deck.\n',
    'docs/guide/uk.md': 'Перевірка за словником ВЕСУМ.\nСлово «йод» у тексті.\n',
    'docs/guide/nfd.md': unicodedata.normalize('NFD', 'Ґрунт: йодистий розчин.\n'),
    'docs/guide/literal.md': 'axb(c) is not the literal\nthe literal a.b(c) is here\n',
    'docs/guide/escape.md': f'needle with {ESC}[31m colour and {BIDI}bidi\n',
    PRIVATE: 'ULP 1-02 private sentinel\nвесум secret hostilename\n',
    'docs/resources/list.txt': 'Season: 1, Title: ULP 1-02 Formal Greetings\n',
    'docs/resources/list.txt.backup': 'Season: 1, Title: ULP 1-02 Formal Greetings\n',
    'docs/old/notes.md': '# Old\nULP 1-02 was mentioned in old notes\n',
    'scripts/build.py': "print('x')\n",
    'scripts/config/issue_streams.yaml': 'streams:\n  docs-knowledge: {epics: [1]}\n',
    'scripts/config/area_assignments.yaml': 'assignments:\n  infra-harness: {slots: []}\n',
    **{name: 'hostilename sits here\n' for name in HOSTILE_NAMES},
}


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=data, capture_output=True, check=True,
                          timeout=30).stdout


def write_catalogue(repo, data):
    (repo / 'docs/knowledge/catalogue.yaml').write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
    git(repo, 'add', 'docs/knowledge/catalogue.yaml')


def make_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    git(root, 'config', 'user.name', 'Fixture')
    for rel, text in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    write_catalogue(root, fixture_catalogue())
    git(root, 'add', '.')
    # A control character in a tracked name: added to the index only (never a worktree file).
    oid = git(root, 'hash-object', '-w', '--stdin', data=b'hostilename in a control-named file\n').decode().strip()
    git(root, 'update-index', '--add', '-z', '--index-info', data=f'100644 {oid}\t{CONTROL_PATH}\0'.encode())
    return root


@pytest.fixture(scope='module')
def repo(tmp_path_factory):
    return make_repo(tmp_path_factory.mktemp('find') / 'repo')


@pytest.fixture
def fresh_repo(tmp_path):
    return make_repo(tmp_path / 'repo')


def paths_of(result):
    return [hit['path'] for hit in result['hits']]


def hit_for(result, path):
    return next(hit for hit in result['hits'] if hit['path'] == path)


# ------------------------------------------------------------------ query normalisation

def test_query_cleaning_replaces_every_non_printable_and_caps_length():
    raw = 'a\nb\tc' + chr(0x2028) + 'd' + chr(0x85) + 'e' + BIDI + 'f' + chr(0xFEFF) + 'g'
    assert clean_query(raw) == 'a b c d e f g'
    assert len(clean_query('x' * 500)) == find_module.MAX_QUERY_CHARS
    assert clean_query(unicodedata.normalize('NFD', 'йод')) == 'йод'


def test_terms_drop_stopwords_and_casefold_without_stemming():
    assert query_terms('Where is the list of Podcast episodes?') == ['list', 'podcast', 'episodes']
    assert query_terms('the of') == ['the', 'of']  # only stopwords: keep them rather than nothing
    assert query_terms('ВЕСУМ словники') == ['весум', 'словники']
    assert query_terms("п'ять") == ["п'ять"]  # the apostrophe stays inside a Ukrainian word


def test_ere_escape_matches_only_the_literal_text():
    import re
    for text in ['a.b(c)', 'x|y', '[a-z]*', 'c++ {1}', 'end$ ^start', 'back\\slash', '?']:
        assert re.fullmatch(ere_escape(text), text)
    assert not re.search(ere_escape('a.b'), 'axb')


def test_excerpts_escape_controls_and_format_characters():
    assert escape_excerpt(f'{ESC}[31m red') == '\\x1b[31m red'
    assert escape_excerpt(f'a{BIDI}b') == 'a\\u202eb'
    assert escape_excerpt('звичайний текст') == 'звичайний текст'


# ------------------------------------------------------------------ ranking and statuses

def test_phrase_ranks_current_then_historical_then_backup_and_never_the_private_family(repo):
    result = find('ULP 1-02', repo=repo)
    assert paths_of(result)[:3] == ['docs/resources/list.txt', 'docs/old/notes.md', 'docs/resources/list.txt.backup']
    current, historical, backup = result['hits'][:3]
    assert (current['status'], current['line'], current['family']) == ('current', 1, 'resources')
    assert current['excerpt'] == 'Season: 1, Title: ULP 1-02 Formal Greetings'
    assert current['query'] == [{'surface': 'git_grep', 'how': 'git grep -n -i -F <term> -- docs/resources/**'}]
    assert historical['status'] == 'historical'
    assert backup['status'] == 'superseded' and backup['superseded_by'] == 'docs/resources/list.txt'
    assert backup['backup_like'] is True
    assert PRIVATE not in paths_of(result)
    assert result['outcome'] == 'found'
    # the one-character word '1' is reported as not searched alone; nothing else cut the search
    assert result['coverage']['incomplete_reasons'] == [
        "content_search_skipped: one-character word(s) '1' not searched alone in text"]


def test_lifecycle_rank_is_what_orders_equal_matches(repo, monkeypatch):
    monkeypatch.setattr(find_module, 'LIFECYCLE_RANK', {k: 0 for k in find_module.LIFECYCLE_RANK})
    monkeypatch.setattr(find_module, 'BACKUP_RANK', 0)
    order = paths_of(find('ULP 1-02', repo=repo))[:3]
    assert order == sorted(order)  # without lifecycle ranking only path order remains


def test_catalogue_match_comes_first_with_entrypoints_family_and_store_hints(repo):
    guide = find('handbook', repo=repo)
    assert (guide['hits'][0]['match'], guide['hits'][0]['path'], guide['hits'][0]['topic']) == (
        'entrypoint', 'docs/guide/index.md', 'guide index')
    family = find('podcast list', repo=repo)['hits'][0]
    assert (family['match'], family['path'], family['paths']) == ('family', None, ['docs/resources/**'])
    store, producer = find('main database', repo=repo)['hits'][:2]
    assert (store['match'], store['path'], store['producer']) == ('data_store', 'data/main.db', ['scripts/build.py'])
    assert store['query'] == [{'surface': 'sqlite', 'how': 'read-only SQL on data/main.db'}]
    assert (producer['match'], producer['path'], producer['status']) == ('producer', 'scripts/build.py', 'uncatalogued')


def test_a_short_keyword_never_matches_a_longer_query_word(repo):
    data = fixture_catalogue()
    data['entries'][4]['keywords'] = ['dec-']  # 'dec' must not claim the query word 'deck'
    hits = find_module._catalogue_hits(_state(repo, data), ['teacher', 'deck'], ['teacher', 'deck'], None)[0]
    assert hits == []


def _state(repo, data):
    schema = json.loads(SCHEMA)
    from scripts.docs import catalogue as cat
    files = cat.index_entries(repo)
    report = cat.validate(data, schema, list(files), {'docs-knowledge', 'infra-harness'})
    return find_module.State(repo, data, report, files, by_id={e['id']: e for e in data['entries']})


def test_names_are_searched_but_never_private_or_control_names(repo):
    result = find('hostilename', repo=repo, limit=50)
    assert sorted(p for p in paths_of(result) if p.startswith('docs/guide/') and 'sub' not in p) == sorted(
        HOSTILE_NAMES)
    assert all('\n' not in p for p in paths_of(result))
    assert PRIVATE not in paths_of(result)
    assert all(hit['line'] == 1 for hit in result['hits'] if hit['path'] in HOSTILE_NAMES)
    assert find('ґанок', repo=repo)['hits'][0]['path'] == 'docs/guide/ґанок.md'


def test_family_filter_uses_literal_pathspecs_for_hostile_names(repo):
    result = find('hostilename', repo=repo, family='guide', limit=50)
    assert sorted(paths_of(result)) == sorted(HOSTILE_NAMES)
    assert result['coverage']['families_searched'] == ['guide']


# ------------------------------------------------------------------ Ukrainian text

@pytest.mark.parametrize('query', ['весум', 'ВЕСУМ', 'Весум', 'ВЕСУМ словник'])
def test_ukrainian_queries_are_case_folded(repo, query):
    result = find(query, repo=repo)
    hit = hit_for(result, 'docs/guide/uk.md')
    assert hit['line'] == 1 and 'ВЕСУМ' in hit['excerpt']
    assert PRIVATE not in paths_of(result)


def test_nfc_and_nfd_text_and_queries_meet(repo):
    assert hit_for(find('ЙОД', repo=repo), 'docs/guide/uk.md')['line'] == 2
    assert 'docs/guide/nfd.md' in paths_of(find('йодистий', repo=repo))  # NFC query, NFD file
    assert 'docs/guide/uk.md' in paths_of(find(unicodedata.normalize('NFD', 'йод'), repo=repo))


# ------------------------------------------------------------------ hostile queries

@pytest.mark.parametrize('query', ['-e', '--all-match', '-l -i', ':(exclude)x', '$(touch pwned)', '`id`',
                                   'a\nb', f'{ESC}[31m', "'; rm -rf /", '(?i)', '--output=pwned x'])
def test_hostile_queries_are_literal_text(repo, query):
    result = find(query, repo=repo)
    assert result['outcome'] in ('found', 'no_match', 'incomplete')
    # no Git error or option injection: the only allowed reason is a reported one-character word
    reasons = result['coverage']['incomplete_reasons']
    assert all(r.startswith('content_search_skipped: ') for r in reasons), reasons
    assert result['outcome'] != 'incomplete' or reasons
    assert not (repo / 'pwned').exists()


@pytest.mark.parametrize('query', ['--', '*', '\\', '[', '-', '...'])
def test_a_query_of_separators_only_has_no_searchable_word(repo, query):
    with pytest.raises(FindError) as caught:
        find(query, repo=repo)
    assert caught.value.code == 'empty_query'


def test_regex_characters_match_literally(repo):
    result = find('a.b(c)', repo=repo)
    hit = hit_for(result, 'docs/guide/literal.md')
    assert hit['line'] == 2  # the literal line, not 'axb(c)'


def test_excerpts_never_carry_raw_controls_or_bidi(repo):
    hit = hit_for(find('needle', repo=repo), 'docs/guide/escape.md')
    assert ESC not in hit['excerpt'] and BIDI not in hit['excerpt']
    assert '\\x1b[31m' in hit['excerpt'] and '\\u202e' in hit['excerpt']


@pytest.mark.parametrize('query, code', [('', 'empty_query'), ('   \n\t', 'empty_query')])
def test_empty_queries_are_rejected(repo, query, code):
    with pytest.raises(FindError) as caught:
        find(query, repo=repo)
    assert caught.value.code == code


@pytest.mark.parametrize('limit', [0, -1, find_module.MAX_LIMIT + 1])
def test_limit_bounds(repo, limit):
    with pytest.raises(FindError) as caught:
        find('guide', limit, repo=repo)
    assert caught.value.code == 'limit'


BAD_LIMITS = [True, False, 1.5, 5.0, '5', None, float('nan'), float('inf'), 10 ** 30]


@pytest.mark.parametrize('limit', BAD_LIMITS, ids=repr)
def test_limit_must_be_a_whole_number_not_a_bool_float_or_text(repo, limit):
    with pytest.raises(FindError) as caught:
        find('guide', limit, repo=repo)
    assert caught.value.code == 'limit' and caught.value.message == find_module.LIMIT_MESSAGE


BAD_BUDGETS = [float('inf'), float('-inf'), float('nan'), 1e100, 10 ** 400, 10 ** 30, -1, -0.5, 0, 0.0, -0.0,
               True, False, '5', None, find_module.MAX_BUDGET_SECONDS + 0.001, 2 ** 63]


@pytest.fixture
def no_search_starts(monkeypatch):
    """Fail the test if any search process or timer starts."""
    def refuse(*_args, **_kwargs):
        raise AssertionError('a search started for a rejected request')
    monkeypatch.setattr(find_module.subprocess, 'Popen', refuse)
    monkeypatch.setattr(find_module.threading, 'Timer', refuse)


@pytest.mark.parametrize('budget', BAD_BUDGETS, ids=repr)
def test_bad_budgets_are_a_typed_error_before_any_search(repo, no_search_starts, budget):
    with pytest.raises(FindError) as caught:
        find('guide', repo=repo, budget_seconds=budget)
    assert caught.value.code == 'budget' and caught.value.message == find_module.BUDGET_MESSAGE
    assert isinstance(caught.value, ValueError)


@pytest.mark.parametrize('budget', [1, 0.5, find_module.MAX_BUDGET_SECONDS, int(find_module.MAX_BUDGET_SECONDS)])
def test_good_budgets_are_accepted(repo, budget):
    assert find('handbook', repo=repo, budget_seconds=budget)['outcome'] == 'found'


def test_a_failing_search_worker_is_incomplete_never_a_traceback(fresh_repo, monkeypatch, capsys):
    # The defect class: an exception inside a worker (here the timer, as OverflowError did
    # for an infinite budget) escaped as a traceback while the result said complete.
    class Exploding:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            raise OverflowError('timeout value is too large')

        def cancel(self):
            pass
    started = []
    real_popen = find_module.subprocess.Popen

    def popen(*args, **kwargs):
        started.append(proc := real_popen(*args, **kwargs))
        return proc
    monkeypatch.setattr(find_module.threading, 'Timer', Exploding)
    monkeypatch.setattr(find_module.subprocess, 'Popen', popen)
    result = find('zzqq', repo=fresh_repo)
    assert result['outcome'] == 'incomplete' and result['coverage']['incomplete']
    assert result['coverage']['incomplete_reasons'] == ["error: the search for 'zzqq' did not finish (OverflowError)"]
    assert started and all(proc.poll() is not None for proc in started)  # no search left running
    assert main(['zzqq', '--repo', str(fresh_repo)]) == 5
    captured = capsys.readouterr()
    assert 'INCOMPLETE' in captured.out and 'Traceback' not in captured.out + captured.err


def test_a_failed_search_never_leaves_its_process_running(monkeypatch):
    # A stand-in for a long search: without the kill, the runner would wait on it and leave it alive.
    class Exploding:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            raise OverflowError('timeout value is too large')

        def cancel(self):
            pass
    started = []
    real_popen = find_module.subprocess.Popen

    def slow(_argv, **kwargs):
        started.append(proc := real_popen([sys.executable, '-c', 'import time; time.sleep(60)'], **kwargs))
        return proc
    monkeypatch.setattr(find_module.threading, 'Timer', Exploding)
    monkeypatch.setattr(find_module.subprocess, 'Popen', slow)
    tick = time.monotonic()
    run = find_module._total_grep(Path('.'), [], time.monotonic() + 30, 1)
    assert (run.outcome, run.detail) == ('error', 'OverflowError')
    assert started[0].poll() is not None and time.monotonic() - tick < 5


def test_any_worker_exception_becomes_an_error_run(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError('unexpected')
    monkeypatch.setattr(find_module, '_git_grep', boom)
    run = find_module._total_grep(Path('.'), [], 0.0, 1)
    assert (run.outcome, run.detail, run.stdout) == ('error', 'RuntimeError', b'')


def test_a_one_character_word_is_searched_not_skipped(fresh_repo):
    (fresh_repo / 'docs/guide/omega.md').write_text('Ω\n', encoding='utf-8')
    git(fresh_repo, 'add', 'docs/guide/omega.md')
    result = find('Ω', repo=fresh_repo)
    assert result['outcome'] == 'found' and not result['coverage']['incomplete']
    assert hit_for(result, 'docs/guide/omega.md')['match'] == 'content'
    assert hit_for(result, 'docs/guide/omega.md')['excerpt'] == 'Ω'
    missing = find('ж', repo=fresh_repo)
    assert (missing['outcome'], missing['coverage']['incomplete']) == ('no_match', False)


def test_a_one_character_word_beside_longer_words_is_reported_not_silent(fresh_repo):
    result = find('zzqq Ω', repo=fresh_repo)  # Ω is in no file here; 'zzqq' and the phrase are searched
    assert result['outcome'] == 'incomplete' and result['coverage']['incomplete']  # never no_match
    assert result['coverage']['incomplete_reasons'] == [
        "content_search_skipped: one-character word(s) 'ω' not searched alone in text"]
    found = find('ULP 1-02', repo=fresh_repo)
    assert found['outcome'] == 'found' and found['coverage']['incomplete']


def test_unknown_family_is_rejected(repo):
    with pytest.raises(FindError) as caught:
        find('guide', repo=repo, family='nope')
    assert caught.value.code == 'unknown_family'


# ------------------------------------------------------------------ privacy: what git is asked to read

def recorded_greps(monkeypatch):
    calls = []
    original = find_module._git_grep

    def recording(repo, args, deadline, cap):
        calls.append(list(args))
        return original(repo, args, deadline, cap)
    monkeypatch.setattr(find_module, '_git_grep', recording)
    return calls


def test_git_never_reads_an_unreadable_path(repo, monkeypatch):
    find_module._STATE_CACHE.clear()
    calls = recorded_greps(monkeypatch)
    find('hostilename secret', repo=repo)
    assert calls
    for args in calls:
        specs = args[args.index('--') + 1:]
        assert all(s.startswith((':(literal)', ':(exclude,literal)')) for s in specs)
        included = [s for s in specs if s.startswith(':(literal)')]
        assert not any('private' in s or '\n' in s for s in included)
        if ':(literal)docs' in included:  # a root search excludes every unreadable path
            assert f':(exclude,literal){PRIVATE}' in specs and f':(exclude,literal){CONTROL_PATH}' in specs


def test_results_are_gated_again_whatever_git_returns(repo, monkeypatch):
    monkeypatch.setattr(find_module, '_pathspecs', lambda state, family: (
        [':(literal)docs'], {p for p in state.report.resolved if find_module.cat.body_readable(state.report, p)}))
    result = find('secret', repo=repo)  # git now reads the private file; the gate must still drop it
    assert PRIVATE not in paths_of(result)


def test_only_the_bounded_runner_starts_git_grep():
    tree = ast.parse(Path(find_module.__file__).read_text(encoding='utf-8'))
    starters = sorted({fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
                       for node in ast.walk(fn) if isinstance(node, ast.Attribute)
                       and node.attr in ('Popen', 'run', 'check_output', 'call')
                       and getattr(node.value, 'id', None) == 'subprocess'})
    assert starters == ['_git_grep']


# ------------------------------------------------------------------ cut-offs are never "no source"

# The smallest budgets: the catalogue load alone (Git subprocesses) outlasts them, so the
# text search always starts past its deadline. Zero is not a budget (it is rejected).
SPENT_BUDGET = 1e-9


def test_an_exhausted_budget_is_incomplete_not_no_match(repo):
    result = find('zzqq-qqzz-xxyy', repo=repo, budget_seconds=SPENT_BUDGET)
    assert result['outcome'] == 'incomplete'
    assert result['coverage']['incomplete'] and result['coverage']['incomplete_reasons']
    assert all(reason.startswith('timeout') for reason in result['coverage']['incomplete_reasons'])


def test_an_output_cap_is_incomplete(repo, monkeypatch):
    monkeypatch.setattr(find_module, 'GREP_OUTPUT_CAP', 1)
    result = find('hostilename', repo=repo)
    assert result['coverage']['incomplete']
    assert any(r.startswith('output_budget') for r in result['coverage']['incomplete_reasons'])
    assert result['outcome'] == 'incomplete'  # never 'no_match'
    named = find('rf hostilename', repo=repo)
    assert named['outcome'] == 'found' and named['coverage']['incomplete']  # a name hit, flagged incomplete


def test_a_complete_search_with_nothing_is_no_match(repo):
    result = find('zzqq-qqzz-xxyy', repo=repo)
    assert (result['outcome'], result['hits'], result['coverage']['incomplete']) == ('no_match', [], False)


def test_a_cut_excerpt_read_keeps_the_hits_and_says_so(repo, monkeypatch):
    monkeypatch.setattr(find_module, 'EXCERPT_OUTPUT_CAP', 1)
    result = find('ULP 1-02', repo=repo)
    assert result['outcome'] == 'found' and not result['coverage']['excerpts_complete']
    # a cut excerpt read adds no incompleteness; only the reported one-character word does
    assert [r.split(':')[0] for r in result['coverage']['incomplete_reasons']] == ['content_search_skipped']


def test_an_invalid_catalogue_reads_no_text_and_says_why(fresh_repo, monkeypatch):
    (fresh_repo / 'docs/knowledge/catalogue.yaml').write_text('entries: [1]\n', encoding='utf-8')
    git(fresh_repo, 'add', '.')
    calls = recorded_greps(monkeypatch)
    result = find('rf', repo=fresh_repo)
    assert calls == []
    assert result['coverage']['incomplete'] and result['coverage']['incomplete_reasons'][0].startswith(
        'catalogue_invalid')
    assert 'docs/guide/-rf.md' in paths_of(result)  # names still answer


def test_coverage_names_searched_and_skipped_families(repo):
    cov = find('guide', repo=repo)['coverage']
    assert cov['families_searched'] == ['guide', 'knowledge', 'old', 'resources']
    assert cov['families_skipped'] == ['guide-private']
    assert cov['catalogue_errors'] == 1  # the control-character path


# ------------------------------------------------------------------ determinism and the memo

def test_results_are_deterministic(repo):
    find_module._STATE_CACHE.clear()
    first = find('ULP 1-02 hostilename', repo=repo, limit=50)
    find_module._STATE_CACHE.clear()
    second = find('ULP 1-02 hostilename', repo=repo, limit=50)
    first.pop('timings_ms'), second.pop('timings_ms')
    assert first == second


def test_the_memo_follows_the_index_and_the_catalogue(fresh_repo):
    assert find('freshword', repo=fresh_repo)['outcome'] == 'no_match'
    (fresh_repo / 'docs/guide/fresh.md').write_text('freshword\n', encoding='utf-8')
    git(fresh_repo, 'add', 'docs/guide/fresh.md')
    assert find('freshword', repo=fresh_repo)['hits'][0]['path'] == 'docs/guide/fresh.md'
    data = fixture_catalogue()
    data['entries'][1]['keywords'] = ['handbook', 'guide', 'freshkeyword']
    write_catalogue(fresh_repo, data)
    assert find('freshkeyword', repo=fresh_repo)['hits'][0]['match'] == 'entrypoint'


# ------------------------------------------------------------------ CLI

def test_cli_text_output_and_exit_codes(repo, capsys):
    assert main(['ULP 1-02', '--repo', str(repo)]) == 0
    out = capsys.readouterr().out
    assert 'docs/resources/list.txt:1' in out
    assert 'superseded -> docs/resources/list.txt, backup copy' in out
    assert main(['zzqq-qqzz-xxyy', '--repo', str(repo)]) == 1
    assert 'no_match' in capsys.readouterr().out
    assert main(['zzqq-qqzz-xxyy', '--repo', str(repo), '--budget', str(SPENT_BUDGET)]) == 5
    assert 'INCOMPLETE' in capsys.readouterr().out


@pytest.mark.parametrize('value', ['inf', '-inf', 'nan', 'NaN', '1e100', '1e400', '9' * 400, '-1', '0', '0.0', '-0',
                                   'abc', 'true', '', '121', '0x10'])
def test_cli_rejects_bad_budgets_with_a_fixed_message(repo, no_search_starts, capsys, value):
    assert main(['guide', '--repo', str(repo), '--json', f'--budget={value}']) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {'error': {'kind': 'invalid_request', 'code': 'budget',
                                                  'message': find_module.BUDGET_MESSAGE}}
    assert captured.err == ''


@pytest.mark.parametrize('value', ['0', '-1', '201', '1.5', 'true', 'abc', '', '9' * 30, '1e2', '0x10'])
def test_cli_rejects_bad_limits_with_a_fixed_message(repo, no_search_starts, capsys, value):
    assert main(['guide', '--repo', str(repo), f'--limit={value}']) == 2
    captured = capsys.readouterr()
    assert captured.out == f'Find could not run (invalid_request): limit: {find_module.LIMIT_MESSAGE}\n'
    assert captured.err == ''


@pytest.mark.parametrize('argv, code', [(['', ], 'empty_query'), (['x', '--limit', '0'], 'limit'),
                                        (['x', '--family', 'nope'], 'unknown_family')])
def test_cli_rejects_bad_requests_with_a_typed_error(repo, capsys, argv, code):
    assert main([*argv, '--repo', str(repo), '--json']) == 2
    assert json.loads(capsys.readouterr().out)['error']['code'] == code


def test_cli_json_is_the_library_result(repo, capsys):
    assert main(['handbook', '--repo', str(repo), '--json', '--limit', '3']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['hits'][0]['path'] == 'docs/guide/index.md' and len(result['hits']) <= 3


def test_cli_reports_an_unreadable_repository(tmp_path, capsys):
    assert main(['x', '--repo', str(tmp_path), '--json']) == 3
    assert json.loads(capsys.readouterr().out)['error']['kind'] == 'unreadable'


def test_cli_text_output_escapes_hostile_paths(fresh_repo, capsys):
    name = f'docs/guide/x{BIDI}y.md'
    (fresh_repo / name).write_text('bidiword\n', encoding='utf-8')
    git(fresh_repo, 'add', '.')
    assert main(['bidiword', '--repo', str(fresh_repo)]) == 0
    out = capsys.readouterr().out
    assert BIDI not in out and "'docs/guide/x\\u202ey.md'" in out


def test_cli_help_meets_the_standard(capsys):
    with pytest.raises(SystemExit):
        main(['--help'])
    out = capsys.readouterr().out
    for part in ('Examples:', 'Outputs:', 'Exit codes:', 'Related:', '--limit', '--family', '--json', 'default'):
        assert part in out


# ------------------------------------------------------------------ Monitor route

@pytest.fixture
def client(repo, monkeypatch):
    monkeypatch.setattr(api_main.app.state, 'ctx', api_main.app.state.ctx.with_roots(live_repo_root=repo))
    return TestClient(api_main.app, raise_server_exceptions=False)


def test_route_returns_the_library_result(client):
    response = client.get('/api/knowledge/find', params={'q': 'ULP 1-02', 'limit': 3})
    assert response.status_code == 200
    body = response.json()
    assert [h['path'] for h in body['hits']] == ['docs/resources/list.txt', 'docs/old/notes.md',
                                                 'docs/resources/list.txt.backup']
    assert body['coverage']['families_skipped'] == ['guide-private']


def test_route_is_not_behind_the_research_registry_kill_switch(client, monkeypatch):
    from scripts.research import registry as reg
    monkeypatch.setenv(reg.ENV_FLAG, 'false')
    monkeypatch.setattr(reg, 'is_enabled', lambda **_kwargs: False)
    assert client.get('/api/knowledge/manifest').json().get('enabled') is False  # the registry is off
    response = client.get('/api/knowledge/find', params={'q': 'handbook'})
    assert response.status_code == 200 and response.json()['hits'][0]['path'] == 'docs/guide/index.md'


@pytest.mark.parametrize('params', [{'q': 'x' * (find_module.MAX_QUERY_CHARS + 1)}, {}, {'q': ''},
                                    {'q': 'x', 'limit': 0}, {'q': 'x', 'limit': find_module.MAX_LIMIT + 1},
                                    {'q': 'x', 'family': 'Bad Family'}, {'q': 'x', 'family': 'a' * 65}])
def test_route_validates_its_parameters(client, params):
    assert client.get('/api/knowledge/find', params=params).status_code == 422


@pytest.mark.parametrize('limit', ['nan', 'inf', '-inf', '1e100', str(10 ** 30), '-1', '0', '1.5', 'true', 'abc', ''])
def test_route_rejects_bad_limits_before_any_search(client, no_search_starts, limit):
    response = client.get('/api/knowledge/find', params={'q': 'guide', 'limit': limit})
    assert response.status_code == 422


def test_route_maps_a_library_limit_error_to_a_typed_422(client, monkeypatch):
    def rejecting(*_args, **_kwargs):
        raise FindError('budget', find_module.BUDGET_MESSAGE)
    monkeypatch.setattr(find_module, 'find', rejecting)
    response = client.get('/api/knowledge/find', params={'q': 'x'})
    assert response.status_code == 422 and response.json()['detail']['code'] == 'budget'


@pytest.mark.parametrize('params, code', [({'q': ' \t '}, 'empty_query'), ({'q': 'x', 'family': 'nope'},
                                                                           'unknown_family')])
def test_route_typed_errors(client, params, code):
    response = client.get('/api/knowledge/find', params=params)
    assert response.status_code == 422
    assert response.json()['detail']['code'] == code


def test_route_unreadable_repository_is_a_typed_503(client, monkeypatch):
    def broken(*_args, **_kwargs):
        raise subprocess.CalledProcessError(128, ['git'])
    monkeypatch.setattr(find_module, 'find', broken)
    response = client.get('/api/knowledge/find', params={'q': 'x'})
    assert response.status_code == 503 and response.json()['detail']['code'] == 'CalledProcessError'


def test_route_source_never_consults_the_kill_switch():
    tree = ast.parse((REPO / 'scripts/api/knowledge_router.py').read_text(encoding='utf-8'))
    handler = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'knowledge_find')
    names = {n.attr for n in ast.walk(handler) if isinstance(n, ast.Attribute)}
    assert 'is_enabled' not in names and 'reg' not in {n.id for n in ast.walk(handler) if isinstance(n, ast.Name)}


def test_line_reads_send_git_exactly_one_pattern():
    # Several -e patterns with -n take tens of seconds on a large file (31.8 s measured on a
    # 20 MB YAML for two fixed strings, 0.45 s as one alternation), so line reads must
    # always pass one escaped alternation.
    import re
    args = find_module._line_args(['ulp', '02', 'весум', 'a.b(c)'], [':(literal)docs/x.md'], 10)
    assert args.count('-e') == 1 and '-E' in args and '-F' not in args
    alternation = args[args.index('-e') + 1]
    for form in ['ulp', '02', 'весум', 'ВЕСУМ', 'Весум', 'a.b(c)']:
        assert re.search(alternation, f'x {form} y')
    assert not re.search(alternation, 'axb(c)')
