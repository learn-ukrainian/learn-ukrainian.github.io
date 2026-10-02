"""The one query surface (#9412): ``scripts/docs/find.py``, its CLI and ``GET /api/knowledge/find``.

Every test runs against a small Git fixture repository, never the real tree (the
real-tree checks, including the dev-set lookups, live in
``tests/test_docs_catalogue_coverage.py``).
"""
import ast
import dataclasses
import functools
import json
import os
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
    # the one-character word '1' is matched in names, the catalogue and the phrase only: complete
    assert result['coverage']['incomplete_reasons'] == [] and result['coverage']['name_only_terms'] == ['1']


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
    assert result['coverage']['incomplete_reasons'] == [
        "error: the search for 'zzqq' did not finish (OverflowError)",
        'error: the code identifier search did not finish (OverflowError)']
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


def _alive(pid):
    try:
        os.kill(pid, 0)  # succeeds for a running or an unreaped (zombie) child
    except ProcessLookupError:
        return False
    return True


def _recording_popen(monkeypatch, argv=None):
    """Record every process the runner starts; ``argv`` swaps in a stand-in command."""
    started = []
    real_popen = find_module.subprocess.Popen

    def popen(real_argv, **kwargs):
        started.append(proc := real_popen(argv or real_argv, **kwargs))
        return proc
    monkeypatch.setattr(find_module.subprocess, 'Popen', popen)
    return started


def test_a_timer_that_cannot_be_built_leaves_no_search_process(fresh_repo, monkeypatch):
    # The defect: the timer was built after the process started and outside the cleanup,
    # so a MemoryError there left every started git grep running behind a typed result.
    def no_memory(*_args, **_kwargs):
        raise MemoryError
    started = _recording_popen(monkeypatch)
    monkeypatch.setattr(find_module.threading, 'Timer', no_memory)
    result = find('zzqq', repo=fresh_repo)
    assert result['outcome'] == 'incomplete'
    assert result['coverage']['incomplete_reasons'] == [
        "error: the search for 'zzqq' did not finish (MemoryError)",
        'error: the code identifier search did not finish (MemoryError)']
    assert all(proc.returncode is not None and not _alive(proc.pid) for proc in started)


@pytest.mark.parametrize('error', [MemoryError, KeyboardInterrupt, SystemExit])
def test_any_failure_after_the_process_starts_kills_and_reaps_it(monkeypatch, error):
    class FailingStart:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            raise error

        def cancel(self):
            pass
    started = _recording_popen(monkeypatch, [sys.executable, '-c', 'import time; time.sleep(60)'])
    monkeypatch.setattr(find_module.threading, 'Timer', FailingStart)
    tick = time.monotonic()
    with pytest.raises(error):  # the runner surfaces it; _total_grep types the Exception subclasses
        find_module._git_grep(Path('.'), [], time.monotonic() + 30, 1)
    assert len(started) == 1 and started[0].returncode is not None and not _alive(started[0].pid)
    assert time.monotonic() - tick < 5


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


def test_a_one_character_word_beside_longer_words_is_matched_in_names_and_reported(fresh_repo):
    # Beside longer words a one-character word is matched in names, the catalogue and the
    # phrase only; it is reported, never silent, and the search it belongs to is complete.
    result = find('zzqq Ω', repo=fresh_repo)  # Ω is in no file here; 'zzqq' and the phrase are searched
    assert (result['outcome'], result['coverage']['incomplete']) == ('no_match', False)
    assert result['coverage']['name_only_terms'] == ['ω'] and result['coverage']['incomplete_reasons'] == []
    found = find('ULP 1-02', repo=fresh_repo)
    assert found['outcome'] == 'found' and not found['coverage']['incomplete']
    assert found['coverage']['name_only_terms'] == ['1']
    assert find('zzqq', repo=fresh_repo)['coverage']['name_only_terms'] == []


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


def test_only_the_bounded_runner_starts_git():
    tree = ast.parse(Path(find_module.__file__).read_text(encoding='utf-8'))
    starters = sorted({fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
                       for node in ast.walk(fn) if isinstance(node, ast.Attribute)
                       and node.attr in ('Popen', 'run', 'check_output', 'call')
                       and getattr(node.value, 'id', None) == 'subprocess'})
    assert starters == ['_run_git']  # every git read (grep, ls-files) goes through the one bounded runner


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
    # a cut excerpt read adds no incompleteness
    assert result['coverage']['incomplete_reasons'] == [] and not result['coverage']['incomplete']


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
    assert 'ASCII digits only (0-9): no sign, no spaces, no decimal point or exponent' in ' '.join(out.split())


def test_openapi_limit_description_states_the_accepted_syntax():
    params = api_main.app.openapi()['paths']['/api/knowledge/find']['get']['parameters']
    limit = next(p for p in params if p['name'] == 'limit')
    assert 'ASCII digits only (0-9): no sign, no spaces, no decimal point or exponent' in limit['description']


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


NON_DIGIT_LIMITS = ['5.0', '5e0', '+5', ' 5', '5 ', '-0', '５', '0x5', '5_0']


@pytest.mark.parametrize('limit', ['nan', 'inf', '-inf', '1e100', str(10 ** 30), '-1', '0', '1.5', 'true', 'abc', '',
                                   *NON_DIGIT_LIMITS])
def test_route_rejects_bad_limits_before_any_search(client, no_search_starts, limit):
    response = client.get('/api/knowledge/find', params={'q': 'guide', 'limit': limit})
    assert response.status_code == 422
    assert response.json()['detail'] == {'code': 'limit', 'message': f'limit: {find_module.LIMIT_MESSAGE}'}


def test_route_checks_every_repeated_limit_before_any_search(client, no_search_starts):
    response = client.get('/api/knowledge/find?q=guide&limit=5.0&limit=5')
    assert response.status_code == 422 and response.json()['detail']['code'] == 'limit'


