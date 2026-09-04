"""
Build Pre-Generated Cloze Shard for Curated Deck.
Extracts authentic textbook sentences from data/sources.db for all teacher vocabulary words,
generates smart distractors, and writes site/public/lexicon/practice-cloze.teacher.json.
"""

import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lexicon.relation_pairs import normalize_relation_word
from scripts.verification.vesum import verify_lemma

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


def find_cloze_sentence(texts: list[str], forms: set[str]) -> tuple[str, str] | None:
    """Blank one complete, VESUM-attested token, never a substring or other lemma."""
    for text in texts:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            if not 15 <= len(sentence) <= 150 or "__" in sentence:
                continue
            for token in re.finditer(r"[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\u0300\u0301\-]+", sentence):
                if normalize_relation_word(token.group()) in forms:
                    return (
                        sentence[:token.start()] + "_____" + sentence[token.end():],
                        token.group(),
                    )
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Build teacher cloze from textbook sentences and VESUM forms. "
        "Use for an authorized full rebuild, not a surgical update of the published deck.",
        epilog="Example: /home/ops/learn-ukrainian/.venv/bin/python -m "
        "scripts.lexicon.build_teacher_deck_cloze --sources-db data/sources.db "
        "--vesum-db data/vesum.db\n"
        "Outputs: both teacher-cloze JSON artifacts; no database writes.\n"
        "Exit codes: 0 success; nonzero missing inputs or build failure.\n"
        "Related: scripts/audit/check_teacher_cloze_content.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--sources-db", type=Path, default=SOURCES_DB,
                        help="Textbook SQLite source (default: data/sources.db).")
    parser.add_argument("--vesum-db", type=Path, default=REPO_ROOT / "data/vesum.db",
                        help="VESUM SQLite dictionary (default: data/vesum.db).")
    args = parser.parse_args()
    if not INTAKE_JSON.exists() or not args.sources_db.exists() or not args.vesum_db.exists():
        parser.error("Missing teacher intake, sources database, or VESUM database")

    with open(INTAKE_JSON, encoding="utf-8") as f:
        teacher_cand = json.load(f)

    teacher_entries = teacher_cand.get("auto_merge", [])
    teacher_lemmas = public_teacher_lemmas(teacher_entries)

    conn = sqlite3.connect(f"file:{args.sources_db.resolve()}?mode=ro", uri=True)

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

        # Filtering must not renumber later candidates from the same intake.
        cloze_count += 1
        forms = {
            normalize_relation_word(row["word_form"])
            for row in verify_lemma(target_word, db_path=args.vesum_db)
        } - {None}
        if not forms:
            continue

        cursor = conn.execute(
            "SELECT text FROM textbooks_fts WHERE text MATCH ? LIMIT 5",
            ('"' + target_word.replace('"', '""') + '"',),
        )
        rows = cursor.fetchall()

        match = find_cloze_sentence([row[0] for row in rows], forms)
        if match is None:
            continue
        blanked, matched_word = match

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

    conn.close()
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
