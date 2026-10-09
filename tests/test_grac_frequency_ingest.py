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
            "lastpage": int(last), "total": len(rows), "api_version": "open-5.71.15",
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


def first_band():
    return [page(('a', 20), total=2), page(('a', 20), last=True)]


def test_pagination_both_attributes_and_provenance(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [*first_band(), page(('b', 10), last=True),
                                page(('A', 18), last=True)])
    assert counts == {'lemma': 2, 'word': 1}
    params = [kw['params'] for _, kw in transport.calls]
    assert [(p['wlattr'], p.get('wlmaxfreq')) for p in params] == [
        ('lemma', None), ('lemma', 20), ('lemma', 19), ('word', None)]
    assert all(p['wlpage'] == 1 and p['wlnums'] == 'frq' and p['wlsort'] == 'frq' for p in params)
    assert all(kw['headers']['User-Agent'] == crawler.USER_AGENT for _, kw in transport.calls)
    assert read(db, 'SELECT attr,last_completed_page,complete FROM checkpoint ORDER BY attr') == [
        ('lemma', 3, 1), ('word', 1, 1)]
    provenance = read(db, 'SELECT corpus,api_version,manatee_version,min_freq,page_size,retrieved_at,item_count FROM provenance')
    assert len(provenance) == 4
    assert all(row[:5] == ('grac19a', 'open-5.71.15', '2.36.7-open-2.225.8', 5, 1000)
               and 'T' in row[5] and row[6] == 1 for row in provenance)
    assert read(db, 'SELECT min_freq,max_freq,requested_items FROM request_bounds WHERE attr="lemma" ORDER BY page') == [
        (5, None, 1000), (20, 20, 1000), (5, 19, 1000)]
    counts, resumed = run(db, [])
    assert counts == {'lemma': 0, 'word': 0} and not resumed.calls


def test_resume_after_interruption(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(KeyboardInterrupt):
        run(db, [*first_band(), KeyboardInterrupt()], attrs=['lemma'])
    assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(2,)]
    _, resumed = run(db, [page(('b', 10), last=True)], attrs=['lemma'])
    assert resumed.calls[0][1]['params']['wlpage'] == 1
    assert resumed.calls[0][1]['params']['wlmaxfreq'] == 19
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]