@pytest.mark.parametrize('limit', ['5', '05', str(find_module.MAX_LIMIT)])
def test_route_accepts_the_digit_limits_the_library_accepts(client, limit):
    assert find_module.limit_from_text(limit) == int(limit)
    response = client.get('/api/knowledge/find', params={'q': 'guide', 'limit': limit})
    assert response.status_code == 200
    assert len(response.json()['hits']) <= int(limit)


@pytest.mark.parametrize('value', NON_DIGIT_LIMITS)
def test_cli_and_library_reject_the_same_non_digit_limits(repo, no_search_starts, capsys, value):
    with pytest.raises(FindError):
        find_module.limit_from_text(value)
    assert main(['guide', '--repo', str(repo), f'--limit={value}']) == 2
    assert capsys.readouterr().out == f'Find could not run (invalid_request): limit: {find_module.LIMIT_MESSAGE}\n'


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


# ------------------------------------------------------------------ status and implementation questions

CODE_FILES = {
    'scripts/checks/verdict.py': (
        '"""Review verdict checks for the fixture."""\n'
        '\n'
        '\n'
        'def parse_review_verdict(text):\n'
        '    """Return the verdict line of a review."""\n'
        '    return text\n'
        '\n'
        '\n'
        'def _containment_anchor(agent):\n'
        '    """Return the dispatch directory when each level is real."""\n'
        '    return agent\n'
        '\n'
        '\n'
        "ERROR = {'type': 'SELF_REVIEW_DETECTED'}\n"
        + '\n' * 20 + '# zebra quokka: a comment past the header is prose, not a definition\n'),
    'scripts/config/models.yaml': 'models:\n  retired-model-9:\n    lifecycle: retired\n    replaced_by: new-model-10\n',
    'scripts/private/secret_tool.py': 'def parse_review_verdict_secret():\n    pass\n',
    'scripts/verdict_dump.json': '{"parse_review_verdict": 1}\n',
    'tests/test_verdict_parsing.py': 'def test_parse_review_verdict():\n    pass\n',
    'docs/guide/verdicts.md': 'Reviewers write a verdict; parse_review_verdict parses the review verdict in code.\n',
    'docs/guide/legacy-deck.txt': 'Legacy deck notes.\n',
    'docs/guide/deck-v2.txt': 'Deck version two.\n',
}


@pytest.fixture(scope='module')
def code_repo(tmp_path_factory):
    root = make_repo(tmp_path_factory.mktemp('find-code') / 'repo')
    for rel, text in CODE_FILES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')
    data = fixture_catalogue()
    guide = next(e for e in data['entries'] if e['id'] == 'guide')
    guide['overrides'] = [{'path': 'docs/guide/legacy-deck.txt', 'lifecycle': 'superseded',
                           'superseded_by': 'docs/guide/deck-v2.txt', 'evidence': 'Replaced by version two.'}]
    data['entries'].append(entry('retired-guide', ['docs/retired/**'], keywords=['retired guide'],
                                 lifecycle='superseded', superseded_by='id:guide'))
    (root / 'docs/retired').mkdir()
    (root / 'docs/retired/old.md').write_text('# Old guide\n', encoding='utf-8')
    write_catalogue(root, data)
    git(root, 'add', '.')
    return root


@pytest.mark.parametrize('query, plan', [
    ('Is the legacy deck still current, and what replaced it?', (['legacy', 'deck'], ['still', 'current', 'replaced'])),
    ('where is resolve-reviewer implemented', (['resolve', 'reviewer'], ['implemented'])),
    ('current', (['current'], [])),  # an intent word alone is the query
    ('is retired-model-9 current', (['retired', 'model', '9'], ['current'])),  # a typed name keeps its words
    ('task lifecycle closeout', (['task', 'lifecycle', 'closeout'], [])),  # lifecycle is a content word
])
def test_intent_words_are_not_search_terms_beside_other_words(query, plan):
    assert find_module.query_plan(query) == plan
    assert query_terms(query) == plan[0]


def test_a_long_question_keeps_its_content_words_within_the_term_cap():
    terms, intent = find_module.query_plan('Is the alpha beta gamma delta epsilon zeta eta theta still current, '
                                           'and what replaced it?')
    assert terms == ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta']
    assert intent == ['still', 'current', 'replaced']


@pytest.mark.parametrize('term, stemmed', [('parsing', 'pars'), ('detected', 'detect'), ('reaps', 'reap'),
                                           ('branches', 'branch'), ('lines', 'line'), ('process', 'process'),
                                           ('uses', 'uses'), ('deck', 'deck')])
def test_stem_strips_one_inflection_and_keeps_four_letters(term, stemmed):
    assert find_module.stem(term) == stemmed


def test_terms_meet_inflected_words_as_prefixes():
    assert find_module._prefix_hits(['parsing', 'verdicts'], ['parse', 'review', 'verdict']) == {'parsing', 'verdicts'}
    assert find_module._prefix_hits(['parsing'], ['sparse']) == set()


# Two inflections of one word meet however far each runs past their shared part; a word that only
# begins with the term's stem and runs on by unrelated letters does not.
@pytest.mark.parametrize('term, word', [
    ('translated', 'translations'), ('mapped', 'mapping'), ('decolonizing', 'decolonization'),
    ('assessing', 'assessment'), ('evaluations', 'evaluation'), ('hallucinated', 'hallucinations'),
    ('recorded', 'recordings'), ('evaluating', 'evaluations'), ('map', 'mapping'), ('set', 'settings'),
    ('parsing', 'parser'), ('reaps', 'reaper'), ('detection', 'detector'), ('pack', 'packed'),
    ('migration', 'migrate'), ('entries', 'entry'), ('invented', 'invention'),
])
def test_a_term_meets_another_inflection_of_its_word(term, word):
    assert find_module._prefix_hits([term], [word]) == {term}


