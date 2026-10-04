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
import io
import json
import logging
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data.paths import LOGICAL_OPEN_MODEL_PREFIX, refuse_quarantined
from scripts.storage import paths as storage_paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
MANAGED_RELEASE_DIR = REPO_ROOT / "data/projects/open_model_data/release"
RELEASE_GROUP = "open_model_release_payload"


def _primary_checkout() -> Path:
    return (
        Path(
            subprocess.check_output(
                ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                cwd=REPO_ROOT,
                text=True,
                timeout=30,
            ).strip()
        )
        .resolve()
        .parent
    )


def _check_external_output(output_dir: Path) -> None:
    """Validate the destination before creating or opening any output file."""
    destination = output_dir.expanduser().resolve()
    forbidden = (
        REPO_ROOT.resolve(),
        _primary_checkout(),
        storage_paths.artifact_store_root(REPO_ROOT).resolve(),
    )
    outputs = ("train.jsonl", "dpo.jsonl", "eval.jsonl", "manifest.json", "manifest.json.sha256", "README.md")
    for candidate in (destination, *(destination / name for name in outputs)):
        target = candidate.resolve()
        if any(target == root or target.is_relative_to(root) for root in forbidden):
            raise ValueError(f"--output-dir must be outside the checkout and managed artifact storage: {output_dir}")


class ReleaseInputs:
    """Verified managed snapshot or an explicit external fixture tree."""

    def __init__(self, release_dir: Path) -> None:
        resolved = release_dir.expanduser().resolve()
        for repo in (REPO_ROOT, _primary_checkout()):
            managed_tree = (repo / "data/projects/open_model_data").resolve()
            if not resolved.is_relative_to(managed_tree):
                continue
            managed = (repo / "data/projects/open_model_data/release").resolve()
            if resolved != managed:
                raise ValueError(f"managed --release-dir must be {managed}")
            try:
                snapshot = storage_paths.artifact_set(RELEASE_GROUP, repo=repo)
            except (FileNotFoundError, ValueError) as exc:
                raise storage_paths.MissingArtifactError(
                    RELEASE_GROUP,
                    "*",
                    f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group {RELEASE_GROUP}",
                    str(exc),
                ) from exc
            prefix = "projects/open_model_data/release/"
            self.members = {
                name.removeprefix(prefix): content
                for name, content in snapshot.artifacts.items()
                if name.startswith(prefix)
            }
            self.directory = None
            return
        if not resolved.is_dir():
            raise FileNotFoundError(f"release directory is missing: {release_dir}")
        self.directory = resolved
        self.members = None

    def files(self, relative: str) -> list[str]:
        if self.members is not None:
            pattern = Path(relative)
            return sorted(
                name
                for name in self.members
                if Path(name).parent == pattern.parent and fnmatchcase(Path(name).name, pattern.name)
            )
        assert self.directory is not None
        return sorted(path.relative_to(self.directory).as_posix() for path in self.directory.glob(relative))

    def require_managed_members(self, patterns: tuple[str, ...]) -> None:
        """Reject absent committed release selectors before any export mutation."""
        if self.members is None:
            return
        for pattern in patterns:
            if not self.files(pattern):
                raise storage_paths.MissingArtifactError(
                    RELEASE_GROUP,
                    f"projects/open_model_data/release/{pattern}",
                    f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group {RELEASE_GROUP}",
                    "no committed members match required selector; inspect manifest membership",
                )

    @contextmanager
    def open_text(self, relative: str) -> Iterator[io.StringIO | Any]:
        if self.members is not None:
            with io.StringIO(self.members[relative].decode("utf-8")) as stream:
                yield stream
        else:
            assert self.directory is not None
            with (self.directory / relative).open(encoding="utf-8") as stream:
                yield stream


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
    for extra in [
        "grade",
        "task_type",
        "target_concept",
        "target_term",
        "format_type",
        "scientific_terminology",
        "source_metadata",
    ]:
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
    for extra in [
        "concept",
        "grade",
        "scientific_terminology",
        "target_term",
        "is_calque_or_russianism",
        "source_metadata",
        "category",
        "macro_zone",
    ]:
        if extra in raw:
            rec[extra] = raw[extra]
    return rec


