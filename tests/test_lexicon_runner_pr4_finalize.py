"""PR4 — leaf sealing handoff, streaming finalization, publication gate (#5230).

Covers the eight acceptance criteria + v2 revisions V1–V9 (Sol-amended V3/V4/V5).
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.deploy.vendor_atlas_tree import VendorError, vendor_atlas_tree
from scripts.lexicon.runner.deterministic_zip import (
    ZIP_EPOCH,
    iter_zip_normalized_view,
    write_deterministic_zip,
)
from scripts.lexicon.runner.finalize import (
    ASSEMBLY_RSS_CEILING_BYTES,
    FinalizeError,
    FinalizeLock,
    _safe_rss_bytes,
    assemble_version_tree,
    build_dry_run_report,
    finalize_run,
)
from scripts.lexicon.runner.ledger import (
    ChunkLedgerState,
    DuplicateRunnerError,
    Ledger,
    OperatorActionKind,
    UnitOutcome,
    compute_run_fingerprint,
)


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    lg = Ledger(tmp_path / "run.ledger.sqlite", max_attempts=5, lease_ttl_seconds=60.0)
    lg.open()
    yield lg
    lg.close()


def _seed_sealed_run(
    ledger: Ledger,
    artifacts_dir: Path,
    *,
    cohort: str = "pr4-cohort",
    lemmas: list[str] | None = None,
    chunk_id: str = "chunk-0",
    also_superseded_parent: bool = False,
) -> tuple[str, str]:
    """Register a fully sealed leaf with lemma artifacts; return (run_id, fingerprint)."""
    lemma_ids = lemmas or ["alpha", "beta", "gamma"]
    fp = compute_run_fingerprint(cohort_digest=cohort)
    run = ledger.start_run(fp).run_id
    assert run

    if also_superseded_parent:
        ledger.register_chunk(
            run,
            "parent",
            lemma_ids,
            is_leaf=False,
            state=ChunkLedgerState.SUPERSEDED.value,
        )
        ledger.register_work_unit(run, "parent", unit_kind="chunk", phase="offline_enrich")
        ledger._require().execute(
            "UPDATE work_units SET state = ? WHERE run_id = ? AND unit_id = ?",
            (ChunkLedgerState.SUPERSEDED.value, run, "parent"),
        )

    ledger.register_chunk_work_units(run, [(chunk_id, lemma_ids)])
    claim = ledger.claim_unit(run, chunk_id, "coord", now=1.0)
    assert claim.ok and claim.lease_generation is not None
    gen = int(claim.lease_generation)

    art_chunk = artifacts_dir / chunk_id
    art_chunk.mkdir(parents=True, exist_ok=True)
    for lid in lemma_ids:
        entry = {"lemma": lid, "url_slug": lid, "gloss": f"g-{lid}"}
        (art_chunk / f"{lid}.json").write_text(
            json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        # Lemma work unit: claim-ish direct insert via register + result path.
        ledger.register_work_unit(run, lid, unit_kind="lemma", phase="offline_enrich")
        conn = ledger._require()
        conn.execute(
            "UPDATE work_units SET state = ?, result_hash = ?, owner = NULL, "
            "leased_until = NULL, attempt_count = 1, updated_at = ? "
            "WHERE run_id = ? AND unit_id = ? AND phase = ?",
            (UnitOutcome.DONE.value, f"hash-{lid}", 2.0, run, lid, "offline_enrich"),
        )

    commit = ledger.commit_result(
        run, chunk_id, "coord", gen, "done", result_hash="chunk-hash", now=3.0
    )
    assert commit.ok
    # After result, owner released; seal uses generation on DONE leaf.
    sealed = ledger.commit_seal(
        run, chunk_id, "coord", gen, seal_sha256=f"seal-{chunk_id}", now=4.0
    )
    assert sealed.ok, sealed.detail
    return run, fp


def test_completion_gate_refuses_unsealed_and_failed_terminal(ledger: Ledger, tmp_path: Path) -> None:
    """V4: non-terminal or failed_terminal in leaf closure refuses; superseded excluded."""
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, also_superseded_parent=True)
    gate = ledger.assess_completion_gate(run)
    assert gate["ok"] is True
    assert gate["sealed_leaf_count"] == 1

    # Inject a second unsealed leaf with a failed lemma.
    ledger.register_chunk_work_units(run, [("chunk-bad", ["omega"])])
    ledger.register_work_unit(run, "omega", unit_kind="lemma", phase="offline_enrich")
    conn = ledger._require()
    conn.execute(
        "UPDATE work_units SET state = ? WHERE run_id = ? AND unit_id = ?",
        (UnitOutcome.FAILED_TERMINAL.value, run, "omega"),
    )
    conn.execute(
        "UPDATE chunks SET state = ? WHERE run_id = ? AND chunk_id = ?",
        (ChunkLedgerState.DONE.value, run, "chunk-bad"),
    )
    gate2 = ledger.assess_completion_gate(run)
    assert gate2["ok"] is False
    assert gate2["unsealed_leaf_count"] >= 1
    assert gate2["failed_terminal_count"] >= 1
    assert any("failed_terminal" in r for r in gate2["reasons"])
    # Superseded parent never counted as a leaf in closure.
    assert gate2["leaf_chunk_count"] == 2  # chunk-0 sealed + chunk-bad, not parent


def test_completion_gate_aggregate_no_in_list_1500(ledger: Ledger, tmp_path: Path) -> None:
    """V9: 1500-lemma leaf assessed via json_each join (no SQLite variable blowup)."""
    lemmas = [f"L{i:04d}" for i in range(1500)]
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, lemmas=lemmas, cohort="big-gate")
    gate = ledger.assess_completion_gate(run)
    assert gate["ok"] is True
    assert gate["constituent_lemma_count"] == 1500
    assert gate["sealed_leaf_count"] == 1


def test_dry_run_report_required_surface(ledger: Ledger, tmp_path: Path) -> None:
    """V8/Q3: finalize --dry-run reports gate, unsealed, sizes, fingerprint."""
    arts = tmp_path / "arts"
    run, fp = _seed_sealed_run(ledger, arts)
    report = build_dry_run_report(
        ledger,
        run,
        artifacts_dir=arts,
        prior_version_dir=None,
        grant_first_run_escape=True,
    )
    assert report.gate_ok is True
    assert report.fingerprint == fp
    assert report.leaf_chunk_count == 1
    assert report.sealed_leaf_count == 1
    assert report.constituent_lemma_count == 3
    assert report.estimated_payload_bytes > 0
    assert report.data_version_preview is not None
    assert report.first_run_escape_required is True
    assert report.first_run_escape_available is True
    assert report.zip_writer_pin["module"] == "zipfile"

    # dry-run path via finalize_run (no writes).
    out = tmp_path / "out"
    out.mkdir()
    dry = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=out,
        grant_first_run_escape=True,
        dry_run=True,
    )
    assert dry.ok
    assert dry.dry_run is not None
    assert dry.dry_run.gate_ok is True
    # Dry-run must not promote a tree.
    assert not (out / "tree" / "atlas").exists()


def test_double_assembly_byte_equality_normalized_zip(ledger: Ledger, tmp_path: Path) -> None:
    """V3 / criterion 3: same sealed inputs → byte-identical ZIP (normalized metadata)."""
    arts = tmp_path / "arts"
    run, fp = _seed_sealed_run(ledger, arts, cohort="double")

    # Fixed prior generation (publish-arc supplies --prior-version-dir).
    prior_named = tmp_path / "v-prior-fixed"
    prior_named.mkdir()
    (prior_named / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runtime-manifest",
                "schemaVersion": 1,
                "dataVersion": "v-prior-fixed",
                "generatedAt": "1970-01-01T00:00:00+00:00",
                "entries": {"tree": {}, "shards": {}},
                "search": {
                    "articles": {"tree": {}, "shards": {}},
                    "aliases": {"tree": {}, "shards": {}},
                },
                "decks": {"levels": {}},
                "counts": {},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (prior_named / "entries").mkdir()
    (prior_named / "entries" / "p00-0.json.gz").write_bytes(
        b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    bytes_list: list[bytes] = []
    digests: list[str] = []
    data_versions: list[str] = []
    for i in range(2):
        out = tmp_path / f"eq-{i}"
        result = finalize_run(
            ledger=ledger,
            run_id=run,
            artifacts_dir=arts,
            out_dir=out,
            prior_version_dir=prior_named,
            verify_vendor=True,
            assert_rss_ceiling=True,
        )
        assert result.ok, result.detail
        assert result.archive_path and result.archive_sha256
        assert result.fingerprint == fp
        digests.append(str(result.archive_sha256))
        data_versions.append(str(result.data_version))
        bytes_list.append(Path(str(result.archive_path)).read_bytes())
        manifest = json.loads(
            (
                Path(str(result.tree_root))
                / "atlas"
                / "versions"
                / str(result.data_version)
                / "manifest.json"
            ).read_text(encoding="utf-8")
        )
        assert manifest["runFingerprint"] == fp

    assert bytes_list[0] == bytes_list[1]
    assert digests[0] == digests[1]
    assert data_versions[0] == data_versions[1]

    # Normalized zip metadata on the equal archives.
    view = iter_zip_normalized_view(tmp_path / "eq-0" / "atlas-tree.zip")
    assert view
    for _name, _payload, meta in view:
        date_time, create_system, external_attr, extra, compress_type = meta
        assert date_time == ZIP_EPOCH
        assert create_system == 3
        assert extra == b""
        assert compress_type == zipfile.ZIP_DEFLATED
        assert external_attr == (0o100644 << 16)


def test_vendor_round_trip_happy_and_corrupt(ledger: Ledger, tmp_path: Path) -> None:
    """Criterion 5: assembly → vendor happy path + corrupt-archive fail path."""
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, cohort="vendor")
    out = tmp_path / "out"
    result = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=out,
        grant_first_run_escape=True,
        verify_vendor=True,
    )
    assert result.ok, result.detail
    assert result.vendor_ok is True
    assert (out / "vendor-dist" / "atlas" / "current.json").is_file()

    # Corrupt archive fails closed.
    archive = Path(str(result.archive_path))
    blob = bytearray(archive.read_bytes())
    blob[-1] = (blob[-1] + 1) % 256
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(bytes(blob))
    dist = tmp_path / "dist-corrupt"
    dist.mkdir()
    with pytest.raises(VendorError, match="sha256 mismatch"):
        vendor_atlas_tree(dist, sha256=str(result.archive_sha256), archive_path=corrupt)
    assert not (dist / "atlas").exists()


def test_assembly_crash_mid_stream_no_partial_tree(ledger: Ledger, tmp_path: Path) -> None:
    """V7 / criterion 7: mid-stream crash leaves no partial versions/<dataVersion>."""
    arts = tmp_path / "arts"
    lemmas = [f"w{i}" for i in range(20)]
    run, fp = _seed_sealed_run(ledger, arts, lemmas=lemmas, cohort="crash")
    out = tmp_path / "out"
    tree_root = out / "tree"
    tree_root.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="injected crash: mid_stream_assembly"):
        assemble_version_tree(
            ledger=ledger,
            run_id=run,
            fingerprint=fp,
            artifacts_dir=arts,
            tree_root=tree_root,
            prior_version_dir=None,
            grant_first_run_escape=True,
            first_run_escape_reason="test",
            crash_mid_stream=True,
            assert_rss_ceiling=True,
        )

    atlas = tree_root / "atlas"
    # Either absent entirely, or if present must not contain a partial current version.
    if atlas.exists():
        versions = atlas / "versions"
        assert not versions.exists() or not any(versions.iterdir())
    # Staging temps cleaned.
    leftovers = list(tree_root.glob(".atlas-assemble-*"))
    assert leftovers == []


def test_duplicate_finalizer_lock_refused(tmp_path: Path) -> None:
    """Criterion 7: second finalizer process refused via single-writer lock."""
    lock_path = tmp_path / ".finalize.lock"
    a = FinalizeLock(lock_path, owner_id="fin-a")
    a.acquire()
    b = FinalizeLock(lock_path, owner_id="fin-b")
    with pytest.raises(DuplicateRunnerError, match="duplicate finalizer refused"):
        b.acquire()
    a.release()
    b.acquire()
    b.release()


def test_first_run_escape_one_time_only(ledger: Ledger, tmp_path: Path) -> None:
    """V5: first-run escape is one-time; cannot survive past first successful publish."""
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, cohort="escape")
    out1 = tmp_path / "out1"
    r1 = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=out1,
        grant_first_run_escape=True,
        verify_vendor=True,
    )
    assert r1.ok, r1.detail
    assert ledger.first_run_escape_consumed()

    # Second run without prior must fail even if grant flag is re-passed.
    out2 = tmp_path / "out2"
    r2 = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=out2,
        grant_first_run_escape=True,
        verify_vendor=False,
    )
    assert r2.ok is False
    assert "first-run escape already consumed" in r2.detail or "not reusable" in r2.detail

    # With a real prior (bootstrap from first publish), finalization works without escape.
    prior = (
        Path(str(r1.tree_root))
        / "atlas"
        / "versions"
        / "atlas-bootstrap-empty"
    )
    assert prior.is_dir()
    out3 = tmp_path / "out3"
    r3 = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=out3,
        prior_version_dir=prior,
        grant_first_run_escape=False,
        verify_vendor=True,
    )
    assert r3.ok, r3.detail
    assert r3.data_version == r1.data_version  # same sealed inputs


def test_fingerprint_mismatch_refuses_publication(ledger: Ledger, tmp_path: Path) -> None:
    """Criterion 6: expected fingerprint mismatch refuses publication."""
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, cohort="fp-mismatch")
    result = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=tmp_path / "out",
        grant_first_run_escape=True,
        expected_fingerprint="0" * 64,
        verify_vendor=False,
    )
    assert result.ok is False
    assert "fingerprint_mismatch_refused" in result.detail


def test_rss_ceiling_constant_and_probe(ledger: Ledger, tmp_path: Path) -> None:
    """Criterion 2 / V2: 200 MiB incremental assembly RSS ceiling (delta, not process total)."""
    assert ASSEMBLY_RSS_CEILING_BYTES == 200 * 1024 * 1024
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(
        ledger,
        arts,
        lemmas=[f"m{i}" for i in range(100)],
        cohort="rss",
    )
    result = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=tmp_path / "out",
        grant_first_run_escape=True,
        verify_vendor=True,
        assert_rss_ceiling=True,
    )
    assert result.ok, result.detail
    # peak_rss_bytes is the assembly *delta*; process absolute may already be large.
    if result.peak_rss_bytes is not None:
        assert result.peak_rss_bytes < ASSEMBLY_RSS_CEILING_BYTES
    if result.peak_rss_delta_bytes is not None:
        assert result.peak_rss_delta_bytes < ASSEMBLY_RSS_CEILING_BYTES
        assert result.peak_rss_bytes == result.peak_rss_delta_bytes
    if result.baseline_rss_bytes is not None and result.peak_rss_delta_bytes is not None:
        assert result.baseline_rss_bytes >= 0
        assert result.peak_rss_delta_bytes >= 0
    # Dry-run report mirrors assembly metrics after a successful finalize.
    assert result.dry_run is not None
    assert result.dry_run.rss_ceiling_bytes == ASSEMBLY_RSS_CEILING_BYTES
    if result.dry_run.peak_rss_delta_bytes is not None:
        assert result.dry_run.peak_rss_delta_bytes == result.peak_rss_delta_bytes


def test_rss_ceiling_delta_ignores_preexisting_process_ballast(
    ledger: Ledger, tmp_path: Path
) -> None:
    """Regression: ~300 MiB process ballast before finalize must not trip the gate.

    Proves the ceiling applies to assembly delta (peak − baseline), not whole-
    process RSS. Without delta semantics, a pytest-xdist worker that already
    holds a large high-water mark would false-fail small payloads.
    """
    arts = tmp_path / "arts"
    run, _fp = _seed_sealed_run(ledger, arts, lemmas=["tiny-a", "tiny-b"], cohort="rss-delta")
    # Touch pages so the OS actually accounts the ballast in ru_maxrss.
    ballast_size = 300 * 1024 * 1024
    ballast = bytearray(ballast_size)
    for i in range(0, ballast_size, 4096):
        ballast[i] = 1
    try:
        pre = _safe_rss_bytes()
        # Process high-water should reflect ballast when the probe works.
        if pre is not None:
            assert pre >= ballast_size // 2, (
                f"expected process RSS high-water ≥ ~150 MiB after ballast, got {pre}"
            )
        result = finalize_run(
            ledger=ledger,
            run_id=run,
            artifacts_dir=arts,
            out_dir=tmp_path / "out-delta",
            grant_first_run_escape=True,
            verify_vendor=False,
            assert_rss_ceiling=True,
        )
        assert result.ok, result.detail
        assert result.peak_rss_delta_bytes is not None
        assert result.peak_rss_delta_bytes < ASSEMBLY_RSS_CEILING_BYTES
        assert result.peak_rss_bytes == result.peak_rss_delta_bytes
        # Absolute process sample remains large; only delta is gated.
        if pre is not None and result.baseline_rss_bytes is not None:
            assert result.baseline_rss_bytes >= ballast_size // 2
    finally:
        del ballast


def test_rss_ceiling_trips_on_assembly_overuse(ledger: Ledger, tmp_path: Path) -> None:
    """Genuine overuse: small ceiling override trips on a large synthetic payload."""
    arts = tmp_path / "arts"
    # One ~32 MiB lemma body forces assembly high-water growth well past 1 MiB.
    huge = "x" * (32 * 1024 * 1024)
    run, fp = _seed_sealed_run(ledger, arts, lemmas=["huge"], cohort="rss-overuse")
    lemma_path = arts / "chunk-0" / "huge.json"
    entry = {"lemma": "huge", "url_slug": "huge", "gloss": huge}
    lemma_path.write_text(
        json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tree_root = tmp_path / "out-overuse" / "tree"
    tree_root.mkdir(parents=True)
    small_ceiling = 1 * 1024 * 1024  # 1 MiB incremental cap
    with pytest.raises(FinalizeError, match=r"assembly RSS delta .* exceeded ceiling"):
        assemble_version_tree(
            ledger=ledger,
            run_id=run,
            fingerprint=fp,
            artifacts_dir=arts,
            tree_root=tree_root,
            prior_version_dir=None,
            grant_first_run_escape=True,
            first_run_escape_reason="test",
            assert_rss_ceiling=True,
            rss_ceiling_bytes=small_ceiling,
        )


def test_deterministic_zip_writer_pin() -> None:
    """V3: writer pin documents Python zipfile + normalized metadata."""
    from scripts.lexicon.runner.deterministic_zip import ZIP_WRITER_PIN

    assert ZIP_WRITER_PIN["module"] == "zipfile"
    assert ZIP_WRITER_PIN["compression"] == "ZIP_DEFLATED"
    members = [("a.txt", b"hello"), ("b/c.txt", b"world")]
    # Write twice to distinct paths — byte equal.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p1 = Path(td) / "1.zip"
        p2 = Path(td) / "2.zip"
        d1 = write_deterministic_zip(p1, members)
        d2 = write_deterministic_zip(p2, members)
        assert d1 == d2
        assert p1.read_bytes() == p2.read_bytes()


def test_seal_mid_transaction_still_rolls_back(ledger: Ledger) -> None:
    """House rule: mid-transaction crash-injection on seal (BEGIN IMMEDIATE + CAS)."""
    fp = compute_run_fingerprint(cohort_digest="mid-seal")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("c1", ["x", "y"])])
    for lid in ("x", "y"):
        ledger.register_work_unit(run, lid, unit_kind="lemma")
        ledger._require().execute(
            "UPDATE work_units SET state = ? WHERE run_id = ? AND unit_id = ?",
            (UnitOutcome.DONE.value, run, lid),
        )
    claim = ledger.claim_unit(run, "c1", "coord", now=1.0)
    gen = int(claim.lease_generation or 0)
    ledger.commit_result(run, "c1", "coord", gen, "done", result_hash="r", now=2.0)
    ledger.crash_mid_seal = True
    with pytest.raises(RuntimeError, match="injected crash: mid_seal"):
        ledger.commit_seal(run, "c1", "coord", gen, seal_sha256="s", now=3.0)
    ledger.crash_mid_seal = False
    n = ledger._require().execute(
        "SELECT COUNT(*) AS n FROM seals WHERE run_id = ?", (run,)
    ).fetchone()
    assert int(n["n"]) == 0
    sealed = ledger.commit_seal(run, "c1", "coord", gen, seal_sha256="s", now=4.0)
    assert sealed.ok


def test_record_finalize_audit(ledger: Ledger, tmp_path: Path) -> None:
    arts = tmp_path / "arts"
    run, fp = _seed_sealed_run(ledger, arts, cohort="audit")
    result = finalize_run(
        ledger=ledger,
        run_id=run,
        artifacts_dir=arts,
        out_dir=tmp_path / "out",
        grant_first_run_escape=True,
        verify_vendor=True,
    )
    assert result.ok, result.detail
    actions = ledger.count_operator_actions(run, OperatorActionKind.FINALIZE.value)
    assert actions >= 1
    events = ledger.list_events(run, event="run_finalized")
    assert events
    phase = ledger._require().execute(
        "SELECT seal_sha256 FROM run_phases WHERE run_id = ? AND phase = 'finalize'",
        (run,),
    ).fetchone()
    assert phase is not None
    assert phase["seal_sha256"] == result.archive_sha256
    assert result.fingerprint == fp