@pytest.mark.parametrize('term, word', [
    ('pack', 'packages'), ('reading', 'readiness'), ('worked', 'worktree'), ('pro', 'projects'),
    ('state', 'status'), ('generated', 'general'), ('com', 'command'), ('invented', 'inventory'),
    ('ci', 'city'),
])
def test_a_term_never_meets_a_word_that_only_begins_like_it(term, word):
    assert find_module._prefix_hits([term], [word]) == set()


def test_two_query_words_meet_a_closed_compound_path_word():
    path = find_module.name_words('docs/resources/ukrainianlessons/MAPPING_REPORT.md')
    assert find_module.compound_hits(['ukrainian', 'lessons', 'mapped'], path) == {'ukrainian', 'lessons'}
    assert find_module.compound_hits(['talk', 'ukrainian'], ['talkukrainian', 'db']) == {'talk', 'ukrainian'}
    assert find_module.compound_hits(['layer', 'b', 'gate'], ['tests', 'layerb']) == {'layer', 'b'}
    assert find_module.compound_hits(['ukrainian'], ['ukrainianlessons']) == set()  # one word is no compound
    assert find_module.compound_hits(['lessons', 'ukrainian'], ['ukrainian', 'lessons']) == set()


def test_a_closed_compound_directory_names_its_files(repo):
    path = 'docs/resources/talkukrainian/talkukrainian_db.json'
    state = dataclasses.replace(_state(repo, fixture_catalogue()), files={path: None})
    terms = ['talk', 'ukrainian', 'database']
    assert find_module._name_candidates(state, terms, terms, None, [])[path].name_terms == {'talk', 'ukrainian'}


@pytest.mark.parametrize('query, units', [
    ('Where is the check_russian_shadow tool handled?', ['check_russian_shadow']),
    ('ULP 1-02', ['1-02']),
    ('resolve-reviewer', []),  # the whole query is the phrase, not a separate unit
    ('"atlas.db" and gpt-6-astra?', ['atlas.db', 'gpt-6-astra']),
    ('teacher deck rebuild', []),
])
def test_compounds_are_the_typed_identifiers(query, units):
    assert find_module.compounds(clean_query(query)) == units


@pytest.mark.parametrize('path, readable', [
    ('scripts/review/closeout_cli.py', True), ('.githooks/pre-push', True), ('AGENTS.md', True),
    ('scripts/config/model_catalog.yaml', True), ('agents_extensions/shared/rules/core.md', True),
    ('scripts/private/tool.py', False), ('scripts/cache/x.py', False), ('docs/guide/x.py', False),
    ('tests/test_x.py', False), ('scripts/data.json', False), ('curriculum/a1/x.yaml', False),
    ('scripts/bad\nname.py', False),
])
def test_code_readable_is_the_privacy_gate_for_code(path, readable):
    assert find_module.code_readable(path) is readable


@pytest.mark.parametrize('path, line_no, line, text', [
    ('a.py', 40, 'def parse_review_verdict(text):', 'parse_review_verdict'),
    ('a.py', 40, 'class CfPreflightResult:', 'Cf Preflight Result'),
    ('a.py', 40, "    sub.add_parser('resolve-reviewer', help='x')", 'resolve-reviewer'),
    ('a.py', 40, "    parser.add_argument('--allow-no-cf-preflight')", '--allow-no-cf-preflight'),
    ('a.py', 40, """    p.add_argument('q', help='Words to look for, e.g. "ULP 1-02"')""", 'Words to look for, e.g.  '),
    ('a.py', 40, "ERROR = {'type': 'SELF_REVIEW_DETECTED'}", 'ERROR SELF_REVIEW_DETECTED'),
    ('a.py', 40, "        raise Fail('SELF_REVIEW_DETECTED')", 'SELF_REVIEW_DETECTED'),
    ('a.py', 2, '"""Safe post-task reaper for dispatch worktrees.', 'Safe post-task reaper for dispatch worktrees.'),
    ('a.py', 2, '# Wrapper for the nightly backup', '# Wrapper for the nightly backup'),
    ('a.py', 40, '# a comment past the header', None),
    ('a.py', 3, '    x = parse(text)', None),
    ('a.yaml', 40, '  gpt-6-astra:', 'gpt-6-astra'),
    ('a.yaml', 40, '  - {id: data-vesum-db, kind: data_store}', 'data-vesum-db'),
    ('a.sh', 40, 'linux_backup_database() {', 'linux_backup_database'),
    ('a.ts', 40, 'export const routeTable = {', 'route Table'),
    ('a.md', 40, '## Review routing', 'Review routing'),
    ('a.md', 40, 'Plain prose about review routing.', None),
    ('a.toml', 40, '[tool.pytest.ini_options]', 'tool.pytest.ini_options'),
])
def test_symbol_text_reads_identifiers_and_file_summaries_only(path, line_no, line, text):
    assert find_module.symbol_text(path, line_no, line) == text


def test_a_code_definition_outranks_prose_that_mentions_it(code_repo):
    result = find('review verdict parsing', repo=code_repo)
    first = result['hits'][0]
    assert (first['path'], first['match'], first['line'], first['excerpt']) == (
        'scripts/checks/verdict.py', 'symbol', 4, 'def parse_review_verdict(text):')
    assert first['matched'] == ['parsing', 'review', 'verdict']
    paths = paths_of(result)
    assert 'docs/guide/verdicts.md' in paths  # prose still answers, below the definition
    assert 'scripts/private/secret_tool.py' not in paths  # privacy-excluded code is never read
    assert hit_for(result, 'tests/test_verdict_parsing.py')['match'] == 'name'  # tests are not implementations
    assert 'scripts/verdict_dump.json' not in paths or hit_for(result, 'scripts/verdict_dump.json')['match'] == 'name'
    assert result['coverage']['code_files_searched'] > 0


