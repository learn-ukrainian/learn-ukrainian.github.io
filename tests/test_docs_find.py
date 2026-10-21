"""The one query surface (#9412): ``scripts/docs/find.py``, its CLI and ``GET /api/knowledge/find``.

Every test runs against a small Git fixture repository, never the real tree (the
real-tree checks live in ``tests/test_docs_catalogue_coverage.py``, and the dev-set
lookups are ranked in ``tests/test_docs_find_lookups_part<k>.py``).
"""
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
from scripts.docs.find import FindError, find, main

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


# ------------------------------------------------------------------ ranking and statuses


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


@pytest.fixture
def no_search_starts(monkeypatch):
    """Fail the test if any search process or timer starts."""
    def refuse(*_args, **_kwargs):
        raise AssertionError('a search started for a rejected request')
    monkeypatch.setattr(find_module.subprocess, 'Popen', refuse)
    monkeypatch.setattr(find_module.threading, 'Timer', refuse)


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


# ------------------------------------------------------------------ cut-offs are never "no source"

# The smallest budgets: the catalogue load alone (Git subprocesses) outlasts them, so the
# text search always starts past its deadline. Zero is not a budget (it is rejected).
SPENT_BUDGET = 1e-9


def test_an_output_cap_is_incomplete(repo, monkeypatch):
    monkeypatch.setattr(find_module, 'GREP_OUTPUT_CAP', 1)
    result = find('hostilename', repo=repo)
    assert result['coverage']['incomplete']
    assert any(r.startswith('output_budget') for r in result['coverage']['incomplete_reasons'])
    assert result['outcome'] == 'incomplete'  # never 'no_match'
    named = find('rf hostilename', repo=repo)
    assert named['outcome'] == 'found' and named['coverage']['incomplete']  # a name hit, flagged incomplete


def test_an_invalid_catalogue_reads_no_text_and_says_why(fresh_repo, monkeypatch):
    (fresh_repo / 'docs/knowledge/catalogue.yaml').write_text('entries: [1]\n', encoding='utf-8')
    git(fresh_repo, 'add', '.')
    calls = recorded_greps(monkeypatch)
    result = find('rf', repo=fresh_repo)
    assert calls == []
    assert result['coverage']['incomplete'] and result['coverage']['incomplete_reasons'][0].startswith(
        'catalogue_invalid')
    assert 'docs/guide/-rf.md' in paths_of(result)  # names still answer


# ------------------------------------------------------------------ determinism and the memo


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


