"""GRAC snapshot mechanics using deterministic NoSketchEngine fixture pages."""

import sqlite3
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from scripts.ingest import grac_frequency_ingest as crawler
from scripts.lib.readonly_sqlite import open_readonly
from scripts.rag import source_query as query


def page(*rows, last=False, **updates):
    return {"Items": [{"str": word, "frq": freq, "relfreq": freq / 2} for word, freq in rows],
            "lastpage": int(last), "api_version": "open-5.71.15",
            "manatee_version": "2.36.7-open-2.225.8", **updates}


class Transport:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        result = next(self.pages)
        if isinstance(result, BaseException):
            raise result
        response = Mock()
        response.json.return_value = result
        return response


def read(db, sql):
    conn = open_readonly(db)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def run(db, pages, **kwargs):
    transport = Transport(pages)
    counts = crawler.ingest(db, transport=transport, sleep=lambda _: None, **kwargs)
    return counts, transport


def test_pagination_both_attributes_and_provenance(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 20)), page(('b', 10), last=True),
                                page(('A', 18), last=True)])
    assert counts == {'lemma': 2, 'word': 1}
    assert [(kw['params']['wlattr'], kw['params']['wlpage']) for _, kw in transport.calls] == [
        ('lemma', 1), ('lemma', 2), ('word', 1)]
    assert all(kw['params']['wlnums'] == 'frq' and kw['params']['wlsort'] == 'frq'
               and kw['headers']['User-Agent'] == crawler.USER_AGENT for _, kw in transport.calls)
    assert read(db, 'SELECT attr,last_completed_page,complete FROM checkpoint ORDER BY attr') == [
        ('lemma', 2, 1), ('word', 1, 1)]
    provenance = read(db, 'SELECT corpus,api_version,manatee_version,min_freq,page_size,retrieved_at,item_count FROM provenance')
    assert len(provenance) == 3
    assert all(row[:5] == ('grac19a', 'open-5.71.15', '2.36.7-open-2.225.8', 5, 1000)
               and 'T' in row[5] and row[6] == 1 for row in provenance)
    counts, resumed = run(db, [])
    assert counts == {'lemma': 0, 'word': 0} and not resumed.calls


def test_resume_after_interruption(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(KeyboardInterrupt):
        run(db, [page(('a', 20)), KeyboardInterrupt()], attrs=['lemma'])
    assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(1,)]
    _, resumed = run(db, [page(('b', 10), last=True)], attrs=['lemma'])
    assert resumed.calls[0][1]['params']['wlpage'] == 2
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]


def test_retry_never_advances_checkpoint_and_delays_are_polite(tmp_path):
    db = tmp_path / 'snapshot.db'
    observed = []
    class RetryTransport(Transport):
        def get(self, url, **kwargs):
            if len(self.calls) > 0:
                observed.append(read(db, 'SELECT last_completed_page FROM checkpoint'))
            return super().get(url, **kwargs)
    transport = RetryTransport([page(('a', 20)), requests.Timeout(), requests.Timeout(), page(('b', 10), last=True)])
    sleep = Mock()
    crawler.ingest(db, attrs=['lemma'], transport=transport, sleep=sleep, retry_backoff=2)
    assert observed == [[(1,)], [(1,)], [(1,)]]
    assert [kw['params']['wlpage'] for _, kw in transport.calls] == [1, 2, 2, 2]
    assert [call.args[0] for call in sleep.call_args_list] == [3.0, 3.0, 4.0]
    assert read(db, 'SELECT page FROM provenance ORDER BY page') == [(1,), (2,)]


