"""Crash + acceptance tests for runner PR3 (network cache + transport).

Spec §PR3 / crash matrix:
- network workers cannot open sources.db
- atomic raw cache + fenced request claims (PR2 CAS generations)
- 429 → retry_scheduled + host cooldown without expiring transport
- packets/bundles content-addressed, compressed, bounded, rsync-resumable
- outer + per-item hash verification
- per-lemma atomic import; stale packet generations rejected
- cached-unparsed recovery, duplicate runner lock, import killed at k,
  retransmission, no double-fetch on retry
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lexicon.runner.bundle_import import import_bundle
from scripts.lexicon.runner.ledger import (
    CasStatus,
    DuplicateRunnerError,
    Ledger,
    OperatorActionKind,
    SchedulableState,
    UnitOutcome,
    compute_run_fingerprint,
)
from scripts.lexicon.runner.network_cache import (
    CacheCasStatus,
    DuplicateCacheRunnerError,
    NetworkCache,
    compute_request_key,
)
from scripts.lexicon.runner.network_worker import (
    NetworkWorkItem,
    assert_network_worker_cannot_open_sources,
    process_packet_to_bundle,
    process_request,
    refuse_sources_db,
)
from scripts.lexicon.runner.packet_export import export_request_packet
from scripts.lexicon.runner.sources_guard import (
    SourcesDbForbiddenError,
    guard_network_worker,
    is_network_worker,
)
from scripts.lexicon.runner.sqlite_ro import open_sources_ro
from scripts.lexicon.runner.transport import (
    BundleItem,
    HashMismatchError,
    PacketItem,
    build_bundle,
    build_packet,
    read_bundle,
    read_packet,
    retransmit_copy,
    split_bundle_items,
    verify_artifact_file,
)


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    lg = Ledger(tmp_path / "run.ledger.sqlite", max_attempts=5, lease_ttl_seconds=60.0)
    lg.open()
    yield lg
    lg.close()


@pytest.fixture
def cache(tmp_path: Path) -> NetworkCache:
    c = NetworkCache(tmp_path / "net.cache.sqlite", max_attempts=5, lease_ttl_seconds=60.0)
    c.open()
    yield c
    c.close()


def _fake_fetch_factory(bodies: dict[str, tuple[int, dict[str, str], bytes]], counter: list[int]):
    def _fetch(
        method: str, url: str, body: bytes | None, headers: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        counter[0] += 1
        if url not in bodies:
            raise AssertionError(f"unexpected fetch url={url}")
        return bodies[url]

    return _fetch


# --- 1. sources.db hard guard ------------------------------------------------


def test_network_workers_cannot_open_sources_db(tmp_path: Path) -> None:
    sources = tmp_path / "sources.db"
    sources.write_bytes(b"")  # presence is enough; open must refuse first
    with pytest.raises(SourcesDbForbiddenError, match=r"cannot open sources\.db"):
        refuse_sources_db(sources)
    with pytest.raises(SourcesDbForbiddenError, match=r"cannot open sources\.db"):
        assert_network_worker_cannot_open_sources(sources)
    with pytest.raises(SourcesDbForbiddenError, match=r"cannot open sources\.db"):
        with guard_network_worker():
            open_sources_ro(sources)
    # Guard is inactive outside network role — open may proceed (file is empty/invalid,
    # but path refusal must not fire).
    assert not is_network_worker()
    # empty file still opens as sqlite (creates schema on connect for non-uri? mode=ro needs file)
    # We only assert the guard path; offline open of a non-db may error — use a real sqlite.
    import sqlite3

    conn = sqlite3.connect(sources)
    conn.execute("CREATE TABLE t(x)")
    conn.commit()
    conn.close()
    ro = open_sources_ro(sources)
    ro.close()


# --- 2. atomic raw cache + fenced claims -------------------------------------


def test_raw_cache_atomic_mid_write_crash_leaves_no_half_row(cache: NetworkCache) -> None:
    key = compute_request_key(method="GET", url="https://example.test/a")
    claim = cache.claim_request(key, "w1", now=1.0)
    assert claim.ok and claim.lease_generation == 1
    cache.crash_mid_cache_write = True
    with pytest.raises(RuntimeError, match="injected crash: mid_cache_write"):
        cache.commit_raw(
            key,
            "w1",
            1,
            method="GET",
            url="https://example.test/a",
            status_code=200,
            body=b'{"ok":true}',
            now=2.0,
        )
    cache.crash_mid_cache_write = False
    assert cache.get_raw(key) is None
    # Retry with same generation is stale (txn rolled back claim? — claim commit already done).
    # Claim row stays leased; re-claim after expiry or commit with same gen after clearing crash.
    ok = cache.commit_raw(
        key,
        "w1",
        1,
        method="GET",
        url="https://example.test/a",
        status_code=200,
        body=b'{"ok":true}',
        now=3.0,
    )
    assert ok.ok
    entry = cache.get_raw(key)
    assert entry is not None
    assert entry.body == b'{"ok":true}'


def test_request_claim_fenced_stale_writer_rejected(cache: NetworkCache) -> None:
    key = compute_request_key(method="GET", url="https://example.test/b")
    c1 = cache.claim_request(key, "owner-a", now=10.0)
    assert c1.ok and c1.lease_generation == 1
    # Second claim while leased fails.
    c2 = cache.claim_request(key, "owner-b", now=11.0)
    assert c2.status is CacheCasStatus.INVALID_STATE
    # Stale commit rejected.
    stale = cache.commit_raw(
        key,
        "owner-b",
        1,
        method="GET",
        url="https://example.test/b",
        status_code=200,
        body=b"nope",
        now=12.0,
    )
    assert stale.status is CacheCasStatus.STALE_COMMIT_REJECTED
    assert cache.get_raw(key) is None


def test_duplicate_network_cache_runner_lock_refused(tmp_path: Path) -> None:
    path = tmp_path / "shared.cache.sqlite"
    a = NetworkCache(path, owner_id="cache-a")
    a.open()
    b = NetworkCache(path, owner_id="cache-b")
    with pytest.raises(DuplicateCacheRunnerError, match="duplicate runner refused"):
        b.open()
    a.close()
    b.open()
    b.close()


def test_duplicate_ledger_runner_lock_refused(tmp_path: Path) -> None:
    """PR3 crash suite also re-proves coordinator OS lock (shared with PR2)."""
    path = tmp_path / "shared.ledger.sqlite"
    a = Ledger(path, owner_id="coord-a")
    a.open()
    b = Ledger(path, owner_id="coord-b")
    with pytest.raises(DuplicateRunnerError, match="duplicate runner refused"):
        b.open()
    a.close()


# --- 3. 429 cooldown without expiring transport ------------------------------


def test_429_cooldown_retry_scheduled_does_not_expire_transport(
    ledger: Ledger, cache: NetworkCache, tmp_path: Path
) -> None:
    fp = compute_run_fingerprint(cohort_digest="cooldown-429")
    run = ledger.start_run(fp).run_id
    assert run
    items = [
        NetworkWorkItem(lemma_id="l1", method="GET", url="https://example.test/429"),
    ]
    exported = export_request_packet(
        ledger,
        run_id=run,
        fingerprint=fp,
        items=items,
        output_dir=tmp_path / "packets",
        now=1.0,
    )
    assert exported.ledger_status is CasStatus.OK
    pkt_row = ledger.get_packet(run, exported.artifact.artifact_id, exported.generation)
    assert pkt_row is not None
    assert pkt_row["state"] == "packet_exported"

    # Local ledger unit for network fetch phase.
    ledger.register_work_unit(run, "l1", unit_kind="lemma", phase="network_fetch", now=2.0)
    claim = ledger.claim_unit(run, "l1", "fetcher", phase="network_fetch", now=3.0)
    assert claim.ok
    gen = int(claim.lease_generation or 0)
    res = ledger.handle_http_429(
        run,
        "l1",
        "fetcher",
        gen,
        host="vps-1",
        next_allowed_at=1000.0,
        phase="network_fetch",
        now=4.0,
    )
    assert res.ok
    unit = ledger.get_work_unit(run, "l1", phase="network_fetch")
    assert unit is not None
    assert unit["state"] == UnitOutcome.RETRY_SCHEDULED.value
    # Transport still live.
    pkt_row2 = ledger.get_packet(run, exported.artifact.artifact_id, exported.generation)
    assert pkt_row2 is not None
    assert pkt_row2["state"] == "packet_exported"
    assert ledger.packet_generation_active(run, exported.generation)

    # Host cooldown gates new claims.
    ledger.register_work_unit(run, "l2", unit_kind="lemma", phase="network_fetch", now=5.0)
    blocked = ledger.claim_unit(
        run, "l2", "fetcher2", phase="network_fetch", host="vps-1", now=10.0
    )
    assert not blocked.ok
    assert "cooldown" in blocked.detail
    # After cooldown, claim works.
    ok = ledger.claim_unit(
        run, "l2", "fetcher2", phase="network_fetch", host="vps-1", now=1001.0
    )
    assert ok.ok

    # Network cache 429 path mirrors the same semantics.
    counter = [0]
    fetch = _fake_fetch_factory(
        {"https://example.test/429": (429, {}, b"slow down")},
        counter,
    )
    out = process_request(
        cache,
        items[0],
        owner="nw",
        fetch=fetch,
        host="vps-1",
        now=50.0,
        cooldown_seconds=100.0,
    )
    assert out.status == "retry_scheduled"
    assert out.error_code == "http_429"
    assert cache.host_cooldown_active("vps-1", now=51.0) is not None
    blocked_c = cache.claim_request(
        compute_request_key(method="GET", url="https://example.test/other"),
        "nw2",
        host="vps-1",
        now=52.0,
    )
    assert blocked_c.status is CacheCasStatus.HOST_COOLDOWN


# --- 4–5. packets/bundles compressed, content-addressed, hashed -------------


def test_packet_and_bundle_content_addressed_and_verified(tmp_path: Path) -> None:
    items = [
        PacketItem.from_request(
            "alpha",
            compute_request_key(method="GET", url="https://example.test/alpha"),
            {"method": "GET", "url": "https://example.test/alpha"},
        ),
        PacketItem.from_request(
            "beta",
            compute_request_key(method="GET", url="https://example.test/beta"),
            {"method": "GET", "url": "https://example.test/beta"},
        ),
    ]
    pkt = build_packet(
        run_id="run-x",
        fingerprint="fp-x",
        generation=1,
        items=items,
        output_dir=tmp_path / "out",
    )
    assert pkt.path.name == f"{pkt.artifact_id}.tar.zst"
    assert pkt.path.suffixes[-2:] == [".tar", ".zst"] or pkt.path.name.endswith(".tar.zst")
    verify_artifact_file(pkt.path, expected_id=pkt.artifact_id)
    loaded = read_packet(pkt.path)
    assert len(loaded.items) == 2
    assert loaded.manifest["generation"] == 1

    b_items = [
        BundleItem.from_result(
            "alpha",
            items[0].request_key,
            {"gloss": "a"},
        ),
        BundleItem.from_result(
            "beta",
            items[1].request_key,
            {"gloss": "b"},
        ),
    ]
    bundle = build_bundle(
        run_id="run-x",
        fingerprint="fp-x",
        packet_id=pkt.artifact_id,
        packet_generation=1,
        items=b_items,
        output_dir=tmp_path / "out",
    )
    loaded_b = read_bundle(bundle.path, expected_id=bundle.artifact_id)
    assert {i["lemma_id"] for i in loaded_b.items} == {"alpha", "beta"}

    # Corrupt per-item hash detection: rewrite file with wrong payload under same name.
    # Easier: declare wrong hash at build time.
    bad = BundleItem(
        lemma_id="gamma",
        request_key="rk",
        result={"x": 1},
        result_hash="0" * 64,
    )
    with pytest.raises(HashMismatchError):
        build_bundle(
            run_id="run-x",
            fingerprint="fp-x",
            packet_id=pkt.artifact_id,
            packet_generation=1,
            items=[bad],
            output_dir=tmp_path / "bad",
        )


def test_bundle_bounded_split(tmp_path: Path) -> None:
    items = [
        BundleItem.from_result(f"l{i:03d}", f"rk{i}", {"i": i}) for i in range(10)
    ]
    groups = split_bundle_items(items, max_items=3)
    assert len(groups) == 4
    assert all(len(g) <= 3 for g in groups)
    with pytest.raises(Exception, match="exceeds bound"):
        build_bundle(
            run_id="r",
            fingerprint="f",
            packet_id="p",
            packet_generation=1,
            items=items,
            output_dir=tmp_path / "b",
            max_items=3,
        )


def test_retransmission_idempotent(tmp_path: Path) -> None:
    item = PacketItem.from_request(
        "one",
        compute_request_key(method="GET", url="https://example.test/one"),
        {"method": "GET", "url": "https://example.test/one"},
    )
    pkt = build_packet(
        run_id="r",
        fingerprint="f",
        generation=1,
        items=[item],
        output_dir=tmp_path / "src",
    )
    dest = retransmit_copy(pkt.path, tmp_path / "dest")
    assert dest.name == pkt.path.name
    assert dest.read_bytes() == pkt.path.read_bytes()
    # Second retransmit is a no-op success.
    dest2 = retransmit_copy(pkt.path, tmp_path / "dest")
    assert dest2 == dest
    # Writing the same packet again to src is idempotent.
    pkt2 = build_packet(
        run_id="r",
        fingerprint="f",
        generation=1,
        items=[item],
        output_dir=tmp_path / "src",
    )
    assert pkt2.artifact_id == pkt.artifact_id


# --- 6. import atomic per lemma + stale generation --------------------------


def test_import_atomic_per_lemma_and_rejects_stale_generation(
    ledger: Ledger, tmp_path: Path
) -> None:
    fp = compute_run_fingerprint(cohort_digest="import-atomic")
    run = ledger.start_run(fp).run_id
    assert run
    work = [
        NetworkWorkItem(lemma_id="a", method="GET", url="https://example.test/a"),
        NetworkWorkItem(lemma_id="b", method="GET", url="https://example.test/b"),
        NetworkWorkItem(lemma_id="c", method="GET", url="https://example.test/c"),
    ]
    exported = export_request_packet(
        ledger,
        run_id=run,
        fingerprint=fp,
        items=work,
        output_dir=tmp_path / "packets",
        now=1.0,
    )
    gen = exported.generation
    bundle_items = [
        BundleItem.from_result(w.lemma_id, w.request_key, {"lemma": w.lemma_id}) for w in work
    ]
    bundle = build_bundle(
        run_id=run,
        fingerprint=fp,
        packet_id=exported.artifact.artifact_id,
        packet_generation=gen,
        items=bundle_items,
        output_dir=tmp_path / "bundles",
    )

    # Kill import after 2 commits.
    with pytest.raises(RuntimeError, match="injected crash: import_killed_at_k"):
        import_bundle(
            ledger,
            bundle.path,
            owner="imp",
            expected_fingerprint=fp,
            now=10.0,
            crash_after_items=2,
        )
    # Exactly 2 imports committed.
    n = ledger._require().execute(
        "SELECT COUNT(*) AS n FROM imports WHERE run_id = ?",
        (run,),
    ).fetchone()
    assert int(n["n"]) == 2

    # Resume import: remaining + no-op on already imported.
    result = import_bundle(
        ledger,
        bundle.path,
        owner="imp",
        expected_fingerprint=fp,
        now=20.0,
    )
    n2 = ledger._require().execute(
        "SELECT COUNT(*) AS n FROM imports WHERE run_id = ?",
        (run,),
    ).fetchone()
    assert int(n2["n"]) == 3
    assert len(result.committed) + len(result.skipped_noop) >= 1

    # Abandon generation → further new imports of a different lemma with same gen fail.
    ledger.abandon_packet(
        run, exported.artifact.artifact_id, gen, "operator abandoned stale transport"
    )
    assert ledger.count_operator_actions(run, OperatorActionKind.ABANDON_PACKET.value) == 1
    extra = BundleItem.from_result("d", "rk-d", {"lemma": "d"})
    stale_bundle = build_bundle(
        run_id=run,
        fingerprint=fp,
        packet_id=exported.artifact.artifact_id,
        packet_generation=gen,
        items=[extra],
        output_dir=tmp_path / "bundles2",
    )
    stale = import_bundle(
        ledger,
        stale_bundle.path,
        owner="imp",
        expected_fingerprint=fp,
        now=30.0,
    )
    assert stale.status is CasStatus.INVALID_STATE
    assert stale.detail == "stale_packet_generation"


# --- 7. crash suite: cached-unparsed, no double-fetch -----------------------


def test_cached_unparsed_recovery_without_refetch(cache: NetworkCache) -> None:
    """Cached but unparsed → resume parses the cached body without fetching."""
    url = "https://example.test/parse-me"
    key = compute_request_key(method="GET", url=url)
    counter = [0]
    body = '{"lemma":"кіт","gloss":"cat"}'.encode()
    fetch = _fake_fetch_factory({url: (200, {"content-type": "application/json"}, body)}, counter)

    item = NetworkWorkItem(lemma_id="кіт", method="GET", url=url)
    first = process_request(cache, item, owner="w", fetch=fetch, now=1.0)
    assert first.fetched is True
    assert counter[0] == 1
    assert cache.fetch_count == 1
    assert first.result is not None

    # Drop parsed cache rows to simulate "cached but unparsed".
    cache._require().execute("DELETE FROM parsed_cache")
    second = process_request(cache, item, owner="w2", fetch=fetch, now=2.0)
    assert second.fetched is False
    assert counter[0] == 1  # no second network fetch
    assert cache.fetch_count == 1
    assert second.status == "cache_hit_parsed"
    assert second.result is not None
    assert second.result["payload"]["lemma"] == "кіт"


def test_retries_do_not_double_fetch_cached_request(cache: NetworkCache) -> None:
    """PROOF: retries after a successful cache commit never re-hit the network."""
    url = "https://example.test/once"
    counter = [0]
    body = b'{"ok":1}'
    fetch = _fake_fetch_factory({url: (200, {}, body)}, counter)
    item = NetworkWorkItem(lemma_id="once", method="GET", url=url)

    for i in range(5):
        out = process_request(cache, item, owner=f"w{i}", fetch=fetch, now=float(i + 1))
        assert out.result is not None

    assert counter[0] == 1, f"expected single fetch, got {counter[0]}"
    assert cache.fetch_count == 1
    hits = cache.list_events(event="cache_hit")
    assert len(hits) >= 4


def test_end_to_end_packet_fetch_bundle_import(
    ledger: Ledger, cache: NetworkCache, tmp_path: Path
) -> None:
    fp = compute_run_fingerprint(cohort_digest="e2e-net")
    run = ledger.start_run(fp).run_id
    assert run
    work = [
        NetworkWorkItem(lemma_id="x", method="GET", url="https://example.test/x"),
        NetworkWorkItem(lemma_id="y", method="GET", url="https://example.test/y"),
    ]
    exported = export_request_packet(
        ledger,
        run_id=run,
        fingerprint=fp,
        items=work,
        output_dir=tmp_path / "packets",
    )
    counter = [0]
    fetch = _fake_fetch_factory(
        {
            "https://example.test/x": (200, {}, b'{"lemma":"x"}'),
            "https://example.test/y": (200, {}, b'{"lemma":"y"}'),
        },
        counter,
    )
    bundle_path, outcomes = process_packet_to_bundle(
        cache,
        exported.artifact.path,
        owner="net",
        fetch=fetch,
        output_dir=tmp_path / "bundles",
        now=5.0,
    )
    assert bundle_path is not None
    assert counter[0] == 2
    assert all(o.result is not None for o in outcomes)

    # Second pass over same packet: zero new fetches (cache hits).
    bundle_path2, outcomes2 = process_packet_to_bundle(
        cache,
        exported.artifact.path,
        owner="net2",
        fetch=fetch,
        output_dir=tmp_path / "bundles2",
        now=6.0,
    )
    assert bundle_path2 is not None
    assert counter[0] == 2
    assert all(o.fetched is False for o in outcomes2)

    imp = import_bundle(
        ledger,
        bundle_path,
        owner="importer",
        expected_fingerprint=fp,
        now=7.0,
    )
    assert imp.status is CasStatus.OK
    assert len(imp.committed) == 2
    for lemma in ("x", "y"):
        unit = ledger.get_work_unit(run, lemma, phase="network_import")
        assert unit is not None
        assert unit["state"] == UnitOutcome.DONE.value


def test_claim_after_claim_crash_rolls_back(cache: NetworkCache) -> None:
    key = compute_request_key(method="GET", url="https://example.test/crash-claim")
    cache.crash_after_claim = True
    with pytest.raises(RuntimeError, match="injected crash: after_claim"):
        cache.claim_request(key, "w", now=1.0)
    cache.crash_after_claim = False
    row = cache._require().execute(
        "SELECT state, lease_generation FROM request_claims WHERE request_key = ?",
        (key,),
    ).fetchone()
    # Either no row or still pending gen 0 — never half-leased.
    if row is not None:
        assert str(row["state"]) == SchedulableState.PENDING.value
        assert int(row["lease_generation"]) == 0
    claim = cache.claim_request(key, "w", now=2.0)
    assert claim.ok and claim.lease_generation == 1
