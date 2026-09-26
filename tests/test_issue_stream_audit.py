"""Hermetic tests for the issue-stream auditor (#4708) — no network, no gh."""

from __future__ import annotations

import json
import re
import subprocess
import textwrap
import threading
from datetime import date

import pytest

from scripts.orchestration import issue_stream_audit
from scripts.orchestration.issue_stream_audit import (
    _MAX_SUBISSUE_PAGES,
    _paginate_subissues,
    _tree_membership,
    classify,
    fetch_issue_states,
    load_milestone_rows,
    load_registry,
    main,
    make_issue_resolver,
    make_membership_resolver,
    milestone_warnings,
    read_membership_index,
    run_audit,
    validate_membership_report,
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


def test_nested_native_descendants_at_depth_two_and_three(registry):
    edges = {100: [10], 10: [11], 11: [12]}
    calls = []

    def fetch_batch(cursors):
        calls.append(set(cursors))
        return {
            number: _page(edges.get(number, []), False, body="see #13" if number == 100 else "") for number in cursors
        }

    membership = _tree_membership({100, 150, 200}, fetch_batch)
    report = classify(_issues(100, 150, 200, 10, 11, 12, 13), registry, membership)
    assert report["orphans"] == []
    assert report["pending_native_link"] == [13]
    assert membership[100][0] == {10, 11, 12}
    assert calls[0] == {100, 150, 200}
    assert calls[1] == {10}


def test_nested_multi_home_keeps_both_root_epics(registry):
    edges = {100: [10], 10: [12], 200: [20], 20: [12]}

    def fetch_batch(cursors):
        return {number: _page(edges.get(number, []), False) for number in cursors}

    membership = _tree_membership({100, 150, 200}, fetch_batch)
    report = classify(_issues(100, 150, 200, 10, 12, 20), registry, membership)
    assert report["multi_homed"] == [{"number": 12, "title": "issue 12", "streams": ["infra", "product"]}]
    assert report["effective_membership"]["12"]["epics"] == [100, 200]


def test_nested_registered_root_owns_its_subtree(registry):
    edges = {100: [150], 150: [10]}

    def fetch_batch(cursors):
        return {number: _page(edges.get(number, []), False) for number in cursors}

    membership = _tree_membership({100, 150}, fetch_batch)
    report = classify(_issues(100, 150, 10), {"product": [100, 150]}, membership)
    assert membership[100][0] == set()
    assert membership[150][0] == {10}
    assert report["multi_homed"] == []
    assert report["effective_membership"]["10"]["epics"] == [150]


def test_nested_root_does_not_hide_independent_native_path():
    edges = {100: [150, 10], 150: [10]}

    def fetch_batch(cursors):
        return {number: _page(edges.get(number, []), False) for number in cursors}

    membership = _tree_membership({100, 150}, fetch_batch)
    report = classify(_issues(100, 150, 10), {"product": [100, 150]}, membership)
    assert report["effective_membership"]["10"]["epics"] == [100, 150]
    assert [item["number"] for item in report["multi_homed"]] == [10]


def test_known_leaf_children_are_not_queried():
    calls = []

    def fetch_batch(cursors):
        calls.append(dict(cursors))
        if 100 in cursors:
            return {100: _page([10, 11], False, child_totals={10: 0, 11: 1})}
        return {11: _page([12], False, child_totals={12: 0})}

    membership = _tree_membership({100}, fetch_batch)
    assert membership[100][0] == {10, 11, 12}
    assert calls == [{100: None}, {11: None}]


def test_tree_traversal_pages_parent_before_next_level():
    calls = []

    def fetch_batch(cursors):
        calls.append(dict(cursors))
        if cursors == {100: None}:
            return {100: _page([10], True, "next", body="see #13")}
        if cursors == {100: "next"}:
            return {100: _page([11], False)}
        return {number: _page([number + 10] if number in {10, 11} else [], False) for number in cursors}

    membership = _tree_membership({100}, fetch_batch)
    assert {10, 11, 20, 21} <= membership[100][0]
    assert membership[100][1] == {13}
    assert calls[:3] == [{100: None}, {100: "next"}, {10: None, 11: None}]


def test_native_descent_stops_at_depth_eight(registry):
    edges = {100: [1], **{number: [number + 1] for number in range(1, 9)}}
    queried = []

    def fetch_batch(cursors):
        queried.extend(cursors)
        return {number: _page(edges.get(number, []), False) for number in cursors}

    warnings = []
    membership = _tree_membership({100}, fetch_batch, warnings)
    assert membership[100][0] == set(range(1, 9))
    assert 8 not in queried
    report = classify(_issues(100, *range(1, 10)), {"product": [100]}, membership)
    assert [item["number"] for item in report["orphans"]] == [9]
    assert warnings == [{"code": "truncated_depth", "depth": 8, "frontier": [8]}]
    assert "WARN: native sub-issue traversal truncated at depth 8" in issue_stream_audit.human_summary(
        {**report, "warnings": warnings}
    )


def test_depth_eight_known_leaf_does_not_warn():
    edges = {100: [1], **{number: [number + 1] for number in range(1, 8)}}
    warnings = []

    def fetch_batch(cursors):
        return {
            number: _page(
                edges.get(number, []),
                False,
                child_totals={child: 0 if child == 8 else 1 for child in edges.get(number, [])},
            )
            for number in cursors
        }

    membership = _tree_membership({100}, fetch_batch, warnings)
    assert membership[100][0] == set(range(1, 9))
    assert warnings == []


def test_subissue_batch_uses_one_query_for_multiple_parents(monkeypatch):
    calls = []
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))

    def fake_gh_json(args, *, cwd):
        calls.append((args, cwd))
        return {"data": {"repository": {"i100": _page([10], False, body="see #13"), "i200": _page([20], False)}}}

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    pages = issue_stream_audit._fetch_subissue_batch({100: None, 200: "cursor"}, body_roots={100})
    assert len(calls) == 1
    query = calls[0][0][-1]
    assert "i100:issue(number:100){body subIssues(first:100)" in query
    assert 'i200:issue(number:200){subIssues(first:100,after:"cursor")' in query
    assert "nodes{number repository{nameWithOwner} subIssuesSummary{total}}" in query
    assert {number: page["subIssues"]["nodes"][0]["number"] for number, page in pages.items()} == {100: 10, 200: 20}


def test_closed_epic_remains_registered_but_is_not_an_audit_root():
    path = issue_stream_audit.REGISTRY_PATH
    registry = load_registry(path)
    assert "eval-harness" not in registry
    assert "a1-upgrade" not in registry
    assert registry["open-model-data"] == [6321, 7423]

    audit_registry = load_registry(path, audit_only=True)
    assert audit_registry["open-model-data"] == [6321]
    assert 7423 not in {n for epics in audit_registry.values() for n in epics}
    report = classify(_issues(*[n for epics in audit_registry.values() for n in epics]), audit_registry, {})
    assert report["closed_or_missing_epics"] == []
    assert report["ok"] is True