def test_tie_interruption_replays_uncommitted_band(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(KeyboardInterrupt):
        run(db, [page(('a', 20), total=2), KeyboardInterrupt()], attrs=['lemma'])
    for table in ('items', 'provenance', 'checkpoint', 'frequency_cursor', 'request_bounds'):
        assert not read(db, f'SELECT * FROM {table}')
    counts, _ = run(db, [page(('a', 20), ('b', 20), last=True)], attrs=['lemma'])
    assert counts == {'lemma': 2}


def test_retry_never_advances_checkpoint_and_delays_are_polite(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['lemma'], max_pages=1)
    observed = []
    class RetryTransport(Transport):
        def get(self, url, **kwargs):
            observed.append(read(db, 'SELECT last_completed_page FROM checkpoint'))
            return super().get(url, **kwargs)
    transport = RetryTransport([requests.Timeout(), requests.Timeout(), page(('b', 10), last=True)])
    sleep = Mock()
    crawler.ingest(db, attrs=['lemma'], transport=transport, sleep=sleep, retry_backoff=2)
    assert observed == [[(2,)], [(2,)], [(2,)]]
    assert [kw['params']['wlmaxfreq'] for _, kw in transport.calls] == [19, 19, 19]
    assert [call.args[0] for call in sleep.call_args_list] == [3.0, 4.0]
    assert read(db, 'SELECT page FROM provenance ORDER BY page') == [(1,), (2,), (3,)]


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
        run(db, first_band(), attrs=['lemma'], max_pages=1)
    response = requests.Response()
    response.status_code = status
    if retry_after:
        response.headers['Retry-After'] = retry_after
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(crawler.requests, 'Session', Mock(return_value=session))
    sleep = Mock(side_effect=AssertionError('stop conditions must not sleep/retry'))
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
    params = session.get.call_args.kwargs['params']
    assert params['wlpage'] == 1
    assert params.get('wlmaxfreq') == (19 if resume else None)
    session.close.assert_called_once()
    sleep.assert_not_called()
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == ([(2, 0)] if resume else [])
    assert read(db, 'SELECT page FROM provenance ORDER BY page') == ([(1,), (2,)] if resume else [])
    assert read(db, 'SELECT str FROM items') == ([('a',)] if resume else [])


@pytest.mark.parametrize('status', [403, 429])
def test_http_stop_during_tie_preserves_entire_band(tmp_path, status):
    db = tmp_path / 'snapshot.db'
    response = requests.Response()
    response.status_code = status
    response._content = b'{}'
    transport = Transport([page(('a', 20), total=2)])
    get = transport.get
    def stop_on_tie(url, **kwargs):
        return get(url, **kwargs) if not transport.calls else response
    transport.get = stop_on_tie
    with pytest.raises(crawler.GracIngestHalted, match=f'HTTP {status}'):
        crawler.ingest(db, attrs=['lemma'], transport=transport, sleep=lambda _: None)
    assert not read(db, 'SELECT * FROM checkpoint')
    assert not read(db, 'SELECT * FROM items')


def test_empty_nonterminal_page_retries_same_page_without_checkpoint(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['word'], max_pages=1)
    observed = []
    class EmptyTransport(Transport):
        def get(self, url, **kwargs):
            observed.append(read(db, 'SELECT last_completed_page,complete FROM checkpoint'))
            return super().get(url, **kwargs)
    transport = EmptyTransport([page(), page(('b', 10), last=True)])
    sleep = Mock()
    assert crawler.ingest(db, attrs=['word'], transport=transport, sleep=sleep) == {'word': 1}
    assert [kw['params']['wlmaxfreq'] for _, kw in transport.calls] == [19, 19]
    assert observed == [[(2, 0)], [(2, 0)]]
    assert [call.args[0] for call in sleep.call_args_list] == [3.0]
    assert read(db, 'SELECT page,item_count FROM provenance ORDER BY page') == [(1, 1), (2, 1), (3, 1)]


def test_exhausted_empty_page_preserves_resume_checkpoint(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['word'], max_pages=1)
    transport = Transport([page(), page()])
    with pytest.raises(ValueError, match='empty page without lastpage=1'):
        crawler.ingest(db, attrs=['word'], transport=transport, retries=1, sleep=lambda _: None)
    assert [kw['params']['wlmaxfreq'] for _, kw in transport.calls] == [19, 19]
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 0)]
    _, resumed = run(db, [page(('b', 10), last=True)], attrs=['word'])
    assert resumed.calls[0][1]['params']['wlmaxfreq'] == 19


def test_floor_is_inclusive_and_stops_before_next_page(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 6), ('b', 5), last=True)], attrs=['lemma'])
    assert counts == {'lemma': 2} and len(transport.calls) == 1
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]
    assert read(db, 'SELECT complete FROM checkpoint') == [(1,)]


def test_floor_tie_is_retrieved_whole_before_completion(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 5), total=2),
                                page(('b', 5), ('a', 5), last=True)], attrs=['word'])
    assert counts == {'word': 2}
    assert [(kw['params']['wlminfreq'], kw['params'].get('wlmaxfreq')) for _, kw in transport.calls] == [
        (5, None), (5, 5)]
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 1)]
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',)]


def test_full_final_page_uses_live_api_end_signal(tmp_path):
    db = tmp_path / 'snapshot.db'
    counts, transport = run(db, [page(('a', 30), ('b', 25), total=4), page(('b', 25), last=True),
                                page(('c', 24), ('d', 23), last=True)],
                            attrs=['lemma'], min_freq=20, page_size=2)
    assert counts == {'lemma': 4} and len(transport.calls) == 3
    assert transport.calls[-1][1]['params']['wlmaxfreq'] == 24
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(3, 1)]


