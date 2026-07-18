"""Offline reduce: network-cache raw ULIF envelopes → structured candidate (#5230).

Read-only against the durable network cache (no exclusive writer lock). Writes
go to a separate reduce ledger + artifact tree so the completed ``network_fetch``
run is never disturbed.

Resume model matches the fetch driver: per-lemma work units under phase
``offline_reduce``, claim → parse → atomic artifact write → commit.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import zlib
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import canonical_json
from scripts.lexicon.runner.ledger import CasStatus, Ledger, compute_run_fingerprint
from scripts.lexicon.runner.stream_manifest import StreamingCandidateWriter
from scripts.lexicon.runner.ulif_dictua_parse import (
    ULIF_NORMALIZER_VERSION,
    ULIF_PARSER_VERSION,
    ULIF_STRUCTURED_SCHEMA_VERSION,
    artifact_filename,
    candidate_entry_from_artifact,
    parse_dictua_envelope,
    summarize_artifacts,
)

PHASE = "offline_reduce"
DEFAULT_CHUNK_SIZE = 25
# Match fetch-phase lease budget so kill -9 resume does not sit for the 300s
# ledger default while a single orphaned lease blocks completion.
DEFAULT_REDUCE_LEASE_TTL_SECONDS = 60.0


def open_raw_cache_ro(path: Path) -> sqlite3.Connection:
    """Open network-cache.sqlite read-only without the exclusive writer lock."""
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    uri = f"file:{resolved.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.row_factory = sqlite3.Row
    return conn


def build_lemma_request_index(conn: sqlite3.Connection) -> dict[str, str]:
    """Map lemma → request_key from ``raw_cache.meta_json`` (no body decompress)."""
    index: dict[str, str] = {}
    for request_key, meta_json in conn.execute("SELECT request_key, meta_json FROM raw_cache"):
        try:
            meta = json.loads(str(meta_json or "{}"))
        except json.JSONDecodeError:
            continue
        lemma = meta.get("lemma") if isinstance(meta, dict) else None
        if lemma is None:
            continue
        index[str(lemma)] = str(request_key)
    return index


def load_raw_envelope(
    conn: sqlite3.Connection,
    request_key: str,
) -> tuple[dict[str, Any], str]:
    """Return (envelope_dict, body_sha256) for one request_key."""
    row = conn.execute(
        "SELECT body_zlib, body_sha256 FROM raw_cache WHERE request_key = ?",
        (request_key,),
    ).fetchone()
    if row is None:
        raise KeyError(request_key)
    body = zlib.decompress(bytes(row["body_zlib"]))
    envelope = json.loads(body.decode("utf-8"))
    if not isinstance(envelope, dict):
        raise ValueError(f"raw body for {request_key} is not a JSON object")
    return envelope, str(row["body_sha256"])


def cohort_lemmas(path: Path) -> tuple[list[str], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    lemmas = [line.strip() for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(set(lemmas)) != len(lemmas):
        raise RuntimeError("cohort contains duplicate lemma identifiers")
    return lemmas, digest


def _event(name: str, **fields: Any) -> None:
    print(
        json.dumps({"event": name, "at": time.time(), **fields}, ensure_ascii=False, sort_keys=True),
        flush=True,
    )


def _counts(ledger: Ledger, run_id: str) -> dict[str, int]:
    rows = (
        ledger._require()
        .execute(
            "SELECT state, COUNT(*) AS n FROM work_units WHERE run_id = ? AND phase = ? GROUP BY state",
            (run_id, PHASE),
        )
        .fetchall()
    )
    return {str(row["state"]): int(row["n"]) for row in rows}


def _next_pending(ledger: Ledger, run_id: str) -> str | None:
    row = (
        ledger._require()
        .execute(
            "SELECT unit_id FROM work_units WHERE run_id = ? AND phase = ? "
            "AND state IN ('pending', 'retry_scheduled') ORDER BY unit_id LIMIT 1",
            (run_id, PHASE),
        )
        .fetchone()
    )
    return None if row is None else str(row["unit_id"])


def _reclaim_foreign_leases(ledger: Ledger, run_id: str, owner_id: str) -> list[str]:
    """Single-writer reduce: free leases held by a dead previous coordinator.

    Only this process owns the reduce ledger, so foreign owners after kill -9
    are safe to reclaim immediately (network cache is independent/read-only).
    """
    conn = ledger._require()
    ts = time.time()
    rows = conn.execute(
        "SELECT unit_id, lease_generation FROM work_units "
        "WHERE run_id = ? AND phase = ? AND state = 'leased' "
        "AND (owner IS NULL OR owner != ?)",
        (run_id, PHASE, owner_id),
    ).fetchall()
    reclaimed: list[str] = []
    for row in rows:
        cur = conn.execute(
            "UPDATE work_units SET state = 'pending', owner = NULL, leased_until = NULL, "
            "updated_at = ? WHERE run_id = ? AND unit_id = ? AND phase = ? "
            "AND lease_generation = ? AND state = 'leased'",
            (ts, run_id, row["unit_id"], PHASE, int(row["lease_generation"])),
        )
        if cur.rowcount == 1:
            reclaimed.append(str(row["unit_id"]))
    return reclaimed


def _artifact_path(artifacts_root: Path, lemma: str) -> Path:
    return artifacts_root / artifact_filename(lemma)


def _write_artifact_atomic(path: Path, artifact: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(artifact) + "\n"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)
    return digest


def reduce_lemma(
    conn: sqlite3.Connection,
    *,
    lemma: str,
    request_key: str | None,
    artifacts_root: Path,
    include_raw_html: bool = False,
) -> tuple[dict[str, Any], str]:
    """Parse one lemma from the raw cache and write its artifact."""
    if not request_key:
        artifact = {
            "lemma": lemma,
            "lemma_id": lemma,
            "status": "not_found",
            "source_status": "missing_raw",
            "sections": {},
            "stages": [],
            "response_count": 0,
            "parser_version": ULIF_PARSER_VERSION,
            "normalizer_version": ULIF_NORMALIZER_VERSION,
            "schema_version": ULIF_STRUCTURED_SCHEMA_VERSION,
            "request_key": "",
            "body_sha256": "",
            "canonical_headword": lemma,
            "source_id": "ulif_dictua",
            "official_url": "https://lcorp.ulif.org.ua/dictua/",
        }
        digest = _write_artifact_atomic(_artifact_path(artifacts_root, lemma), artifact)
        return artifact, digest

    envelope, body_sha = load_raw_envelope(conn, request_key)
    artifact = parse_dictua_envelope(
        envelope,
        request_key=request_key,
        body_sha256=body_sha,
        include_raw_html=include_raw_html,
    )
    # Ensure lemma_id matches the cohort key (fetch envelope lemma == query).
    artifact["lemma_id"] = lemma
    if not artifact.get("lemma"):
        artifact["lemma"] = lemma
    digest = _write_artifact_atomic(_artifact_path(artifacts_root, lemma), artifact)
    return artifact, digest


def iter_done_artifacts(
    ledger: Ledger,
    run_id: str,
    artifacts_root: Path,
    lemmas: Sequence[str],
) -> Iterator[dict[str, Any]]:
    for lemma in lemmas:
        unit = ledger.get_work_unit(run_id, lemma, phase=PHASE)
        if unit is None or str(unit.get("state")) != "done":
            continue
        path = _artifact_path(artifacts_root, lemma)
        if not path.is_file():
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            yield obj


def write_candidate_export(
    *,
    output_path: Path,
    artifacts: Iterable[dict[str, Any]],
    meta: dict[str, Any],
) -> dict[str, Any]:
    count = 0
    with StreamingCandidateWriter(output_path, meta=meta) as writer:
        for artifact in artifacts:
            writer.write_entry(candidate_entry_from_artifact(artifact))
            count += 1
    return {"output_path": str(output_path), "entry_count": count}


def write_divergence_summary(
    path: Path,
    *,
    ulif_summary: dict[str, Any],
    baseline_path: Path | None,
    baseline_summary: dict[str, Any] | None,
    blocked_reason: str | None,
) -> dict[str, Any]:
    report = {
        "kind": "atlas-ulif-offline-reduce-divergence",
        "issue_refs": ["#5230", "#5331"],
        "ulif": ulif_summary,
        "baseline_path": str(baseline_path) if baseline_path else None,
        "baseline": baseline_summary,
        "blocked_reason": blocked_reason,
        "note": (
            "Aggregate CEFR/relations deltas require a live Atlas baseline manifest "
            "or finalized offline_enrich candidate. ULIF section coverage is always "
            "reported from reduce artifacts."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def summarize_baseline_manifest(path: Path, *, lemma_filter: set[str] | None = None) -> dict[str, Any]:
    """Cheap aggregate over a baseline manifest (JSON with entries or JSONL)."""
    from scripts.lexicon.runner.stream_manifest import stream_manifest_entries_json

    cefr_present = 0
    relation_edges = {"synonym": 0, "antonym": 0, "homonym": 0, "paronym": 0}
    ulif_present = 0
    total = 0
    for entry in stream_manifest_entries_json(path):
        lemma = str(entry.get("lemma") or entry.get("url_slug") or "")
        if lemma_filter is not None and lemma not in lemma_filter:
            continue
        total += 1
        if entry.get("cefr") or entry.get("cefr_level") or entry.get("estimated_cefr"):
            cefr_present += 1
        if entry.get("ulif_dictua") or entry.get("ulif"):
            ulif_present += 1
        relations = entry.get("relations")
        if isinstance(relations, list):
            for rel in relations:
                if not isinstance(rel, dict):
                    continue
                kind = str(rel.get("kind") or rel.get("type") or "").casefold()
                if kind in relation_edges:
                    relation_edges[kind] += 1
        elif isinstance(relations, dict):
            for kind, items in relations.items():
                key = str(kind).casefold()
                if key in relation_edges and isinstance(items, list):
                    relation_edges[key] += len(items)
    return {
        "entry_count": total,
        "cefr_present": cefr_present,
        "ulif_present": ulif_present,
        "relation_edge_counts": relation_edges,
    }


def reduce_offline_slice(
    *,
    network_cache: Path,
    work_dir: Path,
    cohort_path: Path | None = None,
    lemmas: Sequence[str] | None = None,
    cohort_digest: str | None = None,
    output_path: Path | None = None,
    divergence_path: Path | None = None,
    baseline_path: Path | None = None,
    ledger_path: Path | None = None,
    run_id: str | None = None,
    force_new_run: bool = False,
    max_lemmas: int | None = None,
    include_raw_html: bool = False,
    owner_id: str | None = None,
    expected_cohort_sha256: str | None = None,
    expected_cohort_count: int | None = None,
    lease_ttl_seconds: float = DEFAULT_REDUCE_LEASE_TTL_SECONDS,
) -> dict[str, Any]:
    """Resumable offline reduce over a cohort against the durable network cache."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    artifacts_root = work_dir / "artifacts" / "ulif_reduce"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    if lemmas is None:
        if cohort_path is None:
            raise ValueError("cohort_path or lemmas is required")
        lemma_list, digest = cohort_lemmas(Path(cohort_path))
        if expected_cohort_sha256 and digest != expected_cohort_sha256:
            raise RuntimeError(f"cohort sha mismatch: got {digest}, expected {expected_cohort_sha256}")
        if expected_cohort_count is not None and len(lemma_list) != expected_cohort_count:
            raise RuntimeError(f"cohort count mismatch: got {len(lemma_list)}, expected {expected_cohort_count}")
    else:
        lemma_list = [str(x) for x in lemmas]
        digest = cohort_digest or hashlib.sha256("\n".join(lemma_list).encode("utf-8")).hexdigest()

    fingerprint = compute_run_fingerprint(
        cohort_digest=digest,
        enrichment_config={
            "phase": PHASE,
            "parser_version": ULIF_PARSER_VERSION,
            "schema_version": ULIF_STRUCTURED_SCHEMA_VERSION,
            "normalizer_version": ULIF_NORMALIZER_VERSION,
        },
        network_versions={"cache": "raw_cache_ro", "source": "ulif_dictua"},
    )

    ledger_db = Path(ledger_path) if ledger_path else work_dir / "reduce-ledger.sqlite"
    cache_conn = open_raw_cache_ro(network_cache)
    try:
        index = build_lemma_request_index(cache_conn)
        ledger = Ledger(
            ledger_db,
            owner_id=owner_id,
            lease_ttl_seconds=float(lease_ttl_seconds),
        )
        ledger.open()
        try:
            if run_id is not None:
                resumed = ledger.resume_run(run_id, fingerprint)
                if not resumed.ok:
                    return {
                        "error": resumed.status.value,
                        "detail": resumed.detail,
                        "run_id": run_id,
                        "fingerprint": fingerprint,
                    }
                active_run_id = str(resumed.run_id)
                lifecycle = "resumed"
            else:
                existing = ledger.find_incomplete_by_fingerprint(fingerprint)
                if existing and not force_new_run:
                    resumed = ledger.resume_run(existing, fingerprint)
                    if not resumed.ok:
                        return {
                            "error": resumed.status.value,
                            "detail": resumed.detail,
                            "resumable_run_id": existing,
                            "fingerprint": fingerprint,
                        }
                    active_run_id = existing
                    lifecycle = "resumed"
                else:
                    started = ledger.start_run(
                        fingerprint,
                        force_new=force_new_run,
                        config={
                            "phase": PHASE,
                            "cohort_sha256": digest,
                            "cohort_count": len(lemma_list),
                            "parser_version": ULIF_PARSER_VERSION,
                            "schema_version": ULIF_STRUCTURED_SCHEMA_VERSION,
                        },
                    )
                    if not started.ok or not started.run_id:
                        return {
                            "error": started.status.value,
                            "detail": started.detail,
                            "resumable_run_id": started.resumable_run_id,
                            "fingerprint": fingerprint,
                        }
                    active_run_id = str(started.run_id)
                    lifecycle = "started"

            ledger.set_phase(active_run_id, PHASE, "running")
            for lemma in lemma_list:
                ledger.register_work_unit(active_run_id, lemma, unit_kind="lemma", phase=PHASE)
            foreign = _reclaim_foreign_leases(ledger, active_run_id, ledger.owner_id)
            expired = ledger.reclaim_expired(active_run_id)
            if foreign or expired:
                _event(
                    "startup_reclaim",
                    run_id=active_run_id,
                    foreign=len(foreign),
                    expired=len(expired),
                )
            _event(
                "reduce_ready",
                lifecycle=lifecycle,
                run_id=active_run_id,
                fingerprint=fingerprint,
                cohort_count=len(lemma_list),
                cache_index_size=len(index),
                counts=_counts(ledger, active_run_id),
            )

            processed = 0
            while True:
                reclaimed = ledger.reclaim_expired(active_run_id)
                if reclaimed:
                    _event(
                        "leases_reclaimed",
                        run_id=active_run_id,
                        count=len(reclaimed),
                        units=reclaimed[:10],
                    )
                lemma = _next_pending(ledger, active_run_id)
                if lemma is None:
                    counts = _counts(ledger, active_run_id)
                    if counts.get("leased", 0):
                        # Wait for the soonest orphaned lease rather than spinning.
                        row = (
                            ledger._require()
                            .execute(
                                "SELECT MIN(leased_until) AS until FROM work_units "
                                "WHERE run_id = ? AND phase = ? AND state = 'leased' "
                                "AND leased_until IS NOT NULL",
                                (active_run_id, PHASE),
                            )
                            .fetchone()
                        )
                        until = float(row["until"]) if row and row["until"] is not None else time.time()
                        wait_s = max(0.05, min(until - time.time() + 0.05, 5.0))
                        _event(
                            "await_lease_expiry",
                            run_id=active_run_id,
                            wait_seconds=wait_s,
                            leased=counts.get("leased", 0),
                        )
                        time.sleep(wait_s)
                        continue
                    if not counts.get("failed_terminal", 0):
                        ledger.set_phase(active_run_id, PHASE, "done")
                        ledger.mark_run_completed(active_run_id)
                        _event("reduce_completed", run_id=active_run_id, counts=counts)
                    else:
                        _event(
                            "reduce_terminal_failures",
                            run_id=active_run_id,
                            counts=counts,
                        )
                    break

                claim = ledger.claim_unit(active_run_id, lemma, ledger.owner_id, phase=PHASE)
                if not claim.ok:
                    if claim.status is CasStatus.ATTEMPT_CAP_EXHAUSTED:
                        _event(
                            "attempt_cap_exhausted",
                            run_id=active_run_id,
                            lemma=lemma,
                        )
                    continue
                assert claim.lease_generation is not None
                try:
                    _artifact, result_hash = reduce_lemma(
                        cache_conn,
                        lemma=lemma,
                        request_key=index.get(lemma),
                        artifacts_root=artifacts_root,
                        include_raw_html=include_raw_html,
                    )
                    commit = ledger.commit_result(
                        active_run_id,
                        lemma,
                        ledger.owner_id,
                        claim.lease_generation,
                        "done",
                        result_hash=result_hash,
                        phase=PHASE,
                    )
                    outcome = "done" if commit.ok else commit.status.value
                except Exception as exc:
                    commit = ledger.commit_result(
                        active_run_id,
                        lemma,
                        ledger.owner_id,
                        claim.lease_generation,
                        "failed_terminal",
                        error_code="reduce_error",
                        phase=PHASE,
                    )
                    outcome = "failed_terminal"
                    _event(
                        "lemma_reduce_error",
                        run_id=active_run_id,
                        lemma=lemma,
                        error=str(exc),
                        committed=commit.status.value,
                    )
                processed += 1
                _event(
                    "lemma_reduced",
                    run_id=active_run_id,
                    lemma=lemma,
                    outcome=outcome,
                    counts=_counts(ledger, active_run_id),
                )
                if max_lemmas is not None and processed >= max_lemmas:
                    _event(
                        "invocation_limit_reached",
                        run_id=active_run_id,
                        processed=processed,
                        counts=_counts(ledger, active_run_id),
                    )
                    break

            # Export + summary only when every registered unit is done (or for slice tests).
            counts = _counts(ledger, active_run_id)
            all_done = counts.get("done", 0) == len(lemma_list) and not counts.get("failed_terminal", 0)
            done_arts = list(iter_done_artifacts(ledger, active_run_id, artifacts_root, lemma_list))
            ulif_summary = summarize_artifacts(done_arts)

            out_candidate = output_path or (work_dir / "candidate-ulif-reduce.json")
            export_meta = {
                "enrichment_generated": False,
                "phase": PHASE,
                "parser_version": ULIF_PARSER_VERSION,
                "schema_version": ULIF_STRUCTURED_SCHEMA_VERSION,
                "cohort_digest": digest,
                "ledger_run_id": active_run_id,
                "ledger_fingerprint": fingerprint,
                "network_cache": str(Path(network_cache).resolve()),
                "ulif_summary": ulif_summary,
                "complete": all_done,
            }
            export_info = write_candidate_export(
                output_path=out_candidate,
                artifacts=done_arts,
                meta=export_meta,
            )

            baseline_summary = None
            blocked_reason = None
            if baseline_path is not None and Path(baseline_path).is_file():
                baseline_summary = summarize_baseline_manifest(
                    Path(baseline_path),
                    lemma_filter=set(lemma_list),
                )
            else:
                blocked_reason = (
                    "no baseline manifest provided or path missing; "
                    "ULIF section aggregates only (#5331 CEFR/relations deltas deferred)"
                )

            out_div = divergence_path or (work_dir / "divergence-summary.json")
            div_report = write_divergence_summary(
                out_div,
                ulif_summary=ulif_summary,
                baseline_path=Path(baseline_path) if baseline_path else None,
                baseline_summary=baseline_summary,
                blocked_reason=blocked_reason,
            )

            return {
                "run_id": active_run_id,
                "fingerprint": fingerprint,
                "lifecycle": lifecycle,
                "cohort_digest": digest,
                "cohort_count": len(lemma_list),
                "processed_this_invocation": processed,
                "counts": counts,
                "complete": all_done,
                "ulif_summary": ulif_summary,
                "candidate": export_info,
                "divergence": {
                    "path": str(out_div),
                    "blocked_reason": blocked_reason,
                    "summary": div_report,
                },
                "ledger_path": str(ledger_db),
                "artifacts_root": str(artifacts_root),
            }
        finally:
            ledger.close()
    finally:
        cache_conn.close()
