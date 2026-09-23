#!/usr/bin/env python3
"""Build Grammar Component for Open Model Data (#8342, Epic #6321).

Rebuilds the verified Ukrainian grammar, valency, prepositional government,
and anti-calque training and evaluation datasets from authentic human-annotated
sentences in UA-GEC (commit 4757f72f192c4a41e4c8fb1d9690a948f87cf6d6).

Features:
1. Strict 75.0% substantive corrections / 25.0% clean controls mixture.
2. In-scope tags: strictly G/* + F/Calque (16 tags).
3. Document-level 90:10 train/eval partition strictly by doc_id SHA-256 hash.
4. Clean controls drawn from 0-error train UA-GEC sentences and Brown-UK.
5. Task mix: 45% silent rewrites / 55% explained corrections.
6. 100% authoritative citations matching approved Ukrainian linguistics authorities.
7. Compliant with audit_dataset_acceptance.py and profile grammar_8342.yaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.projects.open_model_data.grammar_linguistic_catalog import (
    AUTHORITY_PROFILES,
    CONTROL_PROFILE,
    IN_SCOPE_TAGS,
    PROMPT_TEMPLATES_BY_REGISTER,
    PROMPT_TEMPLATES_EVAL,
    TAG_TO_COARSE_CATEGORY,
    build_query,
    build_query_eval,
    build_reasoning_and_response,
    build_reasoning_and_response_eval,
    classify_sentence_register,
    resolve_specific_linguistic_citation,
)

DEFAULT_UA_GEC_TRAIN_M2 = (
    PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "train" / "gec-fluency.train.m2"
)
DEFAULT_UA_GEC_TEST_M2 = (
    PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "test" / "gec-fluency.test.m2"
)
DEFAULT_FIREWALL_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "evidence"
    / "grammar_held_out_firewall_manifest.json"
)
DEFAULT_BROWN_UK_EVAL = (
    PROJECT_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "release"
    / "uldr_v05_grammar_valency"
    / "brown_uk_negative_control_eval.jsonl"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "components" / "grammar"


def detokenize(text: str) -> str:
    """Detokenize Ukrainian text from Stanza space-separated tokenization."""
    # 1. Close spaces before punctuation: , . ! ? : ; % ) ] } » ”
    text = re.sub(r"\s+([,.\!?:;%\]\}»”])", r"\1", text)
    # 2. Close spaces after opening quotes/brackets: ( [ { « “
    text = re.sub(r"([(\[\{«“])\s+", r"\1", text)
    # 3. Handle ellipses like . . . -> ...
    text = re.sub(r"\.\s+\.\s+\.", "...", text)
    # 4. Handle apostrophes
    text = re.sub(r"([’ʼ\x27])\s+", r"\1", text)
    text = re.sub(r"\s+([’ʼ\x27])", r"\1", text)
    return text.strip()


def load_held_out_firewall(
    manifest_path: Path = DEFAULT_FIREWALL_MANIFEST,
    test_m2_path: Path | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """Load complete held-out test split firewall (doc IDs, source sentences, target sentences).

    Fails closed if the persistent committed firewall manifest is missing or empty.
    """
    if not manifest_path.is_file():
        raise RuntimeError(
            f"Held-out test firewall manifest missing at {manifest_path}. "
            "Cannot proceed without guaranteed test partition containment."
        )

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    test_doc_ids = set(data.get("test_doc_ids", []))
    test_sources = set(data.get("test_source_sentences", []))
    test_targets = set(data.get("test_target_sentences", []))

    if not test_doc_ids or not test_sources or not test_targets:
        raise RuntimeError(
            f"Held-out test firewall manifest at {manifest_path} is empty or invalid. "
            f"Stats: docs={len(test_doc_ids)}, sources={len(test_sources)}, targets={len(test_targets)}"
        )

    return test_doc_ids, test_sources, test_targets


def load_brown_uk_controls(brown_path: Path) -> list[dict[str, Any]]:
    """Load pristine control sentences with authentic attribution from Brown-UK corpus."""
    if not brown_path.is_file():
        raise RuntimeError(f"Required Brown-UK control file missing at {brown_path}")
    controls = []
    brown_doc_counters: Counter[str] = Counter()
    with brown_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                sent = data.get("sentence_text", "").strip()
                doc_id = data.get("document_id") or "brown_uk"
                doc_name = data.get("source_metadata", {}).get("doc_name") or f"{doc_id}.txt"
                eval_id = data.get("eval_id")
                sent_idx = brown_doc_counters[doc_id]
                brown_doc_counters[doc_id] += 1
                if sent:
                    controls.append(
                        {
                            "doc_id": doc_id,
                            "doc_name": doc_name,
                            "eval_id": eval_id,
                            "sent_idx": sent_idx,
                            "original_text": sent,
                            "source_type": "brown_uk_good",
                            "source_corpus": "brown_uk",
                            "license": "CC BY-NC-SA 4.0",
                        }
                    )
    return controls


def parse_m2_sentences(m2_path: Path) -> list[dict[str, Any]]:
    """Parse M2 file into structured sentence records."""
    records = []
    doc_id = None
    cur_sent = None
    cur_edits: dict[int, list[tuple[int, int, str, str]]] = {}
    sent_idx = 0

    with m2_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    sent_idx += 1
                    cur_sent = None
                    cur_edits = {}
                continue
            if line.startswith("S # "):
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    cur_sent = None
                    cur_edits = {}
                doc_id = line[4:].strip()
                sent_idx = 0
            elif line.startswith("S "):
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    sent_idx += 1
                cur_sent = line[2:].strip()
                cur_edits = {}
            elif line.startswith("A "):
                parts = line[2:].split("|||")
                span = parts[0].split()
                start, end = int(span[0]), int(span[1])
                tag = parts[1]
                corr = parts[2]
                ann_id = int(parts[5]) if len(parts) > 5 else 0
                if ann_id not in cur_edits:
                    cur_edits[ann_id] = []
                cur_edits[ann_id].append((start, end, tag, corr))

    if cur_sent is not None:
        records.append(
            {
                "doc_id": doc_id,
                "sent_idx": sent_idx,
                "sent_tokens": cur_sent.split(),
                "edits_by_ann": cur_edits,
            }
        )
    return records


def build_grammar_dataset(
    train_m2_path: Path = DEFAULT_UA_GEC_TRAIN_M2,
    test_m2_path: Path = DEFAULT_UA_GEC_TEST_M2,
    firewall_manifest_path: Path = DEFAULT_FIREWALL_MANIFEST,
    brown_path: Path = DEFAULT_BROWN_UK_EVAL,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Execute complete dataset build pipeline."""
    print("🚀 Initializing Grammar Component Build (#8342)...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load test firewall blacklist (Fail-closed)
    test_doc_ids, test_sources, test_targets = load_held_out_firewall(
        manifest_path=firewall_manifest_path,
        test_m2_path=test_m2_path,
    )
    print(
        f"🔒 Held-out test firewall active: {len(test_doc_ids)} docs, "
        f"{len(test_sources)} source sents, {len(test_targets)} target sents."
    )

    # 2. Load Brown-UK pristine controls
    brown_controls = load_brown_uk_controls(brown_path)
    print(f"📖 Loaded {len(brown_controls)} pristine Brown-UK control sentences.")

    # 3. Parse UA-GEC train sentences
    if not train_m2_path.is_file():
        raise RuntimeError(f"UA-GEC train M2 missing at {train_m2_path}")
    raw_sentences = parse_m2_sentences(train_m2_path)
    print(f"📄 Parsed {len(raw_sentences)} sentences from {train_m2_path.name}.")

    # 4. Partition UA-GEC documents 90:10 by doc_id SHA-256 hash (filtering test doc IDs)
    doc_splits = {}
    for item in raw_sentences:
        d = item["doc_id"]
        if d in test_doc_ids:
            continue
        if d not in doc_splits:
            h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
            doc_splits[d] = "eval" if (h % 10 == 0) else "train"

    train_doc_count = sum(1 for s in doc_splits.values() if s == "train")
    eval_doc_count = sum(1 for s in doc_splits.values() if s == "eval")
    print(
        f"🔀 UA-GEC partition: {train_doc_count} train docs ({train_doc_count/len(doc_splits):.1%}), "
        f"{eval_doc_count} eval docs ({eval_doc_count/len(doc_splits):.1%})."
    )

    # 5. Extract substantive corrections and pristine zero-error controls
    seen_corrections: set[tuple[str, int, str, str]] = set()
    seen_control_texts: set[str] = set()

    train_corrections = []
    eval_corrections = []
    train_clean_candidates = []
    eval_clean_candidates = []
    parallel_target_retentions = 0

    for item in raw_sentences:
        d = item["doc_id"]
        if d in test_doc_ids or d not in doc_splits:
            continue
        split = doc_splits[d]
        orig_tokens = item["sent_tokens"]
        orig_text = detokenize(" ".join(orig_tokens))

        if not orig_text or orig_text in test_sources or orig_text in test_targets:
            continue

        # Check if sentence has zero errors across all annotators
        all_edits = [e for elist in item["edits_by_ann"].values() for e in elist if e[2] != "noop"]
        if not all_edits:
            if orig_text not in seen_control_texts:
                seen_control_texts.add(orig_text)
                clean_item = {
                    "doc_id": d,
                    "doc_name": f"{d}.txt",
                    "sent_idx": item["sent_idx"],
                    "original_text": orig_text,
                    "source_type": "ua_gec_gold_clean",
                    "source_corpus": "ua_gec_2.0",
                    "license": "CC BY 4.0",
                }
                if split == "eval":
                    eval_clean_candidates.append(clean_item)
                else:
                    train_clean_candidates.append(clean_item)
            continue

        # Process in-scope substantive corrections
        distinct_targets_for_sentence: set[str] = set()
        for ann_id, edit_list in sorted(item["edits_by_ann"].items()):
            in_scope = [e for e in edit_list if e[2] in IN_SCOPE_TAGS]
            if not in_scope:
                continue

            # Apply ALL non-noop edits from this annotator so all concurrent errors (e.g. spelling) are resolved
            all_non_noop = [e for e in edit_list if e[2] != "noop"]
            all_sorted = sorted(all_non_noop, key=lambda x: (x[0], x[1]), reverse=True)

            # Check overlap
            valid = True
            for i in range(len(all_sorted) - 1):
                if all_sorted[i][0] < all_sorted[i + 1][1]:
                    valid = False
                    break
            if not valid:
                continue

            toks = list(orig_tokens)
            for start, end, _tag, corr in all_sorted:
                repl = corr.split() if corr else []
                toks[start:end] = repl

            corr_text = detokenize(" ".join(toks))
            if (
                orig_text != corr_text
                and corr_text not in test_sources
                and corr_text not in test_targets
            ):
                tuple_key = (d, ann_id, orig_text, corr_text)
                if tuple_key in seen_corrections:
                    continue
                seen_corrections.add(tuple_key)
                if len(distinct_targets_for_sentence) > 0:
                    parallel_target_retentions += 1
                distinct_targets_for_sentence.add(corr_text)

                sorted_in_scope = sorted(
                    in_scope,
                    key=lambda e: (
                        0 if resolve_specific_linguistic_citation(
                            e[2],
                            " ".join(orig_tokens[e[0] : e[1]]),
                            e[3],
                            orig_text,
                            corr_text,
                        ) is not None else 1,
                        e[0],
                    ),
                )
                primary_edit = sorted_in_scope[0]
                primary_tag = primary_edit[2]
                err_span = " ".join(orig_tokens[primary_edit[0] : primary_edit[1]])
                repl_span = primary_edit[3]
                all_tags = [e[2] for e in in_scope]

                corr_item = {
                    "doc_id": d,
                    "doc_name": f"{d}.txt",
                    "sent_idx": item["sent_idx"],
                    "ann_id": ann_id,
                    "original_text": orig_text,
                    "corrected_text": corr_text,
                    "primary_tag": primary_tag,
                    "all_tags": all_tags,
                    "err_span": err_span,
                    "repl_span": repl_span,
                    "source_type": "ua_gec_human_annotated",
                    "source_corpus": "ua_gec_2.0",
                    "license": "CC BY 4.0",
                }

                if split == "eval":
                    eval_corrections.append(corr_item)
                else:
                    train_corrections.append(corr_item)

    print(
        f"📊 Extracted substantive corrections: {len(train_corrections)} train, "
        f"{len(eval_corrections)} eval. Parallel annotator target retentions: {parallel_target_retentions}."
    )
    print(f"🛡️  Extracted clean control candidates: {len(train_clean_candidates)} train, {len(eval_clean_candidates)} eval.")

    # 6. Formulate exact 75.0% corrections / 25.0% controls mixture
    num_train_corrections = len(train_corrections)
    target_train_controls = round(num_train_corrections * (0.25 / 0.75))

    num_eval_corrections = len(eval_corrections)
    target_eval_controls = round(num_eval_corrections * (0.25 / 0.75))

    print(f"🎯 Target controls for 25.0% share: {target_train_controls} train, {target_eval_controls} eval.")

    # Partition Brown-UK controls strictly by doc_id hash (90:10)
    brown_train_available = []
    brown_eval_available = []
    seen_corr_sources = {c["original_text"] for c in train_corrections + eval_corrections}

    for b in brown_controls:
        txt = b["original_text"]
        if (
            txt in test_sources
            or txt in test_targets
            or txt in seen_control_texts
            or txt in seen_corr_sources
        ):
            continue
        h = int(hashlib.sha256(b["doc_id"].encode("utf-8")).hexdigest(), 16)
        if h % 10 == 0:
            brown_eval_available.append(b)
        else:
            brown_train_available.append(b)

    # Populate train controls: prioritize Brown-UK (up to 400), then gold UA-GEC train clean
    train_controls = []
    brown_train_allocation = min(400, len(brown_train_available))

    for b in brown_train_available[:brown_train_allocation]:
        seen_control_texts.add(b["original_text"])
        train_controls.append(b)

    for item in train_clean_candidates:
        if len(train_controls) >= target_train_controls:
            break
        train_controls.append(item)

    # Populate eval controls: from gold UA-GEC eval clean candidates, supplemented by brown_eval_available if needed
    eval_controls = []
    for item in eval_clean_candidates:
        if len(eval_controls) >= target_eval_controls:
            break
        eval_controls.append(item)

    if len(eval_controls) < target_eval_controls:
        for b in brown_eval_available:
            if len(eval_controls) >= target_eval_controls:
                break
            if b["original_text"] not in seen_control_texts:
                seen_control_texts.add(b["original_text"])
                eval_controls.append(b)

    print(
        f"✅ Formed train slice: {len(train_corrections)} corrections + {len(train_controls)} controls = "
        f"{len(train_corrections) + len(train_controls)} total (control share: {len(train_controls) / (len(train_corrections) + len(train_controls)):.2%})."
    )
    print(
        f"✅ Formed eval slice: {len(eval_corrections)} corrections + {len(eval_controls)} controls = "
        f"{len(eval_corrections) + len(eval_controls)} total (control share: {len(eval_controls) / (len(eval_corrections) + len(eval_controls)):.2%})."
    )

    # 7. Build records with diversified queries, 45/55 task mix, and authoritative citations
    def format_records(
        corrections: list[dict[str, Any]],
        controls: list[dict[str, Any]],
        split_name: str,
    ) -> list[dict[str, Any]]:
        dataset_records = []
        global_seed = 0 if split_name == "train" else 50000

        # Interleave corrections and controls
        all_raw_items = []
        for c in corrections:
            all_raw_items.append((True, c))
        for c in controls:
            all_raw_items.append((False, c))

        # Deterministic shuffle / sort by content hash
        all_raw_items.sort(
            key=lambda x: hashlib.sha256(f"{x[1]['doc_id']}_{x[1]['original_text']}".encode()).hexdigest()
        )

        # Assign task mix: calibrated to land ~55% explained corrections post citation drop
        used_queries: set[str] = set()
        for idx, (is_err, item) in enumerate(all_raw_items):
            seed_idx = global_seed + idx
            orig_text = item["original_text"]
            reg = classify_sentence_register(orig_text)

            if split_name == "eval":
                query = ""
                for offset in range(len(PROMPT_TEMPLATES_EVAL)):
                    cand = PROMPT_TEMPLATES_EVAL[(seed_idx + offset) % len(PROMPT_TEMPLATES_EVAL)].format(sentence=orig_text)
                    if cand not in used_queries:
                        query = cand
                        used_queries.add(cand)
                        seed_idx = seed_idx + offset
                        break
                if not query:
                    query = build_query_eval(orig_text, seed_idx)
            else:
                templates = PROMPT_TEMPLATES_BY_REGISTER.get(reg) or PROMPT_TEMPLATES_BY_REGISTER["journalistic"]
                query = ""
                for offset in range(len(templates)):
                    cand = templates[(seed_idx + offset) % len(templates)].format(sentence=orig_text)
                    if cand not in used_queries:
                        query = cand
                        used_queries.add(cand)
                        seed_idx = seed_idx + offset
                        break
                if not query:
                    query = build_query(orig_text, reg, seed_idx)

            is_explained = (idx % 100 < 64)

            if is_err:
                corr_text = item["corrected_text"]
                primary_tag = item["primary_tag"]
                coarse_category = TAG_TO_COARSE_CATEGORY.get(primary_tag, "syntax_structure")
                err_span = item["err_span"]
                repl_span = item["repl_span"]
                doc_id = item["doc_id"]
                doc_name = item.get("doc_name") or f"{doc_id}.txt"
                ann_id = item.get("ann_id", 0)
                sent_idx = item.get("sent_idx", idx)
                record_id = f"gram_{doc_id}_s{sent_idx}_a{ann_id}"
                source_corpus = item.get("source_corpus", "ua_gec_2.0")
                license_type = item.get("license", "CC BY 4.0")

                if split_name == "eval":
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response_eval(
                        original_text=orig_text,
                        corrected_text=corr_text,
                        is_erroneous=True,
                        is_explained=is_explained,
                        primary_tag=primary_tag,
                        register=reg,
                        error_span=err_span,
                        replacement_span=repl_span,
                        seed_index=seed_idx,
                    )
                else:
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response(
                        original_text=orig_text,
                        corrected_text=corr_text,
                        is_erroneous=True,
                        is_explained=is_explained,
                        primary_tag=primary_tag,
                        register=reg,
                        error_span=err_span,
                        replacement_span=repl_span,
                        seed_index=seed_idx,
                    )

                actual_task_type = "explained_correction" if reasoning_steps else "silent_rewrite"

                source_meta["doc_id"] = doc_id
                source_meta["doc_name"] = doc_name
                source_meta["annotator_id"] = ann_id
                source_meta["license"] = license_type
                source_meta["source_corpus"] = source_corpus
                source_meta["task_type"] = actual_task_type

                rec = {
                    "record_id": record_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "split": split_name,
                    "category": coarse_category,
                    "tag": primary_tag,
                    "in_scope_tags": item["all_tags"],
                    "disposition": "correction",
                    "is_erroneous": True,
                    "task_type": actual_task_type,
                    "register": reg,
                    "query": query,
                    "original_text": orig_text,
                    "corrected_text": corr_text,
                    "final_response": final_response,
                    "reasoning_steps": reasoning_steps,
                    "chosen": corr_text,
                    "rejected": orig_text,
                    "source_corpus": source_corpus,
                    "license": license_type,
                    "source_metadata": source_meta,
                }
            else:
                doc_id = item["doc_id"]
                doc_name = item.get("doc_name") or f"{doc_id}.txt"
                sent_idx = item.get("sent_idx", idx)
                record_id = f"ctrl_{doc_id}_s{sent_idx}"
                coarse_category = "protective_authentic_control"
                source_corpus = item.get(
                    "source_corpus",
                    "brown_uk" if "brown" in item.get("source_type", "") else "ua_gec_2.0",
                )
                license_type = item.get(
                    "license",
                    "CC BY-NC-SA 4.0" if "brown" in item.get("source_type", "") else "CC BY 4.0",
                )

                if split_name == "eval":
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response_eval(
                        original_text=orig_text,
                        corrected_text=orig_text,
                        is_erroneous=False,
                        is_explained=is_explained,
                        primary_tag="control_clean",
                        register=reg,
                        error_span="",
                        replacement_span="",
                        seed_index=seed_idx,
                    )
                else:
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response(
                        original_text=orig_text,
                        corrected_text=orig_text,
                        is_erroneous=False,
                        is_explained=is_explained,
                        primary_tag="control_clean",
                        register=reg,
                        error_span="",
                        replacement_span="",
                        seed_index=seed_idx,
                    )

                actual_task_type = "explained_control" if reasoning_steps else "silent_control"

                source_meta["doc_id"] = doc_id
                source_meta["doc_name"] = doc_name
                if item.get("eval_id"):
                    source_meta["eval_id"] = item["eval_id"]
                source_meta["license"] = license_type
                source_meta["source_corpus"] = source_corpus
                source_meta["task_type"] = actual_task_type

                rec = {
                    "record_id": record_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "split": split_name,
                    "category": coarse_category,
                    "tag": "control_clean",
                    "in_scope_tags": [],
                    "disposition": "control",
                    "is_erroneous": False,
                    "task_type": actual_task_type,
                    "register": reg,
                    "query": query,
                    "original_text": orig_text,
                    "corrected_text": orig_text,
                    "final_response": final_response,
                    "reasoning_steps": reasoning_steps,
                    "chosen": orig_text,
                    "rejected": None,
                    "source_corpus": source_corpus,
                    "license": license_type,
                    "source_metadata": source_meta,
                }

            dataset_records.append(rec)
        return dataset_records

    train_dataset_records = format_records(train_corrections, train_controls, "train")
    eval_dataset_records = format_records(eval_corrections, eval_controls, "eval")

    # 8. Write JSONL shards (< 1.8 MB each to respect repository 2,000,000 byte gate)
    train_shard_size = 450
    num_train_shards = (len(train_dataset_records) + train_shard_size - 1) // train_shard_size
    manifest_splits = {}

    for shard_idx in range(num_train_shards):
        shard_records = train_dataset_records[shard_idx * train_shard_size : (shard_idx + 1) * train_shard_size]
        fname = f"grammar_train_shard_{shard_idx + 1:02d}_of_{num_train_shards:02d}.jsonl"
        shard_path = output_dir / fname
        with shard_path.open("w", encoding="utf-8") as f:
            for r in shard_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest_splits[fname] = "train"

    eval_shard_size = 300
    num_eval_shards = (len(eval_dataset_records) + eval_shard_size - 1) // eval_shard_size

    for shard_idx in range(num_eval_shards):
        shard_records = eval_dataset_records[shard_idx * eval_shard_size : (shard_idx + 1) * eval_shard_size]
        fname = f"grammar_eval_shard_{shard_idx + 1:02d}_of_{num_eval_shards:02d}.jsonl"
        shard_path = output_dir / fname
        with shard_path.open("w", encoding="utf-8") as f:
            for r in shard_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest_splits[fname] = "eval"

    print(f"💾 Wrote {len(train_dataset_records)} train records across {num_train_shards} shards.")
    print(f"💾 Wrote {len(eval_dataset_records)} eval records across {num_eval_shards} shards.")

    # 9. Write cases.json catalog
    cases = []
    for tag in sorted(IN_SCOPE_TAGS):
        prof = AUTHORITY_PROFILES[tag]
        cases.append(
            {
                "case_id": f"gram_tag_{tag.replace('/', '_').lower()}",
                "tag": tag,
                "category": TAG_TO_COARSE_CATEGORY.get(tag, "syntax_structure"),
                "authority": prof["authority"],
                "description": prof["description"],
                "rule_template": prof["rule_template"],
                "status": "active_in_scope",
            }
        )
    cases.append(
        {
            "case_id": "gram_control_clean",
            "tag": "control_clean",
            "category": "protective_authentic_control",
            "authority": CONTROL_PROFILE["authority"],
            "description": CONTROL_PROFILE["description"],
            "rule_template": CONTROL_PROFILE["rule_template"],
            "status": "active_control",
        }
    )

    cases_file = output_dir / "cases.json"
    with cases_file.open("w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"💾 Wrote {len(cases)} cases to {cases_file.name}.")

    # 10. Write manifest.json
    total_records = len(train_dataset_records) + len(eval_dataset_records)
    total_corrections = len(train_corrections) + len(eval_corrections)
    total_controls = len(train_controls) + len(eval_controls)

    manifest = {
        "dataset_name": "grammar_v1",
        "version": "1.0.0",
        "task_type": "correction",
        "has_evaluation_split": True,
        "splits": manifest_splits,
        "description": "Verified Ukrainian grammar, valency, and morphosyntactic corrections rebuilt from authentic human-annotated sentences in UA-GEC (#8342).",
        "governing_issues": ["#8342", "#6321"],
        "licenses": {
            "ua_gec_2.0": {
                "license": "CC BY 4.0",
                "attribution": "UA-GEC: Corpus of Annotated Sentences for Ukrainian GEC",
            },
            "brown_uk": {
                "license": "CC BY-NC-SA 4.0",
                "attribution": "Brown-UK: Corpus of Contemporary Ukrainian (BrUK)",
            },
        },
        "statistics": {
            "total_records": total_records,
            "train_records": len(train_dataset_records),
            "eval_records": len(eval_dataset_records),
            "substantive_corrections": total_corrections,
            "clean_controls": total_controls,
            "clean_control_share": round(total_controls / total_records, 4),
            "substantive_correction_share": round(total_corrections / total_records, 4),
            "category_counts": dict(Counter(r["category"] for r in train_dataset_records + eval_dataset_records)),
            "source_corpus_counts": dict(Counter(r["source_corpus"] for r in train_dataset_records + eval_dataset_records)),
            "license_counts": dict(Counter(r["license"] for r in train_dataset_records + eval_dataset_records)),
        },
    }

    manifest_file = output_dir / "manifest.json"
    with manifest_file.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"💾 Wrote dataset manifest to {manifest_file.name}.")

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Grammar Component Dataset (#8342)")
    parser.add_argument("--train-m2", type=Path, default=DEFAULT_UA_GEC_TRAIN_M2)
    parser.add_argument("--test-m2", type=Path, default=DEFAULT_UA_GEC_TEST_M2)
    parser.add_argument("--firewall-manifest", type=Path, default=DEFAULT_FIREWALL_MANIFEST)
    parser.add_argument("--brown", type=Path, default=DEFAULT_BROWN_UK_EVAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    build_grammar_dataset(
        train_m2_path=args.train_m2,
        test_m2_path=args.test_m2,
        firewall_manifest_path=args.firewall_manifest,
        brown_path=args.brown,
        output_dir=args.output_dir,
    )