def test_page_cap_and_empty_last_page(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['lemma'], max_pages=1)
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(2, 0)]
    # A terminal empty window cannot excuse a missing item.
    with pytest.raises(ValueError, match='gap=1'):
        run(db, [page(last=True)], attrs=['lemma'], max_pages=2)
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(3, 0)]
    empty = tmp_path / 'empty.db'
    counts, _ = run(empty, [page(last=True)], attrs=['lemma'])
    assert counts == {'lemma': 0}
    assert read(empty, 'SELECT complete FROM checkpoint') == [(1,)]


@pytest.mark.parametrize('bad', [None, {'error': 'busy'}, {}, page(('a', 10), ('b', 20)),
                               page(('a', 10), api_version=''), page(('a', -1)),
                               page(('a', 10), ('a', 9)), page(('a', 10), total=None),
                               page(('a', 10), total=True), page(('a', 10), total=-1),
                               {'Items': [{'str': '', 'frq': 10, 'relfreq': 5}], 'lastpage': 1,
                                'api_version': 'api', 'manatee_version': 'manatee', 'total': 1},
                               {'Items': [{'str': 'a', 'frq': 10, 'relfreq': -1}], 'lastpage': 1,
                                'api_version': 'api', 'manatee_version': 'manatee', 'total': 1}])
def test_malformed_pages_never_checkpoint(tmp_path, bad):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError):
        run(db, [bad], attrs=['lemma'], retries=0)
    assert not read(db, 'SELECT * FROM checkpoint')


def test_repeated_page_and_changed_settings_refuse_resume(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['lemma'], max_pages=1)
    for kwargs, pages in [({}, [page(('a', 20))]), ({'min_freq': 10}, []),
                          ({'page_size': 10}, []), ({}, [page(('b', 10), api_version='new')])]:
        with pytest.raises(ValueError):
            run(db, pages, attrs=['lemma'], **kwargs)
        assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(2,)]


def test_rows_provenance_checkpoint_roll_back_together(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['lemma'], max_pages=1)
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TRIGGER reject_checkpoint BEFORE UPDATE ON checkpoint BEGIN SELECT RAISE(ABORT,'fixture'); END")
    with pytest.raises(sqlite3.IntegrityError):
        run(db, [page(('b', 10), last=True)], attrs=['lemma'])
    assert read(db, 'SELECT str FROM items') == [('a',)]
    assert read(db, 'SELECT page FROM provenance ORDER BY page') == [(1,), (2,)]
    assert read(db, 'SELECT last_completed_page FROM checkpoint') == [(2,)]
    assert read(db, 'SELECT next_max_freq FROM frequency_cursor') == [(19,)]
    assert read(db, 'SELECT page FROM request_bounds ORDER BY page') == [(1,), (2,)]


def test_dropped_tied_item_recovered_even_when_group_exceeds_page_size(tmp_path):
    db = tmp_path / 'snapshot.db'
    # a was seen on the boundary; b reappears away from it in another
    # unstable slice, while c would be dropped by offset paging.
    pages = [page(('top', 30), ('a', 20), total=5),
             page(('b', 20), ('a', 20), total=3),
             page(('c', 20), ('b', 20), ('a', 20), last=True),
             page(('end', 10), last=True)]
    counts, transport = run(db, pages, attrs=['lemma'], page_size=2)
    assert counts == {'lemma': 5}
    assert read(db, 'SELECT str FROM items ORDER BY str') == [('a',), ('b',), ('c',), ('end',), ('top',)]
    assert [kw['params']['wlmaxitems'] for _, kw in transport.calls] == [2, 2, 3, 2]
    assert [kw['params'].get('wlmaxfreq') for _, kw in transport.calls] == [None, 20, 20, 19]
    assert read(db, 'SELECT complete FROM checkpoint') == [(1,)]


@pytest.mark.parametrize('full', [page(('a', 20), last=True, total=2),
                                  page(('a', 20), ('b', 20), total=2),
                                  page(('a', 20), ('b', 20), last=True, total=3),
                                  page(('b', 20), ('c', 20), last=True)])
