#!/usr/bin/env python3
"""Compile the Ukrainian Calque + Grammar Evaluation Dataset (UNLP 2027 target).

Reads curated gold UA-GEC entries, loads and applies the taxonomy specification from
``docs/projects/ua-eval-harness/taxonomy.yaml``, executes the Heritage Dialect
Safeguard check, and outputs a HuggingFace-compatible JSONL evalset.

Usage
-----
    PYTHONPATH=.:scripts .venv/bin/python scripts/projects/ua_eval_harness/compile_evalset.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_GOLD_FIXTURE = ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json"
DEFAULT_TAXONOMY_PATH = ROOT / "docs" / "projects" / "ua-eval-harness" / "taxonomy.yaml"
DEFAULT_OUTPUT_JSONL = ROOT / "data" / "projects" / "ua_eval_harness" / "evalset_v1.jsonl"


@dataclass(frozen=True)
class EditSpan:
    start: int
    end: int
    source_span: str
    target_span: str
    category: str
    subtype: str
    is_regionalism: bool
    authority: list[str]
    explanation: str


@dataclass(frozen=True)
class DialectVerdict:
    is_regionalism: bool
    verdict: str
    evidence: list[str]
    authority: list[str]


@dataclass(frozen=True)
class EvalsetItem:
    id: str
    text: str
    target: str
    lang: str
    edits: list[dict[str, Any]]
    dialect: dict[str, Any]
    provenance: dict[str, Any]


def generate_item_id(text: str, source_span: str, category: str) -> str:
    digest = hashlib.sha256(f"{text}:{source_span}:{category}".encode()).hexdigest()[:12]
    return f"eval-{category.lower().replace('/', '_')}-{digest}"


def load_taxonomy(taxonomy_path: Path = DEFAULT_TAXONOMY_PATH) -> dict[str, Any]:
    """Load and return the taxonomy specification dictionary from YAML."""
    if not taxonomy_path.exists():
        raise FileNotFoundError(f"Taxonomy specification file not found: {taxonomy_path}")
    with taxonomy_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_heritage_safeguard(error_word: str, correction_word: str) -> DialectVerdict:
    """Evaluate whether error_word is an authentic regionalism/archaism rather than a true Russianism.

    Pilot implementation: Uses a initial seed set of attested Ukrainian regionalisms.
    Future iterations integrate full VESUM + Grinchenko 1907 + ESUM DB lookups.
    """
    known_regionalisms = {"бутелька", "кнайпа", "фірка", "файно", "тельбух"}
    if error_word.lower() in known_regionalisms:
        return DialectVerdict(
            is_regionalism=True,
            verdict="heritage_protected",
            evidence=[f"attested_regionalism:{error_word}"],
            authority=["ua-gec", "heritage_dict"],
        )

    return DialectVerdict(
        is_regionalism=False,
        verdict="cleared",
        evidence=[f"ua_gec_pair:{error_word}->{correction_word}"],
        authority=["ua-gec"],
    )


def compile_evalset(
    gold_path: Path = DEFAULT_GOLD_FIXTURE,
    output_path: Path = DEFAULT_OUTPUT_JSONL,
    taxonomy_path: Path = DEFAULT_TAXONOMY_PATH,
) -> int:
    if not gold_path.exists():
        print(f"Error: Gold fixture file not found: {gold_path}", file=sys.stderr)
        return 1

    if not taxonomy_path.exists():
        print(f"Error: Taxonomy specification file not found: {taxonomy_path}", file=sys.stderr)
        return 1

    taxonomy = load_taxonomy(taxonomy_path)
    allowed_categories = set(taxonomy.get("categories", {}).keys())

    with gold_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    raw_items = data.get("items", [])
    eval_items: list[EvalsetItem] = []
    category_counts: dict[str, int] = {}
    regionalism_count = 0

    for _idx, item in enumerate(raw_items, start=1):
        source_text = item.get("source_excerpt", "")
        target_text = item.get("corrected_excerpt", "")
        error_word = item.get("error", "")
        correction_word = item.get("correction", "")
        category = item.get("tag", "F/Calque")

        if allowed_categories and category not in allowed_categories:
            print(f"Warning: Category '{category}' not found in taxonomy.yaml", file=sys.stderr)

        span_info = item.get("spans", {}).get("source", {})
        start_char = span_info.get("start", 0)
        end_char = span_info.get("end", start_char + len(error_word))

        # Re-verify and adjust span character offsets if excerpt text diverges
        if source_text and error_word and source_text[start_char:end_char] != error_word:
            found_idx = source_text.find(error_word)
            if found_idx != -1:
                start_char = found_idx
                end_char = found_idx + len(error_word)

        verdict = check_heritage_safeguard(error_word, correction_word)
        if verdict.is_regionalism:
            regionalism_count += 1

        edit = EditSpan(
            start=start_char,
            end=end_char,
            source_span=error_word,
            target_span=correction_word,
            category=category,
            subtype="calque" if "Calque" in category else "grammar",
            is_regionalism=verdict.is_regionalism,
            authority=verdict.authority,
            explanation=f"UA-GEC edit: '{error_word}' -> '{correction_word}' ({category})",
        )

        item_id = generate_item_id(source_text, error_word, category)
        eval_item = EvalsetItem(
            id=item_id,
            text=source_text,
            target=target_text,
            lang="uk",
            edits=[asdict(edit)],
            dialect={
                "is_regionalism": verdict.is_regionalism,
                "verdict": verdict.verdict,
                "evidence": verdict.evidence,
            },
            provenance={
                "dataset": "learn-ukrainian/ua-gec-calque-eval",
                "license": "CC-BY-4.0",
                "source": "UA-GEC v2 (Grammarly Ukraine)",
                "ua_gec_error_id": item.get("ua_gec_error_id"),
                "taxonomy_version": taxonomy.get("version", "1.0.0"),
                "version": "1.0.0",
            },
        )
        eval_items.append(eval_item)
        category_counts[category] = category_counts.get(category, 0) + 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_f:
        for item in eval_items:
            out_f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    rel_out = output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path
    print(f"✅ Successfully compiled {len(eval_items)} evalset items to {rel_out}")
    print(f"📊 Category Breakdown: {category_counts}")
    print(f"🛡️ Heritage Protected Regionalisms: {regionalism_count}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile Ukrainian Calque + Grammar Evalset (UNLP 2027 target)")
    parser.add_argument("--gold-fixture", type=Path, default=DEFAULT_GOLD_FIXTURE, help="Path to ua-gec-gold.json")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY_PATH, help="Path to taxonomy.yaml")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_JSONL, help="Output JSONL path")
    args = parser.parse_args(argv)

    return compile_evalset(gold_path=args.gold_fixture, output_path=args.output, taxonomy_path=args.taxonomy)


if __name__ == "__main__":
    raise SystemExit(main())
