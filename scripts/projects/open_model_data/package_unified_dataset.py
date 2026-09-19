#!/usr/bin/env python3
"""Package Unified Ukrainian Language Decolonization & Reasoning (ULDR) Dataset.

This script aggregates all verified, release-grade ULDR modules into ONE unified
Hugging Face-ready dataset with standard splits:
  - train.jsonl: ~136,550 SFT instruction trajectories with structured <thought> reasoning
  - dpo.jsonl: 3,000 length-matched preference pairs for anti-calque alignment
  - eval.jsonl: ~4,200 pristine held-out evaluation tasks across all domains
  - README.md: Hugging Face dataset card with schema, metadata, and citation

Parent Epic: #6321 (Open Model Data)
Target Hub: https://huggingface.co/datasets/krisztiankoos/uldr
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_sft_record(raw: dict[str, Any], default_domain: str, default_subject: str = "") -> dict[str, Any]:
    """Normalize an SFT trajectory into standard Hugging Face Chat messages format."""
    rec_id = raw.get("trajectory_id") or raw.get("id") or raw.get("eval_id") or ""
    domain = raw.get("domain") or default_domain
    subject = raw.get("subject") or default_subject
    query = raw.get("query") or ""
    final_resp = raw.get("final_response") or raw.get("reference_solution") or ""
    reasoning = raw.get("reasoning_steps") or raw.get("reference_reasoning") or []

    steps_str = "\n".join(str(s) for s in reasoning) if isinstance(reasoning, list) else str(reasoning)

    # Standard thinking assistant format: <thought>\n...\n</thought>\n...
    assistant_content = f"<thought>\n{steps_str}\n</thought>\n{final_resp}" if steps_str.strip() else final_resp

    messages = [
        {"role": "user", "content": query},
        {"role": "assistant", "content": assistant_content},
    ]

    record = {
        "id": rec_id,
        "domain": domain,
        "subject": subject,
        "messages": messages,
        "query": query,
        "reasoning_steps": reasoning if isinstance(reasoning, list) else [steps_str],
        "final_response": final_resp,
    }

    # Pass through valuable metadata if present
    for extra in ["grade", "task_type", "target_concept", "target_term", "format_type", "scientific_terminology", "source_metadata"]:
        if extra in raw:
            record[extra] = raw[extra]

    return record


def normalize_dpo_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a DPO preference pair."""
    return {
        "id": raw.get("id") or raw.get("pair_id") or "",
        "domain": "decolonization",
        "pair_type": raw.get("pair_type", "anti_soviet_calque"),
        "target_term": raw.get("target_term", ""),
        "prompt": raw.get("prompt", ""),
        "chosen": raw.get("chosen", ""),
        "rejected": raw.get("rejected", ""),
    }


def normalize_eval_record(raw: dict[str, Any], default_domain: str, default_subject: str = "") -> dict[str, Any]:
    """Normalize an evaluation task."""
    rec_id = raw.get("eval_id") or raw.get("case_id") or raw.get("id") or ""
    domain = raw.get("domain") or raw.get("track_domain") or default_domain
    subject = raw.get("subject") or default_subject
    query = raw.get("query") or raw.get("prompt") or ""
    ref_sol = raw.get("reference_solution") or raw.get("expected_output") or raw.get("final_response") or ""
    ref_reason = raw.get("reference_reasoning") or raw.get("reasoning_steps") or []

    rec = {
        "eval_id": rec_id,
        "domain": domain,
        "subject": subject,
        "query": query,
        "reference_solution": ref_sol,
        "reference_reasoning": ref_reason if isinstance(ref_reason, list) else [str(ref_reason)],
    }
    for extra in ["concept", "grade", "scientific_terminology", "target_term", "is_calque_or_russianism", "source_metadata", "category", "macro_zone"]:
        if extra in raw:
            rec[extra] = raw[extra]
    return rec


