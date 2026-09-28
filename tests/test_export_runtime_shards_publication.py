"""Runtime shard exporter publication tests, split for loadfile scheduling."""

from __future__ import annotations

import errno
import gc
import hashlib
import json
import os
import random
import sqlite3
import threading
import tracemalloc
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import ExportError, gzip_bytes, open_readonly_db, verify_tree
from tests.test_export_runtime_shards import (
    _CHANGED_LIMITS,
    _FSYNC_STEPS,
    _KILL_POINTS,
    _STORED_PATTERN,
    _TREE_A,
    _TREE_B,
    _build_indexes,
    _export,
    _framed,
    _fsync_target,
    _make_source_db,
    _pointed_manifest,
    _pointer,
    _publish_synthetic,
    _ref_load_search_rows,
    _run_killed,
    _snapshot,
    _synthetic_stage,
    _traced_in_fresh_interpreter,
    _version_dirs,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)

@pytest.mark.parametrize("changed", _CHANGED_LIMITS, ids=lambda item: next(iter(item)))
def test_changed_limits_keep_every_old_url_and_publish_alternate_tree(
    edge_db: Path, tmp_path: Path, changed: dict
) -> None:
    out = tmp_path / "out"
    base = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    first = _export(edge_db, out, **base)
    old_manifest = _pointed_manifest(out)
    before = _snapshot(out)

    second = _export(edge_db, out, **{**base, **changed})

    assert second["dataVersion"] == first["dataVersion"]  # same data, different transport bytes
    after = _snapshot(out)
    assert {name: blob for name, blob in after.items() if name in before and name != "atlas/current.json"} == {
        name: blob for name, blob in before.items() if name != "atlas/current.json"
    }, "no previously published URL may change or disappear"
    new_root = _pointed_manifest(out).parent
    assert new_root.name == f"{first['dataVersion']}-transport-{exporter._tree_digest(new_root)}"
    assert second["manifestUrl"] == _pointer(out)["manifestUrl"] == f"versions/{new_root.name}/manifest.json"
    assert verify_tree(out, "atlas")["dataVersion"] == first["dataVersion"]
    # An old-manifest reader stays valid after the pointer switched.
    assert old_manifest.is_file()
    assert verify_tree(out, "atlas", manifest_path=old_manifest)["dataVersion"] == first["dataVersion"]

    # Repeating the changed export reuses the alternate tree; the original limits point back home.
    settled = _snapshot(out)
    _export(edge_db, out, **{**base, **changed})
    assert _snapshot(out) == settled
    _export(edge_db, out, **base)
    assert _pointer(out)["manifestUrl"] == first["manifestUrl"]
    assert len(_version_dirs(out)) == 2


@pytest.mark.parametrize(
    ("point", "changed"),
    # An identical re-export installs nothing (it reuses the tree), so only its pointer switch can be killed.
    [(point, True) for point in _KILL_POINTS] + [("before-pointer", False), ("after-pointer", False)],
)
def test_sigkill_during_publication_always_leaves_pointer_to_complete_tree(
    edge_db: Path, tmp_path: Path, point: str, changed: bool
) -> None:
    out = tmp_path / "out"
    base = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    first = _export(edge_db, out, **base)
    old_pointer = (out / "atlas" / "current.json").read_bytes()
    old_manifest = _pointed_manifest(out)
    old_tree = _snapshot(old_manifest.parent)

    _run_killed(edge_db, out, point, **({**base, "compression_level": 6} if changed else base))

    assert _snapshot(old_manifest.parent) == old_tree, "the published tree is never touched"
    result = verify_tree(out, "atlas")  # pointer resolves to a complete, verifying tree
    assert result["dataVersion"] == first["dataVersion"]
    if point != "after-pointer" or not changed:
        assert (out / "atlas" / "current.json").read_bytes() == old_pointer
    else:
        assert _pointed_manifest(out).parent.name.startswith(f"{first['dataVersion']}-transport-")
    assert verify_tree(out, "atlas", manifest_path=old_manifest)["dataVersion"] == first["dataVersion"]

    # The next healthy run cleans the dead staging tree and converges.
    _export(edge_db, out, **({**base, "compression_level": 6} if changed else base))
    assert not [name for name in os.listdir(out / "atlas" / "versions") if name.startswith(".export-")]
    assert not list((out / "atlas").glob(".current-*"))
    assert verify_tree(out, "atlas")["dataVersion"] == first["dataVersion"]


@pytest.mark.parametrize("point", _KILL_POINTS)
def test_sigkill_during_first_export_never_publishes_a_dangling_pointer(
    edge_db: Path, tmp_path: Path, point: str
) -> None:
    out = tmp_path / "out"
    _run_killed(edge_db, out, point)
    pointer = out / "atlas" / "current.json"
    if point == "after-pointer":
        assert verify_tree(out, "atlas")["publicRoutes"] > 0
    else:
        assert not pointer.exists()
    report = _export(edge_db, out)
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]