def test_exhausted_error_resumes_same_page(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(requests.Timeout):
        run(db, [requests.Timeout(), requests.Timeout()], attrs=['word'], retries=1)
    assert not read(db, 'SELECT * FROM checkpoint')
    assert not read(db, 'SELECT * FROM provenance')
    _, transport = run(db, [page(('a', 5), last=True)], attrs=['word'])
    assert transport.calls[0][1]['params']['wlpage'] == 1


@pytest.mark.parametrize('status,retry_after', [
    (403, None), (429, None), (429, '120'), (429, 'Wed, 07 Oct 2026 17:00:00 GMT'),
])
@pytest.mark.parametrize('resume', [False, True])
def test_http_stop_is_typed_and_never_retries_or_checkpoints(tmp_path, monkeypatch, capsys, status, retry_after, resume):
    db = tmp_path / 'snapshot.db'
    if resume:
        run(db, [page(('a', 20))], attrs=['lemma'], max_pages=1)
    response = requests.Response()
    response.status_code = status
    if retry_after:
        response.headers['Retry-After'] = retry_after
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(crawler.requests, 'Session', Mock(return_value=session))
    sleep = Mock(side_effect=AssertionError('stop conditions must not sleep/retry'))
    # Exercise the real ingest and CLI error handler together.
    ingest = crawler.ingest
    def no_sleep_ingest(*args, **kwargs):
        return ingest(*args, **kwargs, sleep=sleep)
    monkeypatch.setattr(crawler, 'ingest', no_sleep_ingest)
    assert crawler.main(['--db', str(db), '--attr', 'lemma', '--retries', '3']) == 1
    message = capsys.readouterr().err
    assert f'GracIngestHalted: HTTP {status}' in message
    assert ('operator should wait' if status == 429 else 'operator should stop') in message
    assert 'checkpoint unchanged' in message
    if retry_after:
        assert f'honour Retry-After: {retry_after}' in message
    session.get.assert_called_once()
    assert session.get.call_args.kwargs['params']['wlpage'] == (2 if resume else 1)
    session.close.assert_called_once()
    sleep.assert_not_called()
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == ([(1, 0)] if resume else [])
    assert read(db, 'SELECT page FROM provenance') == ([(1,)] if resume else [])
    assert read(db, 'SELECT str FROM items') == ([('a',)] if resume else [])


def test_empty_nonterminal_page_retries_same_page_without_checkpoint(tmp_path):
    db = tmp_path / 'snapshot.db'
    observed = []
    class EmptyTransport(Transport):
        def get(self, url, **kwargs):
            if self.calls:
                observed.append(read(db, 'SELECT last_completed_page,complete FROM checkpoint'))
            return super().get(url, **kwargs)
    transport = EmptyTransport([page(('a', 20)), page(), page(('b', 10), last=True)])
    sleep = Mock()
    assert crawler.ingest(db, attrs=['word'], transport=transport, sleep=sleep) == {'word': 2}
    assert [kw['params']['wlpage'] for _, kw in transport.calls] == [1, 2, 2]
    assert observed == [[(1, 0)], [(1, 0)]]
    assert [call.args[0] for call in sleep.call_args_list] == [3.0, 3.0]
    assert read(db, 'SELECT page,item_count FROM provenance ORDER BY page') == [(1, 1), (2, 1)]


def test_exhausted_empty_page_preserves_resume_checkpoint(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 20))], attrs=['word'], max_pages=1)
    transport = Transport([page(), page()])
    with pytest.raises(ValueError, match='empty page without lastpage=1'):
        crawler.ingest(db, attrs=['word'], transport=transport, retries=1, sleep=lambda _: None)
    assert [kw['params']['wlpage'] for _, kw in transport.calls] == [2, 2]
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(1, 0)]
    assert read(db, 'SELECT page FROM provenance') == [(1,)]
    _, resumed = run(db, [page(('b', 10), last=True)], attrs=['word'])
    assert resumed.calls[0][1]['params']['wlpage'] == 2


def test_floor_is_inclusive_and_stops_before_next_page(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 6), ('b', 5), ('c', 4))], attrs=['lemma'])
    assert counts == {'lemma': 2} and len(transport.calls) == 1
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]
    assert read(db, 'SELECT complete FROM checkpoint') == [(1,)]


def test_floor_tie_continues_until_below_floor(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 5)), page(('b', 5), ('c', 4))], attrs=['word'])
    assert counts == {'word': 2}
    assert [kw['params']['wlpage'] for _, kw in transport.calls] == [1, 2]
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 1)]
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]


def test_full_final_page_uses_live_api_end_signal(tmp_path):
    # Live bounded lemma probe: wlminfreq=25000000, wlmaxitems=2,
    # total=4; a full second page has lastpage=1 (page 1 has lastpage=0).
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('на', 30952990), ('і', 29365276), total=4),
                                page(('в', 28025537), ('у', 25420685), last=True, total=4)],
                            attrs=['lemma'], min_freq=25000000, page_size=2)
    assert counts == {'lemma': 4} and len(transport.calls) == 2
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 1)]


def test_page_cap_and_empty_last_page(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 10))], attrs=['lemma'], max_pages=1)
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(1, 0)]
    _, transport = run(db, [page(last=True)], attrs=['lemma'], max_pages=2)
    assert transport.calls[0][1]['params']['wlpage'] == 2
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 1)]


@pytest.mark.parametrize('bad', [None, {'error': 'busy'}, {}, page(('a', 10), ('b', 20)),
                               page(('a', 10), api_version=''), page(('a', -1)),
                               page(('a', 10), ('a', 9))])