def test_incomplete_or_changed_tie_never_advances_cursor(tmp_path, full):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError):
        run(db, [page(('a', 20), total=3), page(('a', 20), total=2), full],
            attrs=['lemma'], page_size=1)
    for table in ('items', 'checkpoint', 'frequency_cursor', 'provenance', 'request_bounds'):
        assert not read(db, f'SELECT * FROM {table}')


def test_full_tie_must_include_items_from_partial_tie_probe(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError, match='tie changed or omitted'):
        run(db, [page(('a', 20), total=2), page(('b', 20), total=2),
                 page(('a', 20), ('c', 20), last=True)], attrs=['lemma'], page_size=1)
    assert not read(db, 'SELECT * FROM checkpoint')
    assert not read(db, 'SELECT * FROM items')


@pytest.mark.parametrize('total', [1, 3])
def test_reconciliation_mismatch_blocks_completion_and_resume(tmp_path, total):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError, match=f'gap={total - 2}'):
        run(db, [page(('a', 20), ('b', 10), last=True, total=total)], attrs=['lemma'])
    assert read(db, 'SELECT complete FROM checkpoint') == [(0,)]
    assert read(db, 'SELECT COUNT(*) FROM items') == [(2,)]
    with pytest.raises(ValueError, match='incomplete'):
        run(db, [], attrs=['lemma'])


def test_completed_snapshot_rechecks_distinct_count(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, [page(('a', 20), last=True)], attrs=['lemma'])
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO items VALUES ('lemma','extra',10,5,1)")
    with pytest.raises(ValueError, match='gap=-1'):
        run(db, [], attrs=['lemma'])
    assert read(db, 'SELECT complete FROM checkpoint') == [(0,)]


@pytest.mark.parametrize('legacy_complete', [0, 1])
def test_resume_existing_page_12_shape_keeps_provenance_and_recovers_overlap(tmp_path, legacy_complete):
    db = tmp_path / 'snapshot.db'
    # Create only the original schema, not the new cursor/bounds tables.
    with sqlite3.connect(db) as conn:
        conn.executescript(crawler.SCHEMA.split('CREATE TABLE IF NOT EXISTS frequency_cursor')[0])
        for n in range(1, 13):
            conn.execute('INSERT INTO provenance VALUES (?,?,?,?,?,?,?,?,?)',
                         ('lemma', n, crawler.GRAC_CORPUS, 'open-5.71.15', '2.36.7-open-2.225.8',
                          5, 1000, f'2026-01-01T00:00:{n:02}+00:00', 1000))
            conn.executemany('INSERT INTO items VALUES (?,?,?,?,?)',
                             [('lemma', f'old-{i}', 20, 10.0, n) for i in range((n-1)*1000, n*1000)])
        conn.execute('INSERT INTO checkpoint VALUES (?,?,?)', ('lemma', 12, legacy_complete))
    old_provenance = read(db, 'SELECT * FROM provenance ORDER BY page')
    counts, transport = run(db, [page(('old-11999', 20), ('old-200', 20), total=12001),
                                page(*[(f'old-{i}', 20) for i in range(12000)], ('dropped', 20), last=True)],
                            attrs=['lemma'])
    assert counts == {'lemma': 1}
    assert transport.calls[0][1]['params']['wlpage'] == 1
    assert 'wlmaxfreq' not in transport.calls[0][1]['params']
    assert read(db, 'SELECT * FROM provenance WHERE page<=12 ORDER BY page') == old_provenance
    assert read(db, 'SELECT COUNT(*) FROM items') == [(12001,)]
    assert read(db, 'SELECT last_completed_page,complete FROM checkpoint') == [(14, 1)]
    assert read(db, 'SELECT page FROM items WHERE str="old-11999"') == [(12,)]
    assert read(db, 'SELECT page FROM items WHERE str="dropped"') == [(14,)]