def test_install_reuses_identical_and_never_overwrites_different(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_A) == "atlas-v1-x"
    canonical = base / "versions" / "atlas-v1-x"
    inode = canonical.stat().st_ino
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_A) == "atlas-v1-x"
    assert canonical.stat().st_ino == inode

    digest = exporter._tree_digest(_synthetic_stage(base, "atlas-v1-x", _TREE_B).root)
    name = _publish_synthetic(base, "atlas-v1-x", _TREE_B)
    assert name == f"atlas-v1-x-transport-{digest}"
    assert _snapshot(canonical) == _TREE_A
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_B) == name  # identical suffix is reused
    assert _version_dirs(tmp_path) == sorted(["atlas-v1-x", name])


def test_transport_collision_with_different_bytes_fails_closed(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    _publish_synthetic(base, "atlas-v1-x", _TREE_A)
    probe = _synthetic_stage(base, "atlas-v1-x", _TREE_B)
    squatter = base / "versions" / f"atlas-v1-x-transport-{exporter._tree_digest(probe.root)}"
    probe.discard()
    squatter.mkdir()
    (squatter / "manifest.json").write_bytes(b"squatter")
    with pytest.raises(ExportError, match="refusing to overwrite"):
        _publish_synthetic(base, "atlas-v1-x", _TREE_B)
    assert _snapshot(squatter) == {"manifest.json": b"squatter"}
    assert _snapshot(base / "versions" / "atlas-v1-x") == _TREE_A


@pytest.mark.parametrize("winner", ["identical", "different"])
def test_concurrent_destination_creation_never_overwrites_the_winner(
    tmp_path: Path, monkeypatch, winner: str
) -> None:
    base = tmp_path / "atlas"
    loser = _synthetic_stage(base, "atlas-v1-x", _TREE_A)
    rival = _synthetic_stage(base, "atlas-v1-x", _TREE_A if winner == "identical" else _TREE_B)
    real_rename = os.rename
    state = {"raced": False}

    def rename(src, dst, *a, **k):
        if Path(src) == loser.root and not state["raced"]:
            state["raced"] = True  # the rival lands on the canonical destination first
            real_rename(rival.root, Path(dst))
        return real_rename(src, dst, *a, **k)

    monkeypatch.setattr(exporter.os, "rename", rename)
    name = loser.install()
    loser.discard()
    monkeypatch.undo()
    canonical = base / "versions" / "atlas-v1-x"
    assert _snapshot(canonical) == (_TREE_A if winner == "identical" else _TREE_B)
    if winner == "identical":
        assert name == "atlas-v1-x"
        assert _version_dirs(tmp_path) == ["atlas-v1-x"]
    else:
        assert name.startswith("atlas-v1-x-transport-")
        assert _snapshot(base / "versions" / name) == _TREE_A


def test_concurrent_publishers_do_not_overwrite_each_other(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    trees = [_TREE_A, _TREE_B] * 3
    barrier = threading.Barrier(len(trees))
    outcomes: list[tuple[dict[str, bytes], str]] = []
    errors: list[BaseException] = []

    def worker(files: dict[str, bytes]) -> None:
        try:
            stage = _synthetic_stage(base, "atlas-v1-x", files)
            barrier.wait(timeout=30)
            try:
                publication = stage.publish(lambda url: json.dumps({"manifestUrl": url}).encode())
                assert publication.durable
                outcomes.append((files, publication.manifest_url))
            finally:
                stage.discard()
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(files,)) for files in trees]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not errors, errors
    assert len(outcomes) == len(trees)
    for files, manifest_url in outcomes:
        assert _snapshot((base / manifest_url).parent) == files
    installed = _version_dirs(tmp_path)
    assert len(installed) == 2 and "atlas-v1-x" in installed
    assert (base / json.loads((base / "current.json").read_text())["manifestUrl"]).is_file()


