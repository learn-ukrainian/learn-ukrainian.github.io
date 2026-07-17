"""Offline enrichment coordinator for PR1 (streaming + sealed phases + capped workers)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import (
    ChunkSpec,
    ChunkState,
    ErrorCode,
    LedgerStub,
    OomSplitChildren,
    PacketStub,
    SealStub,
)
from scripts.lexicon.runner.memory import (
    MemoryPolicy,
    require_hard_cap_protection,
    run_startup_self_test,
)
from scripts.lexicon.runner.phase_cefr import cefr_candidate_words, sealed_cefr_precompute
from scripts.lexicon.runner.phase_relations import extract_and_close_relations
from scripts.lexicon.runner.side_db import (
    build_balla_reverse_side_db,
    build_dmklinger_side_db,
    build_kaikki_side_db,
)
from scripts.lexicon.runner.split import mark_parent_superseded, split_on_oom
from scripts.lexicon.runner.stream_manifest import (
    StreamingCandidateWriter,
    stage_manifest_to_sqlite,
    stream_manifest_entries_sqlite,
)
from scripts.lexicon.runner.worker import run_capped_worker


def enrich_offline_slice(
    *,
    manifest_path: Path,
    sources_db: Path,
    kaikki_json: Path,
    work_dir: Path,
    output_path: Path,
    grac_cache: dict[str, Any],
    memory_policy: MemoryPolicy | None = None,
    chunk_size: int = 50,
    require_memory_self_test: bool = True,
    skip_workers: bool = False,
) -> dict[str, Any]:
    """Run PR1 offline pipeline on a staged cohort.

    PR2 ledger / PR3 packets / PR4 seals remain stubs — this function performs
    the engine isolation work and writes a streaming candidate.
    """
    from scripts.lexicon import enrich_manifest as em

    work_dir.mkdir(parents=True, exist_ok=True)
    policy = memory_policy or MemoryPolicy()

    proof = run_startup_self_test(test_max_bytes=min(64 * 1024 * 1024, policy.max_bytes))
    if require_memory_self_test:
        require_hard_cap_protection(proof)

    staged = stage_manifest_to_sqlite(manifest_path, work_dir / "staged_manifest.sqlite")
    entries = list(stream_manifest_entries_sqlite(Path(staged["path"])))

    sources = sqlite3.connect(f"file:{sources_db.resolve().as_posix()}?mode=ro", uri=True)
    try:
        balla_art = build_balla_reverse_side_db(
            sources,
            work_dir / "side" / "balla_reverse.sqlite",
            candidate_keys=em._balla_reverse_candidate_keys,
            headword_fn=em._balla_reverse_headword,
            segment_fn=em._balla_reverse_definition_segments,
            token_re=em._BALLA_REVERSE_UKRAINIAN_TOKEN_RE,
        )
        dmk_art = build_dmklinger_side_db(
            sources,
            work_dir / "side" / "dmklinger.sqlite",
            key_fn=em._dmklinger_key,
        )
        kaikki_art = build_kaikki_side_db(kaikki_json, work_dir / "side" / "kaikki.sqlite")

        def puls_fn(lemma: str) -> dict[str, str] | None:
            return em._puls_cefr(sources, lemma)

        # Warm GRAC before sealing — mirrors legacy ``_prepare_cefr_estimates``.
        # Without this, missing cache keys silently drop out of quantile ranking.
        unique_words = cefr_candidate_words(
            (str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=puls_fn,
            grac_lookup_key_fn=em._grac_lookup_key,
        )
        em._ensure_grac_frequency_cache(unique_words)
        # After warm, prefer the shared cache (ensure mutates it in place).
        # Caller-injected dicts (tests) are merged so pre-seeded ranks survive.
        warmed_grac = em._load_grac_frequency_cache()
        if grac_cache is not warmed_grac:
            for word in unique_words:
                if word not in grac_cache and word in warmed_grac:
                    grac_cache[word] = warmed_grac[word]
            effective_grac = grac_cache
        else:
            effective_grac = warmed_grac

        cefr_seal = sealed_cefr_precompute(
            lemmas=(str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=puls_fn,
            grac_lookup_key_fn=em._grac_lookup_key,
            grac_cache=effective_grac,
            output_db=work_dir / "seals" / "cefr.sqlite",
        )

        headwords = em._manifest_headwords({"entries": entries})
        has_sum11 = em._sum11_has_flag_columns(sources)

        def syn_extractor(entry: dict[str, Any]) -> list[dict[str, Any]]:
            return em._definition_pointer_relations(
                sources,
                str(entry.get("lemma") or ""),
                has_sum11_flags=has_sum11,
            )

        def ant_extractor(entry: dict[str, Any]) -> list[dict[str, Any]]:
            return em._definition_antonym_relations(
                sources,
                str(entry.get("lemma") or ""),
                has_sum11_flags=has_sum11,
            )

        def hom_extractor(entry: dict[str, Any]) -> list[dict[str, Any]]:
            return em._homonym_relations(sources, str(entry.get("lemma") or ""))

        def par_extractor(entry: dict[str, Any]) -> list[dict[str, Any]]:
            return em._paronym_relations(sources, str(entry.get("lemma") or ""))

        rel_seal = extract_and_close_relations(
            entries=entries,
            extractors={
                "synonym": syn_extractor,
                "antonym": ant_extractor,
                "homonym": hom_extractor,
                "paronym": par_extractor,
            },
            headwords=headwords,
            canonical_term_fn=em._canonical_synonym_term,
            vesum_valid_fn=em._vesum_valid_synonym,
            output_db=work_dir / "seals" / "relations.sqlite",
            reciprocal_kinds=frozenset({"synonym", "antonym"}),
        )
    finally:
        sources.close()

    # PR2/3/4 stubs recorded for fingerprint/docs — not functional.
    ledger = LedgerStub(run_id="pr1-offline", fingerprint=str(staged["cohort_digest"]))
    _packet = PacketStub(packet_id="pr1-no-network")
    _seal = SealStub(chunk_id="pr1-coordinator")

    lemma_ids = [str(e.get("url_slug") or e.get("lemma") or "") for e in entries]
    chunks: list[ChunkSpec] = []
    for i in range(0, len(lemma_ids), chunk_size):
        part = lemma_ids[i : i + chunk_size]
        chunks.append(
            ChunkSpec(
                chunk_id=f"chunk-{i // chunk_size:04d}",
                lemma_ids=part,
                state=ChunkState.PENDING,
            )
        )

    artifacts_root = work_dir / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    entry_by_id = {str(e.get("url_slug") or e.get("lemma") or ""): e for e in entries}
    completed: dict[str, dict[str, Any]] = {}
    failed_terminal: list[dict[str, Any]] = []

    pending = list(chunks)
    while pending:
        chunk = pending.pop(0)
        if chunk.state == ChunkState.SUPERSEDED:
            continue
        chunk_entries = [entry_by_id[lid] for lid in chunk.lemma_ids if lid in entry_by_id]
        entries_path = work_dir / "chunks" / f"{chunk.chunk_id}.json"
        entries_path.parent.mkdir(parents=True, exist_ok=True)
        entries_path.write_text(
            json.dumps(chunk_entries, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifact_dir = artifacts_root / chunk.chunk_id
        payload = {
            "job": "enrich",
            "chunk_id": chunk.chunk_id,
            "entries_path": str(entries_path),
            "sources_db": str(sources_db),
            "cefr_seal_db": str(work_dir / "seals" / "cefr.sqlite"),
            "relations_seal_db": str(work_dir / "seals" / "relations.sqlite"),
            "balla_side_db": balla_art.path,
            "dmklinger_side_db": dmk_art.path,
            "kaikki_side_db": kaikki_art.path,
            "artifact_dir": str(artifact_dir),
            "memory_high_bytes": policy.high_bytes,
            "memory_max_bytes": policy.max_bytes,
        }
        if skip_workers:
            from scripts.lexicon.runner.worker_enrich import enrich_chunk_payload

            # Still apply sealed phases + side DBs, but in-process (tests without
            # spawning). Memory self-test already ran above.
            arts = enrich_chunk_payload(payload)
            for lemma_id, _digest in arts.items():
                completed[lemma_id] = json.loads(
                    (artifact_dir / f"{lemma_id}.json").read_text(encoding="utf-8")
                )
            continue

        result = run_capped_worker(
            payload,
            result_path=work_dir / "results" / f"{chunk.chunk_id}.json",
        )
        if result.error_code == ErrorCode.FAILED_OOM.value:
            split_result = split_on_oom(chunk)
            if isinstance(split_result, OomSplitChildren):
                mark_parent_superseded(chunk)
                pending.extend([split_result.left, split_result.right])
            else:
                failed_chunk, code = split_result
                failed_terminal.append(
                    {
                        "chunk_id": failed_chunk.chunk_id,
                        "lemma_ids": failed_chunk.lemma_ids,
                        "error_code": code,
                        "state": ChunkState.FAILED_TERMINAL.value,
                    }
                )
            continue
        if result.outcome != "done":
            failed_terminal.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "error_code": result.error_code,
                    "message": result.message,
                }
            )
            continue
        for lemma_id in chunk.lemma_ids:
            artifact_file = artifact_dir / f"{lemma_id}.json"
            if artifact_file.is_file():
                completed[lemma_id] = json.loads(artifact_file.read_text(encoding="utf-8"))

    with StreamingCandidateWriter(
        output_path,
        meta={
            "enrichment_generated": True,
            "runner_engine_version": "runner-pr1-v1",
            "cohort_digest": staged["cohort_digest"],
            "cefr_seal": cefr_seal.seal_sha256,
            "relations_seal": rel_seal.seal_sha256,
            "ledger_stub_run_id": ledger.run_id,
            "side_db_digests": {
                "balla": balla_art.sha256,
                "dmklinger": dmk_art.sha256,
                "kaikki": kaikki_art.sha256,
            },
            "memory_self_test": {
                "kind": proof.kind,
                "enforced": proof.enforced,
                "detail": proof.detail,
            },
            "failed_terminal": failed_terminal,
        },
    ) as writer:
        for lemma_id in lemma_ids:
            if lemma_id in completed:
                writer.write_entry(completed[lemma_id])
            elif lemma_id in entry_by_id:
                writer.write_entry(entry_by_id[lemma_id])

    return {
        "cohort_digest": staged["cohort_digest"],
        "entry_count": staged["entry_count"],
        "cefr_seal": cefr_seal.seal_sha256,
        "relations_seal": rel_seal.seal_sha256,
        "completed": len(completed),
        "failed_terminal": failed_terminal,
        "output_path": str(output_path),
        "memory_proof": {
            "kind": proof.kind,
            "enforced": proof.enforced,
            "detail": proof.detail,
        },
    }
