"""Writer-driven vocabulary generation for the словник tab.

The writer produces vocabulary YAML after writing module content.
This module handles deduplication and VESUM enrichment.

Architecture:
  WRITE (prose) → VOCAB GEN (writer outputs YAML) → DEDUPE → VESUM → словник

Issue: #1025
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"

# Ukrainian POS labels
_POS_LABELS = {
    "noun": "ім.",
    "verb": "дієсл.",
    "adj": "прикм.",
    "adv": "присл.",
    "numr": "числ.",
    "prep": "прийм.",
    "conj": "спол.",
    "part": "част.",
    "intj": "виг.",
    "pron": "займ.",
}

_GENDER_MAP = {":m:": "ч.", ":f:": "ж.", ":n:": "с."}


def dedupe_vocab(
    current: list[dict], previous_words: set[str]
) -> list[dict]:
    """Remove words already taught in previous modules.

    Case-insensitive matching. Returns filtered list.
    """
    previous_lower = {w.lower() for w in previous_words}
    return [
        entry for entry in current
        if entry.get("word", "").lower() not in previous_lower
    ]


def vesum_enrich_entry(entry: dict) -> dict:
    """Add POS, gender, stress, and VESUM verification to a vocabulary entry.

    Skips expressions (multi-word phrases) for VESUM lookup.
    After VESUM lookup, runs stress annotation on the word field.
    Flags words NOT found in VESUM with ``verified: false``.

    Returns the entry with added 'pos', 'gender', 'verified' fields
    and stress-annotated 'word'.
    """
    result = dict(entry)
    result.setdefault("pos", "")
    result.setdefault("gender", "")

    # Skip expressions — VESUM doesn't have multi-word entries
    if entry.get("expression"):
        result["verified"] = True  # expressions skip VESUM check
        return result

    word = entry.get("word", "").strip("?!.,")
    if not word:
        result["verified"] = False
        return result

    found_in_vesum = False

    if VESUM_DB.exists():
        try:
            db = sqlite3.connect(str(VESUM_DB))
            try:
                row = db.execute(
                    "SELECT pos, tags FROM forms WHERE word_form = ? LIMIT 1",
                    (word.lower(),),
                ).fetchone()
                if not row:
                    # Try lemma lookup
                    row = db.execute(
                        "SELECT pos, tags FROM forms WHERE lemma = ? LIMIT 1",
                        (word.lower(),),
                    ).fetchone()
                if row:
                    found_in_vesum = True
                    result["pos"] = _POS_LABELS.get(row[0], "")
                    if row[0] == "noun":
                        for tag, label in _GENDER_MAP.items():
                            if tag in row[1]:
                                result["gender"] = label
                                break
            finally:
                db.close()
        except Exception:
            pass

    result["verified"] = found_in_vesum
    if not found_in_vesum:
        logger.debug("vocab: word %r not found in VESUM — flagged verified=false", word)

    # Add stress marks to the word
    try:
        from pipeline.stress_annotator import annotate_stress
        stressed_word, count = annotate_stress(word)
        if count > 0:
            result["word"] = stressed_word
    except Exception:
        pass  # Stress annotation is best-effort

    return result


def get_previous_vocab(level: str, current_seq: int) -> set[str]:
    """Collect all vocabulary from previous modules' vocab files.

    Reads vocabulary/{slug}.yaml files for modules with sequence < current_seq.
    Falls back to plan vocabulary_hints if no vocab file exists.
    """
    plans_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level
    vocab_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / level / "vocabulary"

    if not plans_dir.is_dir():
        return set()

    previous: set[str] = set()

    for plan_file in plans_dir.glob("*.yaml"):
        try:
            plan = yaml.safe_load(plan_file.read_text("utf-8"))
            if not isinstance(plan, dict):
                continue
            seq = plan.get("sequence", 999)
            if seq >= current_seq:
                continue
            slug = plan.get("slug", plan_file.stem)

            # Try vocab file first
            vocab_file = vocab_dir / f"{slug}.yaml"
            if vocab_file.exists():
                vocab_data = yaml.safe_load(vocab_file.read_text("utf-8"))
                if isinstance(vocab_data, dict):
                    for entry in vocab_data.get("vocabulary", []):
                        previous.add(entry.get("word", "").lower())
                continue

            # Fall back to plan vocabulary_hints
            hints = plan.get("vocabulary_hints", {})
            for category in ("required", "recommended"):
                for item in hints.get(category, []):
                    # Parse "мама (mother)" format
                    word = str(item).split("(")[0].strip().lower()
                    if word:
                        previous.add(word)
        except Exception:
            continue

    return previous


def parse_vocab_yaml(raw: str) -> list[dict]:
    """Parse vocabulary YAML from writer output.

    Handles both ```yaml``` blocks and raw YAML.
    Returns list of vocabulary entries.
    """
    import re

    # Extract from ```yaml``` block if present
    match = re.search(r"```yaml\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        raw = match.group(1)

    # Try parsing
    try:
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and "vocabulary" in data:
            return data["vocabulary"]
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return []


def _stress_word(word: str) -> str:
    """Add stress mark to a word for display in the slovnyk table.

    Best-effort: returns the original word if stress annotation fails.
    """
    try:
        from pipeline.stress_annotator import annotate_stress
        stressed, count = annotate_stress(word)
        if count > 0:
            return stressed
    except Exception:
        pass
    return word


def build_slovnyk_markdown(
    plan_vocab: list[dict],
    additional_vocab: list[dict],
    expressions: list[dict],
) -> str:
    """Build the словник tab: dictionary table + interactive FlashcardDeck below.

    Structure:
    1. Markdown tables (reference dictionary)
    2. FlashcardDeck (interactive practice)
    3. Expressions table
    """
    GENDER_COLORS = {
        "ч.": "#0057B8", "м.": "#0057B8",
        "ж.": "#C2185B", "ф.": "#C2185B",
        "с.": "#E65100", "н.": "#E65100",
    }

    lines = []

    # 1. Dictionary tables
    if plan_vocab:
        lines.extend([
            "",
            "### Обов'язкові та рекомендовані слова",
            "",
            "| Слово | Переклад | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
        ])
        for entry in plan_vocab:
            word = _stress_word(entry.get("word", ""))
            trans = entry.get("translation", "")
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")
            lines.append(f"| **{word}** | {trans} | {pos} | {gender} |")

    if additional_vocab:
        lines.extend([
            "",
            "### Додаткові слова з уроку",
            "",
            "| Слово | Переклад | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
        ])
        for entry in additional_vocab:
            word = _stress_word(entry.get("word", ""))
            trans = entry.get("translation", "")
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")
            lines.append(f"| **{word}** | {trans} | {pos} | {gender} |")

    if expressions:
        lines.extend([
            "",
            "### Вирази",
            "",
            "| Вираз | Переклад |",
            "|-------|----------|",
        ])
        for entry in expressions:
            word = entry.get("word", "")
            trans = entry.get("translation", "")
            lines.append(f"| **{word}** | {trans} |")

    # 2. Interactive flashcards below the tables
    all_words = (plan_vocab or []) + (additional_vocab or [])
    if all_words:
        cards = []
        for entry in all_words:
            word = _stress_word(entry.get("word", ""))
            trans = entry.get("translation", "")
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")

            card_parts = [f'front: "{_esc(word)}", back: "{_esc(trans)}"']
            if pos:
                card_parts.append(f'subtitle: "{_esc(pos)}"')
            if gender:
                card_parts.append(f'tag: "{_esc(gender)}"')
                color = GENDER_COLORS.get(gender, "")
                if color:
                    card_parts.append(f'tagColor: "{color}"')
            cards.append("{ " + ", ".join(card_parts) + " }")

        cards_js = ", ".join(cards)
        lines.extend([
            "",
            "### Картки — Flashcards",
            "",
            f'<FlashcardDeck client:only="react" cards={{[{cards_js}]}} />',
        ])

    lines.append("")
    return "\n".join(lines)


def _esc(s: str) -> str:
    """Escape quotes for JSX string props."""
    return s.replace("\\", "\\\\").replace('"', '\\"')
