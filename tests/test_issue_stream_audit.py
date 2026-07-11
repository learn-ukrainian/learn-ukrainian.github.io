"""Hermetic tests for the issue-stream auditor (#4708) — no network, no gh."""

from __future__ import annotations

import textwrap

import pytest

from scripts.orchestration.issue_stream_audit import (
    _MAX_SUBISSUE_PAGES,
    _paginate_subissues,
    classify,
    load_registry,
    make_issue_resolver,
    make_membership_resolver,
    read_membership_index,
)


@pytest.fixture()
def registry(tmp_path):
    path = tmp_path / "issue_streams.yaml"
    path.write_text(
        textwrap.dedent(
            """
            schema_version: 1
            streams:
              product:
                title: "Product"
                epics: [100, 150]
              infra:
                title: "Infra"
                epics: [200]
            """
        ),
        encoding="utf-8",
    )
    return load_registry(path)


def _issues(*numbers):
    return [{"number": n, "title": f"issue {n}"} for n in numbers]


def test_orphan_detected(registry):
    report = classify(
        _issues(100, 150, 200, 5, 6),
        registry,
        {100: ({5}, set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert [o["number"] for o in report["orphans"]] == [6]
    assert report["ok"] is False


def test_epics_are_exempt_from_membership(registry):
    report = classify(
        _issues(100, 150, 200),
        registry,
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["orphans"] == []
    assert report["ok"] is True


def test_body_reference_counts_but_flags_pending_migration(registry):
    report = classify(
        _issues(100, 150, 200, 7),
        registry,
        {100: (set(), {7}), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["orphans"] == []
    assert report["pending_native_link"] == [7]


def test_multi_homed_across_streams_flagged(registry):
    report = classify(
        _issues(100, 150, 200, 8),
        registry,
        {100: ({8}, set()), 150: (set(), set()), 200: ({8}, set())},
    )
    assert [m["number"] for m in report["multi_homed"]] == [8]
    assert report["multi_homed"][0]["streams"] == ["infra", "product"]
    # codex F1: multi-homed violates the exactly-one-stream invariant.
    assert report["ok"] is False


def test_same_stream_double_native_link_is_ambiguous(registry):
    """Native membership in TWO epics of the SAME stream is still two owners —
    exact membership means exactly one effective epic, not merely one stream
    name (codex/gemini review, PR #4998; this assertion used to read
    ``== []`` under the pre-fix bug where same-stream ambiguity was invisible)."""
    report = classify(
        _issues(100, 150, 200, 9),
        registry,
        {100: ({9}, set()), 150: ({9}, set()), 200: (set(), set())},
    )
    assert [m["number"] for m in report["multi_homed"]] == [9]
    assert report["multi_homed"][0]["streams"] == ["product"]
    assert report["ok"] is False


def test_closed_epic_surfaces(registry):
    report = classify(
        _issues(100, 200),  # 150 is not open
        registry,
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["closed_or_missing_epics"] == [150]
    assert report["ok"] is False


def test_registry_rejects_empty_stream(tmp_path):
    path = tmp_path / "issue_streams.yaml"
    path.write_text("streams:\n  broken:\n    title: x\n    epics: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="broken"):
        load_registry(path)


def test_native_link_wins_over_prose_mention(registry):
    """Once an issue is a native sub-issue somewhere, body refs elsewhere must
    not multi-home it (prose mentions are not membership)."""
    report = classify(
        _issues(100, 150, 200, 11),
        registry,
        {100: ({11}, set()), 150: (set(), set()), 200: (set(), {11})},
    )
    assert report["multi_homed"] == []
    assert report["orphans"] == []


# --------------------------------------------------------------------------- #
# ADR-011 P4 — effective issue→epic membership index + strict-gate resolvers
# --------------------------------------------------------------------------- #
def test_effective_membership_native_wins_over_body_epic(registry):
    # issue 11: native in epic 100 (product), body-ref in epic 200 (infra).
    report = classify(
        _issues(100, 150, 200, 11),
        registry,
        {100: ({11}, set()), 150: (set(), set()), 200: (set(), {11})},
    )
    entry = report["effective_membership"]["11"]
    assert entry == {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
    # Resolves for the native epic, not the body-mentioning one.
    resolve = make_membership_resolver(report)
    assert resolve(11, 100) is True
    assert resolve(11, 200) is False


def test_effective_membership_body_fallback(registry):
    report = classify(
        _issues(100, 150, 200, 7),
        registry,
        {100: (set(), {7}), 150: (set(), set()), 200: (set(), set())},
    )
    entry = report["effective_membership"]["7"]
    assert entry["via"] == "body" and entry["epics"] == [100] and entry["unique_stream"] is True
    assert make_membership_resolver(report)(7, 100) is True


def test_effective_membership_multi_home_rejected(registry):
    report = classify(
        _issues(100, 150, 200, 8),
        registry,
        {100: ({8}, set()), 150: (set(), set()), 200: ({8}, set())},
    )
    entry = report["effective_membership"]["8"]
    assert entry["unique_stream"] is False and entry["streams"] == ["infra", "product"]
    resolve = make_membership_resolver(report)
    assert resolve(8, 100) is False and resolve(8, 200) is False  # multi-home fails closed


def test_effective_membership_excludes_only_epics_not_closed_children(registry):
    """Epics themselves are exempt from the index, but a native/body-linked
    child stays indexed even when it is CLOSED or absent from the open-issue
    set entirely — record ownership proof is historical, not a liveness claim
    (PR #4998 corrective pass, item 1/2). 99 here is native to epic 100 but
    not present in the open-issues list passed to ``classify`` (i.e. closed)."""
    report = classify(
        _issues(100, 200, 5),
        registry,
        {100: ({5, 99}, set()), 150: (set(), set()), 200: (set(), set())},
    )
    index = report["effective_membership"]
    assert "100" not in index and "150" not in index  # epics exempt
    assert index["5"]["epics"] == [100]
    # 99 is closed (not in the open-issues list) but still uniquely owned —
    # ownership proof must accept it.
    assert index["99"] == {
        "epics": [100], "streams": ["product"], "via": "native", "unique_stream": True
    }
    assert make_membership_resolver(report)(99, 100) is True
    # But 99 is NOT open, so it must never resolve as a live issue consumer.
    assert make_issue_resolver(report)("99") is False


def test_issue_resolver_only_open_issues(registry):
    report = classify(_issues(100, 150, 200, 42), registry,
                      {100: ({42}, set()), 150: (set(), set()), 200: (set(), set())})
    resolve = make_issue_resolver(report)
    assert resolve("42") is True
    assert resolve("999") is False  # not open
    assert resolve("not-a-number") is False


def test_issue_resolver_rejects_open_orphan_issue(registry):
    """An open issue with NO stream ownership at all must not resolve as a
    consumer — being in the open set alone is not proof of adoption."""
    report = classify(_issues(100, 150, 200, 42), registry,
                      {100: (set(), set()), 150: (set(), set()), 200: (set(), set())})
    assert make_issue_resolver(report)("42") is False


def test_issue_resolver_rejects_ambiguously_owned_issue(registry):
    """An open issue that IS in the open set but is ambiguously multi-homed
    (unique_stream False) must not resolve — same proof the ownership gate uses."""
    report = classify(_issues(100, 150, 200, 8), registry,
                      {100: ({8}, set()), 150: (set(), set()), 200: ({8}, set())})
    assert make_issue_resolver(report)("8") is False


def test_same_stream_two_epics_is_ambiguous_not_unique(registry):
    """Native membership in TWO epics that share one stream is still ambiguous —
    exact membership means exactly one EFFECTIVE EPIC, not merely one stream
    name (codex/gemini review, PR #4998)."""
    report = classify(
        _issues(100, 150, 200, 77),
        registry,
        {100: ({77}, set()), 150: ({77}, set()), 200: (set(), set())},
    )
    entry = report["effective_membership"]["77"]
    assert entry["epics"] == [100, 150]
    assert entry["streams"] == ["product"]  # one stream name...
    assert entry["unique_stream"] is False  # ...but NOT unique membership
    # The general auditor must surface this as ambiguity too, not report "ok".
    assert [m["number"] for m in report["multi_homed"]] == [77]
    assert report["ok"] is False
    resolve = make_membership_resolver(report)
    assert resolve(77, 100) is False and resolve(77, 150) is False
    assert make_issue_resolver(report)("77") is False


def test_read_membership_index_freshness(tmp_path, registry):
    import json
    import time

    cache = tmp_path / "issue_stream_audit.json"
    report = classify(_issues(100, 150, 200, 42), registry,
                      {100: ({42}, set()), 150: (set(), set()), 200: (set(), set())})
    # Fresh cache → returned.
    report["generated_at"] = int(time.time())
    cache.write_text(json.dumps(report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is not None
    # Stale cache → fail closed to None.
    report["generated_at"] = int(time.time()) - 10_000
    cache.write_text(json.dumps(report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is None
    # Missing cache → None.
    assert read_membership_index(3600, cache_path=tmp_path / "nope.json") is None
    # Pre-P4 cache without the index → None (can't verify → fail closed).
    cache.write_text(json.dumps({"generated_at": int(time.time())}), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is None


# --------------------------------------------------------------------------- #
# ADR-011 P4 — cache authority hardening: malformed/future-skewed evidence
# must fail closed, never raise (codex/gemini review, PR #4998)
# --------------------------------------------------------------------------- #
def _valid_report(now: float) -> dict:
    return {
        "generated_at": now,
        "effective_membership": {
            "42": {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
        },
        "open_issue_numbers": [42, 100, 150, 200],
    }


def test_read_membership_index_rejects_future_skewed_cache(tmp_path):
    import json
    import time

    cache = tmp_path / "cache.json"
    report = _valid_report(time.time() + 10_000)  # far in the future
    cache.write_text(json.dumps(report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is None


def test_read_membership_index_rejects_non_finite_generated_at(tmp_path):
    import json
    import time

    cache = tmp_path / "cache.json"
    now = time.time()
    for bad in (float("nan"), float("inf"), True, "not-a-number", None):
        report = _valid_report(now)
        report["generated_at"] = bad
        cache.write_text(json.dumps(report, allow_nan=True), encoding="utf-8")
        assert read_membership_index(3600, cache_path=cache) is None  # never raises


def test_read_membership_index_rejects_malformed_entries(tmp_path):
    import json
    import time

    cache = tmp_path / "cache.json"
    now = time.time()
    bad_entries = [
        {"epics": [100, 150], "streams": ["product"], "via": "native", "unique_stream": True},  # inconsistent
        {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": "true"},  # truthy string, not bool
        {"epics": [100], "streams": ["product"], "via": "carrier-pigeon", "unique_stream": True},  # unknown via
        {"epics": [-1], "streams": ["product"], "via": "native", "unique_stream": True},  # non-positive epic
        {"epics": [100], "streams": [], "via": "native", "unique_stream": True},  # empty streams
    ]
    for entry in bad_entries:
        report = _valid_report(now)
        report["effective_membership"] = {"42": entry}
        cache.write_text(json.dumps(report), encoding="utf-8")
        assert read_membership_index(3600, cache_path=cache) is None, entry


def test_read_membership_index_rejects_non_positive_int_key(tmp_path):
    import json
    import time

    cache = tmp_path / "cache.json"
    report = _valid_report(time.time())
    report["effective_membership"] = {
        "-5": {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
    }
    cache.write_text(json.dumps(report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is None


def test_read_membership_index_rejects_malformed_open_numbers(tmp_path):
    import json
    import time

    cache = tmp_path / "cache.json"
    report = _valid_report(time.time())
    report["open_issue_numbers"] = [42, "100", -1, True]
    cache.write_text(json.dumps(report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache) is None


# --------------------------------------------------------------------------- #
# ADR-011 P4 corrective pass (PR #4998, item 7) — subIssues GraphQL pagination.
# No network/gh subprocess: ``_paginate_subissues`` takes an injected page
# fetcher, exactly as production wires it to ``_fetch_subissues_page``.
# --------------------------------------------------------------------------- #
def _page(nodes, has_next, end_cursor=None, body=""):
    return {
        "body": body,
        "subIssues": {
            "nodes": [{"number": n} for n in nodes],
            "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
        },
    }


def test_paginate_subissues_single_page_no_truncation():
    def fetch_page(epic, cursor):
        assert cursor is None
        return _page([1, 2, 3], has_next=False, body="see #9")

    native, body = _paginate_subissues(100, fetch_page)
    assert native == {1, 2, 3}
    assert body == "see #9"


def test_paginate_subissues_walks_multiple_pages_past_100():
    # Two pages of 100 + a final partial page — proves an epic with >100
    # children is not silently truncated at the first page.
    pages = [
        _page(range(0, 100), has_next=True, end_cursor="c1", body="epic body"),
        _page(range(100, 200), has_next=True, end_cursor="c2"),
        _page(range(200, 205), has_next=False),
    ]
    calls: list[str | None] = []

    def fetch_page(epic, cursor):
        calls.append(cursor)
        return pages[len(calls) - 1]

    native, body = _paginate_subissues(100, fetch_page)
    assert native == set(range(0, 205))
    assert body == "epic body"  # only the first page's body is kept
    assert calls == [None, "c1", "c2"]


def test_paginate_subissues_stops_without_end_cursor():
    """``hasNextPage: true`` with no ``endCursor`` must stop, not loop forever
    or crash trying to use a null cursor."""
    def fetch_page(epic, cursor):
        return _page([1], has_next=True, end_cursor=None)

    native, _body = _paginate_subissues(100, fetch_page)
    assert native == {1}  # only the one page fetched


def test_paginate_subissues_bounded_against_runaway_pagination():
    """A server that always claims ``hasNextPage: true`` with a fresh cursor
    must not loop forever — the hard page ceiling is the backstop."""
    calls = {"n": 0}

    def fetch_page(epic, cursor):
        calls["n"] += 1
        return _page([calls["n"]], has_next=True, end_cursor=f"c{calls['n']}")

    native, _body = _paginate_subissues(100, fetch_page)
    assert calls["n"] == _MAX_SUBISSUE_PAGES
    assert len(native) == _MAX_SUBISSUE_PAGES
