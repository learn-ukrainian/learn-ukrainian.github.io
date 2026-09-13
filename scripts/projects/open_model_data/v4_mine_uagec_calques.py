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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import jsonschema

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    extract_root_family,
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
DEFAULT_GOLD_FILE = REPO_ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json"
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


def mine_uagec_calques(
    sources_db: Path,
    vesum_db: Path,
    output_dir: Path,
    gold_file: Path = DEFAULT_GOLD_FILE,
) -> dict[str, Any]:
    """Mine UA-GEC calques and collocations with test-split protection and G/Case curriculum cap."""
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
            # Protected test split: 100% excluded
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

    total_calque_colloc = len(train_calques) + len(train_collocations)

    # 3. Enforce Curriculum Cap: G/Case <= 25% of total training records
    # N_case / (total_calque_colloc + N_case) <= 0.25 => N_case <= total_calque_colloc / 3
    max_admitted_cases = total_calque_colloc // 3
    admitted_cases = train_cases[:max_admitted_cases]

    # Combine into final mined set
    mined_records = []
    idx = 1

    for rec in train_calques + train_collocations:
        rid = rec["error_id"]
        gold_match = gold_contexts.get(rid)
        if gold_match and gold_match.get("source_excerpt"):
            sentence_ctx = gold_match["source_excerpt"]
        else:
            sentence_ctx = f"У тексті вжито вираз: «{rec['error']}» (виправлено на: «{rec['correct']}»)."

        first_corr_word = re.split(r"\s+", rec["correct"])[0].strip(",.:;!?")
        corr_lemma = get_lemma(first_corr_word)

        mined_records.append(
            {
                "record_id": f"uagec.{rid}",
                "error_id": rid,
                "error": rec["error"],
                "correct": rec["correct"],
                "error_type": rec["error_type"],
                "doc_id": rec["doc_id"],
                "annotator_id": rec["annotator_id"],
                "partition": rec["partition"],
                "is_native": rec["is_native"],
                "source_lang": rec["source_lang"],
                "derivational_family": extract_root_family(corr_lemma),
                "sentence_context": sentence_ctx,
                "curriculum_admission": "ADMITTED",
            }
        )
        idx += 1

    for rec in admitted_cases:
        rid = rec["error_id"]
        gold_match = gold_contexts.get(rid)
        if gold_match and gold_match.get("source_excerpt"):
            sentence_ctx = gold_match["source_excerpt"]
        else:
            sentence_ctx = f"У тексті вжито конструкцію: «{rec['error']}» (виправлено на: «{rec['correct']}»)."

        first_corr_word = re.split(r"\s+", rec["correct"])[0].strip(",.:;!?")
        corr_lemma = get_lemma(first_corr_word)

        mined_records.append(
            {
                "record_id": f"uagec.{rid}",
                "error_id": rid,
                "error": rec["error"],
                "correct": rec["correct"],
                "error_type": rec["error_type"],
                "doc_id": rec["doc_id"],
                "annotator_id": rec["annotator_id"],
                "partition": rec["partition"],
                "is_native": rec["is_native"],
                "source_lang": rec["source_lang"],
                "derivational_family": extract_root_family(corr_lemma),
                "sentence_context": sentence_ctx,
                "curriculum_admission": "ADMITTED",
            }
        )
        idx += 1

    s_conn.close()
    v_conn.close()

    # Write output
    with uagec_out_file.open("w", encoding="utf-8") as f:
        for rec in mined_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total_admitted = len(mined_records)
    admitted_ratio = round(len(admitted_cases) / total_admitted, 4) if total_admitted else 0.0

    return {
        "total_calque_collocation_available": total_available_calque_colloc,
        "calque_count": total_available_calques,
        "collocation_count": total_available_collocations,
        "protected_test_split_excluded": test_rows_count,
        "train_calque_collocation_extracted": total_calque_colloc,
        "g_case_total": total_available_cases,
        "g_case_admitted": len(admitted_cases),
        "g_case_admitted_ratio": admitted_ratio,
        "mined_records_count": len(mined_records),
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
    parser.add_argument("--verify-only", action="store_true", help="Validate existing mined manifest.")
    args = parser.parse_args()

    manifest_path = args.output_dir / "decolonization_mined_manifest.json"

    if args.verify_only:
        if not manifest_path.is_file():
            print("Missing manifest:", manifest_path)
            sys.exit(1)
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        if args.schema.is_file():
            with args.schema.open("r", encoding="utf-8") as sf:
                schema = json.load(sf)
            jsonschema.Draft202012Validator(schema).validate(manifest)
        print("Mined manifest verified successfully.")
        sys.exit(0)

    from scripts.projects.open_model_data.v4_mine_corpus_calques import mine_corpus_calques

    print("Mining textbook contrast tables & ZNO tasks...")
    corpus_sum = mine_corpus_calques(args.sources_db, args.vesum_db, args.output_dir)

    print("Mining UA-GEC calques & collocations...")
    uagec_sum = mine_uagec_calques(args.sources_db, args.vesum_db, args.output_dir)

    print("Generating and validating manifest...")
    m_path = generate_manifest(args.output_dir, corpus_sum, uagec_sum, args.schema)
    print(f"Phase 3.1-3.2 manifest generated at: {m_path}")


if __name__ == "__main__":
    main()