def test_the_code_search_never_reads_a_private_path(code_repo, monkeypatch):
    find_module._STATE_CACHE.clear()
    calls = recorded_greps(monkeypatch)
    find('review verdict parsing', repo=code_repo)
    code_call = next(c for c in calls if ':(literal)scripts' in c)
    assert ':(exclude,literal)scripts/private/secret_tool.py' in code_call
    assert ':(exclude,literal)scripts/verdict_dump.json' in code_call
    assert not any(arg.startswith(':(literal)docs') or arg.startswith(':(literal)tests') for arg in code_call)


def test_a_definition_and_its_docstring_are_one_unit(code_repo):
    hit = hit_for(find('dispatch anchor', repo=code_repo), 'scripts/checks/verdict.py')
    # The unit is the definition's span; its excerpt is the definition line.
    assert hit['matched'] == ['anchor', 'dispatch'] and (hit['line'], hit['excerpt']) == (
        9, 'def _containment_anchor(agent):')


def test_a_quoted_typed_code_is_an_identifier(code_repo):
    hit = hit_for(find('where is self review detected', repo=code_repo), 'scripts/checks/verdict.py')
    assert hit['match'] == 'symbol' and hit['matched'] == ['detected', 'review', 'self']


def test_a_comment_past_the_header_is_not_an_identifier(code_repo):
    result = find('zebra quokka', repo=code_repo)
    assert 'scripts/checks/verdict.py' not in paths_of(result)


def test_a_typed_identifier_ranks_its_definition_first(code_repo):
    result = find('where is parse_review_verdict', repo=code_repo)
    assert paths_of(result)[0] == 'scripts/checks/verdict.py'
    assert 'docs/guide/verdicts.md' in paths_of(result)


def test_a_configuration_key_answers_a_status_question(code_repo):
    result = find('is retired-model-9 still current', repo=code_repo)
    assert result['intent_words'] == ['still', 'current'] and result['terms'] == ['retired', 'model', '9']
    hit = hit_for(result, 'scripts/config/models.yaml')
    assert (hit['match'], hit['line'], hit['excerpt']) == ('symbol', 2, 'retired-model-9:')


def test_a_superseded_hit_is_followed_by_its_replacement(code_repo):
    result = find('legacy deck still current', repo=code_repo)
    paths = paths_of(result)
    old = paths.index('docs/guide/legacy-deck.txt')
    assert result['hits'][old]['status'] == 'superseded'
    replacement = result['hits'][old + 1]
    assert (replacement['path'], replacement['match'], replacement['replaces'], replacement['status']) == (
        'docs/guide/deck-v2.txt', 'replacement', 'docs/guide/legacy-deck.txt', 'current')
    assert paths.count('docs/guide/deck-v2.txt') == 1  # never twice
    text = find_module.format_text(result)
    assert 'docs/guide/legacy-deck.txt:1  [content; guide; superseded -> docs/guide/deck-v2.txt]' in text
    assert 'docs/guide/deck-v2.txt  [replacement; guide; current, replaces docs/guide/legacy-deck.txt]' in text


def test_a_family_superseded_by_an_entry_is_followed_by_that_entry(code_repo):
    result = find('retired guide', repo=code_repo)
    hits = result['hits']
    family = next(i for i, h in enumerate(hits) if h.get('family') == 'retired-guide')
    assert hits[family]['superseded_by'] == 'id:guide'
    assert (hits[family + 1]['path'], hits[family + 1]['match'], hits[family + 1]['replaces']) == (
        'docs/guide/index.md', 'replacement', 'retired-guide')


def test_a_status_question_ranks_every_lifecycle_alike_except_backups(repo):
    state = find_module.load_state(repo)
    assert find_module._lifecycle_rank(state, 'docs/old/notes.md') == 2
    assert find_module._lifecycle_rank(state, 'docs/old/notes.md', status_question=True) == 0
    assert find_module._lifecycle_rank(state, 'docs/resources/list.txt.backup', status_question=True) == (
        find_module.BACKUP_RANK)


def test_code_rarity_counts_identifier_files(code_repo):
    state = find_module.load_state(code_repo)
    scan = find_module._symbol_scan(state, ['verdict', 'zzqq'], time.monotonic() + 30)
    assert scan.df == {'verdict': 1} and scan.failure is None
    assert scan.lines['scripts/checks/verdict.py'][1] == 1  # the first line with the most words: the summary


def test_a_code_search_failure_is_reported_incomplete(code_repo, monkeypatch):
    monkeypatch.setattr(find_module, 'CODE_OUTPUT_CAP', 1)
    result = find('review verdict parsing', repo=code_repo)
    assert result['coverage']['incomplete']
    assert 'output_budget: the code identifier search did not finish' in result['coverage']['incomplete_reasons']


def test_the_code_search_is_skipped_with_a_family(code_repo):
    result = find('verdict', family='guide', repo=code_repo)
    assert result['coverage']['code_files_searched'] == 0
    assert 'scripts/checks/verdict.py' not in paths_of(result)


# ------------------------------------------------------------------ ranking helpers and lifecycle records

@pytest.mark.parametrize('term, stemmed', [('approval', 'approv'), ('proposals', 'propos'), ('renewal', 'renew'),
                                           ('signal', 'signal'), ('usual', 'usual'), ('journal', 'journal')])
def test_a_verbs_al_noun_meets_the_verb(term, stemmed):
    assert find_module.stem(term) == stemmed


def test_numerals_meet_their_words_both_ways():
    assert find_module._prefix_hits(['four', 'rounds'], ['cap', 'at', '4', 'rounds']) == {'four', 'rounds'}
    assert find_module._prefix_hits(['4'], ['four', 'rounds']) == {'4'}
    assert find_module._prefix_hits(['four'], ['44']) == set()