@pytest.mark.parametrize(
    "selector",
    ["a1-upgrade", "eval-harness", "infra.a1-upgrade", "infra.eval-harness"],
)
def test_retired_stream_launchers_fail_closed(selector):
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_resolve "$2"',
            "bash",
            str(issue_stream_audit.ROOT / "scripts/lib/handoff_identity.sh"),
            selector,
        ],
        cwd=issue_stream_audit.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert f"retired lane selector: {selector}" in result.stderr


# --------------------------------------------------------------------------- #
# #5898 — advisory stream-milestone hygiene. These fixtures never invoke gh;
# issue states are injected into the pure warning classifier.
# --------------------------------------------------------------------------- #
def test_milestone_warnings_cover_marked_rows_closed_issues_and_old_confirmations(tmp_path):
    workstreams = tmp_path / "WORKSTREAMS.md"
    workstreams.write_text(
        textwrap.dedent(
            """
            # Workstreams

            ## Stream milestones (the focus layer)

            | Stream | State | Current milestone | Done when |
            | --- | --- | --- | --- |
            | product | STALE | Repair #41 [confirmed-at: 2026-01-01] | Never inspect #99 |
            | intake | ACTIVE | Rebuild #42 | — |
            | corpus | *(VACANT — operator to set)* | Choose #50–#52 | — |

            ## Next section
            | Stream | State | Current milestone | Done when |
            | ignored | STALE | #100 | — |
            """
        ),
        encoding="utf-8",
    )

    rows = load_milestone_rows(workstreams)
    assert [row["stream"] for row in rows] == ["product", "intake", "corpus"]
    assert rows[0]["issue_numbers"] == {41}
    assert rows[2]["issue_numbers"] == {50, 51, 52}

    warnings = milestone_warnings(
        rows,
        {41: "OPEN", 42: "CLOSED", 50: "CLOSED", 51: "OPEN"},
        unavailable_issue_numbers={52},
        today=date(2026, 2, 1),
        max_confirmed_age_days=14,
    )

    assert warnings == [
        {"code": "milestone_row_marked", "stream": "product", "marker": "STALE"},
        {
            "code": "milestone_confirmed_at_stale",
            "stream": "product",
            "confirmed_at": "2026-01-01",
            "age_days": 31,
            "max_age_days": 14,
        },
        {"code": "milestone_closed_issue", "stream": "intake", "issue": 42},
        {"code": "milestone_row_marked", "stream": "corpus", "marker": "VACANT"},
        {"code": "milestone_closed_issue", "stream": "corpus", "issue": 50},
        {
            "code": "milestone_issue_state_unavailable",
            "stream": "corpus",
            "issue": 52,
        },
    ]


def test_milestone_marker_is_scoped_to_state_cell(tmp_path):
    workstreams = tmp_path / "WORKSTREAMS.md"
    workstreams.write_text(
        textwrap.dedent(
            """
            ## Stream milestones (the focus layer)

            | Stream | State | Current milestone | Done when |
            | --- | --- | --- | --- |
            | product | ACTIVE | Refresh stale cache for #41 | — |
            | intake | VACANT | Assign #42 | — |
            """
        ),
        encoding="utf-8",
    )

    rows = load_milestone_rows(workstreams)

    assert [row["marker"] for row in rows] == [None, "VACANT"]


def test_milestone_issue_state_lookup_degrades_to_warning(monkeypatch):
    def fake_gh_json(args, **_kwargs):
        if args[2] == "41":
            return {"number": 41, "state": "CLOSED"}
        raise RuntimeError("not found")

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    states, unavailable = fetch_issue_states({41, 42})

    assert states == {41: "CLOSED"}
    assert unavailable == {42}


def test_milestone_issue_state_lookup_reuses_known_open_issues(monkeypatch):
    def unexpected_gh_json(*_args, **_kwargs):
        raise AssertionError("known-open issue must not be queried")

    monkeypatch.setattr(issue_stream_audit, "_gh_json", unexpected_gh_json)

    states, unavailable = fetch_issue_states({41}, known_open_issue_numbers={41})

    assert states == {41: "OPEN"}
    assert unavailable == set()


def test_milestone_warnings_report_closed_issue_and_ignore_invalid_confirmation():
    warnings = milestone_warnings(
        [
            {
                "stream": "product",
                "marker": None,
                "issue_numbers": {41},
                "confirmed_at": date(2026, 1, 1),
            },
            {
                "stream": "intake",
                "marker": None,
                "issue_numbers": set(),
                # Invalid confirmed-at values are ignored by the parser, so
                # they must not be invented into age warnings downstream.
                "confirmed_at": None,
            },
        ],
        {41: "CLOSED"},
        today=date(2026, 2, 1),
        max_confirmed_age_days=14,
    )

    assert warnings == [
        {"code": "milestone_closed_issue", "stream": "product", "issue": 41},
        {
            "code": "milestone_confirmed_at_stale",
            "stream": "product",
            "confirmed_at": "2026-01-01",
            "age_days": 31,
            "max_age_days": 14,
        },
    ]


def test_invalid_confirmed_at_marker_is_ignored(tmp_path):
    workstreams = tmp_path / "WORKSTREAMS.md"
    workstreams.write_text(
        textwrap.dedent(
            """
            ## Stream milestones (the focus layer)

            | Stream | State | Current milestone | Done when |
            | --- | --- | --- | --- |
            | product | ACTIVE | Repair #41 [confirmed-at: 2026-02-30] | — |
            """
        ),
        encoding="utf-8",
    )

    assert load_milestone_rows(workstreams)[0]["confirmed_at"] is None


def test_milestone_warnings_are_non_fatal_in_check_mode(monkeypatch, capsys):
    report = classify(
        _issues(100, 150, 200),
        {"product": [100, 150], "infra": [200]},
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )
    report["warnings"] = [
        {"code": "milestone_row_marked", "stream": "product", "marker": "STALE"},
        {"code": "milestone_closed_issue", "stream": "infra", "issue": 42},
        {"code": "milestone_issue_state_unavailable", "stream": "infra", "issue": 43},
        {
            "code": "milestone_confirmed_at_stale",
            "stream": "infra",
            "confirmed_at": "2026-01-01",
            "age_days": 31,
            "max_age_days": 14,
        },
    ]
    monkeypatch.setattr(issue_stream_audit, "run_audit", lambda **_kwargs: report)

    assert main(["--check"]) == 0
    output = capsys.readouterr().out
    assert "WARN: stream milestone product marked STALE" in output
    assert "WARN: stream milestone infra references closed issue #42" in output
    assert "WARN: stream milestone infra could not verify issue #43 status" in output
    assert "WARN: stream milestone infra confirmed-at 2026-01-01 is 31 days old (max 14)" in output
    assert "ok: True" in output


