"""Unit tests for scripts/ci/cache_hygiene.py (#9101)."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from scripts.ci import cache_hygiene
from scripts.ci.cache_hygiene import (
    CacheEntry,
    IncompleteListingError,
    delete_entries,
    list_caches,
    lock_hash,
    open_pr_base_shas,
    plan_deletions,
)

NOW = datetime(2026, 9, 29, 19, 0, tzinfo=UTC)
MAIN = "refs/heads/main"
TRAP_JS = "codeql-trap-1-2.27.1-javascript-"
TRAP_PY = "codeql-trap-1-2.27.1-python-"
UV = "setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-24.04-3.12.14-"
CURRENT = "c" * 64
OLD = "a" * 64
OLDER = "b" * 64


def _sha(n: int) -> str:
    return f"{n:040x}"


def _raw(cache_id: int, key: str, ref: str = MAIN, hours_ago: float = 1.0, read_hours_ago: float | None = None) -> dict:
    created = NOW - timedelta(hours=hours_ago)
    accessed = NOW - timedelta(hours=hours_ago if read_hours_ago is None else read_hours_ago)
    return {
        "id": cache_id,
        "key": key,
        "ref": ref,
        "version": "v",
        "size_in_bytes": 247_000_000,
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "last_accessed_at": accessed.isoformat().replace("+00:00", "Z"),
    }


def _entry(*args, **kwargs) -> CacheEntry:
    return CacheEntry.from_api(_raw(*args, **kwargs))


def _deleted_ids(entries: list[CacheEntry], pr_base_shas: set[str] | None = None) -> set[int]:
    plan = plan_deletions(entries, CURRENT, NOW, pr_base_shas=pr_base_shas or set())
    return {d.entry.id for d in plan.deletions}


def _cache_pages(raws: list[dict], total_count: int | None = None):
    """Fake gh api serving ``raws`` as ``created_at``-ordered pages of 100."""
    calls: list[str] = []

    def fake_gh_api(args: list[str]) -> str:
        calls.append(args[0])
        page = int(re.search(r"[?&]page=(\d+)", args[0]).group(1))
        batch = raws[(page - 1) * 100 : page * 100]
        total = len(raws) if total_count is None else total_count
        return json.dumps({"total_count": total, "actions_caches": batch})

    return fake_gh_api, calls


def _pr_page(total: int, numbers: list[int], shas: list[str | None], next_cursor: str | None) -> str:
    nodes = [{"number": n, "baseRefOid": sha} for n, sha in zip(numbers, shas, strict=True)]
    return json.dumps(
        {
            "data": {
                "repository": {
                    "pullRequests": {
                        "totalCount": total,
                        "pageInfo": {"hasNextPage": next_cursor is not None, "endCursor": next_cursor},
                        "nodes": nodes,
                    }
                }
            }
        }
    )


def test_keeps_newest_trap_per_family_by_created_at() -> None:
    entries = [
        _entry(1, TRAP_JS + _sha(1), hours_ago=5),
        _entry(2, TRAP_JS + _sha(2), hours_ago=1),
        # An older entry read recently is still dead weight: newest is by created_at.
        _entry(3, TRAP_JS + _sha(3), hours_ago=3, read_hours_ago=0.1),
        _entry(4, TRAP_PY + _sha(4), hours_ago=9),
        _entry(5, TRAP_PY + _sha(5), hours_ago=2),
    ]
    assert _deleted_ids(entries) == {1, 3, 4}


def test_single_trap_entry_is_kept() -> None:
    assert _deleted_ids([_entry(1, TRAP_JS + _sha(1), hours_ago=100)]) == set()


def test_trap_entries_on_other_refs_are_deleted() -> None:
    entries = [
        _entry(1, TRAP_JS + _sha(1), hours_ago=5),
        _entry(2, TRAP_JS + _sha(2), ref="refs/pull/9000/merge", hours_ago=0.1),
    ]
    assert _deleted_ids(entries) == {2}


def test_non_main_trap_like_keys_without_full_shape_are_left_alone() -> None:
    pr = "refs/pull/9000/merge"
    entries = [
        _entry(1, "codeql-trap-custom-" + _sha(1), ref=pr),
        _entry(2, TRAP_JS + "unknown", ref=pr),
        _entry(3, TRAP_JS + _sha(3)[:39], ref=pr),
        _entry(4, "codeql-trap-1-latest-javascript-" + _sha(4), ref=pr),
        _entry(5, "codeql-trap-1-2.27.1-" + _sha(5), ref=pr),
        _entry(6, "codeql-trap-1-2.27.1+20260901-python-" + _sha(6), ref=pr),
    ]
    assert _deleted_ids(entries) == {6}


def test_trap_entry_at_an_open_pr_base_is_kept() -> None:
    entries = [
        _entry(1, TRAP_JS + _sha(1), hours_ago=9),
        _entry(2, TRAP_JS + _sha(2), hours_ago=5),
        _entry(3, TRAP_JS + _sha(3), hours_ago=1),
        _entry(4, TRAP_PY + _sha(2), hours_ago=5),
        _entry(5, TRAP_PY + _sha(5), hours_ago=1),
    ]
    # An open PR based on commit 2 restores exactly TRAP_* + sha(2), in every family.
    assert _deleted_ids(entries, pr_base_shas={_sha(2)}) == {1}
    plan = plan_deletions(entries, CURRENT, NOW, pr_base_shas={_sha(2)})
    assert plan.kept == {"newest TRAP per family": 2, "TRAP at an open PR base": 2}


def test_unknown_prefixes_and_unmatched_keys_are_left_alone() -> None:
    entries = [
        _entry(1, "stanza-uk-model-v2-Linux-" + OLD, hours_ago=500),
        _entry(2, "node-cache-Linux-x64-npm-" + OLD, hours_ago=500),
        _entry(3, "setup-python-Linux-x64-24.04-Ubuntu-python-3.12.14-pip-" + OLD, hours_ago=500),
        # TRAP-like key without a commit sha on main: not a known family.
        _entry(4, "codeql-trap-1-2.27.1-javascript-notasha", hours_ago=500),
        _entry(5, TRAP_JS + _sha(5), hours_ago=1),
    ]
    assert _deleted_ids(entries) == set()


def test_uv_keeps_current_lock_and_newest_and_waits_for_grace() -> None:
    entries = [
        # Current lock, older than a newer stray entry: kept for the lock match.
        _entry(1, UV + CURRENT, hours_ago=40, read_hours_ago=48),
        # Newest entry for a different hash: kept as newest.
        _entry(2, UV + OLD, hours_ago=2),
        # Superseded and unread for 30 h: deleted.
        _entry(3, UV + OLDER, hours_ago=90, read_hours_ago=30),
    ]
    assert _deleted_ids(entries) == {3}


def test_uv_superseded_entry_read_recently_is_kept() -> None:
    entries = [
        _entry(1, UV + CURRENT, hours_ago=2),
        _entry(2, UV + OLD, hours_ago=30, read_hours_ago=3),
    ]
    assert _deleted_ids(entries) == set()


def test_uv_entries_on_other_refs_are_left_alone() -> None:
    entries = [
        _entry(1, UV + CURRENT, hours_ago=2),
        _entry(2, UV + OLD, ref="refs/pull/9000/merge", hours_ago=90),
    ]
    assert _deleted_ids(entries) == set()


def test_list_caches_follows_pagination_in_created_at_order() -> None:
    fake_gh_api, calls = _cache_pages([_raw(i, TRAP_JS + _sha(i)) for i in range(1, 251)])
    entries = list_caches("owner/repo", gh_api=fake_gh_api)
    assert [e.id for e in entries] == list(range(1, 251))
    assert calls == [
        f"repos/owner/repo/actions/caches?per_page=100&page={p}&sort=created_at&direction=asc" for p in (1, 2, 3)
    ]


def test_list_caches_rejects_a_short_listing() -> None:
    # 150 reported, the second page comes back empty: 50 entries were never seen.
    fake_gh_api, _ = _cache_pages([_raw(i, TRAP_JS + _sha(i)) for i in range(100)], total_count=150)
    with pytest.raises(IncompleteListingError, match="100 entries"):
        list_caches("owner/repo", gh_api=fake_gh_api)


def test_list_caches_rejects_total_count_changing_between_pages() -> None:
    pages = iter(
        [
            {"total_count": 150, "actions_caches": [_raw(i, TRAP_JS + _sha(i)) for i in range(100)]},
            {"total_count": 149, "actions_caches": [_raw(i, TRAP_JS + _sha(i)) for i in range(100, 149)]},
        ]
    )
    with pytest.raises(IncompleteListingError, match=r"\[149, 150\]"):
        list_caches("owner/repo", gh_api=lambda _args: json.dumps(next(pages)))


def test_list_caches_rejects_duplicated_entries() -> None:
    # An eviction shifts page 2 back by one: entry 99 repeats and one entry is missed.
    pages = iter(
        [
            {"total_count": 150, "actions_caches": [_raw(i, TRAP_JS + _sha(i)) for i in range(100)]},
            {"total_count": 150, "actions_caches": [_raw(i, TRAP_JS + _sha(i)) for i in range(99, 149)]},
        ]
    )
    with pytest.raises(IncompleteListingError, match="149 distinct ids"):
        list_caches("owner/repo", gh_api=lambda _args: json.dumps(next(pages)))


def test_open_pr_base_shas_follows_cursors() -> None:
    seen: list[list[str]] = []
    documents = []
    pages = iter(
        [
            _pr_page(3, [1, 2], [_sha(1), _sha(1)], "c1"),
            _pr_page(3, [3], [_sha(2)], None),
        ]
    )

    def fake_gh_api(args: list[str]) -> str:
        from pathlib import Path
        documents.append(json.loads(Path(args[args.index("--input") + 1]).read_text()))
        seen.append(args)
        return next(pages)

    assert open_pr_base_shas("owner/repo", gh_api=fake_gh_api) == {_sha(1), _sha(2)}
    assert "cursor=c1" not in seen[0]
    assert documents[0]["variables"]["cursor"] is None
    assert documents[1]["variables"]["cursor"] == "c1"
    assert seen[1][:3] == ["--method", "POST", "graphql"]
    assert documents[0]["variables"] == {"owner": "owner", "name": "repo", "cursor": None}


def test_open_pr_base_shas_rejects_a_short_listing() -> None:
    with pytest.raises(IncompleteListingError, match="1 pull requests"):
        open_pr_base_shas("owner/repo", gh_api=lambda _args: _pr_page(2, [1], [_sha(1)], None))


@pytest.mark.parametrize("base", [None, "", "g" * 40, _sha(1)[:39], "A" * 40, 1])
def test_open_pr_base_shas_rejects_a_pr_without_a_valid_base_sha(base: object) -> None:
    with pytest.raises(IncompleteListingError, match="#2 has no valid base SHA"):
        open_pr_base_shas("owner/repo", gh_api=lambda _args: _pr_page(2, [1, 2], [_sha(1), base], None))


def test_main_aborts_when_an_open_pr_has_no_base_sha(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("x\n")
    entries = [_entry(1, TRAP_JS + _sha(1), hours_ago=5), _entry(2, TRAP_JS + _sha(2))]
    monkeypatch.setattr(cache_hygiene, "list_caches", lambda _repo: entries)
    monkeypatch.setattr(
        cache_hygiene,
        "open_pr_base_shas",
        lambda repo: open_pr_base_shas(repo, gh_api=lambda _args: _pr_page(1, [7], [None], None)),
    )
    monkeypatch.setattr(cache_hygiene, "delete_entries", lambda *_a: pytest.fail("deleted without every PR base"))

    assert cache_hygiene.main(["--repo", "owner/repo", "--lock-file", str(lock), "--apply"]) == 2
    captured = capsys.readouterr()
    assert "aborting, nothing deleted" in captured.err
    assert "#7 has no valid base SHA: None" in captured.err
    assert "DELETE" not in captured.out


def test_lock_hash_matches_hashfiles(tmp_path) -> None:
    lock = tmp_path / "requirements-lock.txt"
    lock.write_bytes(b"pytest==9.1.1\n")
    # hashFiles(): SHA-256 of the file's SHA-256 digest, not of the content itself.
    assert lock_hash(lock) == "40a2641f12d28fada89c7c544883666ff71a12f955f2776295959fdf98124d4e"


def test_delete_entries_tolerates_already_gone_and_reports_failures() -> None:
    deletions = plan_deletions(
        [
            _entry(1, TRAP_JS + _sha(1), hours_ago=5),
            _entry(2, TRAP_JS + _sha(2), hours_ago=4),
            _entry(3, TRAP_JS + _sha(3)),
        ],
        CURRENT,
        NOW,
    ).deletions
    seen: list[list[str]] = []

    def fake_gh_api(args: list[str]) -> str:
        seen.append(args)
        if args[-1].endswith("/1"):
            raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 404: Not Found")
        raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 500")

    failed = delete_entries("owner/repo", deletions, gh_api=fake_gh_api)
    assert failed == [TRAP_JS + _sha(2)]
    assert seen == [
        ["--method", "DELETE", "repos/owner/repo/actions/caches/1"],
        ["--method", "DELETE", "repos/owner/repo/actions/caches/2"],
    ]


def test_main_dry_run_never_deletes(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("x\n")
    entries = [
        CacheEntry.from_api(_raw(1, TRAP_JS + _sha(1), hours_ago=5)),
        CacheEntry.from_api(_raw(2, TRAP_JS + _sha(2), hours_ago=3)),
        CacheEntry.from_api(_raw(3, TRAP_JS + _sha(3))),
        CacheEntry.from_api(_raw(4, "node-cache-Linux-x64-npm-" + OLD)),
    ]
    monkeypatch.setattr(cache_hygiene, "list_caches", lambda _repo: entries)
    monkeypatch.setattr(cache_hygiene, "open_pr_base_shas", lambda _repo: {_sha(2)})
    monkeypatch.setattr(cache_hygiene, "delete_entries", lambda *_a: pytest.fail("dry run deleted"))

    assert cache_hygiene.main(["--repo", "owner/repo", "--lock-file", str(lock)]) == 0
    out = capsys.readouterr().out
    assert f"would delete {MAIN} {TRAP_JS + _sha(1)} (0.25 GB)" in out
    assert "keep: 1 newest TRAP per family; 1 TRAP at an open PR base; 0 uv for the current lock" in out
    assert "; 1 not managed" in out
    assert "delete 1 entries, 0.25 GB; remaining 3 entries, 0.74 GB" in out


@pytest.mark.parametrize(
    "failure",
    [
        IncompleteListingError("cache list is incomplete"),
        subprocess.CalledProcessError(1, "gh", stderr="HTTP 502"),
        json.JSONDecodeError("bad", "", 0),
    ],
)
def test_main_aborts_without_deleting_when_open_pr_lookup_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys, failure: Exception
) -> None:
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("x\n")
    entries = [_entry(1, TRAP_JS + _sha(1), hours_ago=5), _entry(2, TRAP_JS + _sha(2))]

    def fail(_repo: str) -> set[str]:
        raise failure

    monkeypatch.setattr(cache_hygiene, "list_caches", lambda _repo: entries)
    monkeypatch.setattr(cache_hygiene, "open_pr_base_shas", fail)
    monkeypatch.setattr(cache_hygiene, "delete_entries", lambda *_a: pytest.fail("deleted after a failed lookup"))

    assert cache_hygiene.main(["--repo", "owner/repo", "--lock-file", str(lock), "--apply"]) == 2
    captured = capsys.readouterr()
    assert "aborting, nothing deleted" in captured.err
    assert "would delete" not in captured.out and "DELETE" not in captured.out


def test_main_aborts_on_incomplete_cache_listing(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("x\n")
    fake_gh_api, _ = _cache_pages([_raw(i, TRAP_JS + _sha(i)) for i in range(1, 101)], total_count=150)
    monkeypatch.setattr(cache_hygiene, "list_caches", lambda repo: list_caches(repo, gh_api=fake_gh_api))
    monkeypatch.setattr(cache_hygiene, "delete_entries", lambda *_a: pytest.fail("deleted after a short listing"))

    assert cache_hygiene.main(["--repo", "owner/repo", "--lock-file", str(lock), "--apply"]) == 2
    assert "cache list is incomplete: 100 entries" in capsys.readouterr().err