@pytest.mark.parametrize('lines, record', [
    ([(1, '| dec-3 | superseded | Cap review fix rounds at 4 |')], {'review', 'fix', 'four'}),
    ([(1, 'Review fix rounds are capped at 4.')], set()),  # no lifecycle word: not a record
    ([(1, 'The legacy review notes.')], set()),  # one query word beside "legacy" is any sentence
    ([(1, 'x' * 1001 + ' superseded review fix')], set()),  # a one-line dump is no record
    ([(1, '# the glm lane is retired'), (2, 'review: fix')], set()),  # marker and words on different lines
])
def test_a_lifecycle_record_is_one_line_with_a_marker_and_two_query_words(lines, record):
    assert find_module.lifecycle_record(lines, ['review', 'fix', 'four']) == record


def test_a_record_counts_only_when_it_names_most_of_the_question():
    weights = {'zorbl': 3.0, 'loops': 1.0, 'cap': 0.5}
    named = find_module.Candidate('a', record_terms={'zorbl', 'loops'})
    common = find_module.Candidate('b', record_terms={'loops', 'cap'})
    assert find_module.record_share(named, ['zorbl', 'loops', 'cap'], weights) == pytest.approx(4 / 4.5)
    assert find_module.record_share(common, ['zorbl', 'loops', 'cap'], weights) == 0.0
    assert find_module.field_weight(named, 'zorbl', record=True) == 1.0
    assert find_module.field_weight(named, 'zorbl') == 0.0  # outside a status question a record is no field


@pytest.mark.parametrize('hit, historical', [
    ({'path': 'docs/a.md', 'lifecycle': 'archive'}, True),
    ({'path': 'docs/a.md', 'lifecycle': 'superseded'}, True),
    ({'path': 'docs/a.md', 'lifecycle': 'active', 'backup_like': True}, True),
    ({'path': 'scripts/legacy/tool/run.py', 'lifecycle': None}, True),
    ({'path': 'scripts/assets/scripts-deprecated/a.js', 'lifecycle': None}, True),
    ({'path': 'scripts/oldest/a.py', 'lifecycle': None}, False),  # a word, not a prefix
    ({'path': 'docs/a.md', 'lifecycle': 'active'}, False),
])
def test_a_historical_hit_is_catalogued_backed_up_or_named_so(hit, historical):
    assert find_module.is_historical(hit) is historical


@pytest.mark.parametrize('path, found', [
    ('.gitattributes', ['git', 'attributes']), ('site/.gitignore', ['site', 'git', 'ignore']),
    ('docs/guide/README.md', ['docs', 'guide']), ('docs/guide/notes.md', ['docs', 'guide', 'notes', 'md']),
])
def test_name_words_split_git_files_and_drop_index_names(path, found):
    assert find_module.name_words(path) == found


@pytest.mark.parametrize('path, line, text', [
    ('.gitattributes', 'data/texts/*.jsonl filter=lfs diff=lfs -text', 'data/texts/*.jsonl filter=lfs diff=lfs -text'),
    ('site/.gitignore', 'node_modules/', 'node_modules/'),
    ('.gitattributes', '   ', None),
])
def test_git_pattern_files_are_read_as_identifiers(path, line, text):
    assert find_module.symbol_text(path, 40, line) == text


@pytest.mark.parametrize('text, process', [
    ('what stops an agent from deleting a worktree', True), ('where do we check the trailer', True),
    ('where is resolve-reviewer implemented', True), ('teacher deck rebuild', False),
    ('where is the podcast list', False), ('check the trailer', False),
])
def test_a_process_question_asks_where_something_is_done(text, process):
    assert find_module.is_process_question(text, find_module.query_plan(text)[1]) is process


def test_a_passage_is_query_words_together_within_a_few_lines():
    lines = [(1, 'alpha here'), (2, 'beta there'), (9, 'gamma far away'), (10, 'x' * 1001 + ' alpha beta gamma')]
    assert find_module.best_passage(lines, ['alpha', 'beta', 'gamma']) == {'alpha', 'beta'}
    assert find_module.best_passage([(1, 'alpha only')], ['alpha', 'beta']) == set()


@pytest.mark.parametrize('path, covered', [
    ('.python-version', True), ('docs/python-version-notes.md', False), ('docs/README.md', False),
])
def test_a_name_is_covered_when_every_word_of_it_is_a_query_word(path, covered):
    assert find_module.name_covered(path, ['python', 'version', 'pin']) is covered


def test_length_factor_and_rarity_follow_bm25():
    assert find_module.length_factor(None, 100.0) == 1.0
    assert find_module.length_factor(10, 100.0) == 1.0  # capped: a short file is never above a name
    assert find_module.length_factor(1000, 100.0) < find_module.length_factor(200, 100.0) < 1.0
    assert find_module.rarity(1000, 1) > find_module.rarity(1000, 100) > find_module.rarity(1000, 900)
    assert find_module.rarity(1000, 1000) == find_module.MIN_RARITY


def test_summary_lines_are_the_header_of_a_program_and_the_lead_of_markdown():
    py = [(1, '#!/usr/bin/env python'), (2, '"""Prune stale worktrees.'), (3, 'Second line."""'),
          (4, 'import os'), (5, '# not the header')]
    assert find_module.summary_lines('a.py', py) == py[1:3]
    md = [(1, '---'), (2, 'description: Rules for agents'), (3, '---'), (4, '# Title'), (5, 'First paragraph.'),
          (6, ''), (7, 'Second paragraph.')]
    assert find_module.summary_lines('a.md', md) == [md[1], md[3], md[4]]
    ini = [(1, '[Unit]'), (2, 'Description=Nightly backup'), (3, 'After=network.target')]
    assert find_module.summary_lines('a.service', ini) == [ini[1]]