@pytest.mark.parametrize("point", _FSYNC_STEPS)
def test_fsync_failure_fails_export_only_before_the_pointer_replacement(
    edge_db: Path, tmp_path: Path, monkeypatch, point: str
) -> None:
    """Before ``os.replace(pending, current.json)`` a failed fsync is a failed export (pointer untouched).

    After it the export is published: readers already resolve the new pointer, so
    reporting failure would misclassify it, and restoring the old pointer could
    clobber a concurrent publisher. The export succeeds and its report says the
    pointer's durability is unconfirmed.
    """
    out = tmp_path / "out"
    atlas = out / "atlas"
    kwargs = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    first = _export(edge_db, out, **kwargs)
    assert "publication" not in first, "a durable publication reports exactly as before"
    before = _snapshot(out)
    synced: list[str] = []
    real_fsync = os.fsync

    def fsync(fd: int) -> None:
        synced.append(_fsync_target(fd, atlas))
        if synced[-1] == point:
            raise OSError(errno.EIO, f"injected {point}")
        real_fsync(fd)

    monkeypatch.setattr(exporter.os, "fsync", fsync)
    if point == "base-dir":
        report = _export(edge_db, out, **kwargs, compression_level=6)
    else:
        with pytest.raises(OSError, match=f"injected {point}"):
            _export(edge_db, out, **kwargs, compression_level=6)
    monkeypatch.undo()
    assert synced == _FSYNC_STEPS[: _FSYNC_STEPS.index(point) + 1]

    after = _snapshot(out)
    unchanged = {name: blob for name, blob in before.items() if name != "atlas/current.json"}
    assert {name: blob for name, blob in after.items() if name in unchanged} == unchanged, "every old URL stays"
    assert all(
        name.startswith(f"atlas/versions/{first['dataVersion']}-transport-")
        for name in after.keys() - before.keys()
    )
    assert not list(atlas.glob(".current-*")) and not list((atlas / "versions").glob(".export-*"))
    if point == "base-dir":
        assert report["publication"] == {
            "committed": True, "durable": False, "error": f"fsync of {atlas} failed: [Errno 5] injected base-dir",
        }
        assert _pointer(out)["manifestUrl"] == report["manifestUrl"] != json.loads(before["atlas/current.json"])[
            "manifestUrl"
        ]
    else:
        assert after["atlas/current.json"] == before["atlas/current.json"]
    assert verify_tree(out, "atlas")["dataVersion"] == first["dataVersion"]


@pytest.mark.parametrize("point", ["pointer-file", "base-dir"])
def test_failure_around_the_commit_never_moves_a_concurrent_publishers_pointer(
    tmp_path: Path, monkeypatch, point: str
) -> None:
    """A rival publishes completely inside the failing fsync; the failing publisher never touches its pointer."""
    base = tmp_path / "atlas"
    publisher = _synthetic_stage(base, "atlas-v1-x", _TREE_A)
    rival = _synthetic_stage(base, "atlas-v1-y", _TREE_B)
    real_fsync = os.fsync
    raced: list[exporter.Publication] = []

    def build_current(url: str) -> bytes:
        return json.dumps({"manifestUrl": url}).encode()

    def fsync(fd: int) -> None:
        if not raced and _fsync_target(fd, base) == point:
            raced.append(None)  # type: ignore[arg-type]  # the rival's own fsyncs pass through
            raced[0] = rival.publish(build_current)
            raise OSError(errno.EIO, "injected")
        real_fsync(fd)

    monkeypatch.setattr(exporter.os, "fsync", fsync)
    try:
        if point == "pointer-file":
            with pytest.raises(OSError, match="injected"):
                publisher.publish(build_current)
        else:
            publication = publisher.publish(build_current)
            assert publication.manifest_url == "versions/atlas-v1-x/manifest.json"
            assert not publication.durable and "injected" in str(publication.durability_error)
    finally:
        monkeypatch.undo()
        publisher.discard()
        rival.discard()
    assert raced[0].durable and raced[0].manifest_url == "versions/atlas-v1-y/manifest.json"
    assert json.loads((base / "current.json").read_text()) == {"manifestUrl": raced[0].manifest_url}
    assert _snapshot(base / "versions" / "atlas-v1-x") == _TREE_A
    assert _snapshot(base / "versions" / "atlas-v1-y") == _TREE_B
    assert not list(base.glob(".current-*"))


def test_cli_reports_unconfirmed_pointer_durability_without_failing(
    edge_db: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    out = tmp_path / "out"
    real_fsync_dir = exporter._fsync_dir

    def fsync_dir(path: Path) -> None:
        if path == out / "atlas":
            raise OSError(errno.EIO, "injected")
        real_fsync_dir(path)

    monkeypatch.setattr(exporter, "_fsync_dir", fsync_dir)
    argv = ["--db", str(edge_db), "--out-dir", str(out), "--no-decks", "--verify"]
    assert exporter.main(argv) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["publication"]["committed"] is True and report["publication"]["durable"] is False
    assert captured.err.startswith(f"warning: published {report['manifestUrl']}, but its durability is unconfirmed")
    assert _pointer(out)["manifestUrl"] == report["manifestUrl"]


def test_concurrent_full_exports_with_different_limits_all_stay_valid(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    variants = [{"compression_level": 9}, {"compression_level": 6}] * 2
    errors: list[BaseException] = []

    def worker(kwargs: dict) -> None:
        try:
            _export(edge_db, out, **kwargs)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(kwargs,)) for kwargs in variants]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=110)
    assert not errors, errors
    dirs = _version_dirs(out)
    assert len(dirs) == 2
    for name in dirs:
        assert verify_tree(out, "atlas", manifest_path=out / "atlas" / "versions" / name / "manifest.json")
    assert verify_tree(out, "atlas")["dataVersion"]


