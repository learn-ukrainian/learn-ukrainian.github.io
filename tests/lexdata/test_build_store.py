"""Single writer, generation swap, L1 reuse and the writer target (design r3 §3, §6, §9)."""

from __future__ import annotations

import fcntl
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.lexdata import build_store, generation, verify
from scripts.lexdata.canonical import sha256_file
from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology
from tests.lexdata._support import (
    FIXTURE_SOURCE,
    FixtureAdapter,
    FixtureStage,
    fixture_binding,
    make_sqlite,
    mutate_sqlite,
)

pytestmark = pytest.mark.usefixtures("local_fs")


def _l1_rows(path: Path) -> list[tuple]:
    with closing(open_readonly(path)) as conn:
        return conn.execute("SELECT item_key, raw_span, surface, key_stressed, key_unstressed, key_fold, "
                            "case_signal, refusal_code, row_sha256 FROM l1_lex_item ORDER BY item_key").fetchall()


# --- writer target -------------------------------------------------------------------------

@pytest.fixture
def checkouts(tmp_path):
    primary, worker = tmp_path / "primary", tmp_path / "worker"
    for root in (primary, worker):
        (root / "scripts").mkdir(parents=True)
        (root / "data").mkdir()
    gitdir = primary / ".git" / "worktrees" / "worker"
    gitdir.mkdir(parents=True)
    (worker / ".git").write_text(f"gitdir: {gitdir}\n")
    return primary, worker


def test_writer_target_is_the_primary_checkout_data_dir(checkouts) -> None:
    primary, worker = checkouts
    assert build_store.writer_target(primary).data_dir == primary.resolve() / "data"
    with pytest.raises(build_store.BuildRefused, match="linked_worktree"):
        build_store.writer_target(worker)
    assert not (worker / "data" / "lexdata.db").exists() and not (primary / "data" / "lexdata.db").exists()


@pytest.mark.parametrize("link", ["data", "data/lexdata", "data/lexdata.db"])
def test_writer_target_refuses_symlinked_parents(checkouts, tmp_path, link) -> None:
    primary, _ = checkouts
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    path = primary / link
    if path.exists():
        path.rmdir()
    path.symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(build_store.BuildRefused, match="symlinked_parent"):
        build_store.writer_target(primary)


@pytest.mark.parametrize("fs,reason", [("nfs", "locality_network"), ("cifs", "locality_network"),
                                       (None, "locality_unknown"), ("fuse.unknown", "locality_unknown")])
def test_writer_target_refuses_network_and_unknown_filesystems(checkouts, monkeypatch, fs, reason) -> None:
    monkeypatch.setattr(topology, "_fs_type_for_path", lambda path: fs)
    with pytest.raises(build_store.BuildRefused, match=reason):
        build_store.writer_target(checkouts[0])


def test_writer_target_requires_an_existing_data_dir(tmp_path) -> None:
    with pytest.raises(build_store.BuildRefused, match="data_dir_missing"):
        build_store.writer_target(test_data_dir=tmp_path / "absent")


# --- publication ---------------------------------------------------------------------------

def test_published_generation_is_self_contained_and_untouched_after_swap(harness, monkeypatch) -> None:
    swapped = {}
    real_replace = os.replace

    def recording_replace(src, dst):
        swapped["sha"] = sha256_file(Path(src))
        swapped["src"] = Path(src)
        real_replace(src, dst)

    monkeypatch.setattr(build_store.os, "replace", recording_replace)
    result = harness.build(stage=FixtureStage())
    published = harness.target.published
    assert sha256_file(published) == swapped["sha"]  # nothing written after the swap
    assert not swapped["src"].exists()
    assert not any(Path(f"{published}{s}").exists() for s in ("-wal", "-shm", "-journal"))
    header = published.read_bytes()[:20]
    assert header[18:20] == b"\x01\x01"  # rollback journal, not WAL
    assert result.size_bytes == published.stat().st_size
    with closing(open_readonly(published)) as conn:
        meta = generation.read_meta(conn)
        assert meta["status"] == "published" and meta["verify_receipt_sha256"]
        assert meta["verify_receipt_sha256"] == verify.verify_generation(conn).receipt_sha256()
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []
    reports = sorted(p.name for p in harness.target.reports_dir.iterdir())
    assert reports == [f"build-{result.generation}.json", f"verify-{result.generation}.json"]