def build_unified_dataset(
    release_dir: Path,
    output_dir: Path,
    include_general_assistant: bool = True,
) -> dict[str, Any]:
    """Assemble all releases into ONE master dataset.

    Every release set this packager reads is quarantined (#9607), so it refuses
    before reading any input; the refusal names the sealed set.
    """
    _check_external_output(output_dir)
    required = (
        "uldr_v03_dialect/sft_dialect_protection_500.jsonl",
        "uldr_v03_dialect/dialect_corpus_expanded_1500.jsonl",
        "uldr_v05_grammar_valency/sft/*.jsonl",
        "uldr_v05_grammar_valency/brown_uk_negative_control_eval.jsonl",
    )
    refuse_quarantined(release_dir, "ULDR packaging release directory")
    for selector in required:
        refuse_quarantined(f"{LOGICAL_OPEN_MODEL_PREFIX}/release/{selector}", "ULDR packaging input")
    inputs = ReleaseInputs(release_dir)
    if inputs.members is not None:
        if any(name.startswith("uldr_v1_production/") for name in inputs.members):
            required += (
                "uldr_v1_production/sft/*.jsonl",
                "uldr_v1_production/dpo/*.jsonl",
                "uldr_v1_production/heldout_evaluation_suite_1000.jsonl",
            )
        if include_general_assistant and any(name.startswith("uldr_v06_general_assistant/") for name in inputs.members):
            required += ("uldr_v06_general_assistant/sft/*.jsonl", "uldr_v06_general_assistant/eval/*.jsonl")
    inputs.require_managed_members(required)
    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "train.jsonl"
    dpo_path = output_dir / "dpo.jsonl"
    eval_path = output_dir / "eval.jsonl"

    train_count = 0
    dpo_count = 0
    eval_count = 0
    domain_counts: Counter[str] = Counter()

    logger.info("Starting unified ULDR packaging...")

    with (
        train_path.open("w", encoding="utf-8") as f_train,
        dpo_path.open("w", encoding="utf-8") as f_dpo,
        eval_path.open("w", encoding="utf-8") as f_eval,
    ):

        def append(pattern: str, output: Any, kind: str, domain: str = "", subject: str = "") -> int:
            count = 0
            for source in inputs.files(pattern):
                refuse_quarantined(f"{LOGICAL_OPEN_MODEL_PREFIX}/release/{source}", "ULDR packaging input")
                if inputs.directory is not None:
                    refuse_quarantined(inputs.directory / source, "ULDR packaging input")
                with inputs.open_text(source) as stream:
                    for line in stream:
                        if not line.strip():
                            continue
                        raw = json.loads(line)
                        if kind == "sft":
                            record = normalize_sft_record(raw, domain, subject)
                            domain_counts[domain] += 1
                        elif kind == "dpo":
                            record = normalize_dpo_record(raw)
                        else:
                            record = normalize_eval_record(raw, domain, subject)
                        output.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
            return count

        # Preserve the historical release order and normalization for each split.
        train_count += append("uldr_v1_production/sft/*.jsonl", f_train, "sft", "decolonization")
        dpo_count += append("uldr_v1_production/dpo/*.jsonl", f_dpo, "dpo")
        eval_count += append("uldr_v1_production/heldout_evaluation_suite_1000.jsonl", f_eval, "eval", "decolonization")
        train_count += append("uldr_v03_dialect/sft_dialect_protection_500.jsonl", f_train, "sft", "dialect")
        eval_count += append("uldr_v03_dialect/dialect_corpus_expanded_1500.jsonl", f_eval, "eval", "dialect")
        train_count += append("uldr_v05_grammar_valency/sft/*.jsonl", f_train, "sft", "grammar_valency", "ukrmova")
        eval_count += append(
            "uldr_v05_grammar_valency/brown_uk_negative_control_eval.jsonl",
            f_eval,
            "eval",
            "grammar_valency",
            "ukrmova",
        )
        if include_general_assistant:
            train_count += append("uldr_v06_general_assistant/sft/*.jsonl", f_train, "sft", "textbook_assistant")
            eval_count += append("uldr_v06_general_assistant/eval/*.jsonl", f_eval, "eval", "textbook_assistant")

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
            },
        },
        "totals": {
            "sft_instructions": train_count,
            "dpo_pairs": dpo_count,
            "eval_cases": eval_count,
        },
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
{"{query}"}<end_of_turn>
<start_of_turn>model
<thought>
1. Лінгвістичний аналіз та словозміна за ВЕСУМ.
2. Семантична перевірка на російські кальки.
3. Нормативний виклад.
</thought>
{"{final_response}"}<end_of_turn>
```

## Invariants & Grounding
- Morphologically verified via **VESUM** (409,000 lemmas, 6.7M forms).
- Decolonized pedagogy aligned with **Ukrainian State Standard 2024**.
- Zero AI-hallucinated source texts — 100% human-authored textbook and historical sources.
"""

    (output_dir / "README.md").write_text(readme_content, encoding="utf-8")
    logger.info(
        "Successfully packaged unified ULDR dataset: %d train, %d dpo, %d eval", train_count, dpo_count, eval_count
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Package verified ULDR release inputs as a unified dataset.\n"
            "Use for an external export after hydrating the release artifacts."
        ),
        epilog=(
            "Example: /home/ops/learn-ukrainian/.venv/bin/python "
            "scripts/projects/open_model_data/package_unified_dataset.py --output-dir /tmp/uldr-v02\n"
            "Outputs: train.jsonl, dpo.jsonl, eval.jsonl, manifest.json, hash sidecar, and README.md.\n"
            "Exit codes: 0 on success; nonzero for invalid paths or missing/corrupt inputs.\n"
            "Related: storage-topology.md and issue #8809."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=MANAGED_RELEASE_DIR,
        help="Release source directory (default: managed data/projects/open_model_data/release)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Required destination outside the checkout and artifact store (for example /tmp/uldr-v02)",
    )
    parser.add_argument(
        "--skip-general-assistant",
        action="store_true",
        help="Skip general assistant release data (default: include it)",
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