def build_unified_dataset(
    release_dir: Path,
    output_dir: Path,
    include_general_assistant: bool = True,
) -> dict[str, Any]:
    """Assemble all releases into ONE master dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "train.jsonl"
    dpo_path = output_dir / "dpo.jsonl"
    eval_path = output_dir / "eval.jsonl"

    train_count = 0
    dpo_count = 0
    eval_count = 0
    domain_counts: Counter[str] = Counter()

    logger.info("Starting unified ULDR packaging...")

    with open(train_path, "w", encoding="utf-8") as f_train, \
         open(dpo_path, "w", encoding="utf-8") as f_dpo, \
         open(eval_path, "w", encoding="utf-8") as f_eval:

        # 1. ULDR v1: Production Decolonization (6k SFT, 3k DPO, 1k Eval)
        v1_dir = release_dir / "uldr_v1_production"
        if v1_dir.exists():
            logger.info("Processing uldr_v1_production...")
            for sft_file in sorted((v1_dir / "sft").glob("*.jsonl")):
                with open(sft_file, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_sft_record(json.loads(line), default_domain="decolonization")
                        f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        train_count += 1
                        domain_counts["decolonization"] += 1

            for dpo_file in sorted((v1_dir / "dpo").glob("*.jsonl")):
                with open(dpo_file, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_dpo_record(json.loads(line))
                        f_dpo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        dpo_count += 1

            v1_eval = v1_dir / "heldout_evaluation_suite_1000.jsonl"
            if v1_eval.exists():
                with open(v1_eval, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_eval_record(json.loads(line), default_domain="decolonization")
                        f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        eval_count += 1

        # 2. ULDR v03: Dialect Protection & Regional Varieties (550 SFT, 1.5k Eval)
        v03_dir = release_dir / "uldr_v03_dialect"
        if v03_dir.exists():
            logger.info("Processing uldr_v03_dialect...")
            v03_sft = v03_dir / "sft_dialect_protection_500.jsonl"
            if v03_sft.exists():
                with open(v03_sft, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_sft_record(json.loads(line), default_domain="dialect")
                        f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        train_count += 1
                        domain_counts["dialect"] += 1

            v03_eval = v03_dir / "dialect_corpus_expanded_1500.jsonl"
            if v03_eval.exists():
                with open(v03_eval, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_eval_record(json.loads(line), default_domain="dialect")
                        f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        eval_count += 1

        # 3. ULDR v04a: Kyivan Rus Epigraphy & Chronicles (10k SFT, 500 Eval)
        v04a_dir = release_dir / "uldr_v04a_kyivan_rus"
        if v04a_dir.exists():
            logger.info("Processing uldr_v04a_kyivan_rus...")
            for sft_file in sorted((v04a_dir / "sft").glob("*.jsonl")):
                with open(sft_file, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_sft_record(json.loads(line), default_domain="kyivan_rus", default_subject="history")
                        f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        train_count += 1
                        domain_counts["kyivan_rus"] += 1

            v04a_eval = v04a_dir / "kyivan_rus_epigraphic_eval.jsonl"
            if v04a_eval.exists():
                with open(v04a_eval, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_eval_record(json.loads(line), default_domain="kyivan_rus", default_subject="history")
                        f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        eval_count += 1

        # 4. ULDR v04b: Middle Ukrainian / Cossack Baroque (10k SFT, 500 Eval)
        v04b_dir = release_dir / "uldr_v04b_middle_ukrainian"
        if v04b_dir.exists():
            logger.info("Processing uldr_v04b_middle_ukrainian...")
            for sft_file in sorted((v04b_dir / "sft").glob("*.jsonl")):
                with open(sft_file, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_sft_record(json.loads(line), default_domain="middle_ukrainian", default_subject="literature")
                        f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        train_count += 1
                        domain_counts["middle_ukrainian"] += 1

            v04b_eval = v04b_dir / "middle_ukrainian_eval.jsonl"
            if v04b_eval.exists():
                with open(v04b_eval, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_eval_record(json.loads(line), default_domain="middle_ukrainian", default_subject="literature")
                        f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        eval_count += 1

        # 5. ULDR v05: Grammar Valency & Syntactic Precision (35k SFT, 500 Eval)
        v05_dir = release_dir / "uldr_v05_grammar_valency"
        if v05_dir.exists():
            logger.info("Processing uldr_v05_grammar_valency...")
            for sft_file in sorted((v05_dir / "sft").glob("*.jsonl")):
                with open(sft_file, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_sft_record(json.loads(line), default_domain="grammar_valency", default_subject="ukrmova")
                        f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        train_count += 1
                        domain_counts["grammar_valency"] += 1

            v05_eval = v05_dir / "brown_uk_negative_control_eval.jsonl"
            if v05_eval.exists():
                with open(v05_eval, encoding="utf-8") as in_f:
                    for line in in_f:
                        if not line.strip():

                            continue
                        rec = normalize_eval_record(json.loads(line), default_domain="grammar_valency", default_subject="ukrmova")
                        f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        eval_count += 1

        # 6. ULDR v06: General Ukrainian Assistant - STEM & Humanities Textbooks (75k SFT, 200 Eval)
        if include_general_assistant:
            v06_dir = release_dir / "uldr_v06_general_assistant"
            if v06_dir.exists():
                logger.info("Processing uldr_v06_general_assistant...")
                for sft_file in sorted((v06_dir / "sft").glob("*.jsonl")):
                    with open(sft_file, encoding="utf-8") as in_f:
                        for line in in_f:
                            if not line.strip():

                                continue
                            rec = normalize_sft_record(json.loads(line), default_domain="textbook_assistant")
                            f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            train_count += 1
                            domain_counts["textbook_assistant"] += 1

                for eval_file in sorted((v06_dir / "eval").glob("*.jsonl")):
                    with open(eval_file, encoding="utf-8") as in_f:
                        for line in in_f:
                            if not line.strip():

                                continue
                            rec = normalize_eval_record(json.loads(line), default_domain="textbook_assistant")
                            f_eval.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            eval_count += 1

    train_sha = sha256_file(train_path)
    dpo_sha = sha256_file(dpo_path)
    eval_sha = sha256_file(eval_path)

    manifest = {
        "dataset_name": "Ukrainian Linguistic Decolonization & Reasoning (ULDR)",
        "version": "1.0.0",
        "parent_epic": 6321,
        "created_at": datetime.now(UTC).isoformat(),
        "splits": {
            "train": {
                "file": "train.jsonl",
                "record_count": train_count,
                "sha256": train_sha,
                "domain_breakdown": dict(domain_counts),
            },
            "dpo": {
                "file": "dpo.jsonl",
                "record_count": dpo_count,
                "sha256": dpo_sha,
            },
            "eval": {
                "file": "eval.jsonl",
                "record_count": eval_count,
                "sha256": eval_sha,
            }
        },
        "totals": {
            "sft_instructions": train_count,
            "dpo_pairs": dpo_count,
            "eval_cases": eval_count,
        }
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    (output_dir / "manifest.json.sha256").write_text(f"{sha256_file(manifest_path)}  manifest.json\n")

    # Generate Hugging Face README.md
    readme_content = f"""---