HISTORY_FILES = {
    'docs/decisions/INDEX.md': ('# Decisions\n\n| ID | Status | Title |\n| --- | --- | --- |\n'
                                '| dec-9 | superseded | Cap zorbl loops at 4 rounds |\n'
                                '| dec-8 | active | [Quux plan](2026-01-01-quux-plan.md) |\n'),
    'docs/decisions/2026-01-01-quux-plan.md': '# Quux plan\nWe plan the quux rollout.\n',
    'docs/guide/zorbl.md': 'Zorbl loops are fun.\nMore zorbl loops.\n',
    'scripts/legacy/widget/README.md': '# Widget\nDeprecated: the widget runner is not used any more.\n',
    'scripts/legacy/widget/run.py': 'def widget_runner():\n    """Run the widget."""\n',
}


@pytest.fixture(scope='module')
def history_repo(tmp_path_factory):
    root = make_repo(tmp_path_factory.mktemp('find-history') / 'repo')
    for rel, text in HISTORY_FILES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')
    data = fixture_catalogue()
    data['entries'].append(entry('decisions', ['docs/decisions/**'], kind='registry', keywords=['decision journal'],
                                 entrypoints=[{'topic': 'decision index', 'path': 'docs/decisions/INDEX.md'}],
                                 overrides=[{'path': 'docs/decisions/2026-01-01-quux-plan.md', 'lifecycle': 'archive',
                                             'evidence': 'Shipped.'}]))
    write_catalogue(root, data)
    git(root, 'add', '.')
    return root


def test_a_registry_row_answers_a_status_question(history_repo):
    result = find('Do we still cap zorbl loops after four rounds?', repo=history_repo)
    first = result['hits'][0]
    assert (first['path'], first['line']) == ('docs/decisions/INDEX.md', 5)
    assert 'four' in first['matched']
    plain = find('cap zorbl loops four rounds', repo=history_repo)  # no status intent: no record weight
    assert hit_for(plain, 'docs/decisions/INDEX.md')


def test_a_historical_document_is_followed_by_the_index_that_names_it(history_repo):
    result = find('is the quux plan still current', repo=history_repo)
    paths = paths_of(result)
    doc = paths.index('docs/decisions/2026-01-01-quux-plan.md')
    assert result['hits'][doc]['status'] == 'historical'
    record = result['hits'][doc + 1]
    assert (record['path'], record['match'], record['records'], record['line']) == (
        'docs/decisions/INDEX.md', 'lifecycle_record', 'docs/decisions/2026-01-01-quux-plan.md', 6)
    assert 'Quux plan' in record['excerpt'] and paths.count('docs/decisions/INDEX.md') == 1
    assert ('docs/decisions/INDEX.md:6  [lifecycle_record; decisions; current, records the lifecycle of '
            'docs/decisions/2026-01-01-quux-plan.md]') in find_module.format_text(result)


def test_legacy_code_is_followed_by_the_readme_of_its_directory(history_repo):
    result = find('is the widget runner still used', repo=history_repo)
    paths = paths_of(result)
    code = paths.index('scripts/legacy/widget/run.py')
    record = result['hits'][code + 1]
    assert (record['path'], record['match'], record['records'], record['line']) == (
        'scripts/legacy/widget/README.md', 'lifecycle_record', 'scripts/legacy/widget/run.py', None)


def test_lifecycle_records_follow_only_status_questions(history_repo):
    result = find('widget runner', repo=history_repo)
    assert all(hit['match'] != 'lifecycle_record' for hit in result['hits'])


def test_lifecycle_authorities_never_name_an_unreadable_file(history_repo):
    state = find_module.load_state(history_repo)
    assert find_module.lifecycle_authorities(state, 'docs/decisions/2026-01-01-quux-plan.md') == (
        ['docs/decisions/INDEX.md'], ['docs/decisions/INDEX.md'])
    assert find_module.lifecycle_authorities(state, 'scripts/legacy/widget/run.py') == (
        [], ['scripts/legacy/widget/README.md'])
    assert PRIVATE.rsplit('/', 1)[0] not in find_module.directory_indexes(state)


def test_the_catalogue_and_its_generated_map_are_no_second_record(history_repo):
    state = find_module.load_state(history_repo)
    echoes = find_module.catalogue_echoes(state)
    assert {'docs/knowledge/catalogue.yaml', 'docs/README.md'} <= echoes
    assert 'docs/decisions/INDEX.md' not in echoes


# ------------------------------------------------------------------ private directories, abbreviations, function spans

PRIVATE_NOTE = 'docs/guide/sub/private/README.md'


@pytest.fixture(scope='module')
def note_repo(tmp_path_factory):
    root = make_repo(tmp_path_factory.mktemp('find-note') / 'repo')
    (root / PRIVATE_NOTE).write_text('# Private notes\nThese files are compatibility routes, no longer live state.\n',
                                     encoding='utf-8')
    git(root, 'add', '.')
    return root


def test_a_private_directory_note_is_searched_and_its_bodies_never_are(note_repo, monkeypatch):
    find_module._STATE_CACHE.clear()
    calls = recorded_greps(monkeypatch)
    note = find('compatibility routes live state', repo=note_repo)
    assert paths_of(note)[0] == PRIVATE_NOTE and note['hits'][0]['match'] == 'content'
    body = find('private sentinel hostilename', repo=note_repo, limit=50)
    assert PRIVATE not in paths_of(body)
    assert all('sentinel' not in (hit['excerpt'] or '') for hit in body['hits'])
    text_calls = [c for c in calls if ':(literal)docs' in c]
    assert text_calls and all(f':(exclude,literal){PRIVATE}' in c for c in text_calls)
    assert not any(f':(literal){PRIVATE}' in c for c in calls)


def test_a_question_naming_a_private_file_is_answered_by_its_directory_note(note_repo):
    result = find(f'Is {PRIVATE} still live?', repo=note_repo)
    # The catalogue's family hits come first ("guide" is the fixture family's keyword); then the note.
    found = [hit['path'] for hit in result['hits'] if hit['match'] not in ('entrypoint', 'family')]
    assert found[0] == PRIVATE_NOTE and PRIVATE not in paths_of(result)
    state = find_module.load_state(note_repo)
    assert find_module.private_note(state, PRIVATE) == PRIVATE_NOTE
    assert find_module.private_note(state, 'docs/guide/index.md') is None  # not a private path