def test_malformed_pages_never_checkpoint(tmp_path, bad):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError):
        run(db, [bad], attrs=['lemma'], retries=0)
    assert not read(db, 'SELECT * FROM checkpoint')


def test_repeated_page_and_changed_settings_refuse_resume(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 20))], attrs=['lemma'], max_pages=1)
    for kwargs, pages in [({}, [page(('a', 20))]), ({'min_freq': 10}, []),
                          ({'page_size': 10}, []), ({}, [page(('b', 10), api_version='new')])]:
        with pytest.raises(ValueError):
            run(db, pages, attrs=['lemma'], **kwargs)
        assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(1,)]


def test_rows_provenance_checkpoint_roll_back_together(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 20))], attrs=['lemma'], max_pages=1)
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TRIGGER reject_checkpoint BEFORE UPDATE ON checkpoint BEGIN SELECT RAISE(ABORT,'fixture'); END")
    with pytest.raises(sqlite3.IntegrityError):
        run(db, [page(('b', 10))], attrs=['lemma'])
    assert read(db, 'SELECT str FROM items') == [('a',)]
    assert read(db, 'SELECT page FROM provenance') == [(1,)]
    assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(1,)]


@pytest.mark.parametrize('kwargs', [{'attrs': []}, {'attrs': ['wrong']}, {'attrs': ['word', 'word']},
                                  {'min_freq': 0}, {'page_size': 0}, {'max_pages': -1},
                                  {'retries': -1}, {'delay': -1}, {'delay': float('nan')}])
def test_invalid_settings_do_not_create_db(tmp_path, kwargs):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError):
        run(db, [], **kwargs)
    assert not db.exists()


def test_cli_help_defaults_and_error_status(tmp_path, monkeypatch, capsys):
    help_text = crawler.build_parser().format_help()
    for text in ['--max-pages', 'Outputs:', 'Exit codes:', 'Related:', '--delay']:
        assert text in help_text
    assert crawler.main(['--db', str(tmp_path / 'bad.db'), '--min-freq', '0']) == 1
    assert 'GRAC ingest halted' in capsys.readouterr().err
    monkeypatch.setattr(crawler, 'ingest', lambda *a, **kw: {'lemma': 2, 'word': 3})
    assert crawler.main(['--db', str(tmp_path / 'good.db')]) == 0
    assert "'lemma': 2" in capsys.readouterr().out
    def interrupt(*a, **kw):
        raise KeyboardInterrupt
    monkeypatch.setattr(crawler, 'ingest', interrupt)
    assert crawler.main([]) == 130


def test_default_path_storage_resolution_and_override(tmp_path, monkeypatch):
    from scripts.common.repo_root import main_checkout_root
    from scripts.storage.topology import require_local_active_sources_db
    monkeypatch.delenv('LU_GRAC_FREQUENCY_DB', raising=False)
    expected = require_local_active_sources_db(main_checkout_root(Path(query.__file__).resolve().parents[2])).with_name('grac_frequency.db')
    assert query.grac_db_path() == expected
    monkeypatch.setenv('LU_GRAC_FREQUENCY_DB', str(tmp_path / 'override.db'))
    assert query.grac_db_path() == tmp_path / 'override.db'


def test_refuses_network_sqlite(tmp_path, monkeypatch):
    monkeypatch.setattr('scripts.storage.topology.is_network_filesystem_path', lambda _: True)
    with pytest.raises(ValueError):
        query.grac_db_path()
    assert query.grac_frequency('a', cache_only=True, db_path=tmp_path / 'absent.db') is None
    monkeypatch.setattr(crawler, 'is_network_filesystem_path', lambda _: True)
    with pytest.raises(ValueError):
        run(tmp_path / 'snapshot.db', [])


@pytest.fixture
def snapshot(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('lemma', 20), last=True), page(('word', 10), last=True)])
    return db


@pytest.mark.parametrize('cache_only', [True, False])
def test_local_hits_avoid_live_and_preserve_provenance(snapshot, monkeypatch, cache_only):
    live = Mock(side_effect=AssertionError('network forbidden'))
    monkeypatch.setattr(query, '_get', live)
    word = query.grac_frequency('word', cache_only=cache_only, db_path=snapshot)
    lemma = query.grac_lemma_frequency('lemma', cache_only=cache_only, db_path=snapshot)
    assert word['freq'] == 10 and word['rel_freq'] == 5.0
    assert lemma['total_freq'] == 20 and lemma['forms'] == [] and lemma['forms_available'] is False
    for result in (word, lemma):
        assert result['source'] == 'local_snapshot' and result['corpus'] == 'grac19a'
        assert 'T' in result['retrieved_at']
        assert result['api_version'] == 'open-5.71.15'
        assert result['manatee_version'] == '2.36.7-open-2.225.8'
        assert result['min_freq'] == 5
    live.assert_not_called()


