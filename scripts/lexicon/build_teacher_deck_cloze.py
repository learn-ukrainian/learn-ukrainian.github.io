"""
Build Pre-Generated Cloze Shard for Curated Deck.
Extracts authentic textbook sentences from data/sources.db for all teacher vocabulary words,
generates smart distractors, and writes site/public/lexicon/practice-cloze.teacher.json.
"""

import json
import random
import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INTAKE_JSON = REPO_ROOT / "data/lexicon/intake/private_teacher_lesson_intake_candidates.json"
SOURCES_DB = REPO_ROOT / "data/sources.db"
OUTPUT_PUBLIC_JSON = REPO_ROOT / "site/public/lexicon/practice-cloze.teacher.json"
OUTPUT_SRC_JSON = REPO_ROOT / "site/src/data/lexicon-teacher-cloze.json"

# These cards contain private-teacher content or reference it as a distractor.
# Exclude them before either public artifact is written; the browser-side filter
# remains only as a defense in depth for previously deployed shards.
EXCLUDED_TEACHER_CLOZE_IDS = frozenset(
    {
        "teacher_cloze_57",
        "teacher_cloze_581",
        "teacher_cloze_1521",
    }
)
PRIVATE_TEACHER_LEMMA_MARKERS = frozenset({"alona", "альона", "алёна"})


def contains_private_teacher_name(value: object) -> bool:
    """Return whether a card field contains a private teacher-name marker."""
    if isinstance(value, str):
        normalised = value.casefold()
        return any(marker in normalised for marker in PRIVATE_TEACHER_LEMMA_MARKERS)
    if isinstance(value, dict):
        return any(contains_private_teacher_name(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_private_teacher_name(item) for item in value)
    return False


def public_teacher_lemmas(entries: list[dict[str, object]]) -> list[str]:
    """Select intake lemmas that may contribute to public cards or distractors."""
    return [
        str(entry["lemma"])
        for entry in entries
        if entry.get("lemma") and not contains_private_teacher_name(entry["lemma"])
    ]


def exclude_private_cloze_cards(cards: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return only teacher-cloze cards permitted in public artifacts."""
    return [
        card
        for card in cards
        if card.get("clozeId") not in EXCLUDED_TEACHER_CLOZE_IDS
        and not contains_private_teacher_name(card)
    ]


def main():
    if not INTAKE_JSON.exists() or not SOURCES_DB.exists():
        print(f"Error: Missing {INTAKE_JSON} or {SOURCES_DB}")
        return

    with open(INTAKE_JSON, encoding="utf-8") as f:
        teacher_cand = json.load(f)

    teacher_entries = teacher_cand.get("auto_merge", [])
    teacher_lemmas = public_teacher_lemmas(teacher_entries)

    conn = sqlite3.connect(SOURCES_DB)

    extracted_cloze = []
    cloze_count = 0

    all_target_words = []

    for lemma in teacher_lemmas:
        clean_lemma = re.sub(r"[\(\),;\-:=]", " ", lemma).strip()
        words = clean_lemma.split()
        if not words:
            continue
        target_word = words[-1]
        if len(target_word) >= 2:
            all_target_words.append(target_word)

    for lemma in teacher_lemmas:
        clean_lemma = re.sub(r"[\(\),;\-:=]", " ", lemma).strip()
        words = clean_lemma.split()
        if not words:
            continue
        target_word = words[-1]
        if len(target_word) < 2:
            continue

        try:
            cursor = conn.execute(
                "SELECT text FROM textbooks_fts WHERE text MATCH ? LIMIT 5",
                (f'"{target_word}"',),
            )
            rows = cursor.fetchall()
        except Exception:
            continue

        found_sentence = None
        matched_word = None

        for row in rows:
            text = row[0]
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for s in sentences:
                s_clean = s.strip()
                if 15 <= len(s_clean) <= 150 and target_word.lower() in s_clean.lower():
                    tokens = re.findall(r"[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\-]+", s_clean)
                    for t in tokens:
                        if target_word.lower() in t.lower():
                            found_sentence = s_clean
                            matched_word = t
                            break
                if found_sentence:
                    break
            if found_sentence:
                break

        if not (found_sentence and matched_word):
            matched_word = target_word
            found_sentence = f"Ключове слово для вивчення в цьому розділі: «{matched_word}»."

        blanked = found_sentence.replace(matched_word, "_____")
        cloze_count += 1

        # Select 3 distractors
        distractor_pool = [w for w in all_target_words if w.lower() != target_word.lower()]
        random.seed(cloze_count)
        distractor_samples = random.sample(distractor_pool, min(3, len(distractor_pool)))

        options = [
            {"optionId": "opt_ans", "lemmaId": lemma, "label": matched_word, "kind": "answer"}
        ] + [
            {"optionId": f"opt_dec_{idx}", "lemmaId": d.lower(), "label": d, "kind": "distractor"}
            for idx, d in enumerate(distractor_samples)
        ]

        extracted_cloze.append(
            {
                "clozeId": f"teacher_cloze_{cloze_count}",
                "lemmaId": lemma,
                "sentenceFrameId": f"teacher_frame_{cloze_count}",
                "lemma": target_word.lower(),
                "form": matched_word,
                "sentence": blanked,
                "blankCase": "context",
                "caseRule": {
                    "code": "teacher-lesson",
                    "labelUk": "Відібрана добірка",
                    "labelEn": "Teacher Lesson Context",
                    "caseLabel": "знахідний",
                },
                "clozeEn": f"Context sentence for {lemma}",
                "options": options,
            }
        )

    payload = {"cloze": exclude_private_cloze_cards(extracted_cloze)}

    OUTPUT_PUBLIC_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PUBLIC_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    OUTPUT_SRC_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SRC_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {len(payload['cloze'])} Cloze items -> {OUTPUT_PUBLIC_JSON} and {OUTPUT_SRC_JSON}")

if __name__ == "__main__":
    main()