def test_cli_json_is_the_library_result(repo, capsys):
    assert main(['handbook', '--repo', str(repo), '--json', '--limit', '3']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['hits'][0]['path'] == 'docs/guide/index.md' and len(result['hits']) <= 3


def test_cli_reports_an_unreadable_repository(tmp_path, capsys):
    assert main(['x', '--repo', str(tmp_path), '--json']) == 3
    assert json.loads(capsys.readouterr().out)['error']['kind'] == 'unreadable'


def test_cli_help_meets_the_standard(capsys):
    with pytest.raises(SystemExit):
        main(['--help'])
    out = capsys.readouterr().out
    for part in ('Examples:', 'Outputs:', 'Exit codes:', 'Related:', '--limit', '--family', '--json', 'default'):
        assert part in out
    assert 'ASCII digits only (0-9): no sign, no spaces, no decimal point or exponent' in ' '.join(out.split())


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


@pytest.mark.parametrize('value', NON_DIGIT_LIMITS)
def test_cli_and_library_reject_the_same_non_digit_limits(repo, no_search_starts, capsys, value):
    with pytest.raises(FindError):
        find_module.limit_from_text(value)
    assert main(['guide', '--repo', str(repo), f'--limit={value}']) == 2
    assert capsys.readouterr().out == f'Find could not run (invalid_request): limit: {find_module.LIMIT_MESSAGE}\n'


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


def _repo_with(tmp_path, files):
    root = make_repo(tmp_path / 'repo')
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')
    git(root, 'add', '.')
    return root


# A y never becomes e, in either direction (#9531): "story" once ranked store code first.
@pytest.mark.parametrize('query', ['story', 'stories', 'user story'])
def test_a_y_word_never_selects_or_credits_a_word_with_an_e(tmp_path, query):
    root = _repo_with(tmp_path, {
        'docs/guide/stories.md': '# Backlog\nEach user story names its reader.\n',
        'docs/guide/store-layout.md': '# Layout\nThe store keeps stored records for the user.\n',
        'scripts/store_reader.py': '"""Read the store and its stored records."""\n\nSTORE = 1\n',
        'docs/guide/police.md': '# Police\nThe policies of the user story store.\n'})
    result = find(query, repo=root, limit=50)
    found = {hit['path']: hit for hit in result['hits']}
    assert paths_of(result)[0] == 'docs/guide/stories.md', paths_of(result)
    for decoy in ('docs/guide/store-layout.md', 'scripts/store_reader.py'):
        assert 'story' not in found.get(decoy, {}).get('matched', []) and query not in found.get(decoy, {}).get(
            'matched', []), found.get(decoy)


# An -er word may be no agent noun (#9531): a file another query word selects gains no credit for a
# word inside the -er word, so it never ranks with the file holding both words.
@pytest.mark.parametrize('query, decoy, answer', [
    ('proper nouns', 'docs/guide/prop-nouns.md', 'docs/guide/naming.md'),
    ('corner cases', 'docs/guide/corn-cases.md', 'docs/guide/edges.md'),
    ('brother rules', 'docs/guide/broth-rules.md', 'docs/guide/family.md'),
])
def test_an_er_word_never_credits_a_word_inside_it(tmp_path, query, decoy, answer):
    first, second = query.split()
    root = _repo_with(tmp_path, {
        decoy: f'# Notes\nA {decoy.split("/")[-1].split("-")[0]} holds {second} here.\n',
        answer: f'# Notes\nEvery {first} {second} entry is listed here.\n'})
    result = find(query, repo=root, limit=50)
    paths = paths_of(result)
    assert answer in paths and (decoy not in paths or paths.index(answer) < paths.index(decoy)), paths
    if decoy in paths:
        assert first not in hit_for(result, decoy)['matched'], hit_for(result, decoy)


@pytest.mark.parametrize('path, readable', [
    ('scripts/review/closeout_cli.py', True), ('.githooks/pre-push', True), ('AGENTS.md', True),
    ('scripts/config/model_catalog.yaml', True), ('agents_extensions/shared/rules/core.md', True),
    ('scripts/private/tool.py', False), ('scripts/cache/x.py', False), ('docs/guide/x.py', False),
    ('tests/test_x.py', False), ('scripts/data.json', False), ('curriculum/a1/x.yaml', False),
    ('scripts/bad\nname.py', False),
])
def test_code_readable_is_the_privacy_gate_for_code(path, readable):
    assert find_module.code_readable(path) is readable


def test_the_code_search_never_reads_a_private_path(code_repo, monkeypatch):
    find_module._STATE_CACHE.clear()
    calls = recorded_greps(monkeypatch)
    find('review verdict parsing', repo=code_repo)
    code_call = next(c for c in calls if ':(literal)scripts' in c)
    assert ':(exclude,literal)scripts/private/secret_tool.py' in code_call
    assert ':(exclude,literal)scripts/verdict_dump.json' in code_call
    assert not any(arg.startswith(':(literal)docs') or arg.startswith(':(literal)tests') for arg in code_call)


# ------------------------------------------------------------------ ranking helpers and lifecycle records


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


def test_lifecycle_authorities_never_name_an_unreadable_file(history_repo):
    state = find_module.load_state(history_repo)
    assert find_module.lifecycle_authorities(state, 'docs/decisions/2026-01-01-quux-plan.md') == (
        ['docs/decisions/INDEX.md'], ['docs/decisions/INDEX.md'])
    assert find_module.lifecycle_authorities(state, 'scripts/legacy/widget/run.py') == (
        [], ['scripts/legacy/widget/README.md'])
    assert PRIVATE.rsplit('/', 1)[0] not in find_module.directory_indexes(state)


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
def test_a_data_store_purpose_is_the_store_s_own_description(repo):
    # A store has no text (#9531): the words of its record's purpose count like its keywords.
    candidates: dict = {}
    find_module._catalogue_evidence(_state(repo, fixture_catalogue()), ['fixture', 'main'], None, candidates)
    store = candidates['data/main.db']
    assert (store.catalogue_terms, store.purpose_terms) == ({'fixture', 'main'}, set())
    assert store.store['id'] == 'data-main' and store.authority