@pytest.mark.parametrize('fn', [query.grac_frequency, query.grac_lemma_frequency])
def test_cache_only_miss_is_unknown_without_network(snapshot, monkeypatch, fn):
    live = Mock(side_effect=AssertionError('network forbidden'))
    monkeypatch.setattr(query, '_get', live)
    assert fn('missing', cache_only=True, db_path=snapshot) is None
    assert fn('missing', cache_only=True, db_path=snapshot.parent / 'absent.db') is None
    assert not (snapshot.parent / 'absent.db').exists()
    live.assert_not_called()


@pytest.mark.parametrize('fn, payload, total_key', [
    (query.grac_frequency, {'Items': [{'str': 'missing', 'frq': 7, 'relfreq': 3.5}]}, 'freq'),
    (query.grac_lemma_frequency, {'Blocks': [{'Items': [{'str': 'form', 'frq': 7, 'poc': 100}]}]}, 'total_freq'),
])
def test_live_fallback_follows_local_miss(snapshot, monkeypatch, fn, payload, total_key):
    response = Mock()
    response.json.return_value = payload
    order = []
    local = query._grac_local
    def lookup(*args):
        order.append('local')
        return local(*args)
    def get(*args, **kwargs):
        order.append('live')
        return response
    monkeypatch.setattr(query, '_grac_local', lookup)
    monkeypatch.setattr(query, '_get', get)
    result = fn('missing', db_path=snapshot)
    assert order == ['local', 'live']
    assert result[total_key] == 7 and result['source'] == 'live'


@pytest.mark.parametrize('fn, payload', [
    (query.grac_frequency, {'Items': []}), (query.grac_lemma_frequency, {'Blocks': []}),
])
def test_live_empty_and_outage_are_distinct(snapshot, monkeypatch, fn, payload):
    response = Mock()
    response.json.return_value = payload
    monkeypatch.setattr(query, '_get', Mock(return_value=response))
    result = fn('missing', db_path=snapshot)
    if fn is query.grac_frequency:
        assert result is None
    else:
        assert result['total_freq'] == 0 and result['source'] == 'live'
    response.json.return_value = {'error': 'busy'}
    assert fn('missing', db_path=snapshot) is None
    monkeypatch.setattr(query, '_get', Mock(side_effect=requests.Timeout()))
    assert fn('missing', db_path=snapshot) is None


def test_word_pattern_is_literal_and_nonexact_match_never_substituted(snapshot, monkeypatch):
    response = Mock()
    response.json.return_value = {'Items': [{'str': 'axb', 'frq': 9, 'relfreq': 4.5}]}
    live = Mock(return_value=response)
    monkeypatch.setattr(query, '_get', live)
    assert query.grac_frequency('a.b', db_path=snapshot) is None
    assert live.call_args.kwargs['params']['wlpat'] == r'^(?:a\.b)$'


@pytest.mark.parametrize('item', [
    {'str': 'missing'}, {'str': 'missing', 'frq': -1, 'relfreq': 1},
    {'str': 'missing', 'frq': 7}, {'str': 'missing', 'frq': 7, 'relfreq': -1},
    'malformed',
])
def test_live_word_missing_or_malformed_frequency_is_unknown(snapshot, monkeypatch, item):
    response = Mock()
    response.json.return_value = {'Items': [item]}
    monkeypatch.setattr(query, '_get', Mock(return_value=response))
    assert query.grac_frequency('missing', db_path=snapshot) is None


def test_lemma_cql_is_escaped(snapshot, monkeypatch):
    response = Mock()
    response.json.return_value = {'Blocks': []}
    live = Mock(return_value=response)
    monkeypatch.setattr(query, '_get', live)
    query.grac_lemma_frequency('a"b\\c', db_path=snapshot)
    assert live.call_args.kwargs['params']['q'] == 'q[lemma="a\\"b\\\\c"]'


def test_local_date_is_from_the_items_page(tmp_path, monkeypatch):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 20)), page(('b', 10), last=True)], attrs=['word'])
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE provenance SET retrieved_at='2026-01-01T00:00:00+00:00' WHERE page=1")
        conn.execute("UPDATE provenance SET retrieved_at='2026-02-01T00:00:00+00:00' WHERE page=2")
    assert query.grac_frequency('a', cache_only=True, db_path=db)['retrieved_at'].startswith('2026-01-01')
    assert query.grac_frequency('b', cache_only=True, db_path=db)['retrieved_at'].startswith('2026-02-01')