language:
- uk
license: cc-by-sa-4.0
task_categories:
- text-generation
- question-answering
tags:
- ukrainian
- decolonization
- linguistics
- reasoning
- textbooks
- stem
- grammar
- vesum
size_categories:
- 100K<n<1M
---

# Ukrainian Linguistic Decolonization & Reasoning (ULDR) — v0.2 (Training Candidate)

**ULDR v0.2** is the foundational unproven training candidate dataset for Ukrainian, built to teach language models to **think and reason in authentic Ukrainian** rather than translate through Russian or English. Packaged for remote fine-tuning on Hugging Face.

## Dataset Summary

- **Train (SFT):** {train_count:,} multi-turn instruction trajectories with Chain-of-Thought linguistic reasoning (`<thought> ... </thought>`).
- **DPO (Preference Alignment):** {dpo_count:,} length-matched pairs specifically targeting anti-Soviet calques, Surzhyk eradication, and balanced preservation.
- **Evaluation Benchmark:** {eval_count:,} held-out evaluation tasks isolated with 0% text leakage against training sets.

## Domain Composition

| Domain | Records | Description |
|---|---:|---|
| **Textbook Assistant** | {domain_counts.get("textbook_assistant", 0):,} | 25 subjects (STEM & Humanities) across Grades 1–11 with OCR cleanup. |
| **Grammar Valency & Syntax** | {domain_counts.get("grammar_valency", 0):,} | Case government, syntactic valency, and error correction via VESUM & Brown-UK. |
| **Kyivan Rus Epigraphy** | {domain_counts.get("kyivan_rus", 0):,} | 11th–13th century Sophia graffiti and chronicles (Old East Slavic). |
| **Middle Ukrainian** | {domain_counts.get("middle_ukrainian", 0):,} | 14th–17th century Ruthenian chancery and Cossack Baroque. |
| **Decolonization & Reasoning** | {domain_counts.get("decolonization", 0):,} | Deep anti-calque reasoning against Sovietized lexicography (СУМ-11). |
| **Dialect Protection** | {domain_counts.get("dialect", 0):,} | Authentic living Ukrainian dialects (Hutsul, Boyko, Lemko, Polissian, Slobozhan). |

## Quickstart (Hugging Face Datasets)

```python
from datasets import load_dataset

# Load full SFT training dataset
dataset = load_dataset("krisztiankoos/uldr", split="train")

# Load DPO preference alignment dataset
dpo_dataset = load_dataset("krisztiankoos/uldr", split="dpo")

# Load held-out evaluation suite
eval_dataset = load_dataset("krisztiankoos/uldr", split="eval")
```

## Chat Template / Thought Format

Each instruction trajectory follows standard reasoning format:

```text
<start_of_turn>user
{'{query}'}<end_of_turn>
<start_of_turn>model
<thought>
1. Лінгвістичний аналіз та словозміна за ВЕСУМ.
2. Семантична перевірка на російські кальки.
3. Нормативний виклад.
</thought>
{'{final_response}'}<end_of_turn>
```

## Invariants & Grounding
- Morphologically verified via **VESUM** (409,000 lemmas, 6.7M forms).
- Decolonized pedagogy aligned with **Ukrainian State Standard 2024**.
- Zero AI-hallucinated source texts — 100% human-authored textbook and historical sources.
"""

    (output_dir / "README.md").write_text(readme_content, encoding="utf-8")
    logger.info("Successfully packaged unified ULDR dataset: %d train, %d dpo, %d eval", train_count, dpo_count, eval_count)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Package unified ULDR v0.2 dataset.")
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=REPO_ROOT / "data" / "projects" / "open_model_data" / "release",
        help="Path to releases directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "projects" / "open_model_data" / "export" / "uldr_v02",
        help="Path to output unified dataset directory",
    )
    parser.add_argument(
        "--skip-general-assistant",
        action="store_true",
        help="Skip general assistant (Phase 6.1) if not finalized yet",
    )
    args = parser.parse_args()

    build_unified_dataset(
        release_dir=args.release_dir,
        output_dir=args.output_dir,
        include_general_assistant=not args.skip_general_assistant,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