def test_max_confirmed_age_days_cli_reaches_audit(monkeypatch, capsys):
    observed: dict[str, int] = {}
    report = classify(
        _issues(100, 150, 200),
        {"product": [100, 150], "infra": [200]},
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )

    def fake_run_audit(**kwargs):
        observed.update(kwargs)
        return report

    monkeypatch.setattr(issue_stream_audit, "run_audit", fake_run_audit)

    assert main(["--max-confirmed-age-days", "21"]) == 0
    assert observed == {"max_confirmed_age_days": 21}
    assert "ok: True" in capsys.readouterr().out


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
    assert index["99"] == {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
    assert make_membership_resolver(report)(99, 100) is True
    # But 99 is NOT open, so it must never resolve as a live issue consumer.
    assert make_issue_resolver(report)("99") is False


def test_issue_resolver_only_open_issues(registry):
    report = classify(
        _issues(100, 150, 200, 42), registry, {100: ({42}, set()), 150: (set(), set()), 200: (set(), set())}
    )
    resolve = make_issue_resolver(report)
    assert resolve("42") is True
    assert resolve("999") is False  # not open
    assert resolve("not-a-number") is False


def test_issue_resolver_rejects_open_orphan_issue(registry):
    """An open issue with NO stream ownership at all must not resolve as a
    consumer — being in the open set alone is not proof of adoption."""
    report = classify(
        _issues(100, 150, 200, 42), registry, {100: (set(), set()), 150: (set(), set()), 200: (set(), set())}
    )
    assert make_issue_resolver(report)("42") is False


def test_issue_resolver_rejects_ambiguously_owned_issue(registry):
    """An open issue that IS in the open set but is ambiguously multi-homed
    (unique_stream False) must not resolve — same proof the ownership gate uses."""
    report = classify(_issues(100, 150, 200, 8), registry, {100: ({8}, set()), 150: (set(), set()), 200: ({8}, set())})
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
    report = classify(
        _issues(100, 150, 200, 42), registry, {100: ({42}, set()), 150: (set(), set()), 200: (set(), set())}
    )
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
# #6028 — validate_membership_report: same fail-closed rules as
# read_membership_index, applied to an in-memory (not file-cached) report, so
# task_lifecycle.resolve_membership can carry one live run_audit() snapshot
# through a single observation without a second round trip through disk.
# --------------------------------------------------------------------------- #
def test_validate_membership_report_accepts_fresh_in_memory_report():
    import time

    report = _valid_report(time.time())
    assert validate_membership_report(report, 3600) == report


def test_validate_membership_report_rejects_stale_in_memory_report():
    import time

    report = _valid_report(time.time() - 10_000)
    assert validate_membership_report(report, 3600) is None


def test_validate_membership_report_rejects_non_dict():
    assert validate_membership_report(None, 3600) is None
    assert validate_membership_report("not-a-report", 3600) is None
    assert validate_membership_report([], 3600) is None


# --------------------------------------------------------------------------- #
# ADR-011 P4 corrective pass (PR #4998, item 7) — subIssues GraphQL pagination.
# No network/gh subprocess: ``_paginate_subissues`` takes an injected page
# fetcher, exactly as production wires it to ``_fetch_subissues_page``.
# --------------------------------------------------------------------------- #
def _page(nodes, has_next, end_cursor=None, body="", child_totals=None):
    return {
        "body": body,
        "subIssues": {
            "nodes": [
                {"number": n, "subIssuesSummary": {"total": child_totals[n]}}
                if child_totals and n in child_totals
                else {"number": n}
                for n in nodes
            ],
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


# --------------------------------------------------------------------------- #
# Review finding F001 (PR #6030) — ``run_audit`` must carry an explicit repo
# root all the way through registry lookup, ``gh`` execution cwd, and the
# cache it writes, instead of the module's own ``ROOT``. Fake ``gh`` via
# ``subprocess.run`` (not a higher-level seam) so the cwd threading itself is
# proven, not assumed.
# --------------------------------------------------------------------------- #
class _FakeCompletedProcess:
    def __init__(self, stdout: str, returncode: int = 0, stderr: str = "") -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _make_repo(root, *, epics: list[int]) -> None:
    (root / "scripts" / "config").mkdir(parents=True)
    (root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "streams:\n  s:\n    title: s\n    epics: " + json.dumps(epics) + "\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "WORKSTREAMS.md").write_text(
        "## Stream milestones (the focus layer)\n\n"
        "| Stream | State | Current milestone | Done when |\n"
        "| --- | --- | --- | --- |\n"
        "| s | ACTIVE | No issue references | — |\n",
        encoding="utf-8",
    )


def _fake_gh_run(calls, *, owner: str, name: str, open_issues: list[dict]):
    """A ``subprocess.run`` stand-in recording every ``(args, cwd)`` pair and
    answering the exact three ``gh`` calls ``run_audit`` makes for a registry
    with a single epic and no native/body children."""

    def _run(args, capture_output, text, timeout, cwd):
        calls.append((tuple(args), cwd))
        assert args[0] == "gh"
        if args[1:3] == ["issue", "list"]:
            return _FakeCompletedProcess(json.dumps(open_issues))
        if args[1:3] == ["repo", "view"]:
            return _FakeCompletedProcess(json.dumps({"owner": {"login": owner}, "name": name}))
        if args[1] == "api" and args[2] == "graphql":
            return _FakeCompletedProcess(
                json.dumps(
                    {
                        "data": {
                            "repository": {
                                "i100": {
                                    "body": "",
                                    "subIssues": {
                                        "nodes": [],
                                        "pageInfo": {
                                            "hasNextPage": False,
                                            "endCursor": None,
                                        },
                                    },
                                }
                            }
                        }
                    }
                )
            )
        raise AssertionError(f"unexpected gh invocation: {args}")

    return _run


def test_run_audit_scopes_registry_gh_execution_and_cache_to_explicit_root(tmp_path, monkeypatch):
    """A non-default ``repo_root`` passed to ``run_audit`` must be honored for
    the registry, every ``gh`` call's cwd, and the cache write — never the
    auditor module's own ``ROOT`` (finding F001: a closeout invocation
    configured for another checkout must not validate against, or cache
    into, the wrong repository)."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    other_root = tmp_path / "unrelated-checkout"
    _make_repo(other_root, epics=[999])

    target_root = tmp_path / "target-checkout"
    _make_repo(target_root, epics=[100])

    calls: list[tuple[tuple, object]] = []
    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _fake_gh_run(calls, owner="acme", name="target-repo", open_issues=[]),
    )

    report = run_audit(target_root)

    assert report["streams"] == {"s": [100]}
    # Every gh subprocess call ran with cwd pinned to the requested root —
    # never the unrelated sibling root, never the module's own ROOT.
    assert calls, "expected at least one gh invocation"
    assert {cwd for _args, cwd in calls} == {target_root.resolve()}

    cache_path = target_root / "batch_state" / "issue_stream_audit.json"
    assert cache_path.exists()
    assert not (other_root / "batch_state" / "issue_stream_audit.json").exists()


def test_run_audit_default_root_preserves_module_root_behavior(tmp_path, monkeypatch):
    """Calling ``run_audit()`` with no argument must still resolve against the
    module's own ``ROOT`` — the fix must not change plain CLI behavior."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    fake_root = tmp_path / "module-root-stand-in"
    _make_repo(fake_root, epics=[7])
    monkeypatch.setattr(issue_stream_audit, "ROOT", fake_root)

    calls: list[tuple[tuple, object]] = []
    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _fake_gh_run(calls, owner="acme", name="default-repo", open_issues=[]),
    )

    report = run_audit()

    assert report["streams"] == {"s": [7]}
    assert {cwd for _args, cwd in calls} == {fake_root}
    assert (fake_root / "batch_state" / "issue_stream_audit.json").exists()


def test_repo_owner_name_cache_keyed_by_root_does_not_leak(tmp_path, monkeypatch):
    """``_repo_owner_name`` must resolve independently per root — a cache
    warmed for one checkout must not answer for a different one."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root_a = tmp_path / "repo-a"
    root_b = tmp_path / "repo-b"
    root_a.mkdir()
    root_b.mkdir()

    answers = {str(root_a): ("owner-a", "repo-a"), str(root_b): ("owner-b", "repo-b")}

    def _run(args, capture_output, text, timeout, cwd):
        assert args[1:3] == ["repo", "view"]
        owner, name = answers[str(cwd)]
        return _FakeCompletedProcess(json.dumps({"owner": {"login": owner}, "name": name}))

    monkeypatch.setattr(issue_stream_audit.subprocess, "run", _run)

    assert issue_stream_audit._repo_owner_name(root_a) == ("owner-a", "repo-a")
    assert issue_stream_audit._repo_owner_name(root_b) == ("owner-b", "repo-b")
    # Re-resolving root_a must still return root_a's own answer, not root_b's
    # (proves the cache key is the root, not a single shared slot).
    assert issue_stream_audit._repo_owner_name(root_a) == ("owner-a", "repo-a")


# --------------------------------------------------------------------------- #
# #6145 — detached single-flight refresh state
# --------------------------------------------------------------------------- #
def _refresh_paths(tmp_path, monkeypatch):
    state = tmp_path / "issue_stream_audit_refresh.json"
    lock = tmp_path / "issue_stream_audit_refresh.lock"
    monkeypatch.setattr(issue_stream_audit, "REFRESH_STATE_PATH", state)
    monkeypatch.setattr(issue_stream_audit, "REFRESH_LOCK_PATH", lock)
    return state


def test_refresh_lock_file_is_owner_only(tmp_path, monkeypatch):
    _refresh_paths(tmp_path, monkeypatch)

    fd = issue_stream_audit._try_lock_nb()

    assert fd is not None
    issue_stream_audit._release_lock(fd)
    lock_path = tmp_path / "issue_stream_audit_refresh.lock"
    assert lock_path.stat().st_mode & 0o077 == 0


def test_refresh_lock_repairs_legacy_permissions(tmp_path, monkeypatch):
    _refresh_paths(tmp_path, monkeypatch)
    lock_path = tmp_path / "issue_stream_audit_refresh.lock"
    lock_path.touch(mode=0o644)
    lock_path.chmod(0o644)

    fd = issue_stream_audit._try_lock_nb()

    assert fd is not None
    issue_stream_audit._release_lock(fd)
    assert lock_path.stat().st_mode & 0o077 == 0


def _scheduled_state(run_id="new-run", now=100):
    return {
        "schema_version": 1,
        "run_id": run_id,
        "phase": "scheduled",
        "requested_at": now,
        "started_at": None,
        "last_outcome": "none",
        "last_outcome_at": None,
        "failure_code": None,
        "cooldown_until": None,
    }


def test_refresh_missing_and_malformed_state_fail_safe_idle(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    assert issue_stream_audit.read_refresh_state(now=100)["phase"] == "idle"

    state_path.write_text('{"phase":"running","run_id":"secret"', encoding="utf-8")
    public = issue_stream_audit.public_refresh_view(issue_stream_audit.read_refresh_state(now=100))
    assert public == {
        "phase": "idle",
        "requested_at": None,
        "started_at": None,
        "last_outcome": "none",
        "last_outcome_at": None,
        "failure_code": None,
        "retry_after": None,
    }
    assert "run_id" not in public


def test_schedule_refresh_is_single_flight_and_preserves_previous_outcome(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    spawned = []
    monkeypatch.setattr(issue_stream_audit.time, "time", lambda: 100.0)
    monkeypatch.setattr(issue_stream_audit, "_spawn_worker", lambda run_id: spawned.append(run_id) or True)

    first = issue_stream_audit.schedule_refresh()
    second = issue_stream_audit.schedule_refresh(force=True)

    assert first["phase"] == second["phase"] == "scheduled"
    assert first["run_id"] == second["run_id"]
    assert spawned == [first["run_id"]]
    assert json.loads(state_path.read_text(encoding="utf-8"))["run_id"] == first["run_id"]


def test_spawn_worker_uses_live_interpreter_and_snapshot_code(tmp_path, monkeypatch):
    live_root = tmp_path / "live"
    snapshot_root = tmp_path / "release"
    captured = {}

    def _popen(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(issue_stream_audit, "LIVE_REPO_ROOT", live_root)
    monkeypatch.setattr(issue_stream_audit, "ROOT", snapshot_root)
    monkeypatch.setattr(issue_stream_audit.subprocess, "Popen", _popen)

    assert issue_stream_audit._spawn_worker("run-1") is True
    assert captured["argv"] == [
        str(live_root / ".venv" / "bin" / "python"),
        "-m",
        "scripts.orchestration.issue_stream_audit",
        "--refresh-worker",
        "run-1",
    ]
    assert captured["kwargs"]["cwd"] == str(snapshot_root)
    assert captured["kwargs"]["start_new_session"] is True


def test_concurrent_schedulers_spawn_exactly_one_worker(tmp_path, monkeypatch):
    _refresh_paths(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    spawned = []
    results = []

    def _spawn(run_id):
        spawned.append(run_id)
        entered.set()
        assert release.wait(timeout=2)
        return True

    monkeypatch.setattr(issue_stream_audit, "_spawn_worker", _spawn)
    first = threading.Thread(target=lambda: results.append(issue_stream_audit.schedule_refresh()))
    first.start()
    assert entered.wait(timeout=2)

    # The first scheduler still holds the cross-process lock here. The second
    # request can only observe its scheduled run; it cannot spawn another.
    results.append(issue_stream_audit.schedule_refresh(force=True))
    release.set()
    first.join(timeout=2)

    assert not first.is_alive()
    assert len(results) == 2
    assert results[0]["run_id"] == results[1]["run_id"]
    assert spawned == [results[0]["run_id"]]


def test_spawn_failure_cooldown_and_explicit_recovery(tmp_path, monkeypatch):
    _refresh_paths(tmp_path, monkeypatch)
    clock = [100.0]
    monkeypatch.setattr(issue_stream_audit.time, "time", lambda: clock[0])
    monkeypatch.setattr(issue_stream_audit, "_spawn_worker", lambda _run_id: False)

    failed = issue_stream_audit.schedule_refresh()
    assert failed["phase"] == "idle"
    assert failed["last_outcome"] == "failed"
    assert failed["failure_code"] == "spawn_failed"
    assert failed["cooldown_until"] == 160

    # Automatic stale requests respect cooldown; explicit fresh=true bypasses it.
    assert issue_stream_audit.schedule_refresh()["phase"] == "idle"
    monkeypatch.setattr(issue_stream_audit, "_spawn_worker", lambda _run_id: True)
    recovering = issue_stream_audit.schedule_refresh(force=True)
    assert recovering["phase"] == "scheduled"
    assert recovering["last_outcome"] == "failed"
    assert recovering["failure_code"] == "spawn_failed"


def test_worker_failure_then_success_is_fenced_and_truthful(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    clock = [100.0]
    monkeypatch.setattr(issue_stream_audit.time, "time", lambda: clock[0])
    monkeypatch.setattr(issue_stream_audit, "_spawn_worker", lambda _run_id: True)

    scheduled = issue_stream_audit.schedule_refresh()
    run_id = scheduled["run_id"]
    monkeypatch.setattr(issue_stream_audit, "run_audit", lambda: (_ for _ in ()).throw(RuntimeError("secret")))
    assert issue_stream_audit._run_refresh_worker(run_id) == 1
    failed = json.loads(state_path.read_text(encoding="utf-8"))
    assert failed["phase"] == "idle" and failed["failure_code"] == "source_error"
    assert "secret" not in json.dumps(failed)

    clock[0] = 101.0
    recovering = issue_stream_audit.schedule_refresh(force=True)
    assert recovering["last_outcome"] == "failed"
    monkeypatch.setattr(issue_stream_audit, "run_audit", lambda: {"ok": True})
    assert issue_stream_audit._run_refresh_worker(recovering["run_id"]) == 0
    succeeded = json.loads(state_path.read_text(encoding="utf-8"))
    assert succeeded["phase"] == "idle"
    assert succeeded["last_outcome"] == "succeeded"
    assert succeeded["failure_code"] is None


def test_worker_lost_reconciles_and_persists_failure(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    running = _scheduled_state(now=100)
    running.update(phase="running", started_at=101)
    issue_stream_audit._write_refresh_state_atomic(running)

    observed = issue_stream_audit.read_refresh_state(now=120)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert observed == persisted
    assert observed["phase"] == "idle"
    assert observed["failure_code"] == "worker_lost"
    assert observed["cooldown_until"] == 180


def test_stale_worker_run_id_cannot_overwrite_newer_run(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    issue_stream_audit._write_refresh_state_atomic(_scheduled_state("new-run"))
    called = []
    monkeypatch.setattr(issue_stream_audit, "run_audit", lambda: called.append(True))

    assert issue_stream_audit._run_refresh_worker("old-run") == 0
    assert called == []
    assert json.loads(state_path.read_text(encoding="utf-8"))["run_id"] == "new-run"


def test_refresh_state_atomic_replace_never_exposes_partial_json(tmp_path, monkeypatch):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    issue_stream_audit._write_refresh_state_atomic(issue_stream_audit._default_refresh_state())
    failures = []

    def _writer():
        for run in range(25):
            issue_stream_audit._write_refresh_state_atomic(_scheduled_state(f"run-{run}", run))

    thread = threading.Thread(target=_writer)
    thread.start()
    while thread.is_alive():
        try:
            assert isinstance(json.loads(state_path.read_text(encoding="utf-8")), dict)
        except (AssertionError, json.JSONDecodeError) as exc:
            failures.append(exc)
    thread.join()
    assert failures == []


def test_private_cache_keys_includes_open_issue_titles():
    assert "open_issue_titles" in issue_stream_audit.PRIVATE_CACHE_KEYS
    assert issue_stream_audit.PRIVATE_CACHE_KEYS == (
        "effective_membership",
        "open_issue_numbers",
        "open_issue_titles",
    )


# --------------------------------------------------------------------------- #
# #8661 — PR #8660 cross-family review follow-ups: registry validation branch
# tests, per-node traversal degradation, closed_epics upkeep warning, and the
# research-registry adoption pointer.
# --------------------------------------------------------------------------- #
def _write_streams(tmp_path, body: str):
    path = tmp_path / "issue_streams.yaml"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_registry_rejects_non_bool_retired(tmp_path):
    path = _write_streams(
        tmp_path,
        """
        streams:
          broken:
            title: x
            epics: [100]
            retired: "soon"
        """,
    )
    with pytest.raises(ValueError, match=r"broken.*retired"):
        load_registry(path)


def test_registry_rejects_closed_epics_outside_epic_list(tmp_path):
    path = _write_streams(
        tmp_path,
        """
        streams:
          broken:
            title: x
            epics: [100]
            closed_epics: [999]
        """,
    )
    with pytest.raises(ValueError, match=r"broken.*closed epics outside"):
        load_registry(path)


def test_retired_stream_stays_registered_but_is_not_an_audit_root(tmp_path):
    path = _write_streams(
        tmp_path,
        """
        streams:
          live:
            title: x
            epics: [100]
          old:
            title: y
            epics: [200]
            retired: true
        """,
    )
    assert load_registry(path) == {"live": [100], "old": [200]}
    assert load_registry(path, audit_only=True) == {"live": [100]}


def test_research_registry_adoption_guidance_points_at_live_stream():
    """The deferred GEC record must not send readers to the retired eval-harness
    epic #4913: the #8305 decision records that "model evaluation authority now
    lives in open-model-data #6321", so the adoption pointer is #6321."""
    import yaml

    doc = yaml.safe_load(
        (issue_stream_audit.ROOT / "docs" / "references" / "research-registry.yaml").read_text(encoding="utf-8")
    )
    record = next(r for r in doc["records"] if r["id"] == "unlp-2026-gec-minimal-edit")
    reason = record["reason"]
    assert "#4913 is closed" not in reason
    assert "#6321" in reason
    live_roots = {
        epic for epics in load_registry(issue_stream_audit.REGISTRY_PATH, audit_only=True).values() for epic in epics
    }
    assert 6321 in live_roots
    assert 4913 not in live_roots


def test_tree_membership_skips_unresolved_node_with_warning():
    edges = {100: [10, 11]}

    def fetch_batch(cursors):
        return {number: (None if number == 10 else _page(edges.get(number, []), False)) for number in cursors}

    warnings = []
    membership = _tree_membership({100}, fetch_batch, warnings)
    # The link itself is still membership; only the dead node's subtree is lost.
    assert membership[100][0] == {10, 11}
    assert warnings == [{"code": "unresolved_subissue", "issue": 10}]
    assert "WARN: sub-issue #10 no longer resolves" in issue_stream_audit.human_summary(
        {**classify(_issues(100, 10, 11), {"product": [100]}, membership), "warnings": warnings}
    )


def test_tree_membership_does_not_follow_cross_repo_child():
    queried = []

    def fetch_batch(cursors):
        queried.append(set(cursors))
        pages = {}
        for number in cursors:
            if number == 100:
                pages[number] = {
                    "body": "",
                    "subIssues": {
                        "nodes": [
                            {"number": 10, "repository": {"nameWithOwner": "acme/repo"}},
                            {"number": 77, "repository": {"nameWithOwner": "other/foreign"}},
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                }
            else:
                pages[number] = _page([], False)
        return pages

    warnings = []
    membership = _tree_membership({100}, fetch_batch, warnings, repo_slug="acme/repo")
    assert membership[100][0] == {10}
    assert warnings == [{"code": "cross_repo_subissue", "parent": 100, "issue": 77, "repository": "other/foreign"}]
    assert all(77 not in batch for batch in queried)
    report = classify(_issues(100, 10), {"product": [100]}, membership)
    assert "WARN: cross-repo sub-issue other/foreign#77 under #100 not followed" in (
        issue_stream_audit.human_summary({**report, "warnings": warnings})
    )


def test_subissue_batch_returns_none_for_null_node_and_scopes_repo(monkeypatch):
    """A fake ``gh`` answering one alias with a null node: the batch must
    return ``None`` for exactly that node and keep the others."""
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))
    calls = []

    def fake_gh_json(args, *, cwd):
        calls.append(args)
        return {"data": {"repository": {"i100": None, "i200": _page([20], False)}}}

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    pages = issue_stream_audit._fetch_subissue_batch({100: None, 200: None})
    assert pages[100] is None
    assert pages[200]["subIssues"]["nodes"][0]["number"] == 20
    # Node lookups carry their repository so cross-repo children are detectable.
    assert "repository{nameWithOwner}" in calls[0][-1]


def test_subissue_batch_degrades_per_node_when_batch_query_fails(monkeypatch):
    """A ``gh api graphql`` error on the combined batch must not fail the whole
    audit: retry each parent alone so only the poisoned node degrades. A
    failed singleton was never read, so it comes back ``INCOMPLETE_NODE``
    (fail closed, #8661) — not ``None``, which is reserved for a node GitHub
    confirmed absent."""
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))

    def fake_gh_json(args, *, cwd):
        query = args[-1]
        if "i200:issue" in query:
            raise RuntimeError("gh api graphql… failed: errors present")
        return {"data": {"repository": {"i100": _page([10], False)}}}

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    pages = issue_stream_audit._fetch_subissue_batch({100: None, 200: None})
    assert pages[100]["subIssues"]["nodes"][0]["number"] == 10
    assert pages[200] is issue_stream_audit.INCOMPLETE_NODE


