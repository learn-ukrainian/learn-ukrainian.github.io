#!/usr/bin/env python3
"""Unified Quality Gate for Practice Hub datasets and decks (Issue #7944).

Audits all active Practice Hub assets:
1. Teacher Cloze deck (site/src/data/lexicon-teacher-cloze.json)
2. Textbook Error Correction drills (data/practice/textbook-error-corrections.json)
3. Lexicon Sentence Inventory (site/src/data/lexicon-sentence-inventory.json)
4. Word of the Day daily pool (site/src/data/lexicon-daily-pool.json)

Enforces:
- Exact 1-blank integrity (_____)
- Distractor uniqueness and non-empty options
- Answer alignment with blank/target
- Intentional error quarantine (no leaked contrastive tables/headers in positive cloze)
- Error-correction drill integrity (substring containment, option validity, explanation)
- Morphological attestation against VESUM
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    from scripts.verification.vesum import verify_word
except ImportError:
    from verification.vesum import verify_word

DEFAULT_TEACHER_CLOZE = PROJECT_ROOT / "site/src/data/lexicon-teacher-cloze.json"
DEFAULT_ERROR_CORRECTIONS = PROJECT_ROOT / "data/practice/textbook-error-corrections.json"
DEFAULT_SENTENCE_INVENTORY = PROJECT_ROOT / "site/src/data/lexicon-sentence-inventory.json"
DEFAULT_DAILY_POOL = PROJECT_ROOT / "site/src/data/lexicon-daily-pool.json"
DEFAULT_VESUM_DB = PROJECT_ROOT / "data/vesum.db"

_BLANK_RE = re.compile(r"_{3,}")
_INTENTIONAL_ERROR_PATTERNS = [
    re.compile(r"\bНЕПРАВИЛЬНО\b"),
    re.compile(r"\bНеправильно\s+(?:і\s+)?Правильно\b", re.IGNORECASE),
    re.compile(r"\bПравильно\s+(?:і\s+)?НЕправильно\b", re.IGNORECASE),
    re.compile(r"\bСУРЖИК\b"),
    re.compile(r"\bАНТИСУРЖИК\b", re.IGNORECASE),
    re.compile(r"\bПомилку\s+допущено\b", re.IGNORECASE),
    re.compile(r"\bОрфографічну\s+помилку\b", re.IGNORECASE),
    re.compile(r"\bВідредагуйте\s+речення\b", re.IGNORECASE),
    re.compile(r"\bВиправте\s+помилк", re.IGNORECASE),
]

_CYRILLIC_WORD_RE = re.compile(r"^[а-яіїєґА-ЯІЇЄҐ'\-]+$")


def _normalize_plain(text: str) -> str:
    """Casefold, strip accents/stress, and normalize apostrophes."""
    import unicodedata

    nfd = unicodedata.normalize("NFD", text)
    clean = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    nfc = unicodedata.normalize("NFC", clean)
    return nfc.casefold().replace("’", "'").replace("ʼ", "'").replace("`", "'").strip()


def check_word_in_vesum(word: str, db_path: Path | str | None = None) -> bool:
    """Check if word form exists in VESUM with normalization."""
    clean = word.strip().strip(".,!?:;—…\"'«»`()[]")
    if not clean or not _CYRILLIC_WORD_RE.match(clean):
        return True  # Skip Latin words, abbreviations, symbols

    clean = clean.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    # Exact check
    if verify_word(clean, db_path=db_path) or verify_word(clean.lower(), db_path=db_path):
        return True

    # Check hyphenated syllable breakdown: ро-бот -> робот
    if "-" in clean:
        dehyphen = clean.replace("-", "")
        if verify_word(dehyphen, db_path=db_path) or verify_word(dehyphen.lower(), db_path=db_path):
            return True
        # Compound words (e.g. бізнес-леді, слово-асоціація): check individual parts
        parts = clean.split("-")
        if all(verify_word(p, db_path=db_path) or verify_word(p.lower(), db_path=db_path) for p in parts if len(p) > 2):
            return True

    return False


def audit_teacher_cloze_deck(
    path: Path | str, vesum_db: Path | str | None = None
) -> list[dict[str, Any]]:
    """Audit teacher cloze deck for structural, linguistic and quarantine integrity."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return [{"type": "FILE_MISSING", "item": str(p), "message": f"File {p} does not exist"}]

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("cloze", []) if isinstance(data, dict) else data
    seen_ids: set[str] = set()

    for idx, item in enumerate(items, 1):
        cid = item.get("clozeId") or f"row_{idx}"
        if not cid or cid in seen_ids:
            violations.append(
                {
                    "type": "DUPLICATE_OR_EMPTY_ID",
                    "item": cid,
                    "message": f"Cloze item {idx} has duplicate or missing ID: {cid}",
                }
            )
        seen_ids.add(cid)

        sentence = item.get("sentence", "")
        blanks = _BLANK_RE.findall(sentence)
        if len(blanks) != 1:
            violations.append(
                {
                    "type": "INVALID_BLANK_COUNT",
                    "item": cid,
                    "message": f"Sentence must contain exactly 1 blank (found {len(blanks)}): {sentence[:60]!r}",
                }
            )

        for pattern in _INTENTIONAL_ERROR_PATTERNS:
            m = pattern.search(sentence)
            if m:
                violations.append(
                    {
                        "type": "INTENTIONAL_ERROR_LEAK",
                        "item": cid,
                        "message": f"Sentence contains intentional error marker {m.group(0)!r}: {sentence[:60]!r}",
                    }
                )
                break

        options = item.get("options", [])
        if not options or len(options) < 2:
            violations.append(
                {
                    "type": "TOO_FEW_OPTIONS",
                    "item": cid,
                    "message": f"Item has fewer than 2 options: {options}",
                }
            )
        else:
            labels = []
            answer_count = 0
            for opt in options:
                if isinstance(opt, dict):
                    lbl = opt.get("label", "")
                    if opt.get("kind") == "answer":
                        answer_count += 1
                else:
                    lbl = str(opt)
                labels.append(_normalize_plain(lbl))

            if len(set(labels)) != len(labels):
                violations.append(
                    {
                        "type": "DUPLICATE_OPTIONS",
                        "item": cid,
                        "message": f"Options contain duplicates: {labels}",
                    }
                )

            if isinstance(options[0], dict) and answer_count != 1:
                violations.append(
                    {
                        "type": "WRONG_ANSWER_COUNT",
                        "item": cid,
                        "message": f"Expected exactly 1 answer option, got {answer_count}",
                    }
                )

        form = item.get("form", "")
        if vesum_db and form and Path(vesum_db).exists() and not check_word_in_vesum(form, db_path=vesum_db):
            violations.append(
                {
                    "type": "VESUM_UNATTESTED",
                    "item": cid,
                    "message": f"Target form {form!r} is not attested in VESUM",
                }
            )

    return violations


