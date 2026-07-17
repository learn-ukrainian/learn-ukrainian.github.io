"""Offline enrichment coordinator (streaming + sealed phases + capped workers + ledger)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import (
    ENGINE_VERSION,
    ChunkSpec,
    ChunkState,
    ErrorCode,
    LedgerStub,
    OomSplitChildren,
    PacketStub,
)
from scripts.lexicon.runner.ledger import (
    CasStatus,
    ChunkLedgerState,
    Ledger,
    UnitOutcome,
    compute_run_fingerprint,
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
    ledger_path: Path | None = None,
    run_id: str | None = None,
    force_new_run: bool = False,
    stop_after_chunks: int | None = None,
    owner_id: str | None = None,
) -> dict[str, Any]:
    """Run offline pipeline on a staged cohort with PR2 ledger fencing + resume.

    Leaf seal CAS lives in the ledger. Streaming assembly + publication archive
    is :func:`scripts.lexicon.runner.finalize.finalize_run` (PR4).
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

    side_digests = {
        "balla": balla_art.sha256,
        "dmklinger": dmk_art.sha256,
        "kaikki": kaikki_art.sha256,
    }
    fingerprint = compute_run_fingerprint(
        cohort_digest=str(staged["cohort_digest"]),
        side_db_digests=side_digests,
        cefr_versions={"seal": cefr_seal.seal_sha256, "algorithm": cefr_seal.algorithm_version},
        relation_versions={
            "seal": rel_seal.seal_sha256,
            "algorithm": rel_seal.algorithm_version,
        },
        enrichment_config={"chunk_size": chunk_size, "mode": "offline_slice"},
    )

    ledger_db = Path(ledger_path) if ledger_path is not None else work_dir / "ledger.sqlite"
    ledger = Ledger(ledger_db, owner_id=owner_id)
    ledger.open()
    try:
        active_run_id: str
        if run_id is not None:
            resumed = ledger.resume_run(run_id, fingerprint)
            if not resumed.ok:
                return {
                    "error": resumed.status.value,
                    "detail": resumed.detail,
                    "fingerprint": fingerprint,
                    "run_id": run_id,
                }
            active_run_id = str(resumed.run_id)
        else:
            started = ledger.start_run(
                fingerprint,
                force_new=force_new_run,
                config={"chunk_size": chunk_size},
            )
            if not started.ok:
                return {
                    "error": started.status.value,
                    "detail": started.detail,
                    "resumable_run_id": started.resumable_run_id,
                    "fingerprint": fingerprint,
                }
            active_run_id = str(started.run_id)

        ledger.set_phase(
            active_run_id,
            "cefr",
            "done",
            seal_sha256=cefr_seal.seal_sha256,
        )
        ledger.set_phase(
            active_run_id,
            "relations",
            "done",
            seal_sha256=rel_seal.seal_sha256,
        )

        handle = LedgerStub(run_id=active_run_id, fingerprint=fingerprint)
        _packet = PacketStub(packet_id="pr2-no-network")

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

        # Register units once; INSERT OR IGNORE keeps resume idempotent.
        ledger.register_chunk_work_units(
            active_run_id,
            [(c.chunk_id, c.lemma_ids) for c in chunks],
        )

        artifacts_root = work_dir / "artifacts"
        artifacts_root.mkdir(parents=True, exist_ok=True)
        entry_by_id = {str(e.get("url_slug") or e.get("lemma") or ""): e for e in entries}
        completed: dict[str, dict[str, Any]] = {}
        failed_terminal: list[dict[str, Any]] = []

        # Reload already-done lemma artifacts on resume.
        for chunk in chunks:
            chunk_row = ledger.get_chunk(active_run_id, chunk.chunk_id)
            if chunk_row is None:
                continue
            if str(chunk_row["state"]) in {
                ChunkLedgerState.DONE.value,
                ChunkLedgerState.SEALED.value,
            }:
                for lemma_id in chunk.lemma_ids:
                    artifact_file = artifacts_root / chunk.chunk_id / f"{lemma_id}.json"
                    if artifact_file.is_file():
                        completed[lemma_id] = json.loads(
                            artifact_file.read_text(encoding="utf-8")
                        )

        pending = list(chunks)
        processed_this_invocation = 0
        owner = ledger.owner_id

        while pending:
            if stop_after_chunks is not None and processed_this_invocation >= stop_after_chunks:
                break
            chunk = pending.pop(0)
            if chunk.state == ChunkState.SUPERSEDED:
                continue
            existing = ledger.get_chunk(active_run_id, chunk.chunk_id)
            if existing is not None and str(existing["state"]) in {
                ChunkLedgerState.DONE.value,
                ChunkLedgerState.SEALED.value,
                ChunkLedgerState.SUPERSEDED.value,
                ChunkLedgerState.FAILED_TERMINAL.value,
            }:
                continue

            claim = ledger.claim_unit(active_run_id, chunk.chunk_id, owner)
            if not claim.ok:
                if claim.status is CasStatus.ATTEMPT_CAP_EXHAUSTED:
                    failed_terminal.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "error_code": ErrorCode.ATTEMPT_CAP_EXHAUSTED.value,
                            "state": ChunkState.FAILED_TERMINAL.value,
                        }
                    )
                continue
            lease_gen = int(claim.lease_generation or 0)
            hb = ledger.heartbeat(active_run_id, chunk.chunk_id, owner, lease_gen)
            if not hb.ok:
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

                arts = enrich_chunk_payload(payload)
                for lemma_id, _digest in arts.items():
                    completed[lemma_id] = json.loads(
                        (artifact_dir / f"{lemma_id}.json").read_text(encoding="utf-8")
                    )
                result_hash = hashlib.sha256(
                    json.dumps(sorted(arts.items()), sort_keys=True).encode("utf-8")
                ).hexdigest()
                commit = ledger.commit_result(
                    active_run_id,
                    chunk.chunk_id,
                    owner,
                    lease_gen,
                    "done",
                    result_hash=result_hash,
                )
                if commit.ok:
                    processed_this_invocation += 1
                continue

            result = run_capped_worker(
                payload,
                result_path=work_dir / "results" / f"{chunk.chunk_id}.json",
            )
            if result.error_code == ErrorCode.FAILED_OOM.value:
                split_cas = ledger.commit_split(
                    active_run_id,
                    chunk.chunk_id,
                    owner,
                    lease_gen,
                )
                if not split_cas.ok:
                    failed_terminal.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "error_code": split_cas.status.value,
                            "message": split_cas.detail,
                        }
                    )
                    continue
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
                processed_this_invocation += 1
                continue
            if result.outcome != "done":
                ledger.commit_result(
                    active_run_id,
                    chunk.chunk_id,
                    owner,
                    lease_gen,
                    "failed_terminal",
                    error_code=result.error_code,
                )
                failed_terminal.append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "error_code": result.error_code,
                        "message": result.message,
                    }
                )
                processed_this_invocation += 1
                continue
            for lemma_id in chunk.lemma_ids:
                artifact_file = artifact_dir / f"{lemma_id}.json"
                if artifact_file.is_file():
                    completed[lemma_id] = json.loads(artifact_file.read_text(encoding="utf-8"))
            result_hash = hashlib.sha256(
                json.dumps(sorted(result.lemma_artifacts.items()), sort_keys=True).encode("utf-8")
            ).hexdigest()
            ledger.commit_result(
                active_run_id,
                chunk.chunk_id,
                owner,
                lease_gen,
                "done",
                result_hash=result_hash,
            )
            processed_this_invocation += 1

        interrupted = stop_after_chunks is not None and any(
            str((ledger.get_chunk(active_run_id, c.chunk_id) or {}).get("state"))
            in {
                ChunkLedgerState.PENDING.value,
                ChunkLedgerState.LEASED.value,
                UnitOutcome.RETRY_SCHEDULED.value,
            }
            for c in chunks
        )
        if not interrupted and not failed_terminal:
            # All registered leaf chunks done/sealed?
            pending_left = ledger.list_pending_chunk_ids(active_run_id)
            if not pending_left:
                ledger.mark_run_completed(active_run_id)

        with StreamingCandidateWriter(
            output_path,
            meta={
                "enrichment_generated": True,
                "runner_engine_version": ENGINE_VERSION,
                "cohort_digest": staged["cohort_digest"],
                "cefr_seal": cefr_seal.seal_sha256,
                "relations_seal": rel_seal.seal_sha256,
                "ledger_run_id": handle.run_id,
                "ledger_fingerprint": fingerprint,
                "side_db_digests": side_digests,
                "memory_self_test": {
                    "kind": proof.kind,
                    "enforced": proof.enforced,
                    "detail": proof.detail,
                },
                "failed_terminal": failed_terminal,
                "interrupted": interrupted,
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
            "run_id": active_run_id,
            "fingerprint": fingerprint,
            "ledger_path": str(ledger_db),
            "interrupted": interrupted,
            "processed_this_invocation": processed_this_invocation,
            "memory_proof": {
                "kind": proof.kind,
                "enforced": proof.enforced,
                "detail": proof.detail,
            },
        }
    finally:
        ledger.close()
