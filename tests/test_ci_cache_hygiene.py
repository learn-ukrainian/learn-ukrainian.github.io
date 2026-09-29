"""Unit tests for scripts/ci/cache_hygiene.py (#9101)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from scripts.ci import cache_hygiene
from scripts.ci.cache_hygiene import CacheEntry, delete_entries, list_caches, lock_hash, plan_deletions

NOW = datetime(2026, 9, 29, 19, 0, tzinfo=UTC)
MAIN = "refs/heads/main"
TRAP_JS = "codeql-trap-1-2.27.1-javascript-"
TRAP_PY = "codeql-trap-1-2.27.1-python-"
UV = "setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-24.04-3.12.8-"
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


def _deleted_ids(entries: list[CacheEntry]) -> set[int]:
    return {d.entry.id for d in plan_deletions(entries, CURRENT, NOW)}


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


def test_unknown_prefixes_and_unmatched_keys_are_left_alone() -> None:
    entries = [
        _entry(1, "stanza-uk-model-v2-Linux-" + OLD, hours_ago=500),
        _entry(2, "node-cache-Linux-x64-npm-" + OLD, hours_ago=500),
        _entry(3, "setup-python-Linux-x64-24.04-Ubuntu-python-3.12.8-pip-" + OLD, hours_ago=500),
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


def test_list_caches_follows_pagination() -> None:
    raws = [_raw(i, TRAP_JS + _sha(i)) for i in range(1, 251)]
    calls: list[str] = []

    def fake_gh_api(args: list[str]) -> str:
        calls.append(args[0])
        page = int(args[0].rsplit("page=", 1)[1])
        batch = raws[(page - 1) * 100 : page * 100]
        return json.dumps({"total_count": len(raws), "actions_caches": batch})

    entries = list_caches("owner/repo", gh_api=fake_gh_api)
    assert [e.id for e in entries] == list(range(1, 251))
    assert calls == [f"repos/owner/repo/actions/caches?per_page=100&page={p}" for p in (1, 2, 3)]


def test_list_caches_stops_on_empty_page() -> None:
    pages = iter(
        [
            {"total_count": 150, "actions_caches": [_raw(i, TRAP_JS + _sha(i)) for i in range(100)]},
            {"total_count": 150, "actions_caches": []},
        ]
    )
    entries = list_caches("owner/repo", gh_api=lambda _args: json.dumps(next(pages)))
    assert len(entries) == 100


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
    )
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
        CacheEntry.from_api(_raw(2, TRAP_JS + _sha(2))),
    ]
    monkeypatch.setattr(cache_hygiene, "list_caches", lambda _repo: entries)
    monkeypatch.setattr(cache_hygiene, "delete_entries", lambda *_a: pytest.fail("dry run deleted"))

    assert cache_hygiene.main(["--repo", "owner/repo", "--lock-file", str(lock)]) == 0
    out = capsys.readouterr().out
    assert f"would delete {MAIN} {TRAP_JS + _sha(1)} (0.25 GB)" in out
    assert "delete 1 entries, 0.25 GB; remaining 1 entries, 0.25 GB" in out