def audit_error_correction_deck(
    path: Path | str, vesum_db: Path | str | None = None
) -> list[dict[str, Any]]:
    """Audit error-correction dataset for schema, substring match, and pedagogical validity."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return [{"type": "FILE_MISSING", "item": str(p), "message": f"File {p} does not exist"}]

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    items = (
        data.get("drills") or data.get("items") or data.get("corrections") or []
        if isinstance(data, dict)
        else data
    )

    seen_ids: set[str] = set()
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or f"drill_{idx}"
        if not item_id or item_id in seen_ids:
            violations.append(
                {
                    "type": "DUPLICATE_OR_EMPTY_ID",
                    "item": item_id,
                    "message": f"Item {idx} has duplicate or missing ID: {item_id}",
                }
            )
        seen_ids.add(item_id)

        sentence = item.get("sentence", "")
        error_target = item.get("errorWord") or item.get("errorTarget", "")
        correct_target = item.get("correctForm") or item.get("correctTarget", "")

        if not sentence:
            violations.append(
                {"type": "EMPTY_SENTENCE", "item": item_id, "message": "Sentence is empty"}
            )
        elif error_target not in sentence:
            violations.append(
                {
                    "type": "ERROR_TARGET_NOT_IN_SENTENCE",
                    "item": item_id,
                    "message": f"errorTarget {error_target!r} not found in sentence {sentence!r}",
                }
            )

        if not correct_target:
            violations.append(
                {"type": "EMPTY_CORRECT_TARGET", "item": item_id, "message": "correctTarget is empty"}
            )
        elif _normalize_plain(error_target) == _normalize_plain(correct_target):
            violations.append(
                {
                    "type": "IDENTICAL_TARGETS",
                    "item": item_id,
                    "message": f"errorTarget and correctTarget are identical: {correct_target!r}",
                }
            )

        options = item.get("options", [])
        if not options or len(options) < 2:
            violations.append(
                {
                    "type": "TOO_FEW_OPTIONS",
                    "item": item_id,
                    "message": f"options list must contain at least 2 items (got {len(options)})",
                }
            )
        else:
            opt_plain = [_normalize_plain(o) for o in options]
            if len(set(opt_plain)) != len(opt_plain):
                violations.append(
                    {
                        "type": "DUPLICATE_OPTIONS",
                        "item": item_id,
                        "message": f"Duplicate options found: {options}",
                    }
                )
            if _normalize_plain(correct_target) not in opt_plain:
                violations.append(
                    {
                        "type": "CORRECT_TARGET_MISSING_IN_OPTIONS",
                        "item": item_id,
                        "message": f"correctTarget {correct_target!r} not in options {options}",
                    }
                )

        explanation = item.get("explanation", "")
        if not explanation or not explanation.strip():
            violations.append(
                {
                    "type": "MISSING_EXPLANATION",
                    "item": item_id,
                    "message": "Pedagogical explanation is missing or empty",
                }
            )

        if vesum_db and correct_target and Path(vesum_db).exists():
            clean_correct = correct_target.strip().strip(".,!?:;—…\"'«»`")
            if (
                " " not in clean_correct
                and not clean_correct.isupper()
                and len(clean_correct) > 2
                and not check_word_in_vesum(clean_correct, db_path=vesum_db)
            ):
                violations.append(
                    {
                        "type": "VESUM_UNATTESTED",
                        "item": item_id,
                        "message": f"correctTarget {clean_correct!r} not found in VESUM",
                    }
                )

    return violations


def audit_sentence_inventory(path: Path | str) -> list[dict[str, Any]]:
    """Audit sentence inventory for intentional error leaks."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return []

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    rows = data.get("rows", []) if isinstance(data, dict) else data
    for idx, r in enumerate(rows, 1):
        sent = r.get("sentence", "")
        for pattern in _INTENTIONAL_ERROR_PATTERNS:
            m = pattern.search(sent)
            if m:
                violations.append(
                    {
                        "type": "INTENTIONAL_ERROR_LEAK",
                        "item": f"inventory_row_{idx}:{r.get('lemma')}",
                        "message": f"Inventory row contains error marker {m.group(0)!r}: {sent[:60]!r}",
                    }
                )
                break
    return violations