@pytest.mark.parametrize('overlap_position', [0, 1])
def test_tie_overlap_at_and_away_from_boundary_is_deduplicated(tmp_path, overlap_position):
    db = tmp_path / 'snapshot.db'
    tied = [('b', 20), ('c', 20)]
    tied.insert(overlap_position, ('a', 20))
    counts, _ = run(db, [page(('top', 30), ('a', 20), total=4), page(*tied, last=True)],
                    attrs=['lemma'])
    assert counts == {'lemma': 4}
    assert read(db, 'SELECT str,COUNT(*) FROM items GROUP BY str ORDER BY str') == [
        ('a', 1), ('b', 1), ('c', 1), ('top', 1)]
    assert read(db, 'SELECT complete FROM checkpoint') == [(1,)]


def test_tie_version_drift_preserves_checkpoint(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError, match='versions changed'):
        run(db, [page(('a', 20), total=2), page(('a', 20), last=True, api_version='changed')],
            attrs=['lemma'])
    assert not read(db, 'SELECT * FROM checkpoint')


def test_lower_floor_bound_is_enforced(tmp_path):
    db = tmp_path / 'snapshot.db'
    with pytest.raises(ValueError, match='ignored frequency bounds'):
        run(db, [page(('a', 6), ('b', 4), last=True)], attrs=['lemma'])
    assert not read(db, 'SELECT * FROM checkpoint')


def test_remaining_window_total_drift_is_reported(tmp_path):
    db = tmp_path / 'snapshot.db'
    run(db, first_band(), attrs=['lemma'], max_pages=1)
    with pytest.raises(ValueError, match='reconciliation gap=-1'):
        run(db, [page(('b', 10), total=2), page(('b', 10), last=True)],
            attrs=['lemma'], max_pages=1)
    assert read(db, 'SELECT complete FROM checkpoint') == [(0,)]


def test_complete_reference_corpus_with_per_request_tie_permutations_and_resume(tmp_path):
    # Independent server oracle: filter a fixed corpus, then rotate every tie
    # differently on every request, so offset slices cannot be trusted.
    corpus = {attr: [(f'item-{n}', n % modulus + 1) for n in range(83)]
              for attr, modulus in [('lemma', 11), ('word', 13)]}
    class PermutingServer:
        def __init__(self):
            self.calls = []

        def get(self, url, **kwargs):
            params = kwargs['params']
            self.calls.append(params.copy())
            eligible = [(word, freq) for word, freq in corpus[params['wlattr']]
                        if params['wlminfreq'] <= freq <= params.get('wlmaxfreq', 100)]
            ordered = []
            for freq in sorted({freq for _, freq in eligible}, reverse=True):
                group = [row for row in eligible if row[1] == freq]
                shift = len(self.calls) % len(group)
                ordered.extend(group[shift:] + group[:shift])
            size = params['wlmaxitems']
            start = (params['wlpage'] - 1) * size
            result = page(*ordered[start:start + size],
                          total=len(eligible), last=start + size >= len(eligible))
            response = Mock(status_code=200)
            response.json.return_value = result
            return response
    db = tmp_path / 'snapshot.db'
    server = PermutingServer()
    for _ in range(20):
        crawler.ingest(db, transport=server, sleep=lambda _: None, page_size=3, max_pages=1)
        complete = read(db, 'SELECT complete FROM checkpoint ORDER BY attr')
        if complete == [(1,), (1,)]:
            break
    assert complete == [(1,), (1,)]
    expected = sorted((attr, word, freq) for attr, rows in corpus.items()
                      for word, freq in rows if freq >= 5)
    assert read(db, 'SELECT attr,str,frq FROM items ORDER BY attr,str') == expected
    assert all(params['wlpage'] == 1 for params in server.calls)
    assert any(params['wlmaxitems'] > 3 for params in server.calls)


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
    run(db, [*first_band(), page(('b', 10), last=True)], attrs=['word'])
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE provenance SET retrieved_at='2026-01-01T00:00:00+00:00' WHERE page=1")
        conn.execute("UPDATE provenance SET retrieved_at='2026-02-01T00:00:00+00:00' WHERE page=3")
    assert query.grac_frequency('a', cache_only=True, db_path=db)['retrieved_at'].startswith('2026-01-01')
    assert query.grac_frequency('b', cache_only=True, db_path=db)['retrieved_at'].startswith('2026-02-01')