def test_subissue_batch_graphql_errors_are_incomplete_not_absent(monkeypatch):
    """A response carrying a GraphQL ``errors`` payload cannot be trusted: its
    ``null`` alias might be the error, not a genuinely absent node. Degrade
    per node; a singleton that still returns errors is INCOMPLETE_NODE."""
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))

    def fake_gh_json(args, *, cwd):
        query = args[-1]
        if "i200:issue" in query:
            return {"data": {"repository": {"i200": None}}, "errors": [{"message": "boom"}]}
        return {"data": {"repository": {"i100": _page([10], False)}}}

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    pages = issue_stream_audit._fetch_subissue_batch({100: None, 200: None})
    assert pages[100]["subIssues"]["nodes"][0]["number"] == 10
    assert pages[200] is issue_stream_audit.INCOMPLETE_NODE


def test_subissue_batch_caps_singleton_retries_with_budget(monkeypatch):
    """The per-node fallback is bounded (#8661): once the shared budget is
    spent, remaining parents come back INCOMPLETE_NODE with no ``gh`` call."""
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))
    calls = []

    def fake_gh_json(args, *, cwd):
        calls.append(args)
        raise RuntimeError("gh api graphql… failed")

    monkeypatch.setattr(issue_stream_audit, "_gh_json", fake_gh_json)
    budget = issue_stream_audit._RetryBudget(limit=2)
    pages = issue_stream_audit._fetch_subissue_batch({number: None for number in (1, 2, 3, 4, 5)}, retry_budget=budget)
    # 1 failed batch + exactly 2 singleton retries; parents 3–5 never hit the network.
    assert len(calls) == 3
    assert budget.remaining == 0
    assert all(pages[n] is issue_stream_audit.INCOMPLETE_NODE for n in (1, 2, 3, 4, 5))