def test_a_private_file_is_never_spoken_for_by_a_note_above_its_directory(repo):
    # docs/guide/index.md sits above the private directory and does not know its files.
    state = find_module.load_state(repo)
    assert find_module.private_note(state, PRIVATE) is None
    assert 'docs/guide/index.md' not in paths_of(find('secret', repo=repo))


@pytest.mark.parametrize('line, pairs', [
    ('**Definition of Ready (DoR):** may start only when', [('dor', ('definition', 'of', 'ready'))]),
    ('Do not confuse it with the Definition of Done (DoD).', [('dod', ('definition', 'of', 'done'))]),
    ('Independent cross-family (CF) formal review', [('cf', ('cross', 'family'))]),
    ('CF (cross-family) review is mandatory', [('cf', ('cross', 'family'))]),
    ('Formal Code Review (CF) snapshots', []),  # the initials do not spell CF
    ('see the issue (TBD) later', []),
    ('the Model Context Protocol (MCP) server', [('mcp', ('model', 'context', 'protocol'))]),
])
def test_abbreviations_are_the_pairs_whose_initials_spell_them(line, pairs):
    assert find_module.defined_pairs(line) == pairs


def test_abbreviations_meet_their_defined_words_both_ways():
    table = find_module.Abbreviations({'dor': ('definition', 'of', 'ready')})
    assert table.expand(['run', 'dor', 'preflight']) == ['run', 'dor', 'preflight', 'definition', 'ready']
    assert table.expand(['definition', 'of', 'ready', 'report']) == ['definition', 'of', 'ready', 'report', 'dor']
    assert table.expand(['ready', 'definition']) == ['ready', 'definition']  # not the defined run
    assert table.query_patterns(['where', 'is', 'the', 'definition', 'of', 'ready'], ['definition', 'ready']) == (
        [], ['dor'])
    assert table.query_patterns(['dor', 'gate'], ['dor', 'gate']) == (['definit', 'ready'], [])  # stems


def test_a_whole_word_pattern_never_selects_a_longer_word():
    args = find_module._line_args(['gate'], ['x'], None, ['dor'])
    pattern = args[args.index('-e') + 1]
    import re
    assert re.search(pattern, '_run_dor_preflight(', re.IGNORECASE)
    assert re.search(pattern, 'DoR gate', re.IGNORECASE)
    assert not re.search(pattern, 'vendor door', re.IGNORECASE)


SPAN_FILE = (
    'def first():\n'
    '    """One line."""\n'
    'TEMPLATE = """\n'
    'def quoted_inside_a_string():\n'
    '"""\n'
    'class Holder:\n'
    '    """Holds things.\n'
    '\n'
    '    More about holding.\n'
    '    """\n'
    'def bare():\n'
    '    return 1\n'
)


def test_python_spans_run_from_a_definition_to_the_end_of_its_docstring():
    lines = [(no, text) for no, text in enumerate(SPAN_FILE.splitlines(), 1)
             if find_module.DEF_LINE.match(text) or '"""' in text]
    spans = find_module.python_spans(lines)
    assert spans == [(1, 2, 'def first():'), (6, 10, 'class Holder:'), (11, 11, 'def bare():')]
    assert find_module.enclosing_span(spans, 9) == (6, 10, 'class Holder:')
    assert find_module.enclosing_span(spans, 4) is None  # inside a string constant
    assert find_module.enclosing_span(spans, 12) is None  # the body after the docstring


FILLER = ''.join(f'def helper_{i}(value):\n    """Return value {i} unchanged."""\n    return value\n\n'
                 for i in range(400))
TERM_FILES = {
    'agents_extensions/shared/rules/terms.md': (
        '# Terms\n\n**Definition of Ready (DoR):** a task may start only when its card is green.\n'),
    'scripts/gate.py': (
        '"""Fixture launcher with many helpers."""\n\n\n' + FILLER
        + 'def _run_dor_preflight(prompt):\n'
          '    """Look at each issue a brief names.\n\n'
          '    Refuse before any dispatch side effect.\n'
          '    """\n'
          '    return prompt\n'),
    'scripts/report.py': 'def definition_of_ready_report():\n    return 1\n',
    'scripts/noise.py': 'def door_vendor():\n    """Open the vendor door before dispatch."""\n',
}


@pytest.fixture(scope='module')
def term_repo(tmp_path_factory):
    root = make_repo(tmp_path_factory.mktemp('find-terms') / 'repo')
    for rel, text in TERM_FILES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')
    git(root, 'add', '.')
    return root


def test_the_abbreviation_table_is_derived_from_the_governing_documents(term_repo):
    state = find_module.load_state(term_repo)
    table, failure = find_module.abbreviations(state, time.monotonic() + 30)
    assert failure is None and table.defined == {'dor': ('definition', 'of', 'ready')}


def test_a_defined_term_finds_the_function_that_uses_its_abbreviation_in_a_large_file(term_repo):
    result = find('Where is the definition of ready checked before a dispatch?', repo=term_repo)
    first = result['hits'][0]
    assert (first['path'], first['match'], first['excerpt']) == (
        'scripts/gate.py', 'symbol', 'def _run_dor_preflight(prompt):')
    assert {'definition', 'ready', 'dispatch'} <= set(first['matched'])
    assert 'scripts/noise.py' not in paths_of(result)[:1]


def test_a_typed_abbreviation_finds_an_identifier_spelled_out(term_repo):
    result = find('DoR report', repo=term_repo)
    first = result['hits'][0]
    assert first['path'] == 'scripts/report.py' and first['matched'] == ['dor', 'report']


