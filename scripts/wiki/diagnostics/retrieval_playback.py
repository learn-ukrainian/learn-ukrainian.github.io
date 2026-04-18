#!/usr/bin/env python3
"""Replay retrieval for #1330 and diagnose writer/retrieval/corpus gaps."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wiki.sources_db import SOURCES_DB_PATH, search_textbooks

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DISCOVERY_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "a1" / "discovery" / "sounds-letters-and-hello.yaml"
SOURCE_REGISTRY_PATH = PROJECT_ROOT / "wiki" / "pedagogy" / "a1" / "sounds-letters-and-hello.sources.yaml"
PLAYBACK_OUTPUT_PATH = PROJECT_ROOT / "wiki" / ".reviews" / "diagnostics" / "a1-sounds-letters-playback.json"
DIAGNOSIS_OUTPUT_PATH = PROJECT_ROOT / "wiki" / ".reviews" / "diagnostics" / "a1-sounds-letters-and-hello-diagnosis.md"
SUPPORTED_TRACK = "a1"
SUPPORTED_SLUG = "sounds-letters-and-hello"
MAX_EVIDENCE_CHARS = 200

APOSTROPHE_MAP = str.maketrans({
    "’": "'",
    "ʼ": "'",
    "ʹ": "'",
    "`": "'",
    "´": "'",
    "՚": "'",
})

BASE_TARGET_CONCEPTS: dict[str, list[str]] = {
    "syllable_count_rule": [
        "скільки в слові голосних, стільки й складів",
        "стільки складів",
        "число складів",
        "кількість складів",
    ],
    "larynx_touch_exercise": [
        "гортань",
        "поклади руку на горло",
        "відчуй вібрацію",
        "положи руку",
    ],
    "final_voicing": [
        "дзвінкі приголосні в кінці",
        "не оглушуються",
        "зберігають дзвінкість",
        "оглушення",
    ],
    "v_to_w_rule": [
        "[ў]",
        "білабіальн",
        "губно-губн",
        "лев — [леў]",
        "перетворюється на [ў]",
    ],
    "yi_letter_two_sounds": [
        "ї позначає два звуки",
        "[йі]",
        "буква ї",
    ],
    "ya_yu_ye_dual": [
        "я, ю, є позначають",
        "[йа]",
        "[йу]",
        "[йе]",
        "пом'якшує попередній приголосний",
    ],
    "milozvuchnist": [
        "милозвучність",
        "евфонія",
        "уникає важких збігів",
    ],
    "g_ge_history": [
        "вилучення літери ґ",
        "повернення літери ґ",
    ],
    "sound_before_letter": [
        "звук перед буквою",
        "спочатку звук, потім літера",
        "фонематичний підхід",
    ],
    "vowel_consonant_definition": [
        "голосні утворюються",
        "приголосні утворюються",
        "за допомогою голосу",
        "лежить шум",
    ],
}

ADDED_VARIANTS: dict[str, list[str]] = {
    "syllable_count_rule": [
        "у слові стільки складів, скільки голосних звуків",
        "стільки складів, скільки голосних",
    ],
    "larynx_touch_exercise": [
        "покладіть пальці на гортань",
        "поклади пальці на гортань",
        "відчули напруження голосових зв'язок",
    ],
    "final_voicing": [
        "вимовляються дзвінко",
        "не можна оглушувати",
        "вимовляємо чітко",
        "дзвінкі приголосні звуки в кінці слова і складу",
    ],
    "v_to_w_rule": [
        "звук [в] треба вимовляти ніби короткий голосний [ў]",
        "у кінці слова: лев [леў]",
        "був [буў]",
        "у кінці слова",
        "перед приголосним",
    ],
    "yi_letter_two_sounds": [
        "буква ї завжди позначає два звуки",
    ],
    "ya_yu_ye_dual": [
        "букви я, ю, є позначають",
        "після приголосних букви я, ю, є позначають один звук",
        "позначають два звуки: [йа], [йу], [йе]",
    ],
    "milozvuchnist": [
        "милозвучність української мови",
        "забезпечує милозвучність мови",
        "уникаємо збігу голосних або приголосних",
        "чергування у-в та і-й",
    ],
    "g_ge_history": [
        "у правописі 1933 року",
        "літеру ґ було вилучено",
        "літеру ґ було повернуто",
        "повернули літеру ґ",
    ],
    "sound_before_letter": [
        "букви — це умовні знаки, які позначають звуки мови",
        "букви ми бачимо, читаємо і пишемо",
        "звуки ми чуємо",
        "звуки вимовляємо",
        "букви бачимо",
    ],
    "vowel_consonant_definition": [
        "голосні звуки утворюються за допомогою голосу",
        "приголосні звуки утворюються за допомогою голосу та шуму",
        "голос і шум",
    ],
}

TARGET_CONCEPTS: dict[str, list[str]] = {
    key: BASE_TARGET_CONCEPTS[key] + ADDED_VARIANTS.get(key, [])
    for key in BASE_TARGET_CONCEPTS
}


def normalize_text(text: str) -> str:
    """Normalize apostrophes, spacing, and case for concept matching."""
    text = unicodedata.normalize("NFKC", text).translate(APOSTROPHE_MAP)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def extract_ukrainian_keywords(discovery: dict[str, Any]) -> list[str]:
    keywords: set[str] = set()
    for keyword in discovery.get("query_keywords", []):
        if all(ord(ch) < 256 for ch in keyword.replace(" ", "")):
            continue
        for word in keyword.split():
            if any("\u0400" <= ch <= "\u04FF" for ch in word) and len(word) >= 4:
                cleaned = word.strip(".,;:!?\"'«»()—–-`*_")
                if len(cleaned) >= 4:
                    keywords.add(cleaned.lower())
    return sorted(keywords)


def build_concept_result() -> dict[str, Any]:
    return {
        "present_in_returned_41": False,
        "chunks_containing": [],
        "evidence_quote": "",
        "present_in_full_corpus": None,
        "corpus_match_count": 0,
        "sample_chunk_ids": [],
        "sample_grades": [],
    }


def find_evidence_snippet(text: str, phrase: str) -> str:
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)
    start = normalized_text.find(normalized_phrase)
    if start == -1:
        return ""
    snippet_start = max(0, start - 60)
    snippet_end = min(len(normalized_text), start + len(normalized_phrase) + 100)
    return normalized_text[snippet_start:snippet_end][:MAX_EVIDENCE_CHARS].strip()


def match_returned_concepts(chunks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    results = {concept: build_concept_result() for concept in TARGET_CONCEPTS}
    for concept, variants in TARGET_CONCEPTS.items():
        for chunk in chunks:
            normalized_text = normalize_text(chunk.get("text", ""))
            for variant in variants:
                normalized_variant = normalize_text(variant)
                if normalized_variant and normalized_variant in normalized_text:
                    result = results[concept]
                    result["present_in_returned_41"] = True
                    chunk_id = chunk.get("chunk_id", "")
                    if chunk_id and chunk_id not in result["chunks_containing"]:
                        result["chunks_containing"].append(chunk_id)
                    if not result["evidence_quote"]:
                        result["evidence_quote"] = find_evidence_snippet(chunk.get("text", ""), variant)
                    break
    return results


def query_full_corpus_for_concept(
    conn: sqlite3.Connection,
    variants: Iterable[str],
) -> dict[str, Any]:
    deduped_rows: dict[str, sqlite3.Row] = {}
    conn.row_factory = sqlite3.Row
    normalized_sql = (
        "replace("
        "replace("
        "replace("
        "replace("
        "replace(text, '’', char(39)), "
        "'ʼ', char(39)), "
        "'ʹ', char(39)), "
        "'`', char(39)), "
        "'´', char(39))"
    )
    candidate_forms: list[str] = []
    for variant in variants:
        normalized_variant = normalize_text(variant)
        if not normalized_variant:
            continue
        for form in {
            normalized_variant,
            normalized_variant.capitalize(),
            normalized_variant.upper(),
        }:
            for apostrophe in ("'", "’", "ʼ", "ʹ"):
                candidate_forms.append(form.replace("'", apostrophe))

    if not candidate_forms:
        return {
            "present_in_full_corpus": False,
            "corpus_match_count": 0,
            "sample_chunk_ids": [],
            "sample_grades": [],
        }

    unique_forms = list(dict.fromkeys(candidate_forms))
    where = " OR ".join(f"{normalized_sql} LIKE '%' || ? || '%'" for _ in unique_forms)
    rows = conn.execute(
        f"""
        SELECT chunk_id, grade, text
        FROM textbooks
        WHERE {where}
        """,
        tuple(unique_forms),
    ).fetchall()
    normalized_variants = {normalize_text(variant) for variant in variants if normalize_text(variant)}
    for row in rows:
        normalized_text = normalize_text(row["text"])
        if any(variant in normalized_text for variant in normalized_variants):
            deduped_rows[row["chunk_id"]] = row

    ordered_rows = list(deduped_rows.values())
    sample_rows = ordered_rows[:5]
    return {
        "present_in_full_corpus": bool(ordered_rows),
        "corpus_match_count": len(ordered_rows),
        "sample_chunk_ids": [row["chunk_id"] for row in sample_rows],
        "sample_grades": [str(row["grade"]) for row in sample_rows if row["grade"] is not None],
    }


def diagnose_verdict(concepts: dict[str, dict[str, Any]]) -> str:
    returned_present = sum(
        1 for result in concepts.values() if result["present_in_returned_41"]
    )
    full_present = sum(
        1 for result in concepts.values() if result["present_in_full_corpus"]
    )
    if returned_present >= 7:
        return "writer_bottleneck"
    if returned_present < 7 and full_present >= 7:
        return "retrieval_bottleneck"
    if full_present < 7:
        return "corpus_bottleneck"
    return "mixed"


def summarize_counts(concepts: dict[str, dict[str, Any]]) -> tuple[int, int, int]:
    returned_present = sum(
        1 for result in concepts.values() if result["present_in_returned_41"]
    )
    absent_returned_but_present_corpus = sum(
        1
        for result in concepts.values()
        if not result["present_in_returned_41"] and result["present_in_full_corpus"]
    )
    absent_corpus = sum(
        1 for result in concepts.values() if not result["present_in_full_corpus"]
    )
    return returned_present, absent_returned_but_present_corpus, absent_corpus


def format_grades(result: dict[str, Any]) -> str:
    if result["present_in_returned_41"]:
        chunk_grades = result.get("returned_sample_grades", [])
        if chunk_grades:
            return ", ".join(chunk_grades)
    if result["sample_grades"]:
        return ", ".join(result["sample_grades"])
    return "—"


def build_recommendation(verdict: str, concepts: dict[str, dict[str, Any]]) -> list[str]:
    missing_concepts = [
        name for name, result in concepts.items() if not result["present_in_full_corpus"]
    ]
    retrieval_only_concepts = [
        name
        for name, result in concepts.items()
        if not result["present_in_returned_41"] and result["present_in_full_corpus"]
    ]
    if verdict == "writer_bottleneck":
        return [
            "Returned chunks already cover most target concepts; fix the writer/reviewer grounding behavior before changing retrieval.",
        ]
    if verdict == "retrieval_bottleneck":
        return [
            "Proceed with the retrieval bakeoff issue; the corpus already contains the missing concepts, but the A1 playback did not surface them.",
            f"Retrieval misses: {', '.join(retrieval_only_concepts)}.",
        ]
    if verdict == "corpus_bottleneck":
        missing = ", ".join(missing_concepts) if missing_concepts else "none"
        return [
            f"File a corpus-ingestion follow-up for: {missing}.",
        ]
    return [
        f"Retrieval-only misses: {', '.join(retrieval_only_concepts) or 'none'}.",
        f"Corpus gaps: {', '.join(missing_concepts) or 'none'}.",
    ]


def render_diagnosis_markdown(
    concepts: dict[str, dict[str, Any]],
    verdict: str,
    returned_count: int,
) -> str:
    present_returned, absent_returned_present_corpus, absent_corpus = summarize_counts(concepts)
    lines = [
        "# Retrieval Diagnosis — a1/sounds-letters-and-hello",
        "",
        "## Summary",
        f"- Concepts present in {returned_count} returned chunks: {present_returned} / 10",
        f"- Concepts absent from {returned_count} but present in full corpus: {absent_returned_present_corpus} / 10",
        f"- Concepts absent from full corpus entirely: {absent_corpus} / 10",
        "",
        "## Verdict",
        verdict,
        "",
        "## Per-concept table",
        f"| Concept | In returned {returned_count}? | In full corpus? | Sample grade(s) |",
        "|---|---|---|---|",
    ]

    for concept, result in concepts.items():
        lines.append(
            "| "
            f"{concept} | "
            f"{'yes' if result['present_in_returned_41'] else 'no'} | "
            f"{'yes' if result['present_in_full_corpus'] else 'no'} | "
            f"{format_grades(result)} |"
        )

    lines.extend(
        [
            "",
            "## Recommendation",
            *[f"- {line}" for line in build_recommendation(verdict, concepts)],
            "",
            "## Notes",
            f"- Playback returned {returned_count} chunk(s); the script logs the actual count instead of assuming 41.",
            "- Added concept variants after inspecting actual chunk wording:",
        ]
    )
    for concept, variants in ADDED_VARIANTS.items():
        lines.append(f"- {concept}: {', '.join(variants)}")
    return "\n".join(lines) + "\n"


def collect_returned_grade_samples(
    chunks: list[dict[str, Any]],
    concepts: dict[str, dict[str, Any]],
) -> None:
    by_chunk_id = {chunk.get("chunk_id"): chunk for chunk in chunks}
    for result in concepts.values():
        grades: list[str] = []
        for chunk_id in result["chunks_containing"]:
            chunk = by_chunk_id.get(chunk_id)
            grade = "" if chunk is None else str(chunk.get("grade", "")).strip()
            if grade and grade not in grades:
                grades.append(grade)
        result["returned_sample_grades"] = grades


def ensure_supported_target(track: str, slug: str) -> None:
    if track != SUPPORTED_TRACK or slug != SUPPORTED_SLUG:
        raise SystemExit(
            f"This diagnostic only supports {SUPPORTED_TRACK}/{SUPPORTED_SLUG}; "
            f"received {track}/{slug}."
        )


def run_diagnostic(track: str, slug: str) -> dict[str, Any]:
    ensure_supported_target(track, slug)
    discovery = load_yaml(DISCOVERY_PATH)
    registry = load_yaml(SOURCE_REGISTRY_PATH)
    ukr_keywords = extract_ukrainian_keywords(discovery)
    returned_chunks = search_textbooks(set(ukr_keywords), max_total=40, track=track)
    concept_results = match_returned_concepts(returned_chunks)
    collect_returned_grade_samples(returned_chunks, concept_results)

    with sqlite3.connect(str(SOURCES_DB_PATH)) as conn:
        for concept, result in concept_results.items():
            if result["present_in_returned_41"]:
                result["present_in_full_corpus"] = True
                result["corpus_match_count"] = len(result["chunks_containing"])
                result["sample_chunk_ids"] = result["chunks_containing"][:5]
                result["sample_grades"] = result["returned_sample_grades"][:5]
                continue
            result.update(query_full_corpus_for_concept(conn, TARGET_CONCEPTS[concept]))

    verdict = diagnose_verdict(concept_results)
    return {
        "track": track,
        "slug": slug,
        "retrieval_query_keywords": ukr_keywords,
        "returned_chunk_count": len(returned_chunks),
        "cited_source_files": [
            source.get("file", "")
            for source in registry.get("sources", [])
            if isinstance(source, dict) and source.get("file")
        ],
        "returned_chunks": [
            {
                "chunk_id": chunk.get("chunk_id", ""),
                "grade": chunk.get("grade", ""),
                "author": chunk.get("author", ""),
                "title": chunk.get("title", ""),
                "score": chunk.get("rank"),
                "text": chunk.get("text", ""),
            }
            for chunk in returned_chunks
        ],
        "concepts": concept_results,
        "verdict": verdict,
    }


def write_outputs(result: dict[str, Any]) -> None:
    PLAYBACK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAYBACK_OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    DIAGNOSIS_OUTPUT_PATH.write_text(
        render_diagnosis_markdown(
            result["concepts"],
            result["verdict"],
            result["returned_chunk_count"],
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", required=True)
    parser.add_argument("--slug", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_diagnostic(track=args.track, slug=args.slug)
    write_outputs(result)
    print(
        f"Wrote {PLAYBACK_OUTPUT_PATH.relative_to(PROJECT_ROOT)} and "
        f"{DIAGNOSIS_OUTPUT_PATH.relative_to(PROJECT_ROOT)} "
        f"(verdict: {result['verdict']}, returned_chunks: {result['returned_chunk_count']})"
    )


if __name__ == "__main__":
    main()