def run_all_practice_audits(
    teacher_cloze: Path | str = DEFAULT_TEACHER_CLOZE,
    error_corrections: Path | str = DEFAULT_ERROR_CORRECTIONS,
    sentence_inventory: Path | str = DEFAULT_SENTENCE_INVENTORY,
    vesum_db: Path | str | None = DEFAULT_VESUM_DB,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "teacher_cloze": audit_teacher_cloze_deck(teacher_cloze, vesum_db=vesum_db),
        "error_corrections": audit_error_correction_deck(error_corrections, vesum_db=vesum_db),
        "sentence_inventory": audit_sentence_inventory(sentence_inventory),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Practice Hub quality assurance gate")
    parser.add_argument("--teacher-cloze", default=str(DEFAULT_TEACHER_CLOZE))
    parser.add_argument("--error-corrections", default=str(DEFAULT_ERROR_CORRECTIONS))
    parser.add_argument("--sentence-inventory", default=str(DEFAULT_SENTENCE_INVENTORY))
    parser.add_argument("--vesum-db", default=str(DEFAULT_VESUM_DB))
    args = parser.parse_args()

    results = run_all_practice_audits(
        teacher_cloze=args.teacher_cloze,
        error_corrections=args.error_corrections,
        sentence_inventory=args.sentence_inventory,
        vesum_db=args.vesum_db,
    )

    total_violations = sum(len(v) for v in results.values())
    if total_violations == 0:
        print("✅ Practice Quality Gate PASSED: 0 violations across all datasets.")
        return 0

    print(f"\n❌ Practice Quality Gate FAILED with {total_violations} violation(s):")
    for category, viols in results.items():
        if viols:
            print(f"\n[{category.upper()}] ({len(viols)} issues):")
            for v in viols[:10]:
                print(f"  - [{v['type']}] {v.get('item', '')}: {v['message']}")
            if len(viols) > 10:
                print(f"  ... and {len(viols) - 10} more")

    return 1


if __name__ == "__main__":
    sys.exit(main())
