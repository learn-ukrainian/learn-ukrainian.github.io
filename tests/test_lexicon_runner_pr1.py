"""Tests for lexicon runner PR1 — engine isolation + bounded lookup rewrite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import enrich_manifest as em
from scripts.lexicon.runner.contracts import ChunkSpec, ChunkState, ErrorCode, OomSplitChildren
from scripts.lexicon.runner.memory import (
    require_hard_cap_protection,
    run_startup_self_test,
)
from scripts.lexicon.runner.phase_cefr import (
    apply_sealed_cefr_to_engine_cache,
    load_sealed_cefr_map,
    sealed_cefr_precompute,
)
from scripts.lexicon.runner.phase_relations import (
    extract_and_close_relations,
    load_closed_relations_by_headword,
)
from scripts.lexicon.runner.side_db import (
    BallaReverseSideDb,
    DmklingerSideDb,
    KaikkiSideDb,
    build_balla_reverse_side_db,
    build_dmklinger_side_db,
    build_kaikki_side_db,
)
from scripts.lexicon.runner.split import child_chunk_id, split_on_oom
from scripts.lexicon.runner.stream_manifest import (
    StreamingCandidateWriter,
    stage_manifest_to_sqlite,
    stream_manifest_entries_json,
)
from scripts.lexicon.runner.worker import run_capped_worker

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lexicon" / "runner_pr1"


def _ensure_fixture() -> None:
    needed = (
        FIXTURE / "baseline.sha256",
        FIXTURE / "baseline_enriched.json",
        FIXTURE / "sources_slice.sqlite",
        FIXTURE / "slice_input.json",
        FIXTURE / "grac_frequency_slice.json",
    )
    if not all(path.is_file() for path in needed):
        from scripts.lexicon.runner.generate_pr1_fixture import main as gen

        assert gen() == 0
        assert all(path.is_file() for path in needed)


@pytest.fixture(scope="module")
def fixture_paths(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    _ensure_fixture()
    return {
        "input": FIXTURE / "slice_input.json",
        "sources": FIXTURE / "sources_slice.sqlite",
        "grac": FIXTURE / "grac_frequency_slice.json",
        "kaikki": FIXTURE / "kaikki_slice.json",
        "baseline": FIXTURE / "baseline_enriched.json",
        "baseline_sha": FIXTURE / "baseline.sha256",
    }


def test_memory_self_test_refuses_unproven_hard_cap() -> None:
    """Production must refuse hard-cap claims when enforcement is unproven."""
    from scripts.lexicon.runner.memory import EnforcementProof

    bad = EnforcementProof(kind="none", enforced=False, detail="unavailable", max_bytes=1)
    with pytest.raises(RuntimeError, match="hard memory cap self-test failed"):
        require_hard_cap_protection(bad)
    # Live OS probe: ``python -m scripts.lexicon.runner.memory_probe`` (PR evidence).
    # Unit tests avoid spawning — pre-commit pipes pytest through ``tail`` and Darwin
    # can SIGSEGV on subprocess teardown after an otherwise-green run.


def test_classify_oom_exitcodes() -> None:
    from scripts.lexicon.runner.memory import classify_oom_exit

    assert classify_oom_exit(-9) is True
    assert classify_oom_exit(137) is True
    assert classify_oom_exit(1) is False
    assert classify_oom_exit(0) is False
    assert classify_oom_exit(0, memory_error=True) is True


@pytest.mark.skipif(
    __import__("sys").platform == "darwin",
    reason="Darwin rejects RLIMIT_AS lowers; live probe is memory_probe CLI / Linux CI",
)
def test_injected_allocation_breach_classified_as_oom(tmp_path: Path) -> None:
    """OS hard limit must stop an injected allocation breach (not polling)."""
    proof = run_startup_self_test()
    if not proof.enforced:
        pytest.skip(f"OS memory limit not enforceable here: {proof.detail}")

    result = run_capped_worker(
        {
            "job": "inject_oom",
            "chunk_id": "oom-probe",
            "memory_high_bytes": proof.max_bytes,
            "memory_max_bytes": proof.max_bytes,
        },
        result_path=tmp_path / "oom_result.json",
        timeout_s=60.0,
    )
    assert result.error_code == ErrorCode.FAILED_OOM.value
    assert result.outcome == "failed_terminal"


def test_deterministic_oom_split_and_single_lemma_failed_oom() -> None:
    parent = ChunkSpec(chunk_id="parent", lemma_ids=["a", "b", "c", "d"])
    split = split_on_oom(parent)
    assert isinstance(split, OomSplitChildren)
    assert split.left.chunk_id == child_chunk_id("parent", 1, ["a", "b"])
    assert split.right.chunk_id == child_chunk_id("parent", 1, ["c", "d"])
    # Crash-retry stability
    again = split_on_oom(parent)
    assert isinstance(again, OomSplitChildren)
    assert again.left.chunk_id == split.left.chunk_id
    assert again.right.chunk_id == split.right.chunk_id

    single = ChunkSpec(chunk_id="leaf", lemma_ids=["only"])
    failed, code = split_on_oom(single)  # type: ignore[misc]
    assert code == ErrorCode.FAILED_OOM.value
    assert failed.state == ChunkState.FAILED_TERMINAL


def test_streaming_manifest_roundtrip(tmp_path: Path, fixture_paths: dict[str, Path]) -> None:
    staged = stage_manifest_to_sqlite(fixture_paths["input"], tmp_path / "staged.sqlite")
    assert staged["entry_count"] == 500
    entries = list(stream_manifest_entries_json(tmp_path / "staged.sqlite"))
    assert len(entries) == 500
    out = tmp_path / "candidate.json"
    with StreamingCandidateWriter(out, meta={"enrichment_generated": True}) as writer:
        for entry in entries:
            writer.write_entry(entry)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["enrichment_generated"] is True
    assert len(data["entries"]) == 500


def test_side_dbs_match_python_index_lookups(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    em._BALLA_SIDE_DB = None
    em._DMKLINGER_SIDE_DB = None
    em._DMKLINGER_INDEX = None
    em._BALLA_REVERSE_INDEX.clear()
    monkeypatch.setattr(em, "_vesum_word_analyses", lambda word: ((word, "noun"),))

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        py_balla = em._load_balla_reverse_index(conn)
        py_dmk = em._load_dmklinger_index(conn)
        balla_art = build_balla_reverse_side_db(
            conn,
            tmp_path / "balla.sqlite",
            candidate_keys=em._balla_reverse_candidate_keys,
            headword_fn=em._balla_reverse_headword,
            segment_fn=em._balla_reverse_definition_segments,
            token_re=em._BALLA_REVERSE_UKRAINIAN_TOKEN_RE,
        )
        dmk_art = build_dmklinger_side_db(
            conn,
            tmp_path / "dmk.sqlite",
            key_fn=em._dmklinger_key,
        )
    finally:
        conn.close()

    kaikki_art = build_kaikki_side_db(fixture_paths["kaikki"], tmp_path / "kaikki.sqlite")
    assert balla_art.sha256
    assert dmk_art.sha256
    assert kaikki_art.sha256

    balla = BallaReverseSideDb(Path(balla_art.path))
    dmk = DmklingerSideDb(Path(dmk_art.path))
    kaikki = KaikkiSideDb(Path(kaikki_art.path))
    try:
        for key, values in py_balla.items():
            assert balla.lookup(key) == values
        for key, values in py_dmk.items():
            assert dmk.lookup(key) == [(str(p or ""), str(t or "")) for p, t in values]
        raw_kaikki = json.loads(fixture_paths["kaikki"].read_text(encoding="utf-8"))
        for key, payload in raw_kaikki.items():
            assert kaikki.get(key) == payload
    finally:
        balla.close()
        dmk.close()
        kaikki.close()


def test_sealed_cefr_matches_legacy_prepare(tmp_path: Path, fixture_paths: dict[str, Path]) -> None:
    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    grac = json.loads(fixture_paths["grac"].read_text(encoding="utf-8"))
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = grac

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        em._prepare_cefr_estimates(conn, {"entries": entries})
        legacy = dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY)
        seal = sealed_cefr_precompute(
            lemmas=(str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=lambda lemma: em._puls_cefr(conn, lemma),
            grac_lookup_key_fn=em._grac_lookup_key,
            grac_cache=grac,
            output_db=tmp_path / "cefr.sqlite",
        )
    finally:
        conn.close()

    sealed = load_sealed_cefr_map(tmp_path / "cefr.sqlite")
    assert seal.row_count == len(legacy) == len(sealed)
    assert sealed == legacy
    # Band boundaries: ranks must map to the same A1..C1 bands.
    for key, row in sealed.items():
        assert row["level"] == legacy[key]["level"]
        assert row["rank"] == legacy[key]["rank"]
        assert row["total"] == legacy[key]["total"]


def test_relation_closure_matches_legacy_by_headword(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        has_sum11 = em._sum11_has_flag_columns(conn)
        manifest = {"entries": entries}
        legacy_syn = em._definition_pointer_relations_by_headword(
            conn, manifest, has_sum11_flags=has_sum11
        )
        legacy_ant = em._definition_antonym_relations_by_headword(
            conn, manifest, has_sum11_flags=has_sum11
        )
        headwords = em._manifest_headwords(manifest)
        extract_and_close_relations(
            entries=entries,
            extractors={
                "synonym": lambda entry: em._definition_pointer_relations(
                    conn, str(entry.get("lemma") or ""), has_sum11_flags=has_sum11
                ),
                "antonym": lambda entry: em._definition_antonym_relations(
                    conn, str(entry.get("lemma") or ""), has_sum11_flags=has_sum11
                ),
            },
            headwords=headwords,
            canonical_term_fn=em._canonical_synonym_term,
            vesum_valid_fn=em._vesum_valid_synonym,
            output_db=tmp_path / "rel.sqlite",
            reciprocal_kinds=frozenset({"synonym", "antonym"}),
        )
    finally:
        conn.close()

    closed_syn = load_closed_relations_by_headword(tmp_path / "rel.sqlite", kind="synonym")
    closed_ant = load_closed_relations_by_headword(tmp_path / "rel.sqlite", kind="antonym")
    assert closed_syn == legacy_syn
    assert closed_ant == legacy_ant


def test_500_lemma_equivalence_cefr_and_relations(
    fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Record-equivalent CEFR + reciprocal relations vs committed legacy baseline."""
    _ensure_fixture()
    baseline = json.loads(fixture_paths["baseline"].read_text(encoding="utf-8"))
    expected_sha = fixture_paths["baseline_sha"].read_text(encoding="utf-8").strip()
    actual_sha = hashlib.sha256(fixture_paths["baseline"].read_bytes()).hexdigest()
    assert actual_sha == expected_sha

    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    grac = json.loads(fixture_paths["grac"].read_text(encoding="utf-8"))
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = grac

    tmp_cefr = fixture_paths["input"].parent / "_tmp_cefr.sqlite"
    tmp_rel = fixture_paths["input"].parent / "_tmp_rel.sqlite"
    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        sealed_cefr_precompute(
            lemmas=(str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=lambda lemma: em._puls_cefr(conn, lemma),
            grac_lookup_key_fn=em._grac_lookup_key,
            grac_cache=grac,
            output_db=tmp_cefr,
        )
        apply_sealed_cefr_to_engine_cache(load_sealed_cefr_map(tmp_cefr), em._CEFR_ESTIMATE_LEVEL_BY_KEY)
        assert dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY) == baseline["cefr_estimates"]

        has_sum11 = em._sum11_has_flag_columns(conn)
        headwords = em._manifest_headwords({"entries": entries})
        extract_and_close_relations(
            entries=entries,
            extractors={
                "synonym": lambda entry: em._definition_pointer_relations(
                    conn, str(entry.get("lemma") or ""), has_sum11_flags=has_sum11
                ),
                "antonym": lambda entry: em._definition_antonym_relations(
                    conn, str(entry.get("lemma") or ""), has_sum11_flags=has_sum11
                ),
                "homonym": lambda entry: em._homonym_relations(
                    conn, str(entry.get("lemma") or "")
                ),
                "paronym": lambda entry: em._paronym_relations(
                    conn, str(entry.get("lemma") or "")
                ),
            },
            headwords=headwords,
            canonical_term_fn=em._canonical_synonym_term,
            vesum_valid_fn=em._vesum_valid_synonym,
            output_db=tmp_rel,
            reciprocal_kinds=frozenset({"synonym", "antonym"}),
        )
        for kind in ("synonym", "antonym", "homonym", "paronym"):
            closed = load_closed_relations_by_headword(tmp_rel, kind=kind)
            assert closed == baseline["relations"][kind], kind
    finally:
        conn.close()
        for path in (tmp_cefr, tmp_rel):
            if path.exists():
                path.unlink()
