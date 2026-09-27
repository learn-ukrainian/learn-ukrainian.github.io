#!/usr/bin/env python3
"""ULDR Phase 3.2: UA-GEC Context Extraction & Curriculum Stratification (Issue #8006).

Extracts authentic, human-annotated calques (F/Calque) and collocations (F/Collocation)
from sources.db table ua_gec_errors within original context.
Strictly excludes the official UA-GEC test split (1,159 test error records).
Enforces curriculum caps: prepositional government (G/Case) capped at <= 25% of total training records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import jsonschema

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    extract_root_family,
    is_phase30_uagec_heldout_doc,
)
from scripts.projects.open_model_data.phase3_mined_candidate_guards import (
    g_case_ratio,
    is_grounded_uagec_sentence,
    is_synthetic_uagec_wrapper,
    verify_mined_manifest,
)


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = REPO_ROOT / rel_path
    if local_p.exists() and local_p.stat().st_size > 0:
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and main_p.stat().st_size > 0:
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "mined"
DEFAULT_GOLD_FILE = REPO_ROOT / "registry" / "ua-gec-gold" / "ua-gec-gold.json"
DEFAULT_SCHEMA_FILE = (
    REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_decolonization_mined_candidates.schema.json"
)


def load_curated_gold_contexts(gold_file: Path) -> dict[int, dict[str, Any]]:
    """Load pre-curated full contexts from ua-gec-gold.json if available."""
    if not gold_file.is_file():
        return {}
    try:
        with gold_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        return {item["ua_gec_error_id"]: item for item in items if "ua_gec_error_id" in item}
    except Exception:
        return {}


_UAGEC_SENTENCE_CACHE: dict[tuple[str, str, str, str], list[str]] = {}


def _uagec_checkout_paths(checkout: Path, partition: str, doc_id: str, annotator_id: str) -> tuple[Path, Path]:
    layer, split = partition.split("/", 1)
    annotated = checkout / "data" / layer / split / "annotated" / f"{doc_id}.a{annotator_id}.ann"
    source = checkout / "data" / layer / split / "source-sentences" / f"{doc_id}.src.txt"
    return annotated, source


def lookup_uagec_source_sentence(
    checkout: Path | None,
    partition: str,
    doc_id: str,
    annotator_id: str,
    error: str,
    *,
    correct: str = "",
) -> str | None:
    """Return the original UA-GEC source sentence, or None (fail closed — never invent)."""
    if checkout is None or not checkout.is_dir():
        return None
    lined = _lookup_uagec_source_sentence_lines(checkout, partition, doc_id, annotator_id, error)
    if lined:
        return lined
    try:
        from scripts.projects.open_model_data.phase3_ua_gec_complete_context import (
            _normalize_edit_text,
            _source_sentences,
            parse_annotated_document,
        )
    except Exception:
        return None

    annotated, source = _uagec_checkout_paths(checkout, partition, doc_id, annotator_id)
    if not annotated.is_file() or not source.is_file():
        return _lookup_uagec_source_sentence_lines(checkout, partition, doc_id, annotator_id, error)
    try:
        parsed = parse_annotated_document(annotated.read_text(encoding="utf-8", errors="strict"))
        source_document = source.read_text(encoding="utf-8", errors="strict")
        sentences = _source_sentences(parsed, source_document)
        want_error = _normalize_edit_text(error)
        want_correct = _normalize_edit_text(correct) if correct else ""
        matches = [item for item in parsed.annotations if _normalize_edit_text(item.error) == want_error]
        if want_correct:
            exact = [item for item in matches if _normalize_edit_text(item.correction) == want_correct]
            if exact:
                matches = exact
        if not matches:
            return _lookup_uagec_source_sentence_lines(checkout, partition, doc_id, annotator_id, error)
        annotation = matches[0]
        for sentence in sentences:
            contains = sentence.source_start <= annotation.source_start and annotation.source_end <= sentence.source_end
            if contains:
                text = parsed.source_text[sentence.source_start : sentence.source_end].strip()
                if is_grounded_uagec_sentence(text, error):
                    return text
        retrieved = source_document[annotation.source_start : annotation.source_end]
        if is_grounded_uagec_sentence(retrieved, error):
            return retrieved.strip()
    except Exception:
        pass
    return _lookup_uagec_source_sentence_lines(checkout, partition, doc_id, annotator_id, error)


def _lookup_uagec_source_sentence_lines(
    checkout: Path,
    partition: str,
    doc_id: str,
    annotator_id: str,
    error: str,
) -> str | None:
    cache_key = (str(checkout.resolve()), partition, doc_id, str(annotator_id))
    lines = _UAGEC_SENTENCE_CACHE.get(cache_key)
    if lines is None:
        _annotated, source = _uagec_checkout_paths(checkout, partition, doc_id, annotator_id)
        if not source.is_file():
            return None
        try:
            lines = source.read_text(encoding="utf-8", errors="strict").splitlines()
        except OSError:
            return None
        _UAGEC_SENTENCE_CACHE[cache_key] = lines
    hits = [line.strip() for line in lines if error and error in line]
    if len(hits) == 1 and is_grounded_uagec_sentence(hits[0], error):
        return hits[0]
    return None


def resolve_uagec_sentence_context(
    rec: Mapping[str, Any],
    gold_contexts: Mapping[int, Mapping[str, Any]],
    checkout: Path | None,
) -> str | None:
    """Fail-closed original sentence: gold excerpt, then pinned UA-GEC checkout. No wrappers."""
    gold_match = gold_contexts.get(rec["error_id"])
    if gold_match:
        excerpt = (gold_match.get("source_excerpt") or "").strip()
        if excerpt and is_grounded_uagec_sentence(excerpt, rec["error"]):
            return excerpt
        if excerpt and not is_synthetic_uagec_wrapper(excerpt) and rec["error"] in excerpt:
            return excerpt
    return lookup_uagec_source_sentence(
        checkout,
        rec["partition"],
        rec["doc_id"],
        str(rec["annotator_id"]),
        rec["error"],
        correct=rec.get("correct", ""),
    )


def mine_uagec_calques(
    sources_db: Path,
    vesum_db: Path,
    output_dir: Path,
    gold_file: Path = DEFAULT_GOLD_FILE,
    ua_gec_root: Path | None = None,
) -> dict[str, Any]:
    """Mine UA-GEC calques and collocations with test-split + Phase 3.0 firewall and G/Case cap."""
    output_dir.mkdir(parents=True, exist_ok=True)
    uagec_out_file = output_dir / "uagec_mined_calques.jsonl"
    gold_contexts = load_curated_gold_contexts(gold_file)

    s_conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    v_conn = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
    sc = s_conn.cursor()
    vc = v_conn.cursor()

    def get_lemma(word: str) -> str:
        clean = word.strip().lower()
        res = vc.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (clean,)).fetchone()
        return res[0] if res else clean

    all_rows = sc.execute(
        "SELECT id, error, correct, error_type, doc_id, annotator_id, partition, is_native, source_lang "
        "FROM ua_gec_errors ORDER BY id"
    ).fetchall()

    # 1. Identify and quarantine protected UA-GEC test split
    test_doc_ids = set()
    test_rows_count = 0
    total_available_calques = 0
    total_available_collocations = 0
    total_available_cases = 0

    for r in all_rows:
        part = r[6]
        doc_id = r[4]
        etype = r[3]
        if etype == "F/Calque":
            total_available_calques += 1
        elif etype == "F/Collocation":
            total_available_collocations += 1
        elif etype == "G/Case":
            total_available_cases += 1

        if "test" in part.lower():
            test_doc_ids.add(doc_id)
            test_rows_count += 1

    total_available_calque_colloc = total_available_calques + total_available_collocations

    # 2. Extract train candidate rows
    train_calques = []
    train_collocations = []
    train_cases = []

    for r in all_rows:
        rid, err, corr, etype, doc_id, ann_id, part, is_nat, src_lang = r
        if doc_id in test_doc_ids or "test" in part.lower():
            # Protected official test split: 100% excluded
            continue
        if is_phase30_uagec_heldout_doc(str(doc_id)):
            # Phase 3.0 pre-extraction firewall: sha256(uagec_doc:{doc_id})[:8] % 10 >= 8
            continue

        err_s = (err or "").strip()
        corr_s = (corr or "").strip()
        if not err_s or not corr_s:
            continue

        rec = {
            "error_id": rid,
            "error": err_s,
            "correct": corr_s,
            "error_type": etype,
            "doc_id": doc_id,
            "annotator_id": ann_id,
            "partition": part,
            "is_native": bool(is_nat),
            "source_lang": src_lang or "",
        }

        if etype == "F/Calque":
            train_calques.append(rec)
        elif etype == "F/Collocation":
            train_collocations.append(rec)
        elif etype == "G/Case":
            train_cases.append(rec)

    def _build_record(rec: dict[str, Any]) -> dict[str, Any] | None:
        sentence_ctx = resolve_uagec_sentence_context(rec, gold_contexts, ua_gec_root)
        if not sentence_ctx or not is_grounded_uagec_sentence(sentence_ctx, rec["error"]):
            return None
        first_corr_word = re.split(r"\s+", rec["correct"])[0].strip(",.:;!?")
        corr_lemma = get_lemma(first_corr_word)
        root_fam = extract_root_family(corr_lemma) or extract_root_family(first_corr_word)
        if not root_fam or len(root_fam) < 2:
            return None
        return {
            "record_id": f"uagec.{rec['error_id']}",
            "error_id": rec["error_id"],
            "error": rec["error"],
            "correct": rec["correct"],
            "error_type": rec["error_type"],
            "doc_id": rec["doc_id"],
            "annotator_id": rec["annotator_id"],
            "partition": rec["partition"],
            "is_native": rec["is_native"],
            "source_lang": rec["source_lang"],
            "derivational_family": root_fam,
            "sentence_context": sentence_ctx,
            "curriculum_admission": "ADMITTED",
        }

    grounded_calques = [built for rec in train_calques + train_collocations if (built := _build_record(rec))]
    grounded_cases = [built for rec in train_cases if (built := _build_record(rec))]
    # N_case / (calques + N_case) <= 0.25 => N_case <= calques / 3 (integer, no rounding hide)
    max_admitted_cases = len(grounded_calques) // 3
    admitted_cases = grounded_cases[:max_admitted_cases]
    mined_records = grounded_calques + admitted_cases

    s_conn.close()
    v_conn.close()

    # Write output
    with uagec_out_file.open("w", encoding="utf-8") as f:
        for rec in mined_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total_admitted = len(mined_records)
    admitted_ratio = g_case_ratio(len(admitted_cases), total_admitted)

    return {
        "total_calque_collocation_available": total_available_calque_colloc,
        "calque_count": total_available_calques,
        "collocation_count": total_available_collocations,
        "protected_test_split_excluded": test_rows_count,
        "train_calque_collocation_extracted": len(grounded_calques),
        "g_case_total": total_available_cases,
        "g_case_admitted": len(admitted_cases),
        "g_case_admitted_ratio": admitted_ratio,
        "mined_records_count": len(mined_records),
        "sha256": hashlib.sha256(uagec_out_file.read_bytes()).hexdigest(),
    }


def repair_existing_uagec_file(
    output_dir: Path,
    gold_file: Path = DEFAULT_GOLD_FILE,
    ua_gec_root: Path | None = None,
) -> dict[str, Any]:
    """Rewrite committed UA-GEC JSONL: drop held-out docs, wrappers, and ungrounded rows."""
    uagec_out_file = output_dir / "uagec_mined_calques.jsonl"
    gold_contexts = load_curated_gold_contexts(gold_file)
    incoming: list[dict[str, Any]] = []
    with uagec_out_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                incoming.append(json.loads(line))

    calques: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for rec in incoming:
        if "test" in str(rec.get("partition", "")).lower():
            continue
        if is_phase30_uagec_heldout_doc(str(rec["doc_id"])):
            continue
        sentence_ctx = resolve_uagec_sentence_context(rec, gold_contexts, ua_gec_root)
        if not sentence_ctx or not is_grounded_uagec_sentence(sentence_ctx, rec["error"]):
            continue
        first_corr_word = re.split(r"\s+", rec["correct"])[0].strip(",.:;!?")
        root_fam = rec.get("derivational_family") or extract_root_family(first_corr_word)
        if not root_fam or len(root_fam) < 2:
            root_fam = extract_root_family(first_corr_word)
        if not root_fam or len(root_fam) < 2:
            continue
        built = {
            **rec,
            "sentence_context": sentence_ctx,
            "derivational_family": root_fam,
            "curriculum_admission": "ADMITTED",
        }
        if rec["error_type"] == "G/Case":
            cases.append(built)
        else:
            calques.append(built)

    admitted_cases = cases[: len(calques) // 3]
    mined_records = calques + admitted_cases
    with uagec_out_file.open("w", encoding="utf-8") as handle:
        for rec in mined_records:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {
        "mined_records_count": len(mined_records),
        "train_calque_collocation_extracted": len(calques),
        "g_case_admitted": len(admitted_cases),
        "g_case_admitted_ratio": g_case_ratio(len(admitted_cases), len(mined_records)),
        "sha256": hashlib.sha256(uagec_out_file.read_bytes()).hexdigest(),
    }


def generate_manifest(
    output_dir: Path,
    corpus_summary: dict[str, Any],
    uagec_summary: dict[str, Any],
    schema_path: Path = DEFAULT_SCHEMA_FILE,
) -> Path:
    """Assemble and validate decolonization_mined_manifest.json against Draft 2020-12 schema."""
    manifest_file = output_dir / "decolonization_mined_manifest.json"

    manifest_data = {
        "schema_version": "v1_decolonization_mined_candidates",
        "issue": 8006,
        "parent_epic": 6321,
        "generated_at": datetime.now(UTC).isoformat(),
        "files": {
            "corpus_contrast_tables": {
                "filename": "corpus_contrast_tables.jsonl",
                "record_count": corpus_summary["contrast_records_count"],
                "sha256": corpus_summary["contrast_sha256"],
                "description": "Human-authored contrast tables (НЕПРАВИЛЬНО -> ПРАВИЛЬНО, ❌ -> ✅) from textbooks.",
            },
            "zno_distractor_tasks": {
                "filename": "zno_distractor_tasks.jsonl",
                "record_count": corpus_summary["zno_records_count"],
                "sha256": corpus_summary["zno_sha256"],
                "description": "1,646 official ZNO/NMT exam tasks with verified stems, distractors, and keys.",
            },
            "uagec_mined_calques": {
                "filename": "uagec_mined_calques.jsonl",
                "record_count": uagec_summary["mined_records_count"],
                "sha256": uagec_summary["sha256"],
                "description": "Human error contexts from UA-GEC (F/Calque, F/Collocation, and capped G/Case).",
            },
        },
        "corpus_contrast_tables_summary": {
            "total_contrast_pairs": corpus_summary["contrast_records_count"],
            "unique_chunks_mined": corpus_summary["unique_chunks_count"],
            "top_authors": corpus_summary["top_authors"],
        },
        "zno_tasks_summary": {
            "total_zno_tasks": corpus_summary["zno_records_count"],
            "lexical_norm_tasks": corpus_summary["topic_distribution"].get("lexical_norm", 0),
            "syntactic_norm_tasks": corpus_summary["topic_distribution"].get("syntactic_norm", 0),
            "topic_distribution": corpus_summary["topic_distribution"],
        },
        "uagec_mining_summary": {
            "total_calque_collocation_available": uagec_summary["total_calque_collocation_available"],
            "calque_count": uagec_summary["calque_count"],
            "collocation_count": uagec_summary["collocation_count"],
            "protected_test_split_excluded": uagec_summary["protected_test_split_excluded"],
            "train_calque_collocation_extracted": uagec_summary["train_calque_collocation_extracted"],
            "g_case_total": uagec_summary["g_case_total"],
            "g_case_admitted": uagec_summary["g_case_admitted"],
            "g_case_admitted_ratio": uagec_summary["g_case_admitted_ratio"],
        },
    }

    if schema_path.is_file():
        with schema_path.open("r", encoding="utf-8") as sf:
            schema = json.load(sf)
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(manifest_data))
        if errors:
            raise ValueError(f"Manifest schema validation failed: {[e.message for e in errors]}")

    with manifest_file.open("w", encoding="utf-8") as mf:
        mf.write(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n")

    return manifest_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine UA-GEC calques and build mined candidates manifest.")
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_FILE)
    parser.add_argument("--ua-gec-root", type=Path, default=None, help="Pinned UA-GEC checkout for original sentences.")
    parser.add_argument(
        "--repair-existing",
        action="store_true",
        help="Rewrite existing UA-GEC JSONL with firewall + original-sentence grounding.",
    )
    parser.add_argument("--verify-only", action="store_true", help="Validate existing mined manifest.")
    args = parser.parse_args()

    if args.verify_only:
        try:
            verify_mined_manifest(args.output_dir, args.schema)
        except ValueError as exc:
            print(f"Verification failed: {exc}")
            sys.exit(1)
        print("Mined artifacts verified (schema, SHA-256, F1–F3 guards).")
        sys.exit(0)

    if args.repair_existing:
        from scripts.projects.open_model_data.v4_mine_corpus_calques import (
            restore_zno_stems_from_official_exam_text,
        )

        zno_path = args.output_dir / "zno_distractor_tasks.jsonl"
        if zno_path.is_file():
            repaired_zno = []
            with zno_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    repaired_zno.append(json.loads(line))
            stats = restore_zno_stems_from_official_exam_text(
                repaired_zno,
                sources_db=args.sources_db,
            )
            if stats["missing"]:
                raise ValueError(f"Official ZNO stems missing for {stats['missing']} records")
            with zno_path.open("w", encoding="utf-8") as handle:
                for rec in repaired_zno:
                    handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

        uagec_sum = repair_existing_uagec_file(args.output_dir, DEFAULT_GOLD_FILE, args.ua_gec_root)
        contrast_path = args.output_dir / "corpus_contrast_tables.jsonl"
        contrast_records = []
        with contrast_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    contrast_records.append(json.loads(line))
        author_counts: dict[str, int] = {}
        unique_chunks = set()
        for rec in contrast_records:
            author_counts[rec["author"]] = author_counts.get(rec["author"], 0) + 1
            unique_chunks.add(rec["chunk_id"])
        zno_records = []
        with zno_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    zno_records.append(json.loads(line))
        topic_counts: dict[str, int] = {}
        for rec in zno_records:
            topic_counts[rec["topic_norm"]] = topic_counts.get(rec["topic_norm"], 0) + 1
        existing_manifest = json.loads(
            (args.output_dir / "decolonization_mined_manifest.json").read_text(encoding="utf-8")
        )
        corpus_sum = {
            "contrast_records_count": len(contrast_records),
            "unique_chunks_count": len(unique_chunks),
            "contrast_sha256": hashlib.sha256(contrast_path.read_bytes()).hexdigest(),
            "zno_records_count": len(zno_records),
            "zno_sha256": hashlib.sha256(zno_path.read_bytes()).hexdigest(),
            "top_authors": dict(sorted(author_counts.items(), key=lambda item: -item[1])[:10]),
            "topic_distribution": topic_counts,
        }
        uagec_sum = {
            **existing_manifest["uagec_mining_summary"],
            **uagec_sum,
        }
        m_path = generate_manifest(args.output_dir, corpus_sum, uagec_sum, args.schema)
        print(f"Repaired mined artifacts and manifest at: {m_path}")
        sys.exit(0)

    from scripts.projects.open_model_data.v4_mine_corpus_calques import mine_corpus_calques

    print("Mining textbook contrast tables & ZNO tasks...")
    corpus_sum = mine_corpus_calques(args.sources_db, args.vesum_db, args.output_dir)

    print("Mining UA-GEC calques & collocations...")
    uagec_sum = mine_uagec_calques(
        args.sources_db,
        args.vesum_db,
        args.output_dir,
        ua_gec_root=args.ua_gec_root,
    )

    print("Generating and validating manifest...")
    m_path = generate_manifest(args.output_dir, corpus_sum, uagec_sum, args.schema)
    print(f"Phase 3.1-3.2 manifest generated at: {m_path}")


if __name__ == "__main__":
    main()