def test_verify_receipt_sha_is_bound_into_meta(harness) -> None:
    result = harness.build(stage=FixtureStage())
    with closing(open_readonly(result.published)) as conn:
        meta = generation.read_meta(conn)
    report = verify.VerifyReport(result.verify_receipt["generation"])
    assert result.verify_receipt["ok"] is True
    assert meta["verify_receipt_sha256"] == build_store.sha256_canonical(result.verify_receipt)
    assert report.generation == meta["generation"]


def test_second_writer_is_refused_while_the_lock_is_held(harness) -> None:
    target = harness.target
    target.work_dir.mkdir()
    fd = os.open(target.lock_path, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with pytest.raises(build_store.BuildRefused, match="build_locked"):
            harness.build()
    finally:
        os.close(fd)
    assert not target.published.exists()
    harness.build()  # the lock is released with its holder
    assert target.published.exists()


def test_failed_verify_publishes_nothing_and_deletes_the_temp(harness) -> None:
    first = harness.build(stage=FixtureStage())
    before = harness.published_sha()

    class LeafWithoutLink(FixtureStage):
        def link(self, conn):
            super().link(conn)
            conn.execute("DELETE FROM l2_candidate WHERE link_id = (SELECT max(link_id) FROM l2_link)")
            conn.execute("DELETE FROM l2_link WHERE link_id = (SELECT max(link_id) FROM l2_link)")

    with pytest.raises(build_store.BuildRefused, match="verify_failed"):
        harness.build(stage=LeafWithoutLink())
    assert harness.published_sha() == before
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []
    opened = generation.open_generation(harness.target.published, binding=fixture_binding(),
                                        repository_root=harness.repository_root)
    assert isinstance(opened, generation.OpenGeneration) and opened.generation == first.generation
    opened.close()


def test_stale_temp_from_a_crashed_build_is_removed(harness) -> None:
    harness.target.work_dir.mkdir()
    stale = harness.target.work_dir / "lexdata.g000009-crashed.db.tmp"
    stale.write_bytes(b"partial")
    Path(f"{stale}-journal").write_bytes(b"partial")
    harness.build()
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []


def test_backups_use_the_online_api_and_rotate(harness) -> None:
    results = [harness.build() for _ in range(4)]
    backups = sorted(harness.target.backups_dir.glob("lexdata-*.db"))
    assert len(backups) == build_store.BACKUPS_KEPT
    assert results[0].backup is None and results[1].backup is not None
    assert {b.name.split("-")[1] for b in backups} == {r.generation.split("-")[0] for r in results[1:3]}
    with closing(open_readonly(backups[-1])) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert generation.read_meta(conn)["status"] == "published"


# --- L0 is read-only; snapshots ------------------------------------------------------------

def test_l0_is_never_written(harness) -> None:
    before = sha256_file(harness.sources_path)

    class WritesL0(FixtureStage):
        stores = ("sources",)

        def link(self, conn):
            conn.execute("INSERT INTO src_sources.fixture_words VALUES (99, 'x')")

    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        harness.build(stage=WritesL0())
    harness.build(stage=FixtureStage(stores=("sources",)))
    assert sha256_file(harness.sources_path) == before


def test_changed_selection_digest_aborts_the_generation(harness) -> None:
    with pytest.raises(build_store.BuildRefused, match=f"input_snapshot_changed:{FIXTURE_SOURCE}"):
        harness.build(adapter=FixtureAdapter(drift_after_first_snapshot=True))
    assert not harness.target.published.exists()


class LateChange(FixtureStage):
    """The reviewer's shape: an external L0 writer changes a selected row during the L2 stage."""

    def __init__(self, sources_path: Path) -> None:
        super().__init__()
        self.sources_path = sources_path

    def link(self, conn) -> None:
        mutate_sqlite(self.sources_path, "UPDATE fixture_words SET word = ? WHERE id = 1", ("мама",))
        super().link(conn)


def test_selected_row_changed_during_l2_refuses_publication(harness) -> None:
    first = harness.build(stage=FixtureStage())
    before = harness.published_sha()
    with pytest.raises(build_store.BuildRefused, match=f"input_snapshot_changed:{FIXTURE_SOURCE}"):
        harness.build(stage=LateChange(harness.sources_path))
    assert harness.published_sha() == before
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []
    opened = generation.open_generation(harness.target.published, binding=fixture_binding())
    assert isinstance(opened, generation.OpenGeneration) and opened.generation == first.generation
    opened.close()


def test_selected_row_changed_after_verify_refuses_the_swap(harness, monkeypatch) -> None:
    """Drift at the last moment (during the pre-swap backup) is caught by the publication barrier."""
    harness.build()
    before = harness.published_sha()
    real_backup = build_store._backup_published

    def backup_then_change(target, generation_id):
        made = real_backup(target, generation_id)
        mutate_sqlite(harness.sources_path, "DELETE FROM fixture_words WHERE id = 3")
        return made

    monkeypatch.setattr(build_store, "_backup_published", backup_then_change)
    with pytest.raises(build_store.BuildRefused, match=f"input_snapshot_changed:{FIXTURE_SOURCE}"):
        harness.build()
    assert harness.published_sha() == before
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []


def test_unrelated_l0_write_during_the_build_still_publishes(harness, tmp_path) -> None:
    mutate_sqlite(harness.sources_path, "CREATE TABLE unrelated (x)")

    class UnrelatedWrite(FixtureStage):
        def link(self, conn) -> None:
            mutate_sqlite(harness.sources_path, "INSERT INTO unrelated VALUES (1)")
            super().link(conn)

    assert harness.build(stage=UnrelatedWrite()).verify_receipt["ok"] is True


def test_identity_store_changed_during_the_build_refuses_publication(harness) -> None:
    class DriftingIdentity(FixtureStage):
        calls = 0

        def store_fingerprints(self, l0):
            DriftingIdentity.calls += 1
            return {"vesum": ("v" if DriftingIdentity.calls == 1 else "w") * 64}

    with pytest.raises(build_store.BuildRefused, match="identity_store_changed"):
        harness.build(stage=DriftingIdentity())
    assert not harness.target.published.exists()


def test_worktree_local_l0_store_is_refused(harness, tmp_path) -> None:
    (harness.repository_root / ".git").write_text(f"gitdir: {tmp_path}/primary/.git/worktrees/x\n")
    (tmp_path / "primary" / ".git" / "worktrees" / "x").mkdir(parents=True)
    (harness.repository_root / "data" / "sources.db").write_bytes(b"")
    with pytest.raises(build_store.BuildRefused, match="store_sources:worktree_local_store"):
        harness.build()


# --- L1 reuse predicate, tombstones, determinism -------------------------------------------

def test_unchanged_rebuild_reuses_every_unit_with_identical_rows(harness) -> None:
    first = harness.build()
    rows = _l1_rows(first.published)
    second = harness.build()
    diff = second.diff["sources"][FIXTURE_SOURCE]
    assert (diff["reused_units"], diff["reparsed_units"], diff["tombstoned_units"]) == (5, 0, 0)
    assert _l1_rows(second.published) == rows


def test_changed_and_missing_units(harness) -> None:
    harness.build()
    mutate_sqlite(harness.sources_path, "UPDATE fixture_words SET word = ? WHERE id = 3", ("шу́ба",))
    mutate_sqlite(harness.sources_path, "DELETE FROM fixture_words WHERE id = 1")
    result = harness.build()
    diff = result.diff["sources"][FIXTURE_SOURCE]
    assert diff["reused_units"] == 3
    assert diff["reparse_reasons"] == {"input_changed": 1}
    assert diff["tombstoned_units"] == 1
    keys = {row[1]: row[3] for row in _l1_rows(result.published)}
    assert keys["шу́ба"] == "шу́ба" and "м’ята" not in keys


def test_removed_source_is_tombstoned(harness) -> None:
    harness.build()
    from scripts.lexdata import transforms
    result = build_store.build(harness.target, binding=transforms.TransformBinding(), adapters={},
                               repository_root=harness.repository_root, admission=build_store.Admission(0, 0))
    assert result.diff["dropped_sources"] == [FIXTURE_SOURCE]
    assert result.diff["sources"][FIXTURE_SOURCE]["tombstoned_units"] == 5
    assert _l1_rows(result.published) == []


def test_two_fresh_builds_are_identical(harness, tmp_path) -> None:
    first = harness.build(stage=FixtureStage(candidates={"шуба": [("lex:a", "eligible")]}))
    other = tmp_path / "other"
    (other / "scripts").mkdir(parents=True)
    (other / "data").mkdir()
    twin = type(harness)(other, harness.sources_path)
    second = twin.build(stage=FixtureStage(candidates={"шуба": [("lex:a", "eligible")]}))
    assert _l1_rows(first.published) == _l1_rows(second.published)
    query = ("SELECT i.item_key, l.status, l.hold_reason, l.lexeme_id, l.candidate_set_sha256 FROM l2_link l "
             "JOIN l1_lex_item i USING (item_id) ORDER BY i.item_key")
    with closing(open_readonly(first.published)) as a, closing(open_readonly(second.published)) as b:
        assert a.execute(query).fetchall() == b.execute(query).fetchall()


def test_leaf_structure_and_links(harness) -> None:
    result = harness.build(stage=FixtureStage(candidates={"шуба": [("lex:a", "eligible")]}))
    with closing(open_readonly(result.published)) as conn:
        statuses = dict(conn.execute(
            "SELECT i.raw_span, l.status FROM l2_link l JOIN l1_lex_item i USING (item_id)").fetchall())
        assert statuses["у, в"] == "split" and statuses["у"] == "unmatched" and statuses["шуба"] == "exact"
        assert statuses["Cпасибі!"] == "refused"
        assert conn.execute("SELECT count(*) FROM l1_lex_item WHERE parent_item_id IS NOT NULL").fetchone() == (2,)
        assert conn.execute("SELECT lexeme_id FROM l3_card_input").fetchall() == [("lex:a",)]
        assert conn.execute("SELECT count(*) FROM l1_sense").fetchone() == (4,)


def test_default_stage_links_every_leaf_as_unavailable_or_refused(harness) -> None:
    result = harness.build()
    assert result.verify_receipt["counts"]["link_status"] == {"refused": 1, "unavailable": 6}
    assert result.verify_receipt["counts"]["l3_card_input"] == 0


# --- budgets -------------------------------------------------------------------------------

def test_disk_admission_refuses_before_writing(harness) -> None:
    with pytest.raises(build_store.BuildRefused, match="disk_admission_refused"):
        harness.build(admission=build_store.Admission(peak_budget_bytes=10 ** 18, reserve_bytes=0))
    assert not harness.target.published.exists()


def test_rss_cap_aborts_at_a_batch_commit(harness) -> None:
    with pytest.raises(build_store.BuildRefused, match="rss_cap_exceeded"):
        harness.build(admission=build_store.Admission(0, 0, rss_cap_bytes=1, batch_rows=1))
    assert not harness.target.published.exists()
    assert list(harness.target.work_dir.glob("lexdata.*.db.tmp*")) == []


def test_unmeasurable_rss_fails_closed(monkeypatch) -> None:
    import builtins
    real_import = builtins.__import__

    def no_psutil(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_psutil)
    monkeypatch.setattr(build_store.Path, "read_text", lambda self, *a, **k: (_ for _ in ()).throw(OSError()))
    with pytest.raises(build_store.BuildRefused, match="rss_unmeasurable"):
        build_store.current_rss_bytes()


# --- reader boundary -----------------------------------------------------------------------

def test_reader_reports_unpublished_and_missing(harness, tmp_path) -> None:
    from scripts.lexdata.schema import FULL_DDL
    candidate = make_sqlite(tmp_path / "candidate.db", FULL_DDL, [(
        "INSERT INTO meta VALUES (1, 'g1', 1, '1', '1', 't', '{}', 'x', '{}', '{}', '{}', 'x', '{}', 'r', '{}', "
        "'candidate', NULL)", ())])
    assert generation.open_generation(candidate) == generation.Unavailable("lexdata_unpublished", "g1")
    assert generation.open_generation(tmp_path / "absent.db") == generation.Unavailable("lexdata_unavailable")
    empty = make_sqlite(tmp_path / "empty.db", "CREATE TABLE x (y);")
    assert generation.open_generation(empty) == generation.Unavailable("lexdata_unpublished")


def test_reader_checks_identity_store_fingerprints(harness) -> None:
    result = harness.build(stage=FixtureStage(fingerprints={"vesum": "v" * 64}))
    path, binding = result.published, fixture_binding()
    assert generation.open_generation(path, binding=binding).reason == "identity_store_unavailable"
    assert generation.open_generation(path, binding=binding,
                                      current_store_fingerprints={"vesum": "w" * 64}).reason == "identity_store_stale"
    opened = generation.open_generation(path, binding=binding, current_store_fingerprints={"vesum": "v" * 64})
    assert isinstance(opened, generation.OpenGeneration)
    opened.close()


# --- SQLite temp files stay in data/lexdata/tmp (§9) ---------------------------------------

def _spill_temp_table(conn) -> set[Path]:
    """The reviewer's temp-probe shape: a FILE temp table forced to spill to disk."""
    before = build_store._sqlite_temp_files()
    conn.execute("PRAGMA temp.cache_size=1")
    conn.execute("CREATE TEMP TABLE probe (value BLOB)")
    conn.execute("INSERT INTO probe VALUES (zeroblob(4000000))")
    opened = build_store._sqlite_temp_files() - before
    conn.execute("DROP TABLE temp.probe")
    conn.execute("PRAGMA temp.cache_size=-262144")
    return opened


def test_build_connection_temp_files_stay_in_the_budgeted_dir(harness, monkeypatch) -> None:
    monkeypatch.delenv("SQLITE_TMPDIR", raising=False)
    target = harness.target
    target.tmp_dir.mkdir(parents=True)
    previous = build_store._get_sqlite_temp_dir()
    with build_store.pinned_sqlite_temp_dir(target.tmp_dir):
        conn = build_store._open_build_connection(target.work_dir / "probe.db", target.tmp_dir)
        try:
            assert conn.execute("PRAGMA temp_store").fetchone() == (1,)
            opened = _spill_temp_table(conn)
        finally:
            conn.close()
    assert opened and {path.parent for path in opened} == {target.tmp_dir.resolve()}
    assert build_store._get_sqlite_temp_dir() == previous
    # Outside the pin, the build connection itself refuses to open.
    with pytest.raises(build_store.BuildRefused, match="sqlite_tmpdir_outside_budget"):
        build_store._open_build_connection(target.work_dir / "probe.db", target.tmp_dir)


def test_temp_files_during_a_whole_build_stay_in_the_budgeted_dir(harness) -> None:
    seen: list[set[Path]] = []

    class SpillingStage(FixtureStage):
        def link(self, conn) -> None:
            seen.append(_spill_temp_table(conn))
            super().link(conn)

    harness.build(stage=SpillingStage())
    assert seen[0] and {path.parent for path in seen[0]} == {harness.target.tmp_dir.resolve()}


def test_build_refuses_when_sqlite_temp_dir_cannot_be_pinned(harness, monkeypatch) -> None:
    monkeypatch.setattr(build_store, "_set_sqlite_temp_dir", lambda directory: None)
    with pytest.raises(build_store.BuildRefused, match="sqlite_tmpdir_outside_budget"):
        harness.build()
    assert not harness.target.published.exists()


def test_build_refuses_when_temp_files_cannot_be_observed(harness, monkeypatch) -> None:
    monkeypatch.setattr(build_store, "_sqlite_temp_files", lambda: set())
    with pytest.raises(build_store.BuildRefused, match="sqlite_tmpdir_unverifiable"):
        harness.build()
    assert not harness.target.published.exists()


def test_temp_dir_lost_mid_build_refuses_publication(harness) -> None:
    """SQLite silently falls back when the pinned directory disappears; the barrier refuses."""
    class RemovesTmpDir(FixtureStage):
        def link(self, conn) -> None:
            harness.target.tmp_dir.rmdir()
            super().link(conn)

    with pytest.raises(build_store.BuildRefused, match="sqlite_tmpdir_outside_budget"):
        harness.build(stage=RemovesTmpDir())
    assert not harness.target.published.exists()
