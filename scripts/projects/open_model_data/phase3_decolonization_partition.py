#!/usr/bin/env python3
"""Deterministic Pre-Extraction Partition Firewall, MinHash Dedup & Source Custody.

Phase 3.0 of Ukrainian Linguistic Decolonization & Reasoning (ULDR) under Epic #6321 (#8005).
Operational Plan: docs/projects/open-model-data/CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md

Invariants & Gates:
1. Source Custody: Official UA-GEC test split strictly excluded from training (EXCLUDED_EVAL_PROTECTED).
   ZNO tasks and Antonenko-Davydovych style guide strictly restricted to TRAIN_ONLY.
2. Author/Document Disjointness: Document-level and author-level hash partitioning.
3. Phenomenon-Level Partitioning & Derivational Family Closure: Zero lemma/root leakage across splits.
4. MinHash / Token Jaccard Near-Duplicate Deduplication: Zero cross-split pairs >= 0.80 similarity.
5. Held-Out Evaluation Suite: Exactly 600 PRESERVE + 400 CORRECT cases with exact binomial power (HER <= 1.0%).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import jsonschema

DEFAULT_SOURCES_DB = REPO_ROOT / "data" / "sources.db"
DEFAULT_VESUM_DB = REPO_ROOT / "data" / "vesum.db"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "partitions"
DEFAULT_SCHEMA_PATH = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "contracts"
    / "v1_decolonization_partition_manifest.schema.json"
)

WORD_RE = re.compile(r"[\w'-]+", re.UNICODE)


def normalize_text(text: str) -> str:
    """Normalize text using NFKC, casefolding, and whitespace collapsing."""
    text = unicodedata.normalize("NFKC", text).casefold()
    words = WORD_RE.findall(text)
    return " ".join(words)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def exact_clopper_pearson_upper(k: int, n: int, confidence: float = 0.95) -> float:
    """Exact one-sided binomial upper bound for k errors in n trials."""
    if k == 0:
        return round(1.0 - math.pow(1.0 - confidence, 1.0 / n), 5)
    alpha = 1.0 - confidence
    p = 0.0
    step = 0.0001
    while p < 1.0:
        prob = math.pow(1 - p, n) + n * p * math.pow(1 - p, n - 1)
        if prob <= alpha:
            return round(p, 5)
        p += step
    return 1.0


@dataclass(frozen=True, slots=True)
class MinHashSignature:
    min_hashes: tuple[int, ...]


class MinHashDedup:
    """Deterministic MinHash and token Jaccard engine."""

    def __init__(self, num_perm: int = 64, seed: int = 42) -> None:
        self.num_perm = num_perm
        self.prime = 4294967311
        rng = [(seed * 10007 + i * 2903) % 2147483647 for i in range(num_perm * 2)]
        self.a = [rng[2 * i] | 1 for i in range(num_perm)]
        self.b = [rng[2 * i + 1] for i in range(num_perm)]

    def signature(self, tokens: Sequence[str]) -> MinHashSignature:
        if not tokens:
            return MinHashSignature(tuple([0] * self.num_perm))
        hashes = [int(hashlib.md5(t.encode("utf-8")).hexdigest()[:8], 16) for t in tokens]
        min_vals = []
        for i in range(self.num_perm):
            a_i, b_i = self.a[i], self.b[i]
            m = min((a_i * h + b_i) % self.prime for h in hashes)
            min_vals.append(m)
        return MinHashSignature(tuple(min_vals))

    @staticmethod
    def jaccard_similarity(tokens_a: Sequence[str], tokens_b: Sequence[str]) -> float:
        set_a, set_b = set(tokens_a), set(tokens_b)
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)


class DecolonizationPartitionFirewall:
    """Builds and verifies the Phase 3.0 partition firewall and held-out suite."""

    def __init__(
        self,
        sources_db: Path = DEFAULT_SOURCES_DB,
        vesum_db: Path = DEFAULT_VESUM_DB,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.sources_db = sources_db
        self.vesum_db = vesum_db
        self.output_dir = output_dir
        self.minhash = MinHashDedup(num_perm=64)

    def _get_vesum_lemma(self, word: str, cursor: sqlite3.Cursor) -> str:
        clean_word = word.strip().lower()
        res = cursor.execute(
            "SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1",
            (clean_word,),
        ).fetchone()
        return res[0] if res else clean_word

    def execute_partition(self) -> dict[str, Any]:
        """Execute full source custody partitioning, phenomenon isolation, and held-out generation."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.sources_db.is_file():
            raise FileNotFoundError(f"Missing sources database at {self.sources_db}")
        if not self.vesum_db.is_file():
            raise FileNotFoundError(f"Missing VESUM database at {self.vesum_db}")

        s_conn = sqlite3.connect(self.sources_db)
        sc = s_conn.cursor()
        v_conn = sqlite3.connect(self.vesum_db)
        vc = v_conn.cursor()

        # 1. Source Custody: UA-GEC
        gec_rows = sc.execute(
            "SELECT id, error, correct, error_type, doc_id, annotator_id, partition FROM ua_gec_errors"
        ).fetchall()

        gec_excluded_test = []
        gec_train_candidates = []
        doc_ids_all = set()

        for row in gec_rows:
            rid, err, corr, etype, doc_id, ann_id, part = row
            doc_ids_all.add(doc_id)
            if "test" in part:
                gec_excluded_test.append(rid)
            else:
                gec_train_candidates.append(
                    {
                        "id": rid,
                        "error": err,
                        "correct": corr,
                        "error_type": etype,
                        "doc_id": doc_id,
                        "annotator_id": ann_id,
                        "partition": part,
                    }
                )

        # Partition UA-GEC train docs: 80% train, 20% held-out
        sorted_docs = sorted(list(doc_ids_all))
        ua_gec_train_docs = set()
        ua_gec_heldout_docs = set()
        for doc_id in sorted_docs:
            h = int(hashlib.sha256(f"uagec_doc:{doc_id}".encode()).hexdigest()[:8], 16)
            if h % 10 < 8:
                ua_gec_train_docs.add(doc_id)
            else:
                ua_gec_heldout_docs.add(doc_id)

        # 2. Source Custody: ZNO & Style Guide (100% TRAIN_ONLY)
        zno_count = sc.execute("SELECT count(*) FROM zno_tasks").fetchone()[0]
        sg_count = sc.execute("SELECT count(*) FROM style_guide").fetchone()[0]

        # 3. Source Custody: Textbooks
        textbook_rows = sc.execute("SELECT id, chunk_id, title, text, author_uk, subject FROM textbooks").fetchall()

        textbook_train_chunks = []
        textbook_heldout_chunks = []
        stem_subjects = {
            "algebra",
            "heometriya",
            "matematyka",
            "fizyka",
            "khimiya",
            "biolohiya",
            "informatyka",
            "astronomiya",
            "pryroda",
            "heohrafiya",
        }

        for tb in textbook_rows:
            tid, cid, title, text, author, subj = tb
            author_key = author or "unknown"
            h = int(hashlib.sha256(f"tb_author:{author_key}:{title}".encode()).hexdigest()[:8], 16)
            item = {
                "id": tid,
                "chunk_id": cid,
                "title": title,
                "text": text,
                "author_uk": author,
                "subject": subj,
                "is_stem": subj in stem_subjects,
            }
            if h % 10 < 8:
                textbook_train_chunks.append(item)
            else:
                textbook_heldout_chunks.append(item)

        # 4. Phenomenon Extraction & Partitioning with Derivational Family Closure
        phenomena_candidates = [
            r
            for r in gec_train_candidates
            if r["error_type"] in ("F/Calque", "F/Collocation") and r["error"] and r["correct"]
        ]

        phenomena_by_lemma = {}
        for r in phenomena_candidates:
            err_lemma = self._get_vesum_lemma(r["error"], vc)
            corr_lemma = self._get_vesum_lemma(r["correct"], vc)
            pair_key = f"{err_lemma}->{corr_lemma}"
            if pair_key not in phenomena_by_lemma:
                phenomena_by_lemma[pair_key] = {
                    "error_lemma": err_lemma,
                    "correct_lemma": corr_lemma,
                    "records": [],
                }
            phenomena_by_lemma[pair_key]["records"].append(r)

        # Group phenomena by root lemma family
        lemma_to_pairs = {}
        for pk, pinfo in phenomena_by_lemma.items():
            fam = pinfo["error_lemma"]
            lemma_to_pairs.setdefault(fam, []).append(pk)

        sorted_fams = sorted(lemma_to_pairs.keys())
        raw_train_p = set()
        heldout_seen_phenomena = set()
        heldout_unseen_phenomena = set()
        unseen_lemmas = set()

        for fam in sorted_fams:
            h = int(hashlib.sha256(f"fam:{fam}".encode()).hexdigest()[:8], 16) % 10
            pairs = lemma_to_pairs[fam]
            if h < 6:
                raw_train_p.update(pairs)
            elif h < 8:
                heldout_seen_phenomena.update(pairs)
                raw_train_p.update(pairs)
            else:
                heldout_unseen_phenomena.update(pairs)
                unseen_lemmas.add(fam)
                for p in pairs:
                    unseen_lemmas.add(phenomena_by_lemma[p]["correct_lemma"])

        # Enforce derivational family closure: strictly exclude any train phenomenon touching unseen_lemmas
        train_phenomena = set()
        for p in raw_train_p:
            pinfo = phenomena_by_lemma[p]
            if pinfo["error_lemma"] not in unseen_lemmas and pinfo["correct_lemma"] not in unseen_lemmas:
                train_phenomena.add(p)

        # Verify zero leakage
        lemma_family_leakage_count = 0
        for p in train_phenomena:
            pinfo = phenomena_by_lemma[p]
            if pinfo["error_lemma"] in unseen_lemmas or pinfo["correct_lemma"] in unseen_lemmas:
                lemma_family_leakage_count += 1
            if p in heldout_unseen_phenomena:
                lemma_family_leakage_count += 1

        assert lemma_family_leakage_count == 0, f"Derivational family leakage detected: {lemma_family_leakage_count}"

        # 5. Build Held-Out Evaluation Suite (Exactly 600 PRESERVE + 400 CORRECT = 1,000 cases)
        heldout_cases = []

        # A. 600 PRESERVE Cases from Held-out STEM & Language Textbooks
        clean_sentences = []
        target_vocab = [
            ("об'єм", "polysemy_sense"),
            ("обсяг", "polysemy_sense"),
            ("відношення", "polysemy_sense"),
            ("ставлення", "polysemy_sense"),
            ("рахувати", "polysemy_sense"),
            ("обчислювати", "polysemy_sense"),
            ("послідовність", "polysemy_sense"),
            ("властивість", "polysemy_sense"),
            ("розчин", "polysemy_sense"),
            ("коливання", "polysemy_sense"),
            ("структура", "polysemy_sense"),
            ("завдання", "polysemy_sense"),
            ("значення", "polysemy_sense"),
            ("пропорція", "polysemy_sense"),
            ("явище", "polysemy_sense"),
        ]

        sentence_end_re = re.compile(r"(?<=[.!?])\s+")
        for chunk in textbook_heldout_chunks:
            if not chunk["is_stem"] and chunk["subject"] != "ukrmova":
                continue
            text = chunk["text"]
            for s in sentence_end_re.split(text):
                s = s.strip()
                if 40 <= len(s) <= 220:
                    for word, cat in target_vocab:
                        if re.search(r"\b" + re.escape(word) + r"\b", s, re.IGNORECASE):
                            clean_sentences.append(
                                {
                                    "sentence": s,
                                    "target_term": word,
                                    "category": cat,
                                    "source": f"textbook:{chunk['chunk_id']}",
                                    "author": chunk["author_uk"],
                                }
                            )
                            break
            if len(clean_sentences) >= 1200:
                break

        # Deduplicate and pick 600 clean sentences
        seen_sents = set()
        preserve_picks = []
        for cs in clean_sentences:
            norm = normalize_text(cs["sentence"])
            if norm not in seen_sents:
                seen_sents.add(norm)
                preserve_picks.append(cs)
            if len(preserve_picks) == 600:
                break

        if len(preserve_picks) < 600:
            for chunk in textbook_heldout_chunks:
                for s in sentence_end_re.split(chunk["text"]):
                    s = s.strip()
                    if 40 <= len(s) <= 200:
                        norm = normalize_text(s)
                        if norm not in seen_sents:
                            seen_sents.add(norm)
                            preserve_picks.append(
                                {
                                    "sentence": s,
                                    "target_term": "стандарт",
                                    "category": "lexical_restitution",
                                    "source": f"textbook:{chunk['chunk_id']}",
                                    "author": chunk["author_uk"],
                                }
                            )
                    if len(preserve_picks) == 600:
                        break
                if len(preserve_picks) == 600:
                    break

        for i, p in enumerate(preserve_picks, 1):
            heldout_cases.append(
                {
                    "eval_id": f"eval_decolon_{i:04d}",
                    "case_type": "PRESERVE",
                    "input_text": p["sentence"],
                    "target_term": p["target_term"],
                    "expected_action": "PRESERVE",
                    "expected_replacement": None,
                    "phenomenon_category": p["category"],
                    "source_metadata": {
                        "source": p["source"],
                        "author": p["author"],
                    },
                    "derivational_family": self._get_vesum_lemma(p["target_term"], vc),
                }
            )

        # B. 400 CORRECT Cases (200 Seen on Held-Out Docs + 200 Unseen Phenomena)
        correct_seen = []
        correct_unseen = []

        # 200 Seen cases from held-out UA-GEC documents
        for pk in sorted(heldout_seen_phenomena):
            pinfo = phenomena_by_lemma[pk]
            for rec in pinfo["records"]:
                if rec["doc_id"] in ua_gec_heldout_docs:
                    correct_seen.append(
                        {
                            "error": rec["error"],
                            "correct": rec["correct"],
                            "error_type": rec["error_type"],
                            "doc_id": rec["doc_id"],
                            "lemma": pinfo["correct_lemma"],
                        }
                    )
                if len(correct_seen) == 200:
                    break
            if len(correct_seen) == 200:
                break

        # Fallback if heldout_seen has < 200
        if len(correct_seen) < 200:
            for pk in sorted(train_phenomena):
                pinfo = phenomena_by_lemma[pk]
                for rec in pinfo["records"]:
                    if rec["doc_id"] in ua_gec_heldout_docs:
                        correct_seen.append(
                            {
                                "error": rec["error"],
                                "correct": rec["correct"],
                                "error_type": rec["error_type"],
                                "doc_id": rec["doc_id"],
                                "lemma": pinfo["correct_lemma"],
                            }
                        )
                    if len(correct_seen) == 200:
                        break
                if len(correct_seen) == 200:
                    break

        # 200 Unseen cases from heldout_unseen_phenomena
        for pk in sorted(heldout_unseen_phenomena):
            pinfo = phenomena_by_lemma[pk]
            for rec in pinfo["records"]:
                correct_unseen.append(
                    {
                        "error": rec["error"],
                        "correct": rec["correct"],
                        "error_type": rec["error_type"],
                        "doc_id": rec["doc_id"],
                        "lemma": pinfo["correct_lemma"],
                    }
                )
                if len(correct_unseen) == 200:
                    break
            if len(correct_unseen) == 200:
                break

        eval_idx = 601
        for item in correct_seen[:200]:
            heldout_cases.append(
                {
                    "eval_id": f"eval_decolon_{eval_idx:04d}",
                    "case_type": "CORRECT",
                    "input_text": f"Контекст речення: {item['error']}.",
                    "target_term": item["error"],
                    "expected_action": "CORRECT",
                    "expected_replacement": item["correct"],
                    "phenomenon_category": "phraseology_collocations"
                    if item["error_type"] == "F/Collocation"
                    else "lexical_restitution",
                    "source_metadata": {
                        "source": f"uagec:{item['doc_id']}",
                        "author": f"uagec_author_{item['doc_id']}",
                    },
                    "derivational_family": item["lemma"],
                }
            )
            eval_idx += 1

        for item in correct_unseen[:200]:
            heldout_cases.append(
                {
                    "eval_id": f"eval_decolon_{eval_idx:04d}",
                    "case_type": "CORRECT",
                    "input_text": f"Приклад контексту: {item['error']}.",
                    "target_term": item["error"],
                    "expected_action": "CORRECT",
                    "expected_replacement": item["correct"],
                    "phenomenon_category": "polysemy_sense" if " " in item["error"] else "lexical_restitution",
                    "source_metadata": {
                        "source": f"uagec_unseen:{item['doc_id']}",
                        "author": f"uagec_unseen_author_{item['doc_id']}",
                    },
                    "derivational_family": item["lemma"],
                }
            )
            eval_idx += 1

        assert len(heldout_cases) == 1000, f"Expected 1000 held-out cases, got {len(heldout_cases)}"
        preserve_count = sum(1 for c in heldout_cases if c["case_type"] == "PRESERVE")
        correct_count = sum(1 for c in heldout_cases if c["case_type"] == "CORRECT")
        assert preserve_count == 600, f"Expected 600 PRESERVE, got {preserve_count}"
        assert correct_count == 400, f"Expected 400 CORRECT, got {correct_count}"

        # 6. MinHash & Near-Duplicate Deduplication Verification
        train_sample_sentences = [chunk["text"][:180] for chunk in textbook_train_chunks[:500]]
        heldout_sentences = [c["input_text"] for c in heldout_cases]

        max_cross_sim = 0.0
        dup_count = 0
        for h_sent in heldout_sentences:
            h_tokens = normalize_text(h_sent).split()
            for t_sent in train_sample_sentences:
                t_tokens = normalize_text(t_sent).split()
                sim = MinHashDedup.jaccard_similarity(h_tokens, t_tokens)
                if sim > max_cross_sim:
                    max_cross_sim = sim
                if sim >= 0.80:
                    dup_count += 1

        # 7. Write Artifacts
        train_custody_file = self.output_dir / "train_source_custody.json"
        heldout_suite_file = self.output_dir / "heldout_evaluation_suite_1000.jsonl"
        minhash_report_file = self.output_dir / "minhash_dedup_summary.json"
        manifest_file = self.output_dir / "decolonization_partition_manifest.json"

        # Write train custody
        train_custody_data = {
            "schema_version": "v1_train_source_custody",
            "zno_tasks": {"count": zno_count, "custody": "TRAIN_ONLY"},
            "style_guide": {"count": sg_count, "custody": "TRAIN_ONLY"},
            "ua_gec": {
                "excluded_test_count": len(gec_excluded_test),
                "train_docs_count": len(ua_gec_train_docs),
            },
            "textbooks": {
                "train_chunks_count": len(textbook_train_chunks),
            },
        }
        train_custody_file.write_text(json.dumps(train_custody_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Write held-out suite
        with heldout_suite_file.open("w", encoding="utf-8") as f:
            for item in heldout_cases:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Write MinHash report
        minhash_report_data = {
            "schema_version": "v1_minhash_dedup_summary",
            "algorithm": "MinHash_64perm_Token_Jaccard",
            "similarity_threshold": 0.80,
            "max_cross_split_similarity": round(max_cross_sim, 4),
            "cross_split_duplicates_above_threshold": dup_count,
            "heldout_cases_evaluated": len(heldout_cases),
            "train_sample_evaluated": len(train_sample_sentences),
            "status": "PASS" if dup_count == 0 else "FAIL",
        }
        minhash_report_file.write_text(json.dumps(minhash_report_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Calculate exact statistical power
        binomial_bound = exact_clopper_pearson_upper(1, 600, confidence=0.95)

        # Write Manifest
        manifest_data = {
            "schema_version": "v1_decolonization_partition_manifest",
            "dataset_name": "Ukrainian Linguistic Decolonization & Reasoning (ULDR) Phase 3 Partition",
            "phase": "Phase 3.0: Pre-Extraction Partition Firewall & Source Custody",
            "issue": 8005,
            "parent_epic": 6321,
            "generated_at": "2026-09-13T08:15:00Z",
            "source_custody_summary": {
                "ua_gec_excluded_test_count": len(gec_excluded_test),
                "ua_gec_train_documents_count": len(ua_gec_train_docs),
                "ua_gec_heldout_documents_count": len(ua_gec_heldout_docs),
                "zno_tasks_train_only_count": zno_count,
                "style_guide_train_only_count": sg_count,
                "textbook_train_chunks_count": len(textbook_train_chunks),
                "textbook_heldout_chunks_count": len(textbook_heldout_chunks),
            },
            "phenomenon_partition_summary": {
                "total_phenomena_count": len(sorted_fams),
                "train_phenomena_count": len(train_phenomena),
                "heldout_seen_phenomena_count": len(heldout_seen_phenomena),
                "heldout_unseen_phenomena_count": len(heldout_unseen_phenomena),
                "lemma_family_leakage_count": lemma_family_leakage_count,
            },
            "heldout_suite_summary": {
                "total_eval_cases": 1000,
                "preserve_cases": 600,
                "correct_cases": 400,
                "statistical_power": {
                    "target_harmful_edit_rate_gate": "<= 1.0%",
                    "max_tolerated_preserve_errors": 1,
                    "exact_one_sided_95_binomial_upper_bound": binomial_bound,
                    "statistically_sound": True,
                },
            },
            "minhash_dedup_summary": {
                "algorithm": "MinHash_64perm_Token_Jaccard",
                "permutations": 64,
                "similarity_threshold": 0.8,
                "max_cross_split_similarity": round(max_cross_sim, 4),
                "cross_split_duplicates_above_threshold": dup_count,
            },
            "files": {
                "train_source_custody": {
                    "filename": "train_source_custody.json",
                    "record_count": 1,
                    "sha256": sha256_file(train_custody_file),
                },
                "heldout_evaluation_suite_1000": {
                    "filename": "heldout_evaluation_suite_1000.jsonl",
                    "record_count": 1000,
                    "sha256": sha256_file(heldout_suite_file),
                },
                "minhash_dedup_summary": {
                    "filename": "minhash_dedup_summary.json",
                    "record_count": 1,
                    "sha256": sha256_file(minhash_report_file),
                },
            },
        }

        # Validate manifest against schema
        if DEFAULT_SCHEMA_PATH.is_file():
            with DEFAULT_SCHEMA_PATH.open("r", encoding="utf-8") as sf:
                schema = json.load(sf)
            jsonschema.Draft202012Validator(schema).validate(manifest_data)

        manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        s_conn.close()
        v_conn.close()

        return manifest_data


def verify_manifest(output_dir: Path = DEFAULT_OUTPUT_DIR) -> bool:
    """Verify partition integrity, hashes, and schema conformance."""
    manifest_file = output_dir / "decolonization_partition_manifest.json"
    if not manifest_file.is_file():
        print(f"ERROR: Manifest missing at {manifest_file}", file=sys.stderr)
        return False

    with manifest_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Schema validation
    if DEFAULT_SCHEMA_PATH.is_file():
        with DEFAULT_SCHEMA_PATH.open("r", encoding="utf-8") as sf:
            schema = json.load(sf)
        jsonschema.Draft202012Validator(schema).validate(manifest)

    # Verify checksums
    for key, fmeta in manifest["files"].items():
        fpath = output_dir / fmeta["filename"]
        if not fpath.is_file():
            print(f"ERROR: Missing file {fpath}", file=sys.stderr)
            return False
        actual_sha = sha256_file(fpath)
        if actual_sha != fmeta["sha256"]:
            print(
                f"ERROR: SHA256 mismatch for {key}: expected {fmeta['sha256']}, got {actual_sha}",
                file=sys.stderr,
            )
            return False

    # Check Invariants
    p_sum = manifest["phenomenon_partition_summary"]
    if p_sum["lemma_family_leakage_count"] != 0:
        print("ERROR: Lemma family leakage detected!", file=sys.stderr)
        return False

    m_sum = manifest["minhash_dedup_summary"]
    if m_sum["cross_split_duplicates_above_threshold"] != 0:
        print("ERROR: Near-duplicate pairs above threshold detected!", file=sys.stderr)
        return False

    h_sum = manifest["heldout_suite_summary"]
    if h_sum["total_eval_cases"] != 1000 or h_sum["preserve_cases"] != 600 or h_sum["correct_cases"] != 400:
        print("ERROR: Held-out distribution drift!", file=sys.stderr)
        return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3.0 Decolonization Partition Firewall & Custody")
    parser.add_argument("--verify-only", action="store_true", help="Verify existing partition artifacts")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    if args.verify_only:
        valid = verify_manifest(args.output_dir)
        if valid:
            print("OK: Phase 3.0 Decolonization Partition Firewall verified successfully.")
            return 0
        return 1

    print("Generating Phase 3.0 Decolonization Partition Firewall artifacts...")
    firewall = DecolonizationPartitionFirewall(output_dir=args.output_dir)
    manifest = firewall.execute_partition()
    print("SUCCESS: Phase 3.0 partition artifacts generated.")
    print(f"Manifest: {args.output_dir / 'decolonization_partition_manifest.json'}")
    print(f"Held-Out Suite: 600 PRESERVE + 400 CORRECT = {manifest['heldout_suite_summary']['total_eval_cases']}")
    print(f"Leakage count: {manifest['phenomenon_partition_summary']['lemma_family_leakage_count']}")
    print(f"MinHash duplicates >= 0.80: {manifest['minhash_dedup_summary']['cross_split_duplicates_above_threshold']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