def test_stale_pending_pointer_from_killed_export_is_reclaimed(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    base = out / "atlas"
    base.mkdir(parents=True)
    dead = base / ".current-999999999-deadbeef.json"
    dead.write_bytes(b"{}")
    alive = base / f".current-{os.getpid()}-cafebabe.json"
    alive.write_bytes(b"{}")
    _export(edge_db, out)
    assert not dead.exists()
    assert alive.exists()


def test_replayed_search_fragments_match_reference_rows_and_order(edge_db: Path, fixture_db: Path) -> None:
    for db in (edge_db, fixture_db):
        conn = open_readonly_db(db)
        try:
            conn.execute("BEGIN")
            articles, aliases = _build_indexes(conn)
            ref_articles, ref_aliases = _ref_load_search_rows(conn)
            assert list(articles.iter_fragments()) == [exporter._fragment_bytes(row) for row in ref_articles]
            assert list(aliases.iter_fragments()) == [exporter._fragment_bytes(row) for row in ref_aliases]
            assert not hasattr(articles, "fragments") and not hasattr(aliases, "fragments")
        finally:
            conn.close()


def test_search_index_memory_follows_key_metadata_not_gloss_bodies(tmp_path: Path) -> None:
    retained: dict[int, int] = {}
    bodies: dict[int, int] = {}
    for gloss_chars in (60, 20_000):
        db = _make_source_db(tmp_path / f"g{gloss_chars}.db", records=700, filler_chars=1, gloss_chars=gloss_chars)
        conn = open_readonly_db(db)
        try:
            conn.execute("BEGIN")
            bodies[gloss_chars] = sum(len(r[0] or "") for r in conn.execute("SELECT gloss FROM articles"))
            gc.collect()
            tracemalloc.start()
            try:
                before = tracemalloc.get_traced_memory()[0]
                articles, aliases = _build_indexes(conn)
                gc.collect()
                retained[gloss_chars] = tracemalloc.get_traced_memory()[0] - before
                assert len(articles) > 600 and len(aliases) > 600
            finally:
                tracemalloc.stop()
            del articles, aliases
        finally:
            conn.close()
    assert bodies[20_000] > 10_000_000
    assert retained[20_000] < retained[60] * 1.25, retained
    assert retained[20_000] < bodies[20_000] * 0.25, (retained, bodies)


def test_export_memory_does_not_grow_with_gloss_bodies(tmp_path: Path) -> None:
    db = _make_source_db(tmp_path / "gloss.db", records=700, filler_chars=1, gloss_chars=20_000)
    glosses = sum(len(r[0] or "") for r in sqlite3.connect(db).execute("SELECT gloss FROM articles"))
    assert glosses > 10_000_000
    kwargs = {"include_decks": False, "deck_dir": None, "compression_level": 1, "verify": True}
    error, peak = _traced_in_fresh_interpreter("export", db=db, out=tmp_path / "out", kwargs=kwargs)
    assert error is None
    assert peak < glosses * 0.25, f"peak {peak} vs gloss bodies {glosses}"


@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_gzip_size_and_streamed_sink_match_one_shot_without_retention(level: int) -> None:
    rng = random.Random(level + 100)
    raw = "".join(rng.choice("абвгдеж abc012,.\n") for _ in range(300_000)).encode("utf-8")
    chunks = [raw[i : i + 5_000] for i in range(0, len(raw), 5_000)]
    expected = gzip_bytes(raw, compression_level=level)
    assert exporter.gzip_size(lambda: iter(chunks), compression_level=level) == len(expected)
    pieces: list[bytes] = []
    result = exporter.stream_gzip(lambda: iter(chunks), compression_level=level, sink=pieces.append)
    assert b"".join(pieces) == expected
    assert result == exporter.GzipResult(
        len(expected), hashlib.sha256(expected).hexdigest(), len(raw), hashlib.sha256(raw).hexdigest()
    )
    if level:
        assert len(pieces) > 2, "levels 1-9 hand compressed pieces over as they are produced"


def test_stored_block_plan_reproduces_observed_one_shot_block_lengths() -> None:
    """Python 3.12.8 / zlib 1.3.1 one-shot framing observed by the reviewer."""
    observed = {
        65_531: [65_531], 65_532: [65_531, 1], 98_304: [65_531, 32_773], 100_000: [65_531, 32_773, 1_696],
    }
    for length, blocks in observed.items():
        assert [size for size, _last in exporter.stored_block_plan(length)] == blocks
        assert _framed(_STORED_PATTERN[:length]) == gzip_bytes(_STORED_PATTERN[:length], compression_level=0)
