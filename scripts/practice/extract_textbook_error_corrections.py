#!/usr/bin/env python3
"""Extract intentional error-correction exercises from Ukrainian textbooks and style guides.

Also provides guardrail classifiers to prevent naive cloze/reading pipelines from ingesting
deliberate pedagogical errors from textbook exercise prompts.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

# Trigger patterns that identify deliberate pedagogical error prompts/tables
ERROR_CONTEXT_PATTERNS = [
    re.compile(r"(?i)\b(?:виправте|виправляючи|відредагуйте|відредагувати|знайдіть\s+помилк\w*|помилково\s+вжито|уникайте\s+помилок|антисуржик|культура\s+слова|культура\s+мовлення)\b"),
    re.compile(r"(?i)\bНЕПРАВИЛЬНО\b[\s\S]{1,100}\bПРАВИЛЬНО\b"),
    re.compile(r"(?i)\bпомилк[а-я]*\s+у\s+(?:слововживанні|будові|узгодженні|керуванні)\b"),
    re.compile(r"(?i)\bвставте\s+пропущен[іі]\s+(?:букви|літери)\b"),
    re.compile(r"(?i)\bрозкрийте\s+дужки\b"),
]


def is_intentional_error_context(text: str) -> bool:
    """Return True if the text belongs to an intentional error exercise or contrastive table."""
    if not text or not isinstance(text, str):
        return False
    return any(p.search(text) for p in ERROR_CONTEXT_PATTERNS)


def parse_contrastive_textbook_tables(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Extract contrastive (НЕПРАВИЛЬНО -> ПРАВИЛЬНО) pairs from school textbooks."""
    query = """
    SELECT grade, author, title, text
    FROM textbooks
    WHERE text LIKE '%НЕПРАВИЛЬНО%' AND text LIKE '%ПРАВИЛЬНО%'
    """
    results = []
    seen = set()

    for grade, author, title, text in conn.execute(query):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        in_table = False
        for line in lines:
            if "НЕПРАВИЛЬНО" in line and "ПРАВИЛЬНО" in line:
                in_table = True
                continue
            if not in_table:
                continue

            # Stop when a new exercise or heading starts
            if re.match(r"^\d+[\.\)]\s*", line) or (line.isupper() and len(line) > 10):
                in_table = False
                continue

            # A contrastive table row typically has two columns separated by whitespace
            parts = re.split(r"\s{2,}|\t+", line)
            if len(parts) == 2:
                bad, good = parts[0].strip(), parts[1].strip()
            else:
                # Try single whitespace split on plausible 2-word/phrase boundaries
                tokens = line.split()
                if len(tokens) == 2:
                    bad, good = tokens[0], tokens[1]
                elif len(tokens) == 4 and len(tokens[0]) > 2:
                    bad, good = " ".join(tokens[:2]), " ".join(tokens[2:])
                else:
                    continue

            # Clean and validate
            bad = bad.strip("-• ")
            good = good.strip("-• ")
            if not bad or not good or bad == good:
                continue
            if len(bad) > 60 or len(good) > 60:
                continue

            pair_key = (bad.lower(), good.lower())
            if pair_key in seen:
                continue
            seen.add(pair_key)

            results.append({
                "source": f"Textbook Gr {grade} ({author or title})",
                "error": bad,
                "correct": good,
                "category": "lexical_norm",
                "grade": grade,
            })

    return results


def parse_style_guide_entries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Extract stylistic corrections and explanations from Antonenko-Davydovych."""
    query = """
    SELECT word, section, text
    FROM style_guide
    """
    results = []
    seen = set()

    for word, section, text in conn.execute(query):
        # Look for explicit quotation contrast patterns in text
        # e.g. Неправильно: ... а треба ... / Замість ... слід казати ...
        matches = re.findall(r"(?i)(?:не\s+можна\s+казати|замість|неправильно)[^«\"']*[«\"']([^»\"']+)[»\"'][^«\"']*(?:слід|треба|правильно)[^«\"']*[«\"']([^»\"']+)[»\"']", text)
        for bad, good in matches:
            bad = bad.strip()
            good = good.strip()
            if not bad or not good or bad.lower() == good.lower():
                continue
            pair_key = (bad.lower(), good.lower())
            if pair_key in seen:
                continue
            seen.add(pair_key)

            # First sentence of text as explanation
            first_sent = text.split(".")[0].strip().replace("\n", " ")
            explanation = first_sent if len(first_sent) < 160 else f"Норма слововживання: {word}"

            results.append({
                "source": f"Antonenko-Davydovych: {word} ({section})",
                "error": bad,
                "correct": good,
                "explanation": explanation,
                "category": "style_norm",
            })

    return results


def create_error_correction_drill(
    error_phrase: str,
    correct_phrase: str,
    explanation: str | None = None,
    source: str = "textbook",
) -> dict[str, Any]:
    """Format an error-correction drill conforming to ErrorCorrectionItemProps."""
    # Build a natural context sentence around the incorrect phrase
    # If the error is a multi-word phrase, use it directly
    sentence = f"Уважно прочитайте: «{error_phrase}» — тут допущено помилку."
    error_word = error_phrase
    correct_form = correct_phrase

    # Build plausible distractors (keep original error + other variants)
    options = [correct_form, error_word]
    if len(options) < 4:
        options.append(f"{correct_form} (застаріле)")
    if len(options) < 4:
        options.append(f"{error_word} (розм.)")

    expl = explanation or f"Правильно вживати «{correct_form}» замість помилкового «{error_phrase}»."

    return {
        "sentence": sentence,
        "errorWord": error_word,
        "correctForm": correct_form,
        "options": sorted(options),
        "explanation": expl,
        "isUkrainian": True,
        "source": source,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract error-correction drills from textbooks and style guide.")
    parser.add_argument("--db", type=Path, default=Path("data/sources.db"), help="Path to sources.db")
    parser.add_argument("--export-json", type=Path, help="Export extracted drills to JSON file")
    parser.add_argument("--check-string", type=str, help="Test if string is intentional error context")
    args = parser.parse_args()

    if args.check_string:
        flag = is_intentional_error_context(args.check_string)
        print(f"Is intentional error context: {flag}")
        return

    conn = sqlite3.connect(args.db)
    textbook_pairs = parse_contrastive_textbook_tables(conn)
    style_pairs = parse_style_guide_entries(conn)

    print(f"Extracted {len(textbook_pairs)} textbook contrastive pairs.")
    print(f"Extracted {len(style_pairs)} style-guide contrastive pairs.")

    all_drills = []
    for item in textbook_pairs:
        all_drills.append(create_error_correction_drill(
            item["error"],
            item["correct"],
            source=item["source"],
        ))
    for item in style_pairs:
        all_drills.append(create_error_correction_drill(
            item["error"],
            item["correct"],
            explanation=item.get("explanation"),
            source=item["source"],
        ))

    print(f"Total error-correction drills synthesized: {len(all_drills)}")

    if args.export_json:
        args.export_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump({"drills": all_drills}, f, ensure_ascii=False, indent=2)
        print(f"Exported drills to {args.export_json}")


if __name__ == "__main__":
    main()