def _run_audit_fake_gh(calls, *, owner: str, name: str, open_issues: list[dict], tree: dict):
    """``subprocess.run`` stand-in for ``run_audit`` over a native-link tree.

    ``tree`` maps an issue number to a list of sub-issue node dicts, or to
    ``None`` when that issue no longer resolves (null GraphQL node).
    """

    def _run(args, capture_output, text, timeout, cwd):
        calls.append((tuple(args), cwd))
        assert args[0] == "gh"
        if args[1:3] == ["issue", "list"]:
            return _FakeCompletedProcess(json.dumps(open_issues))
        if args[1:3] == ["repo", "view"]:
            return _FakeCompletedProcess(json.dumps({"owner": {"login": owner}, "name": name}))
        if args[1:3] == ["issue", "view"]:
            return _FakeCompletedProcess(json.dumps({"number": int(args[3]), "state": "CLOSED"}))
        if args[1] == "api" and args[2] == "graphql":
            repo = {}
            for number_text in re.findall(r"i(\d+):issue\(number:", args[-1]):
                number = int(number_text)
                nodes = tree.get(number, [])
                if nodes is None:
                    repo[f"i{number}"] = None
                else:
                    repo[f"i{number}"] = {
                        "body": "",
                        "subIssues": {
                            "nodes": nodes,
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
            return _FakeCompletedProcess(json.dumps({"data": {"repository": repo}}))
        raise AssertionError(f"unexpected gh invocation: {args}")

    return _run


def _node(number: int, owner: str, name: str, total: int = 0, repo: str | None = None) -> dict:
    return {
        "number": number,
        "repository": {"nameWithOwner": repo or f"{owner}/{name}"},
        "subIssuesSummary": {"total": total},
    }


def test_run_audit_degrades_on_unresolvable_descendant(tmp_path, monkeypatch):
    """Cold-start robustness (#8661 item 3): one descendant that no longer
    resolves must degrade to a per-node warning, not fail the whole audit."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo(root, epics=[100])

    calls = []
    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh(
            calls,
            owner="acme",
            name="repo",
            open_issues=_issues(100, 10),
            tree={100: [_node(10, "acme", "repo", total=1)], 10: None},
        ),
    )

    report = run_audit(root)

    assert {"code": "unresolved_subissue", "issue": 10} in report["warnings"]
    assert report["orphans"] == []
    assert report["ok"] is True
    assert "WARN: sub-issue #10 no longer resolves" in issue_stream_audit.human_summary(report)


def test_run_audit_reports_cross_repo_child_without_following_it(tmp_path, monkeypatch):
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo(root, epics=[100])

    calls = []
    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh(
            calls,
            owner="acme",
            name="repo",
            open_issues=_issues(100),
            tree={100: [_node(77, "acme", "repo", repo="other/foreign")]},
        ),
    )

    report = run_audit(root)

    assert {
        "code": "cross_repo_subissue",
        "parent": 100,
        "issue": 77,
        "repository": "other/foreign",
    } in report["warnings"]
    # The foreign number was never looked up in THIS repository.
    assert not any("i77:issue" in args[-1] for args, _cwd in calls if args[1:2] == ["api"])
    assert report["ok"] is True


def _run_audit_fake_gh_failing_nodes(
    calls, *, owner: str, name: str, open_issues: list[dict], tree: dict, failing: set[int]
):
    """Like ``_run_audit_fake_gh``, but any GraphQL query whose aliases include
    a number in ``failing`` exits non-zero (transport/GitHub failure)."""

    def _run(args, capture_output, text, timeout, cwd):
        calls.append((tuple(args), cwd))
        assert args[0] == "gh"
        if args[1:3] == ["issue", "list"]:
            return _FakeCompletedProcess(json.dumps(open_issues))
        if args[1:3] == ["repo", "view"]:
            return _FakeCompletedProcess(json.dumps({"owner": {"login": owner}, "name": name}))
        if args[1:3] == ["issue", "view"]:
            return _FakeCompletedProcess(json.dumps({"number": int(args[3]), "state": "CLOSED"}))
        if args[1] == "api" and args[2] == "graphql":
            numbers = [int(n) for n in re.findall(r"i(\d+):issue\(number:", args[-1])]
            if failing & set(numbers):
                failed = _FakeCompletedProcess("")
                failed.returncode = 1
                failed.stderr = "connection refused"
                return failed
            repo = {}
            for number in numbers:
                nodes = tree.get(number, [])
                if nodes is None:
                    repo[f"i{number}"] = None
                else:
                    repo[f"i{number}"] = {
                        "body": "",
                        "subIssues": {
                            "nodes": nodes,
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
            return _FakeCompletedProcess(json.dumps({"data": {"repository": repo}}))
        raise AssertionError(f"unexpected gh invocation: {args}")

    return _run


def test_run_audit_incomplete_traversal_is_not_green(tmp_path, monkeypatch):
    """Blocking #8661 fix: a transport failure on one parent leaves its
    subtree UNREAD — it could hide a duplicate membership — so the audit must
    fail closed (``ok: false``) even though everything read classifies clean."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo(root, epics=[100])

    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh_failing_nodes(
            [],
            owner="acme",
            name="repo",
            open_issues=_issues(100, 10),
            tree={100: [_node(10, "acme", "repo", total=1)]},
            failing={10},
        ),
    )

    report = run_audit(root)

    # #10 is natively linked under #100: no orphan, no multi-home — the ONLY
    # reason this audit is not green is the incomplete traversal.
    assert report["orphans"] == []
    assert report["multi_homed"] == []
    assert {"code": "traversal_incomplete", "issue": 10} in report["warnings"]
    assert report["ok"] is False
    summary = issue_stream_audit.human_summary(report)
    assert "WARN: sub-issue #10 could not be fetched; its subtree was never read" in summary
    assert "ok: False" in summary


def test_run_audit_singleton_retry_budget_is_shared_per_run(tmp_path, monkeypatch):
    """Non-blocking #8661 fix: one audit run spends at most
    ``_MAX_SINGLE_RETRIES_PER_AUDIT`` singleton retries across ALL failed
    batches; parents beyond the budget are marked incomplete without a call."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo(root, epics=[100])
    failing = set(range(101, 131))  # 30 unreadable children: two batches (20 + 10)

    calls = []
    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh_failing_nodes(
            calls,
            owner="acme",
            name="repo",
            open_issues=_issues(100),
            tree={100: [_node(n, "acme", "repo", total=1) for n in sorted(failing)]},
            failing=failing,
        ),
    )

    report = run_audit(root)

    singleton_retries = [
        args
        for args, _cwd in calls
        if list(args[1:3]) == ["api", "graphql"]
        and len(re.findall(r"i(\d+):issue\(number:", args[-1])) == 1
        and int(re.search(r"i(\d+):issue\(number:", args[-1]).group(1)) in failing
    ]
    # All 30 children fail: batch of 20 → 20 singleton retries, batch of 10 →
    # only 5 more before the shared per-run budget is spent; the remaining 5
    # are marked incomplete with no network call.
    assert len(singleton_retries) == issue_stream_audit._MAX_SINGLE_RETRIES_PER_AUDIT
    incomplete = [w["issue"] for w in report["warnings"] if w["code"] == "traversal_incomplete"]
    assert sorted(incomplete) == sorted(failing)
    assert report["ok"] is False


def _make_repo_with_closed_epic(root) -> None:
    (root / "scripts" / "config").mkdir(parents=True)
    (root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "streams:\n  s:\n    title: s\n    epics: [100, 200]\n    closed_epics: [200]\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "WORKSTREAMS.md").write_text(
        "## Stream milestones (the focus layer)\n\n"
        "| Stream | State | Current milestone | Done when |\n"
        "| --- | --- | --- | --- |\n"
        "| s | ACTIVE | No issue references | — |\n",
        encoding="utf-8",
    )


def test_run_audit_warns_when_closed_epic_is_actually_open(tmp_path, monkeypatch):
    """closed_epics is hand-maintained (#8661 item 4): a listed epic that is
    OPEN on GitHub must warn, not silently drop out of the audit."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo_with_closed_epic(root)

    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh(
            [],
            owner="acme",
            name="repo",
            open_issues=_issues(100, 200),
            tree={100: []},
        ),
    )

    report = run_audit(root)

    assert {"code": "closed_epic_reopened", "stream": "s", "epic": 200} in report["warnings"]
    assert "WARN: registry closed_epics lists #200 (stream s) but it is OPEN" in (
        issue_stream_audit.human_summary(report)
    )
    # The hand-listed epic is still not an audit root.
    assert report["streams"] == {"s": [100]}


def test_run_audit_quiet_when_closed_epic_is_really_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo_with_closed_epic(root)

    monkeypatch.setattr(
        issue_stream_audit.subprocess,
        "run",
        _run_audit_fake_gh(
            [],
            owner="acme",
            name="repo",
            open_issues=_issues(100),
            tree={100: []},
        ),
    )

    report = run_audit(root)

    assert [w for w in report["warnings"] if w["code"] == "closed_epic_reopened"] == []
    assert report["ok"] is True


def test_tree_membership_pagination_truncation_counts_as_incomplete():
    """Finding 4 (#8661): when pagination hits _MAX_SUBISSUE_PAGES with hasNextPage
    still true, the truncation must be marked as traversal_incomplete."""

    # Parent 100 always returns hasNextPage=True with a cursor
    def fetch_batch(pending):
        return {
            num: {
                "body": "",
                "subIssues": {
                    "nodes": [{"number": num * 10}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor-xyz"},
                },
            }
            for num in pending
        }

    warnings = []
    membership = issue_stream_audit._tree_membership({100}, fetch_batch, warnings)
    assert any(w["code"] == "traversal_incomplete" and w["issue"] == 100 for w in warnings)
    assert 100 in membership


def test_subissue_batch_real_github_not_found_error_is_absent_not_incomplete(monkeypatch):
    """Finding 2 (#8661): real GitHub GraphQL returns exit code 1 with a NOT_FOUND
    error payload when an issue does not exist. _fetch_subissue_batch must recognize
    this as genuinely absent (None), not INCOMPLETE_NODE, while preserving intact nodes."""
    monkeypatch.setattr(issue_stream_audit, "_repo_owner_name", lambda _root: ("acme", "repo"))

    def fake_subprocess_run(args, capture_output, text, timeout, cwd):
        assert args[0] == "gh"
        if args[1:3] == ["api", "graphql"]:
            query = args[-1]
            if "i999:issue" in query and "i100:issue" in query:
                # Batch with one present and one deleted issue
                stdout = json.dumps(
                    {
                        "data": {
                            "repository": {
                                "i100": {
                                    "body": "",
                                    "subIssues": {
                                        "nodes": [{"number": 10}],
                                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    },
                                },
                                "i999": None,
                            }
                        },
                        "errors": [
                            {
                                "type": "NOT_FOUND",
                                "path": ["repository", "i999"],
                                "message": "Could not resolve to an Issue with the number of 999.",
                            }
                        ],
                    }
                )
                return _FakeCompletedProcess(stdout, returncode=1, stderr="gh: Could not resolve...")
            if "i999:issue" in query:
                # Singleton retry for deleted issue
                stdout = json.dumps(
                    {
                        "data": {"repository": {"i999": None}},
                        "errors": [
                            {
                                "type": "NOT_FOUND",
                                "path": ["repository", "i999"],
                                "message": "Could not resolve to an Issue with the number of 999.",
                            }
                        ],
                    }
                )
                return _FakeCompletedProcess(stdout, returncode=1, stderr="gh: Could not resolve...")
        raise AssertionError(f"unexpected invocation: {args}")

    monkeypatch.setattr(issue_stream_audit.subprocess, "run", fake_subprocess_run)
    pages = issue_stream_audit._fetch_subissue_batch({100: None, 999: None})
    assert pages[100]["subIssues"]["nodes"][0]["number"] == 10
    assert pages[999] is None


def test_validate_membership_report_and_read_membership_index_reject_incomplete_cache(tmp_path):
    """Finding 1 (issue #8661): an incomplete traversal report/cache must be rejected
    by validate_membership_report and read_membership_index."""
    import time

    now = time.time()
    incomplete_report = {
        "generated_at": now,
        "membership_complete": False,
        "incomplete_nodes": [20],
        "warnings": [{"code": "traversal_incomplete", "issue": 20}],
        "effective_membership": {
            "42": {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
        },
        "open_issue_numbers": [42, 100],
    }
    assert validate_membership_report(incomplete_report, 3600) is None

    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(incomplete_report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache_file) is None

    # Complete report must validate successfully
    complete_report = {
        "generated_at": now,
        "membership_complete": True,
        "incomplete_nodes": [],
        "warnings": [],
        "effective_membership": {
            "42": {"epics": [100], "streams": ["product"], "via": "native", "unique_stream": True}
        },
        "open_issue_numbers": [42, 100],
    }
    assert validate_membership_report(complete_report, 3600) == complete_report
    cache_file.write_text(json.dumps(complete_report), encoding="utf-8")
    assert read_membership_index(3600, cache_path=cache_file) is not None


def test_run_audit_incomplete_report_has_completeness_flag_and_fails_closed(tmp_path, monkeypatch):
    """Finding 1 (issue #8661): run_audit with incomplete nodes writes membership_complete=False
    and incomplete_nodes, and the resulting cache fails closed."""
    monkeypatch.setattr(issue_stream_audit, "_REPO_CACHE", {})
    root = tmp_path / "repo"
    _make_repo(root, epics=[100])

    def fake_fetch_tree(roots, repo_root, warnings):
        warnings.append({"code": "traversal_incomplete", "issue": 20})
        return {100: ({42}, set())}

    monkeypatch.setattr(issue_stream_audit, "fetch_tree_membership", fake_fetch_tree)
    monkeypatch.setattr(issue_stream_audit, "fetch_open_issues", lambda _r: _issues(100, 42))
    monkeypatch.setattr(
        issue_stream_audit, "fetch_issue_states", lambda nums, _r, **_k: ({n: "OPEN" for n in nums}, set())
    )

    report = run_audit(root)
    assert report["ok"] is False
    assert report["membership_complete"] is False
    assert report["incomplete_nodes"] == [20]

    cache_file = root / "batch_state" / "issue_stream_audit.json"
    assert cache_file.exists()
    assert read_membership_index(3600, cache_path=cache_file) is None
    assert validate_membership_report(report, 3600) is None
