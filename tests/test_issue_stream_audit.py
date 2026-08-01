"""Hermetic tests for the issue-stream auditor (#4708) — no network, no gh."""

from __future__ import annotations

import json
import textwrap
import threading

import pytest

from scripts.orchestration import issue_stream_audit
from scripts.orchestration.issue_stream_audit import (
    _MAX_SUBISSUE_PAGES,
    _paginate_subissues,
    classify,
    load_registry,
    make_issue_resolver,
    make_membership_resolver,
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


# --------------------------------------------------------------------------- #
# Review finding F001 (PR #6030) — ``run_audit`` must carry an explicit repo
# root all the way through registry lookup, ``gh`` execution cwd, and the
# cache it writes, instead of the module's own ``ROOT``. Fake ``gh`` via
# ``subprocess.run`` (not a higher-level seam) so the cwd threading itself is
# proven, not assumed.
# --------------------------------------------------------------------------- #
class _FakeCompletedProcess:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0


def _make_repo(root, *, epics: list[int]) -> None:
    (root / "scripts" / "config").mkdir(parents=True)
    (root / "scripts" / "config" / "issue_streams.yaml").write_text(
        "streams:\n  s:\n    title: s\n    epics: " + json.dumps(epics) + "\n",
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
            return _FakeCompletedProcess(
                json.dumps({"owner": {"login": owner}, "name": name})
            )
        if args[1] == "api" and args[2] == "graphql":
            return _FakeCompletedProcess(
                json.dumps(
                    {
                        "data": {
                            "repository": {
                                "issue": {
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


def test_run_audit_scopes_registry_gh_execution_and_cache_to_explicit_root(
    tmp_path, monkeypatch
):
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
    public = issue_stream_audit.public_refresh_view(
        issue_stream_audit.read_refresh_state(now=100)
    )
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


def test_schedule_refresh_is_single_flight_and_preserves_previous_outcome(
    tmp_path, monkeypatch
):
    state_path = _refresh_paths(tmp_path, monkeypatch)
    spawned = []
    monkeypatch.setattr(issue_stream_audit.time, "time", lambda: 100.0)
    monkeypatch.setattr(
        issue_stream_audit, "_spawn_worker", lambda run_id: spawned.append(run_id) or True
    )

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
    monkeypatch.setattr(
        issue_stream_audit, "run_audit", lambda: (_ for _ in ()).throw(RuntimeError("secret"))
    )
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