def test_a_family_keyword_naming_one_entry_point_credits_that_entry_point_only(tmp_path):
    root = make_repo(tmp_path / 'repo')
    for rel in ('docs/guide/storage-layout.md', 'docs/guide/ci-gate.md'):
        (root / rel).write_text('# Runbook\nSteps.\n', encoding='utf-8')
    data = fixture_catalogue()
    guide = next(e for e in data['entries'] if e['id'] == 'guide')
    guide['keywords'] = ['runbook', 'storage layout', 'ci gate']
    guide['entrypoints'] = [{'topic': 'storage layout: bulk sources and disks', 'path': 'docs/guide/storage-layout.md'},
                            {'topic': 'CI gate', 'path': 'docs/guide/ci-gate.md'}]
    write_catalogue(root, data)
    git(root, 'add', '.')
    state = find_module.load_state(root)
    candidates: dict = {}
    find_module._catalogue_evidence(state, ['storage', 'runbook'], None, candidates)
    assert candidates['docs/guide/storage-layout.md'].catalogue_terms == {'storage', 'runbook'}
    assert candidates['docs/guide/ci-gate.md'].catalogue_terms == {'runbook'}  # a family-wide keyword only


def test_a_family_hit_lists_only_the_entry_points_the_query_names(tmp_path):
    root = make_repo(tmp_path / 'repo')
    for rel in ('docs/guide/storage-layout.md', 'docs/guide/ci-gate.md', 'docs/guide/cleanup.md'):
        (root / rel).write_text('# Runbook\nSteps.\n', encoding='utf-8')
    data = fixture_catalogue()
    guide = next(e for e in data['entries'] if e['id'] == 'guide')
    guide['keywords'] = ['runbook']
    guide['entrypoints'] = [{'topic': 'CI gate', 'path': 'docs/guide/ci-gate.md'},
                            {'topic': 'storage layout: bulk sources and disks', 'path': 'docs/guide/storage-layout.md'},
                            {'topic': 'worktree cleanup', 'path': 'docs/guide/cleanup.md'}]
    write_catalogue(root, data)
    git(root, 'add', '.')

    def entrypoints(query):
        return [hit['path'] for hit in find(query, repo=root)['hits'] if hit['match'] == 'entrypoint']
    # Every word is in the storage entry point's topic: its siblings name no word of the query.
    assert entrypoints('bulk sources disks') == ['docs/guide/storage-layout.md']
    # A family-wide keyword names no entry point: all of them answer it, in catalogue order.
    assert entrypoints('runbook') == ['docs/guide/ci-gate.md', 'docs/guide/storage-layout.md', 'docs/guide/cleanup.md']


def test_named_entrypoints_ranks_the_named_and_drops_the_unnamed():
    points = [{'topic': 'CI gate', 'path': 'docs/a.md'}, {'topic': 'storage layout', 'path': 'docs/b.md'},
              {'topic': 'storage of disks', 'path': 'docs/c.md'}]
    assert [p['path'] for p in find_module.named_entrypoints(points, ['storage', 'layout'])] == ['docs/b.md', 'docs/c.md']
    assert find_module.named_entrypoints(points, ['runbook']) == points


def _candidate(path, text):
    return find_module.Candidate(path, content_terms={'word'} if text else set(),
                                 symbol_terms=set() if text else {'word'})


def test_code_candidates_never_crowd_text_candidates_out_of_the_read_pool():
    # Code evidence is complete before any line is read; a text file's best passage is not yet known.
    ranked = [_candidate(f'scripts/c{i}.py', False) for i in range(5)] + [_candidate(f'docs/t{i}.md', True)
                                                                          for i in range(3)]
    pool = find_module.rerank_pool(ranked, 2, set(), False)
    assert [c.path for c in pool if c.in_content] == ['docs/t0.md', 'docs/t1.md']  # the bound counts reads only
    assert [c.path for c in pool if not c.in_content] == ['scripts/c0.py', 'scripts/c1.py']


def test_the_read_pool_adds_speakers_and_status_records_beyond_its_bound():
    ranked = [_candidate(f'docs/t{i}.md', True) for i in range(4)]
    ranked[3].authority = True
    assert [c.path for c in find_module.rerank_pool(ranked, 1, {'docs/t2.md'}, False)] == ['docs/t0.md', 'docs/t2.md']
    assert [c.path for c in find_module.rerank_pool(ranked, 1, set(), True)] == ['docs/t0.md', 'docs/t3.md']


def test_a_span_holds_only_the_lead_of_a_long_docstring():
    text = 'def long():\n    """Summary.\n\n    Second.\n    Third.\n    Fourth is detail.\n    """\n'
    lines = [(no, line) for no, line in enumerate(text.splitlines(), 1)
             if find_module.DEF_LINE.match(line) or '"""' in line]
    assert find_module.python_spans(lines) == [(1, 2 + find_module.DOCSTRING_LEAD - 1, 'def long():')]


def test_within_a_band_exact_relevance_ranks_before_line_evidence_except_for_a_status_question(repo):
    state = _state(repo, fixture_catalogue())
    terms, weights = ['alpha', 'beta'], {'alpha': 1.0, 'beta': 1.0}
    passage = find_module.Candidate('docs/a.md', content_terms={'alpha', 'beta'}, passage_terms={'alpha', 'beta'},
                                    line_terms=1)  # relevance 0.6: the words together in one passage
    line = find_module.Candidate('docs/b.md', content_terms={'alpha', 'beta'}, line_terms=2)  # 0.4, on one line

    def order(status):
        key = functools.partial(find_module._rank_key, state, terms=terms, weights=weights, status_question=status)
        return [c.path for c in sorted([line, passage], key=key)]
    assert key_band(state, passage, terms, weights) == key_band(state, line, terms, weights)
    assert order(False) == ['docs/a.md', 'docs/b.md']
    assert order(True) == ['docs/b.md', 'docs/a.md']  # a status question's record is the line holding its words


def key_band(state, c, terms, weights):
    return find_module._rank_key(state, c, terms=terms, weights=weights)[:2]
